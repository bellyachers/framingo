"""Smoke test for experiments/train.py; skipped unless the `train` group is installed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from train import GPT, _continue, detokenize  # noqa: E402

from framingo import parse  # noqa: E402

from framingo.render import tokens  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "-> Fall dst:Floor tgt:Red.Tomato",
        "!> Become agt:Green.Apple.Slice -> Deform reason:Inappropriate.Tool tgt:Round.Green.Apple",
        "Blue.Vase was Push by Cat with Knife",
    ],
)
def test_detokenize_inverts_tokens(text):
    assert detokenize(tokens(text)) == text


@pytest.mark.slow
def test_one_epoch_runs_and_reports_every_split(tmp_path):
    subprocess.run(
        [sys.executable, "-W", "ignore", str(ROOT / "experiments" / "train.py"),
         "--train", "200", "--epochs", "1", "--d", "32", "--layers", "1", "--out", str(tmp_path)],
        check=True, capture_output=True,
    )
    result = json.loads((tmp_path / "tagged-seed0.json").read_text())
    for split in ("test_iid", "test_role", "test_combo"):
        assert 0.0 <= result[split]["accuracy"] <= 1.0
        assert "grounding_rate" in result[split]


# -- asking ------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "QUERY: Action: Cut agt:John tgt:Big.Red.Apple tool:Knife -> Result: ?",
        "RULE: Action: Push tgt:Every.Tall.Blue.Vase -> Fall dst:Floor tgt:It -> Result: Become agt:Blue.Vase.Piece",
        "-> At loc:Hall tgt:Robot &> At loc:Hall tgt:Chef",
    ],
)
def test_detokenize_inverts_tokens_for_a_whole_statement(text):
    """A statement's own labels end in a colon and must not glue to what follows.

    `QUERY:Action:Cut` does not parse, so a model that asked correctly would be
    read as having asked nothing.
    """
    assert detokenize(tokens(text)) == text


def test_the_store_s_answer_is_never_a_training_target():
    """The property the whole arrangement rests on.

    Loss is taken on what the model writes — its query and its result — and
    never on the stretch the store supplied. Take loss there and the model is
    being trained to reproduce knowledge, which is to put the knowledge back
    into the weights that the architecture exists to keep it out of.
    """
    from train import Vocab, parts  # noqa: PLC0415

    from framingo.corpus import build  # noqa: PLC0415

    rows = [
        r
        for r in build(n_train=40, n_iid=5, n_held=5, seed=0, max_draws=40_000,
                       invariant="holdout", n_invariant=5, ask=True)
        if r.split == "train"
    ]
    assert rows and all(r.query and r.answer for r in rows)
    vocab = Vocab(
        [getattr(r, f) for r in rows for f in ("tagged_in", "tagged_out")]
        + [r.query for r in rows]
        + [r.answer for r in rows]
    )
    for r in rows:
        stretches = parts(r, vocab, "tagged", True)
        supervised, seq = [], []
        for piece, ours in stretches:
            if ours:
                supervised += list(range(len(seq), len(seq) + len(piece)))
            seq += piece
        answer_at = len(stretches[0][0]) + len(stretches[1][0])
        answer_span = range(answer_at, answer_at + len(stretches[2][0]))
        assert not set(supervised) & set(answer_span), str(r.query)
        # and the model is asked for both of its own stretches
        assert set(supervised) >= set(range(len(stretches[0][0]), answer_at))


def test_batching_prompts_of_different_lengths_changes_nothing():
    """Decoding is batched across unequal prompts, which is only safe because
    a causal model cannot see past its own position. Asserted rather than
    assumed: the evaluation of every arm goes through here, and a batching
    error would move every number at once and look like a result."""
    import random

    torch.manual_seed(0)
    model = GPT(40, 32, 2, 2, max_len=64, dropout=0.0)
    rng = random.Random(0)
    prompts = [
        [1] + [rng.randrange(3, 40) for _ in range(rng.randrange(3, 12))]
        for _ in range(60)
    ]
    assert len({len(p) for p in prompts}) > 4, "the lengths have to differ for this to test anything"
    stop, device = 2, torch.device("cpu")
    together = _continue(model, None, prompts, device, stop, 12)
    apart = [_continue(model, None, [p], device, stop, 12)[0] for p in prompts]
    assert together == apart


# -- the grader, fed the right answer ----------------------------------------
#
# A grader that scores the gold at less than 1.000 reports the model failing at
# something the harness is doing. It has happened: the vessels corpus's first
# stretch is a *question*, and grading it in as though it were a step of the
# derivation compared a question against a meaning containing none, so every
# output scored zero however good it was — and the run that said so took
# twenty minutes of CPU to say it.
#
# The check is nearly free and catches the whole class, so it is a test.


def _vessel_rows(n=120):
    from framingo import vessels

    from train import evaluate_stopping  # noqa: PLC0415

    records = vessels.build(n_train=20, n_iid=n, n_unseen=0, seed=0)
    rows = [r for r in records if r.split == "test_iid"]
    core = parse(vessels.core_rules())
    tails = {
        klass: vessels.TAIL[material]
        for materials in vessels.CONTAINERS.values()
        for klass, material in materials.items()
    }
    return rows, core, tails, evaluate_stopping


def _as_fetched(rows, tail_of=None, head_of=None):
    out = []
    for r in rows:
        head = head_of(r) if head_of else r.head
        tail = tail_of(r) if tail_of else r.tail
        out.append({
            "head": head, "asked_about": [head.split("is:")[1].strip()],
            "handed": r.handed, "tail": tail, "pred": f"{head} {tail}".strip(),
            "lied": r.handed, "pred_lied": f"{head} {tail}".strip(),
        })
    return out


def test_the_grader_scores_the_gold_derivation_perfectly():
    rows, core, tails, evaluate_stopping = _vessel_rows()
    got = evaluate_stopping(rows, _as_fetched(rows), "tagged", core, tails)
    assert got["accuracy"] == 1.0
    assert got["grounding_rate"] == 1.0
    assert got["asked_about_the_right_words"] == 1.0
    assert got["named_what_nobody_supplied"] == 0.0


def test_the_grader_catches_a_container_nobody_supplied():
    """And catches it twice: the answer is wrong and it does not ground."""
    rows, core, tails, evaluate_stopping = _vessel_rows()

    def invent(r):
        letter = sorted(set(r.names) - {"'A", "'B"})[0]
        return r.tail.replace(letter, "'Z")

    got = evaluate_stopping(rows, _as_fetched(rows, tail_of=invent), "tagged", core, tails)
    assert got["accuracy"] == 0.0
    assert got["grounding_rate"] == 0.0
    assert got["named_what_nobody_supplied"] == 1.0


def test_the_grader_notices_the_wrong_class_being_asked_about():
    rows, core, tails, evaluate_stopping = _vessel_rows()
    fixed = _as_fetched(rows, head_of=lambda r: "-> QUERY: State tgt:? is:Pan")
    got = evaluate_stopping(rows, fixed, "tagged", core, tails)
    # a third of the situations really do want a pan, so this is not zero
    assert 0.2 < got["asked_about_the_right_words"] < 0.45
