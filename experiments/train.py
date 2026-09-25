"""Train a small decoder-only Transformer on the world corpus and evaluate it.

    uv run --group train python experiments/train.py --form tagged --seed 0

The model sees an action and must write what follows (``-> Fall tgt:... ``).
It is trained from scratch: it has never seen natural language, and it holds
no knowledge beyond this corpus.

``--invariant holdout`` adds the proposition-4 split (corpus.py): the law
"a division destroys structural modifiers and conserves intrinsic ones" is
demonstrated in training only under ``Cut``, and the split asks for it under
``Drop``/``Push``. ``--invariant control`` is the same corpus with that shape
also present in training, and is the ceiling the holdout arm is read against:
without it, failure to transfer cannot be told apart from a hard split.

Evaluation per held-out split:
- accuracy: the predicted meaning equals the world's, order-invariantly for
  the role-tagged form (via the parser), by exact string for the
  word-order form (whose order is deterministic).
- for the role-tagged form only, the grounding checker is run on every
  prediction (context: the action; core: the world's rules):
  * grounding rate: share of predictions that satisfy the Grounding
    Constraint (charter §11.4 c);
  * wrong predictions are split into fabrications (some predicted event
    is not part of the true result, even allowing dropped slots, or the
    events are true but sequenced in an order the world did not put them
    in) and omissions (every predicted event is true and in order, but
    something is missing).
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
import re
import time
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from framingo import ParseError, parse, parse_one
from framingo import basics, instantiation, scaled, vessels
from framingo.corpus import build
from framingo.knowledge import Store
from framingo.grounding import check, entails
from framingo.render import tokens
from framingo.syntax import Concept, Pipeline, Statement
from framingo.world import core_rules

PAD, BOS, SEP, EOS = "<pad>", "<bos>", "<sep>", "<eos>"
# `--ask`: the model hands over with ASK once its query is written, and the
# harness hands back with GOT once the store has answered. The model writes
# what lies between BOS..ASK and GOT..EOS; the stretch between ASK and GOT is
# the store's, and no loss is taken on it. Training the model to predict the
# answer would be putting the knowledge back into the weights, which is the
# one thing this arrangement exists to avoid.
ASK, GOT = "<ask>", "<got>"


# -- text <-> tokens ---------------------------------------------------------


_SLOT_KEY = re.compile(r"[a-z]+:")
_MARK = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")


def detokenize(toks: list[str]) -> str:
    """Put back together what `render.tokens` took apart.

    Only a lowercase slot key glues to what follows it, because that is the
    only thing `tokens` splits off (`agt:Red.Apple` -> `agt:` `Red` `.`
    `Apple`). A statement's own labels end in a colon too — `QUERY:`,
    `Action:`, `Result:` — and gluing after those would run a query together
    into `QUERY:Action:Cut`, which no longer parses.
    """
    out: list[str] = []
    glue = False
    for t in toks:
        if t == ".":
            out[-1] += "."
            glue = True
        elif glue or (out and _SLOT_KEY.fullmatch(out[-1])):
            out[-1] += t
            glue = False
        else:
            out.append(t)
    return " ".join(out)


class Vocab:
    def __init__(self, texts: list[str]) -> None:
        words = sorted({t for text in texts for t in tokens(text)})
        self.itos = [PAD, BOS, SEP, EOS, ASK, GOT] + words
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


def held_names(splits) -> list[str]:
    order = ("test_iid", "test_role", "test_combo", "test_invariant", "test_unseen")
    named = [n for n in order if splits[n]]
    return named + sorted(k for k in splits if k.startswith("test") and k not in order)


def parts(r, vocab, form, ask: bool, handed: bool = False) -> list[tuple[list[int], bool]]:
    """The sequence as stretches, each marked with whether the model writes it.

    Plainly there are two: the action, then the result. With ``--ask`` there are
    four, and the store's answer is the one stretch the model is not asked to
    predict. ``handed`` is the arrangement the marked vocabulary makes possible
    (spec ch.3 §4bis): the parser has already fetched what every marked word
    means, so there is no query to write and no decision to learn — the lookup
    is simply part of what the model is given.
    """
    fin, fout = fields(form)
    prompt = [vocab.stoi[BOS]] + vocab.encode(getattr(r, fin)) + [vocab.stoi[SEP]]
    result = vocab.encode(getattr(r, fout)) + [vocab.stoi[EOS]]
    if handed and ask:
        # A derivation that stops part way. The model writes as far as the step
        # that brings in a word it does not hold, hands over with ASK, and is
        # given what that word is a kind of. That lookup is the one a parser
        # cannot do in advance: the word did not exist until the model derived
        # it. Loss is taken on what the model writes and on neither handover.
        return [
            (prompt + vocab.encode(r.answer) + [vocab.stoi[GOT]], False),
            (vocab.encode(r.head) + [vocab.stoi[ASK]], True),
            ((vocab.encode(r.handed) if r.handed else []) + [vocab.stoi[GOT]], False),
            ((vocab.encode(r.tail) if r.tail else []) + [vocab.stoi[EOS]], True),
        ]
    if handed:
        return [(prompt + vocab.encode(r.answer) + [vocab.stoi[GOT]], False), (result, True)]
    if not ask:
        return [(prompt, False), (result, True)]
    return [
        (prompt, False),
        (vocab.encode(r.query) + [vocab.stoi[ASK]], True),
        (vocab.encode(r.answer) + [vocab.stoi[GOT]], False),
        (result, True),
    ]


def make_batches(rows, vocab, form, batch_size, rng, ask: bool = False, handed: bool = False):
    seqs = [parts(r, vocab, form, ask, handed) for r in rows]
    rng.shuffle(seqs)
    for i in range(0, len(seqs), batch_size):
        chunk = seqs[i : i + batch_size]
        n = max(sum(len(piece) for piece, _ in s) for s in chunk)
        ids = torch.full((len(chunk), n), vocab.stoi[PAD])
        loss_mask = torch.zeros((len(chunk), n), dtype=torch.bool)
        for j, stretches in enumerate(chunk):
            seq: list[int] = []
            for piece, ours in stretches:
                if ours:
                    # a token at index t is predicted from position t-1
                    loss_mask[j, len(seq) - 1 : len(seq) + len(piece) - 1] = True
                seq += piece
            ids[j, : len(seq)] = torch.tensor(seq)
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


@torch.no_grad()
def generate_asking(model, vocab, rows, store, device, form: str, max_new: int = 64, seed: int = 0):
    """Let the model ask, run *its* question, let it finish — then do it again
    with the wrong answer.

    The store answers the query the model actually wrote, not the one it should
    have written. A model that asks the wrong question gets the wrong answer
    and has to live with it, which is the failure mode worth being able to see;
    handing back the right answer regardless would measure only the second half
    of the task.

    **The second pass is the control this experiment cannot do without.** The
    corpus still pairs an action with its result, so nothing stops a model from
    memorising the physics and treating the answer as scenery: it would then
    score perfectly while retrieving nothing, and every number here would say
    only that the model had learnt the world, which was never in doubt. So each
    prediction is made a second time against another row's answer — real rules,
    for the wrong action, so that what is being tested is whether the answer is
    read at all and not whether the model survives noise. If accuracy holds up
    when the answer is wrong, the retrieval is decorative.
    """
    fin, _ = fields(form)
    ask, got, eos = vocab.stoi[ASK], vocab.stoi[GOT], vocab.stoi[EOS]
    prompts = [[vocab.stoi[BOS]] + vocab.encode(getattr(r, fin)) + [vocab.stoi[SEP]] for r in rows]

    asked = _continue(model, vocab, prompts, device, ask, max_new)
    out = []
    for prompt, written in zip(prompts, asked):
        text = detokenize(vocab.decode(written))
        try:
            statements, failed = list(store.answer(parse_one(text)).statements), False
        except (ParseError, ValueError):
            statements, failed = [], True
        out.append({"query": text, "query_failed": failed, "statements": statements,
                    "head": prompt + written + [ask]})

    # another row's answer, never a row's own
    order = list(range(len(out)))
    random.Random(seed).shuffle(order)
    order = [j if out[j]["statements"] != out[i]["statements"] else (i + 1) % len(out)
             for i, j in enumerate(order)]

    def finish(statements_for):
        heads = [
            o["head"] + vocab.encode(" ".join(str(s) for s in statements_for(i))) + [got]
            if statements_for(i)
            else o["head"] + [got]
            for i, o in enumerate(out)
        ]
        return [detokenize(vocab.decode(w)) for w in _continue(model, vocab, heads, device, eos, max_new)]

    for o, pred, scrambled in zip(
        out, finish(lambda i: out[i]["statements"]), finish(lambda i: out[order[i]]["statements"])
    ):
        o["pred"], o["pred_scrambled"] = pred, scrambled
        del o["head"]
    return out


def _lie_about(handed: str, classes: tuple[str, ...], rng) -> str:
    """The same handover, with every class replaced by one it is not.

    `_scrambled` does this to what the parser hands over before the model has
    written anything. This does it to what comes back *mid-derivation*, in
    answer to the model's own stop, and it is the only control that can say
    whether that second lookup is load-bearing: a model that reads the answer
    follows the lie and gets the wrong tail, a model that had already decided
    the tail from the input is untouched.
    """
    out = []
    for line in handed.split("FACT: "):
        if not line.strip():
            continue
        word, klass = line.split("tgt:")[1].split(" is:")
        wrong = [c for c in classes if c != klass.strip()]
        out.append(f"FACT: State tgt:{word} is:{rng.choice(wrong) if wrong else klass.strip()}")
    return " ".join(out)


_ASKED_CLASS = re.compile(r"is:([A-Za-z][A-Za-z0-9-]*)")
# A container's dictionary line names its material class; the question was
# about the kind. `Clay-Vessel` answers a question about `Vessel`, and the
# store has to know that much to know whether it was asked for what it holds.
_KINDS = {
    klass: (kind,)
    for kind, materials in vessels.CONTAINERS.items()
    for klass in materials
}


def resolve_marked(row, head: str, given: set[str], entries: dict) -> tuple[list, str]:
    """What the harness hands back when the model stops at a word it derived.

    Keyed by what the model can actually write. A marked word is renumbered per
    example (`basics.normalise`), so a store keyed by the world's own names can
    never answer a question about `'C`: the model asked correctly and was
    handed nothing, every time, and then had to guess the rest of the chain.
    What the store holds for this example is what its own handovers say, so the
    entries are built from those. A word the model invented is in neither and
    comes back empty, which is the behaviour that was wanted.
    """
    fresh = [w for w in dict.fromkeys(_MARK.findall(head)) if w not in given]
    local = dict(entries)
    for line in (row.answer + " " + row.handed).split("FACT: "):
        if "tgt:'" in line:
            local["'" + line.split("tgt:'")[1].split()[0]] = "FACT: " + line.strip()
    return fresh, " ".join(local[w] for w in fresh if w in local)


def resolve_query(row, head: str, given: set[str], entries: dict) -> tuple[list, str]:
    """What the store hands back in answer to the model's own question.

    The question is about a class, so what is read out of the model's text is
    the class it named. The store holds the one container this situation
    actually has: asking for a sack where a jug is standing gets nothing, which
    is a fact about the world rather than a punishment, and it is also the one
    condition under which the interesting question can be asked — what does a
    derivation do when what it needs is not to be had.
    """
    asked = _ASKED_CLASS.findall(head)
    if not asked:
        return [], ""
    wanted = asked[-1]
    held = row.handed  # `FACT: State tgt:'C is:Clay-Vessel`
    if not held:
        return [wanted], ""
    kind = held.split(" is:")[1].strip()
    return [wanted], held if wanted in (kind, *_KINDS.get(kind, ())) else ""


@torch.no_grad()
def generate_stopping(
    model, vocab, rows, device, form: str, entries, max_new: int = 48,
    lie_with: tuple[str, ...] = (), seed: int = 0, resolve=resolve_marked,
):
    """Let the model derive, look up what it derived, and let it finish.

    The harness resolves whatever marked words the model's own output brings in
    — not the ones the gold brings in. A model that derives the wrong thing is
    told about the wrong thing and has to live with it, which is the failure
    worth being able to see.

    With ``lie_with``, the same head is finished twice: once from the true
    answer and once from a false one. The head is generated only the once, so
    the two tails differ in nothing but what came back.
    """
    lying = random.Random(f"{seed}-mid-lie")
    fin, _ = fields(form)
    ask, got, eos = vocab.stoi[ASK], vocab.stoi[GOT], vocab.stoi[EOS]
    prompts = [
        [vocab.stoi[BOS]] + vocab.encode(getattr(r, fin)) + [vocab.stoi[SEP]]
        + vocab.encode(r.answer) + [got]
        for r in rows
    ]
    heads = _continue(model, vocab, prompts, device, ask, max_new)
    out = []
    for r, prompt, written in zip(rows, prompts, heads):
        head = detokenize(vocab.decode(written))
        given = set(_MARK.findall(getattr(r, fin) + " " + r.answer))
        fresh, handed = resolve(r, head, given, entries)
        lied = _lie_about(handed, lie_with, lying) if lie_with else ""

        def resume(answer: str) -> list[int]:
            return prompt + written + [ask] + (vocab.encode(answer) if answer else []) + [got]

        out.append(
            {
                "head": head,
                "asked_about": fresh,
                "handed": handed,
                "lied": lied,
                "prompt": resume(handed),
                "prompt_lied": resume(lied),
            }
        )
    for o, written in zip(out, _continue(model, vocab, [o["prompt"] for o in out], device, eos, max_new)):
        o["tail"] = detokenize(vocab.decode(written))
        o["pred"] = (o["head"] + " " + o["tail"]).strip()
        del o["prompt"]
    if lie_with:
        finished = _continue(model, vocab, [o["prompt_lied"] for o in out], device, eos, max_new)
        for o, written in zip(out, finished):
            o["pred_lied"] = (o["head"] + " " + detokenize(vocab.decode(written))).strip()
    for o in out:
        del o["prompt_lied"]
    return out


@torch.no_grad()
def _continue(model, vocab, prompts: list[list[int]], device, stop: int, max_new: int) -> list[list[int]]:
    """Greedy decoding up to ``stop``, which is not included in what is returned.

    Prompts of different lengths go in the same batch. A first version grouped
    by exact length, which is fine while the prompts are a rendered input and
    an answer, and bad once one of them is **the model's own output so far** —
    that varies per example, so batches of 128 became hundreds of batches of
    two, and the evaluation took longer than the training.

    Padding is safe here for the reason a causal model is causal: position t
    attends to positions up to t and no further, so a pad written after a
    prompt cannot reach back into it. Each row keeps its own cursor, reads its
    logits from the token before it, and writes the next token there. Positions
    stay absolute, so nothing shifts and the result is identical to decoding
    each row on its own — which is asserted in `tests/test_train_smoke.py`
    rather than assumed.
    """
    model.eval()
    out: list[list[int]] = [[] for _ in prompts]
    order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]))
    for s in range(0, len(order), 128):
        group = order[s : s + 128]
        cursor = torch.tensor([len(prompts[i]) for i in group], device=device)
        width = min(int(cursor.max()) + max_new, model.max_len)
        ids = torch.full((len(group), width), stop, dtype=torch.long, device=device)
        for row, i in enumerate(group):
            kept = prompts[i][:width]
            ids[row, : len(kept)] = torch.tensor(kept, device=device)
        rows = torch.arange(len(group), device=device)
        done = cursor >= width
        for _ in range(max_new):
            if bool(done.all()):
                break
            logits = model(ids)
            here = cursor.clamp(max=width - 1)
            nxt = logits[rows, here - 1].argmax(-1)
            nxt = torch.where(done, torch.full_like(nxt, stop), nxt)
            ids[rows, here] = nxt
            cursor = torch.where(done, cursor, cursor + 1)
            done |= (nxt == stop) | (cursor >= width)
        for row, i in enumerate(group):
            gen = ids[row, len(prompts[i]) : int(cursor[row])].tolist()
            out[i] = gen[: gen.index(stop)] if stop in gen else gen
    return out


# -- evaluation --------------------------------------------------------------

CORE = parse(core_rules())


def _groups(text: str) -> list[tuple[str, list]]:
    """A result read as a sequence of groups of events that hold at once.

    `&>` joins its two sides into one group (spec ch.4 §1.3): they hold at
    once and neither brings the other about, so which is written first says
    nothing. Everything the graders below ask is asked of groups, never of
    positions, which is what stops the carrier and the carried arriving in
    the other order from counting as a mistake. The connector that opens a
    group is the group's, and it is what says how the group stands to the one
    before it.
    """
    p = parse_one(text).pipeline
    groups: list[tuple[str, list]] = []
    for connector, event in zip(("->",) + p.connectors, p.events):
        if connector == "&>" and groups:
            groups[-1][1].append(event)
        else:
            groups.append((connector, [event]))
    return groups


def _forward(connector: str) -> str:
    """`&>` and `->` both say the group happened; only `!>` says it did not.

    They are not the same claim — `->` asserts causation where `&>` asserts
    none — but the checker accepts either where the core groups the events,
    because skipping a link is permitted and so `->` is read as "not before".
    The grader has to agree with the checker or a fabrication it counts is
    one the checker will never flag, and the detection rate falls for a
    disagreement between two graders rather than for anything a model did.
    """
    return "->" if connector == "&>" else connector


def same_meaning(pred: str, gold: str) -> bool:
    """One meaning told two ways is one meaning.

    Slot order already carries nothing (spec ch.2 §2, and `Event.__eq__`
    follows), and neither does the order inside a group. The connector that
    opens each group does count here, unlike in `is_omission`: writing `->`
    where the world says `&>` is not the world's meaning, even though it
    asserts nothing the core refuses.
    """
    a, b = _groups(pred), _groups(gold)
    return len(a) == len(b) and all(
        ac == bc and sorted(map(str, ae)) == sorted(map(str, be))
        for (ac, ae), (bc, be) in zip(a, b)
    )


def is_omission(pred: str, gold: str) -> bool:
    """Every predicted event is a true event, in the true order, with at most
    some slots left out.

    The connector counts: claiming with ``->`` what the world prevented
    (``!>``) is a fabrication, not an omission. So does the order, for the
    same reason: ``->`` asserts that the left event brought the right one
    about (spec ch.4 §1.1), so a result read back to front — the vase
    shattered and then fell — claims a causal chain that never held, and
    that is a fabrication however true its events are one by one.

    Dropping an event is still an omission: the predicted groups need only
    occur in the gold's order, not consecutively, since ``A -> B -> C``
    licenses the coarser ``A -> C``. Nor need the match be one-to-one: a
    model that claims the same true event twice fabricates no order, and the
    grader leaves that (separate) flaw where it was.
    """
    gold_groups = _groups(gold)
    nouns = frozenset(
        c.segments[-1] for _, events in gold_groups for g in events for c in _slot_concepts(g)
    )

    def weaker(p, g) -> bool:
        # every predicted slot is a gold slot, possibly with modifiers
        # dropped (the same entailment the checker uses)
        return p.verb == g.verb and all(
            any(gk == k and (gv == v or (isinstance(gv, Concept) and isinstance(v, Concept) and entails(gv, v, nouns)))
                for gk, gv in g.slots)
            for k, v in p.slots
        )

    # Walk the gold's groups forwards, never backwards: matching each
    # predicted event to the earliest group it can leaves the longest run of
    # gold for what follows, so if any reading of the prediction respects the
    # order, this one finds it. Within a group there is no order to respect.
    at = 0
    for connector, events in _groups(pred):
        for event in events:
            found = next(
                (
                    i
                    for i in range(at, len(gold_groups))
                    if _forward(gold_groups[i][0]) == _forward(connector)
                    and any(weaker(event, g) for g in gold_groups[i][1])
                ),
                None,
            )
            if found is None:
                return False
            at = found
    return True


def _slot_concepts(event) -> list[Concept]:
    return [v for _, v in event.slots if isinstance(v, Concept)]


def evaluate_asking(rows, fetched: list[dict], form: str) -> dict:
    """Grade a model that fetched its own knowledge, against an empty core.

    The context is the action and *what the model's own query brought back*,
    and the core holds nothing. So the Grounding Constraint is being applied
    exactly as charter chapter 3 arranges it: an output is grounded when it
    traces to what was retrieved, and a model that fetched the wrong thing
    cannot be saved by a core that knew better.
    """
    fin, _ = fields(form)
    n = len(rows)
    correct = parse_fail = grounded = correct_scrambled = 0
    query_exact = query_failed = answer_empty = 0
    fabricated = fabricated_flagged = omitted = benign_flagged = 0
    examples, out = [], []
    for r, got in zip(rows, fetched):
        query_exact += got["query"] == r.query
        query_failed += got["query_failed"]
        answer_empty += not got["statements"]
        try:
            correct_scrambled += same_meaning(
                f"{getattr(r, fin)} {got['pred_scrambled']}", r.meaning
            )
        except (ParseError, ValueError):
            pass
        full = f"{getattr(r, fin)} {got['pred']}"
        out.append({k: got[k] for k in ("query", "pred", "pred_scrambled")})
        try:
            ok = same_meaning(full, r.meaning)
            stmt = parse_one("FACT: " + full)
        except (ParseError, ValueError):
            parse_fail += 1
            fabricated += 1
            fabricated_flagged += 1
            continue
        action = Statement(Pipeline((stmt.pipeline.events[0],)), prefix="FACT")
        report = check([stmt], [action] + list(got["statements"]), ())
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
                examples.append(
                    {"input": getattr(r, fin), "query": got["query"], "asked_for": r.query,
                     "pred": got["pred"], "gold": r.tagged_out, "grounded": report.ok}
                )
        correct += ok
    benign = correct + omitted
    return {
        "n": n,
        "accuracy": correct / n,
        # the control: the same model, answered about a different action. Near
        # the real accuracy means the answer was not being read.
        "accuracy_scrambled": correct_scrambled / n,
        "query_exact_rate": query_exact / n,
        "query_parse_failures": query_failed,
        "empty_answers": answer_empty,
        "parse_failures": parse_fail,
        "grounding_rate": grounded / n,
        "fabricated": fabricated,
        "omitted": omitted,
        "detection_rate": (fabricated_flagged / fabricated) if fabricated else None,
        "false_alarm_rate": (benign_flagged / benign) if benign else None,
        "examples": examples,
        "predictions": out,
    }


def _scrambled(model, vocab, rows, device, form: str, seed: int, classes=None) -> float:
    """Accuracy when the dictionary is made to lie about every marked word.

    The control this corpus cannot do without. A name the model has been
    trained on could have had its class learnt along with it, and a model that
    had done so would score perfectly while consulting nothing — every number
    here would then say only that it had memorised the names. So each
    prediction is made again with every `is:` replaced by a class the word does
    not belong to. Accuracy that survives that is accuracy that was never using
    the lookup.
    """
    rng = random.Random(f"{seed}-scramble")
    classes = sorted(classes if classes is not None else basics.NAMES)
    prompts = []
    for r in rows:
        lied = []
        for line in r.answer.split("FACT: "):
            if not line.strip():
                continue
            word, klass = line.split("tgt:")[1].split(" is:")
            wrong = rng.choice([c for c in classes if c != klass.strip()])
            lied.append(f"FACT: State tgt:{word} is:{wrong}")
        prompt = [vocab.stoi[BOS]] + vocab.encode(getattr(r, fields(form)[0])) + [vocab.stoi[SEP]]
        prompts.append(prompt + vocab.encode(" ".join(lied)) + [vocab.stoi[GOT]])
    correct = 0
    for r, generated in zip(rows, generate(model, vocab, prompts, device)):
        try:
            correct += same_meaning(f"{getattr(r, fields(form)[0])} {detokenize(generated)}", r.meaning)
        except (ParseError, ValueError):
            pass
    return correct / len(rows)


def _plainly(text: str, names: dict) -> str:
    """Put the world's own words back where a variable stands for one.

    A model is shown `'A` and `'B` so that it can learn nothing about any
    particular name. The core is written in words, so grading has to undo that
    before it can ask the core anything. A variable with no way back — one the
    model invented — is left alone, and is then ungrounded, which is what
    should happen to a name nobody handed over.
    """
    if not names:
        return text
    return _MARK.sub(lambda m: names.get(m.group(0), m.group(0)), text)


def _steps(text: str) -> tuple[str, ...]:
    """The verbs of a stretch of pipeline, in order."""
    out = []
    for chunk in re.split(r"(?:->|!>|&>)", text):
        words = chunk.replace("Result:", " ").split()
        if words:
            out.append(words[0])
    return tuple(out)


def evaluate_stopping(rows, fetched: list[dict], form: str, core, tails=None) -> dict:
    """Grade a derivation that stopped part way to look something up.

    Context is the action, what the parser handed over, and what the model's own
    stop brought back — not what the gold would have brought back. The core
    holds the general rules and nothing about any name.
    """
    fin, _ = fields(form)
    n = len(rows)
    correct = parse_fail = grounded = asked_right = 0
    fabricated = fabricated_flagged = omitted = benign_flagged = 0
    # Only the examples where the model's own stop actually brought something
    # back can say anything about whether the answer was used. Scoring the lie
    # over all of them would dilute it with examples that had nothing to lie
    # about, and a number diluted that way looks like robustness.
    handed_back = lied_correct = lied_same = lied_followed = 0
    # Marked words the prediction names that nobody supplied. This is the
    # number the whole business is for: a model that needs something it has not
    # got and writes a name for it anyway is doing what a language model does
    # when it needs a citation and has none.
    invented = 0
    examples, out = [], []
    for r, got in zip(rows, fetched):
        # What should have been asked about: the marked words the derivation
        # brought in, or — where the question is about a class the sentence
        # never mentioned — the class itself, which the record carries.
        wanted = [r.query] if r.query else [
            w for w in dict.fromkeys(_MARK.findall(r.head))
            if w not in set(_MARK.findall(getattr(r, fin) + " " + r.answer))
        ]
        asked_right += got["asked_about"] == wanted
        full = f"{getattr(r, fin)} {got['pred']}"
        out.append({k: got[k] for k in ("head", "handed", "tail", "pred", "asked_about")})
        supplied = set(_MARK.findall(getattr(r, fin) + " " + r.answer + " " + got["handed"]))
        invented += bool(set(_MARK.findall(got["pred"])) - supplied)
        if got["handed"] and "pred_lied" in got:
            handed_back += 1
            lied_same += got["pred_lied"] == got["pred"]
            try:
                lied_correct += same_meaning(f"{getattr(r, fin)} {got['pred_lied']}", r.meaning)
            except (ParseError, ValueError):
                pass
            # Moving is not the same as understanding. A derivation that broke
            # when it was lied to read the answer; one that wrote the tail the
            # lie *implies* read it and applied the rule. Only the second is
            # the behaviour being claimed, so the two are counted apart.
            if tails and got["lied"]:
                state = got["lied"].rsplit(" is:", 1)[-1].split()[0]
                if state in tails:
                    written = _steps(got["pred_lied"][len(got["head"]):])
                    lied_followed += written == tuple(tails[state])
        try:
            ok = same_meaning(full, r.meaning)
            stmt = parse_one("FACT: " + full)
        except (ParseError, ValueError):
            parse_fail += 1
            fabricated += 1
            fabricated_flagged += 1
            continue
        # The core is written in the world's own words and the model was shown
        # variables, so the renaming has to be undone before anything can be
        # checked against it. A variable the model invented has no way back and
        # stays as it is, which leaves it ungrounded — the right answer.
        plain = parse_one("FACT: " + _plainly(full, r.names))
        action = Statement(Pipeline((plain.pipeline.events[0],)), prefix="FACT")
        context = [action] + list(parse(_plainly(r.answer, r.names)))
        if got["handed"]:
            context += list(parse(_plainly(got["handed"], r.names)))
        report = check([plain], context, core)
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
                examples.append({"input": getattr(r, fin), "handed": r.answer,
                                 "asked_about": got["asked_about"], "got": got["handed"],
                                 "pred": got["pred"], "gold": r.tagged_out, "grounded": report.ok})
        correct += ok
    benign = correct + omitted
    return {
        "n": n,
        "accuracy": correct / n,
        "asked_about_the_right_words": asked_right / n,
        "parse_failures": parse_fail,
        "grounding_rate": grounded / n,
        "fabricated": fabricated,
        "omitted": omitted,
        "detection_rate": (fabricated_flagged / fabricated) if fabricated else None,
        "false_alarm_rate": (benign_flagged / benign) if benign else None,
        # How many of those stops brought an answer back, and what became of
        # the derivation when that answer was false. `unmoved_by_the_lie` is
        # the share that came out character for character the same as with
        # the truth — a derivation that never read what it had asked for.
        "handed_back": handed_back,
        "accuracy_when_handed_lies": (lied_correct / handed_back) if handed_back else None,
        "unmoved_by_the_lie": (lied_same / handed_back) if handed_back else None,
        "followed_the_lie": (lied_followed / handed_back) if handed_back else None,
        "named_what_nobody_supplied": invented / n,
        "examples": examples,
        "predictions": out,
    }


def evaluate(rows, predictions: list[str], form: str, core=None, book: str = "") -> dict:
    """Grade predictions, and where a correct one fails to ground, say why.

    `false_alarm_rate` is the share of benign outputs the verifier flags, and
    its name assumes that a correct answer ought to ground. The charter assumes
    the opposite: correctness and groundedness are two signals, and **correct
    but untraceable** is a category the arrangement exists to count, not a
    defect of the verifier. That never showed while the number was zero, which
    it is wherever the model looks its words up. An arm that does not look them
    up puts a fifth of its correct answers there, and calling those false
    alarms would report the verifier working as the verifier failing.

    So the two are separated by asking a second question of each one: would it
    have grounded had the dictionary been in the context? If it would, the flag
    was about a lookup that never happened, and it is a true finding. If it
    would not, something in the core or the checker cannot derive a correct
    derivation, and that is a defect — of which three have been found so far,
    every one by measuring rather than by reading output. `book` is what makes
    the second question askable; without it the two stay added together.
    """
    fin, fout = fields(form)
    n = len(rows)
    correct = parse_fail = grounded = 0
    fabricated = fabricated_flagged = omitted = benign_flagged = 0
    unfetched = underivable = 0
    whole = list(parse(book)) if book else []
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
            names = getattr(r, "names", None) or {}
            plain = parse_one("FACT: " + _plainly(full, names))
            action = Statement(Pipeline((plain.pipeline.events[0],)), prefix="FACT")
            context = [action] + (
                list(parse(_plainly(r.answer, names))) if getattr(r, "answer", "") else []
            )
            rules = CORE if core is None else core
            report = check([plain], context, rules)
            grounded += report.ok

            def split() -> None:
                # the same claim, with everything the dictionary holds in front
                # of it. Grounding now means the flag was about a lookup that
                # did not happen.
                nonlocal unfetched, underivable
                if check([plain], context + whole, rules).ok:
                    unfetched += 1
                else:
                    underivable += 1

            if ok:
                benign_flagged += not report.ok
                if not report.ok and whole:
                    split()
            elif is_omission(full, r.meaning):
                omitted += 1
                benign_flagged += not report.ok
                if not report.ok and whole:
                    split()
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
        if whole:
            result.update(
                # right, but not traceable, because the word was never fetched.
                # The verifier is correct and the name above is not.
                ungrounded_though_correct=unfetched / benign if benign else None,
                # right, traceable in principle, and flagged anyway. This is
                # the only one that is a false alarm.
                flagged_though_derivable=underivable / benign if benign else None,
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
    ap.add_argument("--invariant", choices=("off", "holdout", "control"), default="off")
    # The draw limit is reachable only in principle: `test_role` holds at most
    # 120 distinct meanings (4 agents x 5 destinations x 6 locations), fewer
    # than `n_held`, so the builder's completion test never fires and the loop
    # always runs to this bound. Lowering it changes the random stream and so
    # the corpus, which is why the default stays where the published runs left
    # it; the new arms, having nothing to reproduce, can afford to cut it.
    ap.add_argument("--max-draws", type=int, default=2_000_000)
    ap.add_argument("--n-invariant", type=int, default=500)
    ap.add_argument("--corpus", choices=("world", "instantiation", "basics", "scaled", "vessels"),
                    default="world",
                    help="`instantiation` has no physics in it: only applying the rule that comes back; "
                         "`scaled` is the same world as `basics` at whatever size --classes asks for; "
                         "`vessels` needs something the sentence never mentions")
    ap.add_argument("--rules", type=int, default=150, help="instantiation: rules to train on")
    ap.add_argument("--classes", type=int, default=10, help="scaled: how many classes the world has")
    ap.add_argument("--verbs", type=int, default=4, help="scaled: how many verbs the world has")
    ap.add_argument("--names-per-class", type=int, default=10)
    ap.add_argument("--marked", type=float, default=0.25,
                    help="scaled: share of outcome words carrying the mark; 1.0 makes every "
                         "example exercise the mid-derivation lookup")
    ap.add_argument("--leak", type=float, default=0.0,
                    help="scaled: how often a thing wears the modifier that goes with its class")
    ap.add_argument("--ask", action="store_true",
                    help="the model fetches its own knowledge and the core is graded empty")
    ap.add_argument("--max-len", type=int, default=0, help="0 = 96, or 320 when asking")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default="runs")
    # Two runs on one GPU contend, and a sweep that is already going is worth
    # more than the speed of the run being added to it.
    ap.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    ap.add_argument("--test", type=int, default=1000, help="rows per held-out split")
    ap.add_argument("--empty-store", action="store_true",
                    help="vessels: answer every question with nothing, and see what is written then")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    device = torch.device(
        args.device if args.device != "auto"
        else ("mps" if torch.backends.mps.is_available() else "cpu")
    )

    entries: dict[str, str] = {}
    # Whether the parser hands the dictionary over before the model writes
    # anything. Set here, beside the choice of corpus that decides it, because
    # building the vocabulary already needs to know.
    handed = args.corpus in ("basics", "scaled", "vessels")
    # `basics` is one world written out by hand; `scaled` is the same shape
    # generated at a size. Everything downstream reads them through these three
    # — the dictionary the parser hands over, the core the grading checks
    # against, and the states a mid-derivation lie may draw on — so the two
    # corpora differ nowhere else.
    core_text = basics.core_rules
    lie_with: tuple[str, ...] = ()
    name_classes: list[str] = []
    # What each state leads to, so that grading can ask not just whether the
    # lie moved the derivation but whether it moved it to where the lie points.
    tails: dict[str, tuple[str, ...]] = {}
    if args.corpus == "vessels":
        assert args.ask, "the vessels corpus is only meaningful with --ask"
        records = vessels.build(
            n_train=args.train, n_iid=args.test, n_unseen=args.test, seed=args.data_seed,
        )
        store = None
        core_text = vessels.core_rules
        for line in vessels.dictionary().splitlines():
            entries[line.split("tgt:")[1].split()[0]] = line
        # The lie is told with a container of the other material, so that it is
        # a lie about the only thing the answer is good for.
        lie_with = tuple(sorted({
            klass for materials in vessels.CONTAINERS.values() for klass in materials
        }))
        name_classes = sorted(vessels.names())
        tails = {
            klass: vessels.TAIL[material]
            for materials in vessels.CONTAINERS.values()
            for klass, material in materials.items()
        }
    elif args.corpus in ("basics", "scaled"):
        if args.corpus == "scaled":
            world = scaled.make(
                n_classes=args.classes, n_verbs=args.verbs,
                names_per_class=args.names_per_class, seed=args.data_seed,
                leak=args.leak, marked=args.marked,
            )
            records = scaled.build(
                world, n_train=args.train, n_iid=args.test, n_unseen=args.test,
                seed=args.data_seed,
            )
            dictionary, states = scaled.dictionary(world), world.outcome_class.values()
            core_text = lambda: scaled.core_rules(world)  # noqa: E731
        else:
            records = basics.build(n_train=args.train, seed=args.data_seed)
            dictionary, states = basics.dictionary(), basics.OUTCOME_CLASS.values()
        store = None
        for line in dictionary.splitlines():
            entries[line.split("tgt:")[1].split()[0]] = line
        # The lie is drawn from the states an outcome can really be in, so that
        # nothing but the lookup can tell it from the truth. A lie with a class
        # no outcome ever has would be detectable without reading it.
        lie_with = tuple(sorted(set(states)))
        name_classes = sorted(world.names if args.corpus == "scaled" else basics.NAMES)
        tails = dict(world.tail if args.corpus == "scaled" else basics.TAIL)
    elif args.corpus == "instantiation":
        assert args.ask, "the instantiation corpus is only meaningful with --ask"
        records = instantiation.build(
            n_rules=args.rules,
            facts_per_rule=max(1, args.train // args.rules),
            seed=args.data_seed,
        )
        store = instantiation.store_of(records)
    else:
        records = build(
            n_train=args.train,
            n_iid=2000,
            n_held=1000,
            seed=args.data_seed,
            max_draws=args.max_draws,
            invariant=args.invariant,
            n_invariant=args.n_invariant,
            ask=args.ask,
        )
        store = Store(parse(core_rules()), "core") if args.ask else None
    splits: dict[str, list] = defaultdict(list)
    for r in records:
        splits[r.split].append(r)
    fin, fout = fields(args.form)
    # The store's own words have to be in the vocabulary, or the model could
    # not read an answer even in principle. They are still never a training
    # target (`parts`), so this widens what can be read, not what is learnt.
    texts = [getattr(r, f) for r in splits["train"] for f in (fin, fout)]
    if handed:
        # Every split's handed-over lines, so a held-out name can at least be
        # tokenised. Its embedding stays untrained, which is the honest
        # condition for a word a model has never met.
        texts += [r.answer for r in records] + [getattr(r, fout) for r in records]
        texts += [r.head for r in records] + [r.handed for r in records] + [r.tail for r in records]
    if args.ask:
        # Every split's query and answer, because a model has to be able to
        # *read* what the store hands it. The embeddings of words that occur
        # only in a held-out rule are untrained, which is the honest condition
        # for a symbol a model has no habits about — but it can at least be
        # tokenised, and a model that cannot carry such a symbol across is
        # failing at instantiation rather than at its tokeniser.
        texts += [r.query for r in records] + [r.answer for r in records]
    vocab = Vocab(texts)
    held = held_names(splits)
    if args.corpus == "world":
        for name in held:
            for r in splits[name]:
                for f in (fin, fout):
                    missing = [t for t in tokens(getattr(r, f)) if t not in vocab.stoi]
                    assert not missing, f"{name} uses tokens unseen in training: {missing}"

    max_len = args.max_len or (320 if args.ask else (192 if handed else 96))
    model = GPT(len(vocab.itos), args.d, args.layers, args.heads, max_len=max_len, dropout=args.dropout).to(device)
    params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * math.ceil(len(splits["train"]) / args.batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=steps, pct_start=0.1)

    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        total = count = 0
        for ids, mask in make_batches(splits["train"], vocab, args.form, args.batch, rng, args.ask, handed):
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
    for name in held:
        rows = splits[name]
        if args.ask and handed:
            if args.empty_store:
                # Every question answered with nothing. What a derivation does
                # then is the question this whole arm exists for.
                rows = [replace(r, handed="") for r in rows]
            fetched = generate_stopping(
                model, vocab, rows, device, args.form, entries,
                lie_with=lie_with, seed=args.seed,
                resolve=resolve_query if args.corpus == "vessels" else resolve_marked,
            )
            results[name] = evaluate_stopping(rows, fetched, args.form, parse(core_text()), tails)
        elif args.ask:
            fetched = generate_asking(model, vocab, rows, store, device, args.form, seed=args.seed)
            results[name] = evaluate_asking(rows, fetched, args.form)
        else:
            prompts = [parts(r, vocab, args.form, False, handed)[0][0] for r in rows]
            preds = [detokenize(p) for p in generate(model, vocab, prompts, device)]
            core = parse(core_text()) if handed else None
            results[name] = evaluate(
                rows, preds, args.form, core,
                book="\n".join(entries.values()) if handed else "",
            )
            if handed:
                results[name]["accuracy_scrambled"] = _scrambled(
                    model, vocab, rows, device, args.form, args.seed, name_classes
                )
        line = {k: v for k, v in results[name].items() if k not in ("examples", "predictions")}
        print(name, json.dumps(line), flush=True)

    arm = "" if args.invariant == "off" else f"-{args.invariant}"
    asking = "-ask" if args.ask else ""
    which = "" if args.corpus == "world" else f"-{args.corpus}"
    which += "-empty" if args.empty_store else ""
    if args.corpus == "scaled":
        which += f"-c{args.classes}v{args.verbs}"
        which += f"-leak{args.leak:g}" if args.leak else ""
    out = Path(args.out) / f"{args.form}{which}{asking}{arm}-seed{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"wrote {out}  ({params:,} parameters)")


if __name__ == "__main__":
    main()
