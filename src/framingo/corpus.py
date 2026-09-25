"""Build the proposition-3 corpus: one meaning, two forms, held-out splits.

Splits are decided on meaning, never on surface text, so no test meaning can
leak into training through its other rendering.

- ``train`` / ``test_iid``: random meanings, disjoint.
- ``test_role``: Carry with ``Cat`` as the carried. In training Cat is only
  ever the carrier, and so does occur in training outputs (``At tgt:Cat``
  for where the carrier ended up); only its role is new. See world.py for
  why that matters. A model that binds roles from explicit tags should handle
  this; one that binds roles from position must generalise a positional
  habit to a token it has only seen in the other position.
- ``test_combo``: targets pairing a modifier and base never paired in
  training (``Green.Tomato``, ``Blue.Plate``). Both words occur in training,
  separately.
- ``test_invariant``: charter proposition 4. Drop/Push of a break-prone thing
  that carries a structural modifier. Opt-in, via the ``invariant`` argument
  of ``build``; ``"off"`` reproduces the corpus the earlier runs were built
  from, byte for byte, so those measurements stay reproducible.

Why that shape tests proposition 4. The world conserves intrinsic modifiers
through a division and destroys structural ones (``world.keep_intrinsic``).
Training demonstrates that law only under ``Cut`` (``Big.Red.Apple`` ->
``Red.Apple.Slice``); the split asks for it under ``Drop``/``Push``, whose
division writes ``Piece``. The gold answer keeps the structural modifier in
the first result event and drops it in the second:

    Push tgt:Tall.Blue.Glass
      -> Fall tgt:Tall.Blue.Glass dst:Floor -> Become agt:Blue.Glass.Piece

so the two degenerate strategies fail on opposite events. A model that copies
the target writes ``Tall.Blue.Glass.Piece`` and fails on the second; a model
that has learned "structural modifiers are unstable" as a property of the
words writes ``Fall tgt:Blue.Glass`` and fails on the first. Only a model
that ties the law to the operation passes both. Charter proposition 4 is
falsified by failure here: the model would have learned copying, not
invariance.

Every token of the split occurs in training, as ``test_role`` requires of
itself and for the same reason (world.py, on the SCAN held-out-primitive
trap). Three-segment targets occur under ``Drop`` (``Fall tgt:Big.Red.Apple``,
with no division following, since an apple is not break-prone); the string
``Blue.Glass.Piece`` occurs whenever an unmodified ``Blue.Glass`` is dropped.
What never occurs is the conjunction. Only the application of the law is new.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from . import parse
from .knowledge import Store, query_for
from .render import tagged_pipeline, word_order_pipeline
from .syntax import Concept, Pipeline
from .world import KIND, Sample, core_rules, sample

ROLE_HELD_OUT = "Cat"
COMBOS_HELD_OUT = (("Green", "Tomato"), ("Blue", "Plate"))

# How ``test_invariant`` is treated. "off" leaves the corpus exactly as it was
# before the split existed; "holdout" is the experiment; "control" measures the
# ceiling by letting meanings of that shape train as well, on disjoint
# meanings, which is what tells a failure of transfer apart from a split that
# is simply hard.
INVARIANT_MODES = ("off", "holdout", "control")


def _targets(s: Sample) -> list[Concept]:
    return [v for v in s.action.get("tgt") if isinstance(v, Concept)]


def _is_invariant(s: Sample) -> bool:
    """Drop/Push of a break-prone thing carrying a structural modifier.

    The conjunction is what makes the split new: each conjunct on its own
    occurs throughout training.
    """
    if s.action.verb.segments[0] not in ("Drop", "Push"):
        return False
    for t in _targets(s):
        kind = KIND.get(t.segments[-1])
        if kind is not None and kind.break_prone and set(t.segments) & set(kind.structural):
            return True
    return False


def split_of(s: Sample, invariant: str = "off") -> str | None:
    """Which held-out split a meaning belongs to, if any.

    ``test_invariant`` is checked last, so the two older splits keep every
    meaning they claimed before it existed and their published numbers stay
    comparable.
    """
    for t in _targets(s):
        if t.segments == (ROLE_HELD_OUT,):
            return "test_role"
        for mod, base in COMBOS_HELD_OUT:
            if mod in t.segments and t.segments[-1] == base:
                return "test_combo"
    if invariant != "off" and _is_invariant(s):
        return "test_invariant"
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
    # What the model asks before it answers, and what comes back. Written in
    # canonical form rather than a surface rendering: the query is a statement
    # of the language (spec ch.2 §6.4) and the answer is whatever the store
    # holds, and neither is the place to vary form. Empty when the store had
    # nothing, which is a record of a gap in coverage, not a failure to render.
    query: str = ""
    answer: str = ""
    # A derivation that stops part way to look something up. `head` is what the
    # model writes before it has to, `handed` is what comes back, `tail` is the
    # rest. A marked word the model *derived* could not have been fetched in
    # advance — it did not exist until the step that produced it — so this is
    # the one lookup a parser cannot do for it.
    head: str = ""
    handed: str = ""
    tail: str = ""

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def render(s: Sample, split: str, rng: random.Random, store: Store | None = None) -> Record:
    action = Pipeline((s.action,))
    has_both = bool(s.action.get("agt")) and bool(s.action.get("tgt"))
    passive = has_both and rng.random() < 0.5
    query = answer = ""
    if store is not None:
        # The query is formed from the action, always, without asking whether
        # the answer is already known — see `knowledge` on why that is the
        # whole point rather than a simplification.
        q = query_for(s.action)
        got = store.answer(q)
        query, answer = str(q), " ".join(str(st) for st in got.statements)
    return Record(
        query=query,
        answer=answer,
        split=split,
        meaning=str(s.meaning()),
        tagged_in=tagged_pipeline(action, rng),
        # Inputs are shuffled (order carries nothing); outputs use one fixed
        # order, as the word-order form's do. Shuffling outputs too made the
        # target unpredictable and handicapped the role-tagged form.
        tagged_out=f"{s.connector} {tagged_pipeline(s.result)}",
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
    invariant: str = "off",
    n_invariant: int = 500,
    ask: bool = False,
) -> list[Record]:
    """Draw meanings until each split is full, then render each once per form.

    Train meanings may repeat (with fresh renderings), as a real corpus
    would; test meanings are unique and never occur in train.

    ``invariant`` selects how the proposition-4 split is treated:

    - ``"off"``     no such split; the corpus is what it was before, drawn
                    from an identical random stream, so the earlier runs
                    stay reproducible.
    - ``"holdout"`` the experiment. Meanings of that shape never train.
    - ``"control"`` the ceiling: the same test set, with meanings of that
                    shape training at the rate they occur naturally (~11%).
                    Without this arm a failure of transfer cannot be told
                    apart from a split that is merely hard.

    The test set is drawn in a pass of its own, from a stream of its own, so
    both arms are graded on exactly the same meanings and the composition of
    the training corpus is the only difference between them. It is reserved
    at ``n_invariant``, well below ``n_held``, because the shape has only a
    few thousand distinct meanings: every one reserved is one the control arm
    cannot train on, and holding out a quarter of the space would depress the
    rate the control is supposed to represent. Five hundred is ample for the
    rate being estimated here — the question is whether the arm fails, and at
    that size the standard error is about two points.

    A first version reserved the split inside the main loop instead and let
    the overflow train. It measured nothing: ``train`` fills within a few
    thousand draws while a thousand *distinct* meanings of a shape that is
    one draw in nine take far longer, so every such sample was taken by the
    test set and the control arm trained on **zero** of them — an arm
    identical to the one it was supposed to bound. The failure was invisible
    in the results, which looked like a clean negative, and showed up only on
    counting the shape in the training corpus. Reserve the test set first,
    then let the training corpus be drawn normally.
    """
    if invariant not in INVARIANT_MODES:
        raise ValueError(f"invariant must be one of {INVARIANT_MODES}, not {invariant!r}")
    rng = random.Random(seed)
    train: list[Sample] = []
    train_meanings: set[str] = set()
    iid: dict[str, Sample] = {}
    held: dict[str, dict[str, Sample]] = {"test_role": {}, "test_combo": {}}

    reserved: dict[str, Sample] = {}
    if invariant != "off":
        # A stream of its own, so that both arms are graded on the same
        # meanings however their training corpora then diverge. Meanings the
        # two older splits claim are skipped here, which is the same priority
        # `split_of` applies: they were spoken for before this split existed.
        prng = random.Random(f"{seed}-invariant")
        for _ in range(max_draws):
            if len(reserved) >= n_invariant:
                break
            s = sample(prng)
            if _is_invariant(s) and split_of(s) is None:
                reserved.setdefault(str(s.meaning()), s)
        held["test_invariant"] = reserved

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
            continue
        if invariant != "off" and _is_invariant(s):
            # Never train on a meaning the test set holds, whichever arm.
            # Beyond that, the holdout arm drops the shape and the control
            # arm keeps it, which is the whole of the difference between them.
            if key in reserved or invariant == "holdout":
                continue
        if key not in train_meanings and len(iid) < n_iid and rng.random() < 0.1:
            iid.setdefault(key, s)
        elif key not in iid and len(train) < n_train:
            train.append(s)
            train_meanings.add(key)

    # One store for every split. Holding knowledge back is not done here: the
    # core enumerates a rule per kind and modifier combination, so a shape the
    # splits keep out of training keeps its rule out of every training answer
    # by itself, and the test is handed that rule for the first time at test
    # time. That is the held-out-knowledge experiment, with nothing added.
    store = Store(parse(core_rules()), "core") if ask else None
    out = [render(s, "train", rng, store) for s in train]
    out += [render(s, "test_iid", rng, store) for s in iid.values()]
    for name, samples in held.items():
        out += [render(s, name, rng, store) for s in samples.values()]
    return out


def write(records: list[Record], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(r.to_json() + "\n")
