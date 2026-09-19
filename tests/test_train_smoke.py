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
