"""Train a small decoder-only Transformer on the world corpus and evaluate it.

    uv run --group train python experiments/train.py --form tagged --seed 0

The model sees an action and must write what follows (``-> Fall tgt:... ``).
It is trained from scratch: it has never seen natural language, and it holds
no knowledge beyond this corpus.

Evaluation per held-out split:
- accuracy: the predicted meaning equals the world's, order-invariantly for
  the role-tagged form (via the parser), by exact string for the
  word-order form (whose order is deterministic).
- for the role-tagged form only, the grounding checker is run on every
  prediction (context: the action; core: the world's rules):
  * grounding rate: share of predictions that satisfy the Grounding
    Constraint (charter §11.4 c);
  * wrong predictions are split into fabrications (some predicted event
    is not part of the true result, even allowing dropped slots) and
    omissions (every predicted event is true, but something is missing).
    Only fabrications are hallucinations in the charter's sense; the
    Grounding Constraint accepts omissions by design (abstraction);
  * detection rate: share of fabrications the checker flags (charter ch.8
    proposition 2);
  * false alarms: share of correct or merely incomplete predictions it
    flags.

Torch lives only here, in the optional ``train`` dependency group, so the
language package itself stays dependency-free.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from framingo import ParseError, parse, parse_one
from framingo.corpus import build
from framingo.grounding import check, entails
from framingo.render import tokens
from framingo.syntax import Concept, Pipeline, Statement
from framingo.world import core_rules

PAD, BOS, SEP, EOS = "<pad>", "<bos>", "<sep>", "<eos>"


# -- text <-> tokens ---------------------------------------------------------


def detokenize(toks: list[str]) -> str:
    out: list[str] = []
    glue = False
    for t in toks:
        if t == ".":
            out[-1] += "."
            glue = True
        elif glue or (out and out[-1].endswith(":") and not out[-1].endswith("->")):
            out[-1] += t
            glue = False
        else:
            out.append(t)
    return " ".join(out)


class Vocab:
    def __init__(self, texts: list[str]) -> None:
        words = sorted({t for text in texts for t in tokens(text)})
        self.itos = [PAD, BOS, SEP, EOS] + words
        self.stoi = {t: i for i, t in enumerate(self.itos)}

    def encode(self, text: str) -> list[int]:
        return [self.stoi[t] for t in tokens(text)]

    def decode(self, ids: list[int]) -> list[str]:
        return [self.itos[i] for i in ids]


# -- model -------------------------------------------------------------------


class Block(nn.Module):
    def __init__(self, d: int, heads: int, dropout: float) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d), nn.Dropout(dropout))

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        h = self.ln1(x)
        x = x + self.attn(h, h, h, attn_mask=mask, need_weights=False)[0]
        return x + self.mlp(self.ln2(x))


class GPT(nn.Module):
    def __init__(self, vocab: int, d: int, layers: int, heads: int, max_len: int, dropout: float) -> None:
        super().__init__()
        self.tok = nn.Embedding(vocab, d)
        self.pos = nn.Embedding(max_len, d)
        self.blocks = nn.ModuleList(Block(d, heads, dropout) for _ in range(layers))
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.max_len = max_len

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        n = ids.shape[1]
        mask = torch.triu(torch.ones(n, n, dtype=torch.bool, device=ids.device), diagonal=1)
        x = self.tok(ids) + self.pos(torch.arange(n, device=ids.device))
        for block in self.blocks:
            x = block(x, mask)
        return self.head(self.ln(x))


# -- data --------------------------------------------------------------------


def fields(form: str) -> tuple[str, str]:
    return (f"{form}_in", f"{form}_out")


def make_batches(rows, vocab, form, batch_size, rng):
    fin, fout = fields(form)
    seqs = []
    for r in rows:
        prompt = [vocab.stoi[BOS]] + vocab.encode(getattr(r, fin)) + [vocab.stoi[SEP]]
        target = vocab.encode(getattr(r, fout)) + [vocab.stoi[EOS]]
        seqs.append((prompt, target))
    rng.shuffle(seqs)
    for i in range(0, len(seqs), batch_size):
        chunk = seqs[i : i + batch_size]
        n = max(len(p) + len(t) for p, t in chunk)
        ids = torch.full((len(chunk), n), vocab.stoi[PAD])
        loss_mask = torch.zeros((len(chunk), n), dtype=torch.bool)
        for j, (p, t) in enumerate(chunk):
            seq = p + t
            ids[j, : len(seq)] = torch.tensor(seq)
            loss_mask[j, len(p) - 1 : len(seq) - 1] = True  # predict target tokens only
        yield ids, loss_mask


@torch.no_grad()
def generate(model, vocab, prompts: list[list[int]], device, max_new: int = 48) -> list[list[str]]:
    """Greedy decoding, batched by prompt length so no padding is needed."""
    model.eval()
    by_len: dict[int, list[int]] = defaultdict(list)
    for i, p in enumerate(prompts):
        by_len[len(p)].append(i)
    out: list[list[str]] = [[] for _ in prompts]
    eos = vocab.stoi[EOS]
    for _, idx in by_len.items():
        for s in range(0, len(idx), 256):
            group = idx[s : s + 256]
            ids = torch.tensor([prompts[i] for i in group], device=device)
            done = torch.zeros(len(group), dtype=torch.bool, device=device)
            for _ in range(max_new):
                if ids.shape[1] >= model.max_len:
                    break
                nxt = model(ids)[:, -1].argmax(-1)
                nxt = torch.where(done, torch.full_like(nxt, eos), nxt)
                ids = torch.cat([ids, nxt[:, None]], 1)
                done |= nxt == eos
                if done.all():
                    break
            for row, i in zip(ids.tolist(), group):
                gen = row[len(prompts[i]) :]
                if eos in gen:
                    gen = gen[: gen.index(eos)]
                out[i] = vocab.decode(gen)
    return out


# -- evaluation --------------------------------------------------------------

CORE = parse(core_rules())


def same_meaning(pred: str, gold: str) -> bool:
    a, b = parse_one(pred).pipeline, parse_one(gold).pipeline
    return a.connectors == b.connectors and [e.slots for e in a.events] == [e.slots for e in b.events] and [
        e.verb for e in a.events
    ] == [e.verb for e in b.events]


def _linked(text: str) -> list[tuple[str, object]]:
    """Each event paired with the connector that introduces it."""
    p = parse_one(text).pipeline
    return list(zip(("->",) + p.connectors, p.events))


def is_omission(pred: str, gold: str) -> bool:
    """Every predicted event is a true event with at most some slots left out.

    The connector counts: claiming with ``->`` what the world prevented
    (``!>``) is a fabrication, not an omission.
    """
    gold_events = _linked(gold)
    nouns = frozenset(c.segments[-1] for _, g in gold_events for c in _slot_concepts(g))

    def weaker(p, g) -> bool:
        # every predicted slot is a gold slot, possibly with modifiers
        # dropped (the same entailment the checker uses)
        return p.verb == g.verb and all(
            any(gk == k and (gv == v or (isinstance(gv, Concept) and isinstance(v, Concept) and entails(gv, v, nouns)))
                for gk, gv in g.slots)
            for k, v in p.slots
        )

    return all(any(pc == gc and weaker(p, g) for gc, g in gold_events) for pc, p in _linked(pred))


def _slot_concepts(event) -> list[Concept]:
    return [v for _, v in event.slots if isinstance(v, Concept)]


def evaluate(rows, predictions: list[str], form: str) -> dict:
    fin, fout = fields(form)
    n = len(rows)
    correct = parse_fail = grounded = 0
    fabricated = fabricated_flagged = omitted = benign_flagged = 0
    examples, predictions_out = [], []
    for r, pred in zip(rows, predictions):
        full = f"{getattr(r, fin)} {pred}"
        predictions_out.append(pred)
        if form == "tagged":
            try:
                ok = same_meaning(full, r.meaning)
                stmt = parse_one("FACT: " + full)
            except (ParseError, ValueError):
                parse_fail += 1
                fabricated += 1
                fabricated_flagged += 1  # an unparseable output is rejected outright
                continue
            action = Statement(Pipeline((stmt.pipeline.events[0],)), prefix="FACT")
            report = check([stmt], [action], CORE)
            grounded += report.ok
            if ok:
                benign_flagged += not report.ok
            elif is_omission(full, r.meaning):
                omitted += 1
                benign_flagged += not report.ok
            else:
                fabricated += 1
                fabricated_flagged += not report.ok
                if len(examples) < 8:
                    examples.append({"input": getattr(r, fin), "pred": pred, "gold": getattr(r, fout), "grounded": report.ok})
        else:
            ok = pred == getattr(r, fout)
            if not ok and len(examples) < 5:
                examples.append({"input": getattr(r, fin), "pred": pred, "gold": getattr(r, fout)})
        correct += ok
    result = {"n": n, "accuracy": correct / n}
    if form == "tagged":
        benign = correct + omitted
        result.update(
            parse_failures=parse_fail,
            grounding_rate=grounded / n,
            fabricated=fabricated,
            omitted=omitted,
            detection_rate=(fabricated_flagged / fabricated) if fabricated else None,
            false_alarm_rate=(benign_flagged / benign) if benign else None,
        )
    result["examples"] = examples
    result["predictions"] = predictions_out
    return result


# -- main --------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", choices=("tagged", "word_order"), default="tagged")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data-seed", type=int, default=0)
    ap.add_argument("--train", type=int, default=20000)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default="runs")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    records = build(n_train=args.train, n_iid=2000, n_held=1000, seed=args.data_seed)
    splits: dict[str, list] = defaultdict(list)
    for r in records:
        splits[r.split].append(r)
    fin, fout = fields(args.form)
    vocab = Vocab([getattr(r, f) for r in splits["train"] for f in (fin, fout)])
    for name in ("test_iid", "test_role", "test_combo"):
        for r in splits[name]:
            for f in (fin, fout):
                missing = [t for t in tokens(getattr(r, f)) if t not in vocab.stoi]
                assert not missing, f"{name} uses tokens unseen in training: {missing}"

    model = GPT(len(vocab.itos), args.d, args.layers, args.heads, max_len=96, dropout=args.dropout).to(device)
    params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * math.ceil(len(splits["train"]) / args.batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=steps, pct_start=0.1)

    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        total = count = 0
        for ids, mask in make_batches(splits["train"], vocab, args.form, args.batch, rng):
            ids, mask = ids.to(device), mask.to(device)
            logits = model(ids[:, :-1])
            loss = F.cross_entropy(logits[mask[:, :-1]], ids[:, 1:][mask[:, :-1]])
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            total += loss.item()
            count += 1
        if epoch % 5 == 4 or epoch == args.epochs - 1:
            print(f"epoch {epoch + 1:3}  loss {total / count:.4f}  {time.time() - t0:.0f}s", flush=True)

    results = {"args": vars(args), "params": params, "train_seconds": round(time.time() - t0, 1)}
    for name in ("test_iid", "test_role", "test_combo"):
        rows = splits[name]
        prompts = [[vocab.stoi[BOS]] + vocab.encode(getattr(r, fin)) + [vocab.stoi[SEP]] for r in rows]
        preds = [detokenize(p) for p in generate(model, vocab, prompts, device)]
        results[name] = evaluate(rows, preds, args.form)
        line = {k: v for k, v in results[name].items() if k not in ("examples", "predictions")}
        print(name, json.dumps(line), flush=True)

    out = Path(args.out) / f"{args.form}-seed{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"wrote {out}  ({params:,} parameters)")


if __name__ == "__main__":
    main()
