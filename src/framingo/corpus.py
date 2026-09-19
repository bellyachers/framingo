"""Build the proposition-3 corpus: one meaning, two forms, held-out splits.

Splits are decided on meaning, never on surface text, so no test meaning can
leak into training through its other rendering.

- ``train`` / ``test_iid``: random meanings, disjoint.
- ``test_role``: Push or Carry with ``Cat`` as target. Cat appears in training only
  as an agent. A model that binds roles from explicit tags should handle
  this; one that binds roles from position must generalise a positional
  habit to a token it has only seen in the other position.
- ``test_combo``: targets pairing a modifier and base never paired in
  training (``Green.Tomato``, ``Blue.Plate``). Both words occur in training,
  separately.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .render import tagged_pipeline, word_order_pipeline
from .syntax import Concept, Pipeline
from .world import Sample, sample

ROLE_HELD_OUT = "Cat"
COMBOS_HELD_OUT = (("Green", "Tomato"), ("Blue", "Plate"))


def _targets(s: Sample) -> list[Concept]:
    return [v for v in s.action.get("tgt") if isinstance(v, Concept)]


def split_of(s: Sample) -> str | None:
    """Which held-out split a meaning belongs to, if any."""
    for t in _targets(s):
        if t.segments == (ROLE_HELD_OUT,):
            return "test_role"
        for mod, base in COMBOS_HELD_OUT:
            if mod in t.segments and t.segments[-1] == base:
                return "test_combo"
    return None


@dataclass
class Record:
    split: str
    meaning: str
    tagged_in: str
    tagged_out: str
    word_order_in: str
    word_order_out: str
    passive: bool

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def render(s: Sample, split: str, rng: random.Random) -> Record:
    action = Pipeline((s.action,))
    has_both = bool(s.action.get("agt")) and bool(s.action.get("tgt"))
    passive = has_both and rng.random() < 0.5
    return Record(
        split=split,
        meaning=str(s.meaning()),
        tagged_in=tagged_pipeline(action, rng),
        tagged_out=f"{s.connector} {tagged_pipeline(s.result, rng)}",
        word_order_in=word_order_pipeline(action, passive_first=passive),
        word_order_out=f"{s.connector} {word_order_pipeline(s.result)}",
        passive=passive,
    )


def build(
    n_train: int = 20000,
    n_iid: int = 2000,
    n_held: int = 1000,
    seed: int = 0,
    max_draws: int = 2_000_000,
) -> list[Record]:
    """Draw meanings until each split is full, then render each once per form.

    Train meanings may repeat (with fresh renderings), as a real corpus
    would; test meanings are unique and never occur in train.
    """
    rng = random.Random(seed)
    train: list[Sample] = []
    train_meanings: set[str] = set()
    iid: dict[str, Sample] = {}
    held: dict[str, dict[str, Sample]] = {"test_role": {}, "test_combo": {}}

    for _ in range(max_draws):
        full = len(train) >= n_train and len(iid) >= n_iid and all(len(v) >= n_held for v in held.values())
        if full:
            break
        s = sample(rng)
        key = str(s.meaning())
        split = split_of(s)
        if split is not None:
            if len(held[split]) < n_held:
                held[split].setdefault(key, s)
        elif key not in train_meanings and len(iid) < n_iid and rng.random() < 0.1:
            iid.setdefault(key, s)
        elif key not in iid and len(train) < n_train:
            train.append(s)
            train_meanings.add(key)

    out = [render(s, "train", rng) for s in train]
    out += [render(s, "test_iid", rng) for s in iid.values()]
    for name, samples in held.items():
        out += [render(s, name, rng) for s in samples.values()]
    return out


def write(records: list[Record], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(r.to_json() + "\n")
