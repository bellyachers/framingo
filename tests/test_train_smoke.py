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

from train import detokenize  # noqa: E402

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
