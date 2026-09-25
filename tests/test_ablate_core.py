"""Tests for experiments/ablate_core.py — the core-coverage ablation.

No model and no corpus are needed: the ablation's machinery is the rule
grouping and the re-scoring, and both are exercised here on a handful of
hand-written outputs. What the tests protect is the experiment's meaning — a
label is ground truth handed in from the world, never something the ablated
core computes — and the two ends of the curve.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from ablate_core import Case, groups, load_core, prepare, random_jobs, rule_tags, score  # noqa: E402

CUT = "Cut agt:John tgt:Apple tool:Knife"
TRUE = Case(*prepare(f"{CUT} -> Become agt:Apple.Slice"), "correct", 1)
FABRICATED = Case(*prepare(f"{CUT} -> Become agt:Apple.Piece"), "fabricated", 1)


def test_rule_tags_name_premise_and_conclusions():
    core = load_core()
    tags = [rule_tags(r) for r in core]
    assert all(any(t.startswith("verb:") for t in tag) for tag in tags)
    # the Ruler rule is the world's only prevented outcome, and the only
    # source of Deform
    ruler = [t for t in tags if "tool:Ruler" in t]
    assert ruler and all({"outcome:prevented", "result:Deform"} <= t for t in ruler)
    assert not any("outcome:prevented" in t for t in tags if "tool:Knife" in t)


def test_every_rule_belongs_to_some_group():
    core = load_core()
    covered = {i for idx in groups(core).values() for i in idx}
    assert covered == set(range(len(core)))


def test_random_subsets_are_the_requested_size_and_reproducible():
    jobs = random_jobs(150, [1.0, 0.5, 0.0], repeats=3, seed=0)
    sizes = {name.split()[1]: len(kept) for name, kept in jobs}
    assert sizes == {"1.0": 150, "0.5": 75, "0.0": 0}
    # one subset each where there is nothing to vary, three where there is
    assert len(jobs) == 1 + 3 + 1
    assert random_jobs(150, [0.5], repeats=3, seed=0) == random_jobs(150, [0.5], repeats=3, seed=0)
    assert random_jobs(150, [0.5], repeats=3, seed=1) != random_jobs(150, [0.5], repeats=3, seed=0)


def test_full_core_separates_the_fabrication_from_the_truth():
    result = score([TRUE, FABRICATED], load_core())
    assert result["detection_rate"] == 1.0
    assert result["false_alarm_rate"] == 0.0
    assert result["discrimination"] == 1.0


def test_empty_core_flags_everything_and_discriminates_nothing():
    """The degenerate end of the curve: detection reads 100% and is worthless."""
    result = score([TRUE, FABRICATED], [])
    assert result["detection_rate"] == 1.0
    assert result["false_alarm_rate"] == 1.0
    assert result["discrimination"] == 0.0


def test_ablation_cannot_relabel_an_output():
    """Ground truth comes from the world; the core only decides the flag.

    If a shrunken core could move an output between the fabricated and the
    benign column, the experiment would be measuring the core against itself.
    """
    cases = [TRUE, FABRICATED]
    for core in ([], load_core()[:20], load_core()):
        result = score(cases, core)
        assert result["fabricated"] == 1
        assert result["benign"] == 1
