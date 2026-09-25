"""The adversary must be sound before its numbers mean anything.

An evasion rate is only worth reading if every mutation counted really is a
mutation: parseable, inside the corpus vocabulary, and on the side of the
fabrication/omission line its class claims. These tests check that for every
class, because a mis-built mutation would report the checker as leakier than
it is and send the next verifier revision after a hole that does not exist.

Skipped unless the `train` group is installed: the adversary imports
``train.same_meaning`` and ``train.is_omission`` deliberately, so that it
classifies a mutation exactly as the training run classifies a prediction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import adversary  # noqa: E402
from train import is_omission, same_meaning  # noqa: E402

from framingo import parse  # noqa: E402
from framingo.world import core_rules  # noqa: E402

CORE = parse(core_rules())
VOCABULARY = adversary.corpus_vocabulary(1000, 0)
N = 5


def tally(mutation_class, seed: int = 0):
    return adversary.run_class(mutation_class, CORE, VOCABULARY, N, seed, 1, 5000)


@pytest.fixture(scope="module", params=adversary.CLASSES, ids=lambda mc: mc.name)
def attacked(request):
    return request.param, tally(request.param)


def test_every_class_finds_its_mutations(attacked):
    """A class that cannot build a legal mutation measures nothing."""
    _, t = attacked
    assert t.valid == N
    assert t.unparseable == 0, "a mutation the parser rejects tests the parser, not the constraint"
    assert t.out_of_vocabulary == 0, "every mutation is built from corpus words by construction"


def test_specimen_is_on_the_side_its_class_claims(attacked):
    """Fabrication classes must fabricate; control classes must only weaken."""
    mc, t = attacked
    full = f"{t.specimen['input']} {t.specimen['mutated']}"
    gold = f"{t.specimen['input']} {t.specimen['gold']}"
    benign = same_meaning(full, gold) or is_omission(full, gold)
    assert benign == (mc.kind == adversary.CONTROL)


def test_the_run_is_reproducible():
    """Two runs at one seed must agree, PYTHONHASHSEED included."""
    mc = adversary.CLASSES[0]
    assert tally(mc).to_json() == tally(mc).to_json()
