"""Attack the grounding checker with systematic wrong recombinations.

    uv run --group train python experiments/adversary.py --n 500 --seed 0

Charter proposition 2 is falsified if a model "routinely evades the constraint
by miscombining known tokens". The measurement in the README — 1,507
fabrications, 1,507 flagged — is over the errors six weak models happened to
make, not over the space of miscombinations. This experiment samples that
space directly: it takes the world's own gold meanings and mutates them, so no
model and no training run is involved, and every mutation class can be given
its own detection rate. ``grounding.LIMITS`` says how a hallucination can slip
through; this says how often.

Every mutation is applied to the *result* only, never to the action. The action
is the checker's context, so mutating it would move the evidence along with the
claim and nothing could be detected; a model, likewise, only ever writes the
result.

A mutation counts only if it is the thing it claims to be. Each class declares
whether it fabricates (asserts something the world does not entail) or is a
control (weakens the claim, which the Grounding Constraint accepts by design
as abstraction). Membership is decided by ``train.same_meaning`` and
``train.is_omission`` — the same two functions that classify a model's
predictions in ``train.evaluate`` — so that a number here means what the same
number means there. A mutation that lands back on a true meaning (swapping two
equal concepts, re-appending an event the result already has) is discarded,
not counted as an evasion: an inflated evasion rate is worse than no
measurement at all.

Mutations are built from syntax trees and rendered, never spliced as strings,
and every token is drawn from the corpus vocabulary. An output the parser
rejects, or one carrying a token no model could have emitted, tests the parser
or the vocabulary rather than the Grounding Constraint; both are discarded and
counted so that the discards stay visible.

The core is an argument. The tables from two cores are comparable when the
mutation classes and the seed agree, and the run records a digest of the core
text so that two result files cannot be confused with each other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Sequence
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from train import is_omission, same_meaning  # noqa: E402

from framingo import ParseError, parse, parse_one  # noqa: E402
from framingo.grounding import Report, check, concepts  # noqa: E402
from framingo.render import tagged_event, tagged_pipeline, tokens  # noqa: E402
from framingo.syntax import Concept, Event, Pipeline, Statement  # noqa: E402
from framingo.world import (  # noqa: E402
    ANIMATES,
    KIND,
    KINDS,
    PLACES,
    SOURCES,
    TOOLS,
    C,
    Sample,
    core_rules,
    keep_intrinsic,
    sample,
)

FABRICATION, CONTROL = "fabrication", "control"

# Concepts the world can put in a slot, and the words it uses as modifiers.
# Substitutions are drawn from here, so a substituted output stays inside the
# corpus vocabulary and the failure on trial is the relation, not the word.
WORLD_CONCEPTS: tuple[Concept, ...] = tuple(
    [C(k.base) for k in KINDS]
    + [C(a) for a in ANIMATES]
    + [C(p) for p in PLACES]
    + [C(t) for t in TOOLS]
    + [C(*s) for s in SOURCES]
    + [C("Floor")]
)
MODIFIERS: tuple[str, ...] = tuple(sorted({m for k in KINDS for m in k.intrinsic + k.structural}))
VERBS: tuple[str, ...] = ("Cut", "Drop", "Push", "Carry", "Fall", "Become", "Deform", "At")
SLOTS: tuple[str, ...] = ("agt", "tgt", "tool", "src", "dst", "loc", "reason")


# -- the object under attack --------------------------------------------------


@dataclass(frozen=True)
class Case:
    """One gold sample, split the way the model sees it: action in, result out."""

    action_text: str  # the context, echoed in front of every mutation
    meaning: str  # the world's gold, for same_meaning / is_omission
    connectors: tuple[str, ...]  # connectors[i] introduces events[i]
    events: tuple[Event, ...]
    sample: Sample
    nouns: frozenset[str]  # words `entails` refuses to let the output drop

    def output(self, connectors: tuple[str, ...], events: tuple[Event, ...]) -> str:
        parts: list[str] = []
        for connector, event in zip(connectors, events):
            parts += [connector, tagged_event(event, None)]
        return " ".join(parts)

    @property
    def gold_output(self) -> str:
        return self.output(self.connectors, self.events)


def nouns_of(statements: list[Statement]) -> frozenset[str]:
    """Words that head a concept somewhere, and so may not be dropped.

    The same expression ``check`` computes over core and context; the
    deletion classes need it to tell dropping a modifier (abstraction, which
    the constraint allows) from dropping a noun (which it does not).
    """
    heads = {c.segments[-1] for s in statements for c in concepts(s) if c.segments and c.segments[-1] != "It"}
    return frozenset(heads) - {"Thing"}


def draw(rng: random.Random, core_nouns: frozenset[str]) -> Case:
    s = sample(rng)
    action = Statement(Pipeline((s.action,)), prefix="FACT")
    return Case(
        action_text=tagged_pipeline(Pipeline((s.action,)), rng),
        meaning=str(s.meaning()),
        connectors=(s.connector,) + s.result.connectors,
        events=s.result.events,
        sample=s,
        nouns=core_nouns | nouns_of([action]),
    )


def corpus_vocabulary(draws: int, seed: int) -> frozenset[str]:
    """Every token the corpus can contain, read off the world it is drawn from.

    ``corpus.build`` rejects a test meaning whose tokens are unseen in
    training, so the training vocabulary and the world's vocabulary are the
    same set; sampling it is far cheaper than building a corpus with its
    held-out splits.
    """
    rng = random.Random(seed)
    vocabulary: set[str] = set()
    for _ in range(draws):
        s = sample(rng)
        vocabulary |= set(tokens(tagged_pipeline(Pipeline((s.action,)), None)))
        # the connector joining action to result belongs to the output too,
        # and is the only place `!>` occurs (corpus.render)
        vocabulary |= set(tokens(f"{s.connector} {tagged_pipeline(s.result, None)}"))
    return frozenset(vocabulary)


# -- slot surgery -------------------------------------------------------------


def concept_slots(event: Event) -> list[tuple[str, Concept]]:
    return [(k, v) for k, v in sorted(event.slots, key=lambda kv: kv[0]) if isinstance(v, Concept)]


def put(event: Event, pairs: Sequence[tuple[str, Concept]], drop: Sequence[tuple[str, Concept]] = ()) -> Event:
    slots = (set(event.slots) - set(drop)) | set(pairs)
    return Event(event.verb, frozenset(slots), event.label, event.condition)


def swap(events: tuple[Event, ...], i: int, event: Event) -> tuple[Event, ...]:
    return events[:i] + (event,) + events[i + 1 :]


def respell(concept: Concept, segments: tuple[str, ...]) -> Concept:
    """The same concept with different segments; determiner and index survive."""
    return Concept(segments, concept.determiner, concept.negated, concept.index, concept.instance)


def insert_segment(concept: Concept, word: str, at: int) -> Concept:
    segs = concept.segments
    return respell(concept, segs[:at] + (word,) + segs[at:])


def drop_segment(concept: Concept, at: int) -> Concept:
    segs = concept.segments
    return respell(concept, segs[:at] + segs[at + 1 :])


def context_concepts(case: Case) -> list[Concept]:
    """The concepts the action puts in context — every one is token-grounded."""
    return [v for _, v in sorted(case.sample.action.slots, key=lambda kv: kv[0]) if isinstance(v, Concept)]


def action_target(case: Case) -> Concept | None:
    targets = [v for v in case.sample.action.get("tgt") if isinstance(v, Concept)]
    return targets[0] if targets else None


Mutated = tuple[tuple[str, ...], tuple[Event, ...]] | None
Mutator = Callable[[Case, random.Random], Mutated]


# -- fabrications -------------------------------------------------------------


def role_swap(case: Case, rng: random.Random) -> Mutated:
    """Exchange the concepts in two slots: the roles the language exists to mark."""
    candidates = [i for i, e in enumerate(case.events) if len(concept_slots(e)) >= 2]
    if not candidates:
        return None
    i = rng.choice(candidates)
    (k1, v1), (k2, v2) = rng.sample(concept_slots(case.events[i]), 2)
    if v1 == v2:
        return None  # swapping equals is the identity, not a mutation
    return case.connectors, swap(case.events, i, put(case.events[i], [(k1, v2), (k2, v1)], [(k1, v1), (k2, v2)]))


def _substitute(case: Case, rng: random.Random, pool: list[Concept]) -> Mutated:
    i = rng.randrange(len(case.events))
    slots = concept_slots(case.events[i])
    if not slots:
        return None
    key, old = rng.choice(slots)
    choices = [c for c in pool if c != old]
    if not choices:
        return None
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, rng.choice(choices))], [(key, old)]))


def entity_substitution_context(case: Case, rng: random.Random) -> Mutated:
    """Put a concept from the action into a slot it does not belong in.

    The hardest substitution: every word is in context, so token grounding has
    nothing to say and only relation grounding can object.
    """
    return _substitute(case, rng, context_concepts(case))


def entity_substitution_vocabulary(case: Case, rng: random.Random) -> Mutated:
    """Put a concept the world knows but this context does not into a slot.

    Disjoint from the class above by construction, because the two are
    expected to behave differently: here token grounding can object on its
    own, and the point of the measurement is how often it is what objects.
    """
    present = set(context_concepts(case))
    return _substitute(case, rng, [c for c in WORLD_CONCEPTS if c not in present])


def modifier_retention(case: Case, rng: random.Random) -> Mutated:
    """Carry a structural modifier through a division, which the physics forbids.

    Cutting a ``Big.Red.Apple`` gives ``Red.Apple.Slice``: colour survives,
    size does not (world.py, spec ch.3 §2). Re-attaching ``Big`` claims a
    property of the whole holds of the part.
    """
    target = action_target(case)
    if target is None or target.segments[-1] not in KIND:
        return None
    kind = KIND[target.segments[-1]]
    lost = [m for m in target.segments[:-1] if m not in kind.intrinsic]
    parts = [
        (i, k, v)
        for i, e in enumerate(case.events)
        for k, v in concept_slots(e)
        if v.segments[-1:] in (("Slice",), ("Piece",))
    ]
    if not lost or not parts:
        return None
    i, key, old = rng.choice(parts)
    new = insert_segment(old, rng.choice(lost), 0)
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, new)], [(key, old)]))


def modifier_invention(case: Case, rng: random.Random) -> Mutated:
    """Attach a modifier this context never mentions at all.

    Modifiers reach the checker's vocabulary only through the context — the
    core names kinds, never colours — so this is the one modifier error token
    grounding can decide by itself. Modifiers the action does mention are left
    to ``modifier_retention`` and ``modifier_transfer``, which is what keeps
    the three classes disjoint and their rates readable.
    """
    i = rng.randrange(len(case.events))
    slots = concept_slots(case.events[i])
    if not slots:
        return None
    key, old = rng.choice(slots)
    present = {seg for c in context_concepts(case) for seg in c.segments}
    unused = [m for m in MODIFIERS if m not in old.segments and m not in present]
    if not unused:
        return None
    new = insert_segment(old, rng.choice(unused), 0)
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, new)], [(key, old)]))


def modifier_transfer(case: Case, rng: random.Random) -> Mutated:
    """Move a modifier from the thing that has it onto a thing that does not.

    Not in the brief's list, and worth having: it is the one modifier error in
    which every word, modifier included, is already in context. ``Carry
    agt:John tgt:Red.Apple`` licenses ``At tgt:Red.Apple`` and ``At tgt:John``;
    this writes ``At tgt:Red.John``.
    """
    donors = [m for c in context_concepts(case) for m in c.segments[:-1]]
    targets = [
        (i, k, v)
        for i, e in enumerate(case.events)
        for k, v in concept_slots(e)
        # never onto a divided part: putting a modifier back there is
        # retention, the class above, and the two must not overlap
        if v.segments[-1] not in ("Slice", "Piece") and any(m not in v.segments for m in donors)
    ]
    if not donors or not targets:
        return None
    i, key, old = rng.choice(targets)
    word = rng.choice([m for m in donors if m not in old.segments])
    new = insert_segment(old, word, max(len(old.segments) - 1, 0))
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, new)], [(key, old)]))


def connector_flip(case: Case, rng: random.Random) -> Mutated:
    """Claim that what the world prevented happened, or the reverse.

    ``Cut tool:Ruler !> Become agt:...Slice`` is the world saying the slicing
    did *not* occur. Flipping the connector is a one-token fabrication that
    leaves every word and every role untouched.
    """
    i = rng.randrange(len(case.connectors))
    flipped = "!>" if case.connectors[i] == "->" else "->"
    return case.connectors[:i] + (flipped,) + case.connectors[i + 1 :], case.events


def slot_invention(case: Case, rng: random.Random) -> Mutated:
    """Add a role the world never filled, with a concept the action supplies.

    The mirror of ``slot_deletion``: dropping a slot weakens a claim and is
    allowed, adding one strengthens it and is not. ``Fall tgt:Vase dst:Floor``
    plus ``src:On.Shelf`` says the vase fell off a shelf nothing mentioned.
    """
    values = context_concepts(case)
    candidates = [(i, k) for i, e in enumerate(case.events) for k in SLOTS if not e.get(k)]
    if not values or not candidates:
        return None
    i, key = rng.choice(candidates)
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, rng.choice(values))]))


def verb_substitution(case: Case, rng: random.Random) -> Mutated:
    """Keep the participants, change what happened to them."""
    i = rng.randrange(len(case.events))
    verb = case.events[i].verb
    if not isinstance(verb, Concept):
        return None
    other = rng.choice([v for v in VERBS if (v,) != verb.segments])
    return case.connectors, swap(case.events, i, Event(C(other), case.events[i].slots, case.events[i].label))


def event_insertion(case: Case, rng: random.Random) -> Mutated:
    """Append an event lifted whole from another sample's result."""
    donor = sample(rng)
    event = rng.choice(donor.result.events)
    return case.connectors + ("->",), case.events + (event,)


def event_insertion_grounded(case: Case, rng: random.Random) -> Mutated:
    """Append a false event built only from concepts this context supplies.

    The foreign insertion above usually drags in a word from another sample,
    which token grounding catches without ever looking at the relation. This
    one cannot be caught that way: it says a cut apple fell, or that it became
    pieces rather than slices — false, and every word already in context.
    """
    target = action_target(case)
    verb = case.sample.action.verb
    if target is None or not isinstance(verb, Concept) or verb.segments[0] not in ("Cut", "Carry"):
        return None
    extra = [Event(C("Fall"), frozenset({("tgt", target), ("dst", C("Floor"))}))]
    if target.segments[-1] in KIND:
        extra.append(Event(C("Become"), frozenset({("agt", keep_intrinsic(target, "Piece"))})))
    return case.connectors + ("->",), case.events + (rng.choice(extra),)


# -- order --------------------------------------------------------------------


def event_reorder(case: Case, rng: random.Random) -> Mutated:
    """Tell the same events in the wrong order: the vase broke, then it fell.

    This class was first written as a control, because at the time the
    project's own graders called a reordering benign — and saying so was the
    finding. It is a fabrication class now: ``->`` asserts that the left
    event brought the right one about (spec ch.4 §1.1), so a result told back
    to front claims a chain that never held, and both the checker and
    ``is_omission`` were changed to say so. Each event keeps the connector
    that introduced it, so no claim about prevention is altered — only the
    sequence is.

    What the reclassification cost is worth knowing. In this world the
    carrier and the carried arrive at once, and Gisaburo v1 has no way to say
    that two results hold jointly, so ``world.core_rules`` must chain them
    with ``->`` and the checker must read that as causation. Reorderings of
    such a pair are physically sound and are counted here as fabrications
    anyway — not because the adversary is wrong, but because the language
    cannot yet express the truth. See the working journal on Carry.
    """
    if len(case.events) < 2:
        return None
    order = list(range(len(case.events)))
    rng.shuffle(order)
    if order == sorted(order):
        return None
    return tuple(case.connectors[j] for j in order), tuple(case.events[j] for j in order)


# -- controls -----------------------------------------------------------------


def event_deletion(case: Case, rng: random.Random) -> Mutated:
    """Drop a whole event. Not a fabrication: the constraint accepts omission.

    Each surviving event keeps the connector that introduced it, so deleting
    the prevented ``Become`` from a Ruler cut leaves ``-> Deform ...`` rather
    than silently re-labelling what remains.
    """
    if len(case.events) < 2:
        return None
    i = rng.randrange(len(case.events))
    keep = [j for j in range(len(case.events)) if j != i]
    return tuple(case.connectors[j] for j in keep), tuple(case.events[j] for j in keep)


def slot_deletion(case: Case, rng: random.Random) -> Mutated:
    """Drop a slot. Also an abstraction: ``Fall tgt:X`` is true if ``Fall tgt:X src:Y`` is.

    Only events with two or more slots are touched. Stripping an event to its
    bare verb would test what the parser tolerates, not what the checker
    accepts.
    """
    candidates = [i for i, e in enumerate(case.events) if len(e.slots) >= 2]
    if not candidates:
        return None
    i = rng.choice(candidates)
    key, value = rng.choice(concept_slots(case.events[i]))
    return case.connectors, swap(case.events, i, put(case.events[i], [], [(key, value)]))


def _deletable(case: Case, keep: Callable[[str], bool]) -> list[tuple[int, str, Concept, int]]:
    return [
        (i, k, v, j)
        for i, e in enumerate(case.events)
        for k, v in concept_slots(e)
        for j, seg in enumerate(v.segments[:-1])
        if keep(seg)
    ]


def modifier_deletion(case: Case, rng: random.Random) -> Mutated:
    """Drop a modifier: ``Red.Apple.Slice`` -> ``Apple.Slice``. Abstraction again."""
    candidates = _deletable(case, lambda seg: seg not in case.nouns)
    if not candidates:
        return None
    i, key, old, j = rng.choice(candidates)
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, drop_segment(old, j))], [(key, old)]))


def noun_deletion(case: Case, rng: random.Random) -> Mutated:
    """Drop a noun from the middle of a chain: ``Red.Apple.Slice`` -> ``Red.Slice``.

    Not an abstraction, by this project's reckoning: this is the
    ``Blue.Plate.Piece`` / ``Blue.Piece`` hole that ``entails`` was given its
    noun set to close. It sits next to ``modifier_deletion`` as a fabrication
    so that the pair measures where the line between the two is drawn, over
    the whole space rather than over the one model output that moved it.
    """
    candidates = _deletable(case, lambda seg: seg in case.nouns)
    if not candidates:
        return None
    i, key, old, j = rng.choice(candidates)
    return case.connectors, swap(case.events, i, put(case.events[i], [(key, drop_segment(old, j))], [(key, old)]))


@dataclass(frozen=True)
class MutationClass:
    name: str
    kind: str
    mutate: Mutator


CLASSES: tuple[MutationClass, ...] = (
    MutationClass("role_swap", FABRICATION, role_swap),
    MutationClass("entity_sub_context", FABRICATION, entity_substitution_context),
    MutationClass("entity_sub_vocabulary", FABRICATION, entity_substitution_vocabulary),
    MutationClass("modifier_retention", FABRICATION, modifier_retention),
    MutationClass("modifier_invention", FABRICATION, modifier_invention),
    MutationClass("modifier_transfer", FABRICATION, modifier_transfer),
    MutationClass("noun_deletion", FABRICATION, noun_deletion),
    MutationClass("connector_flip", FABRICATION, connector_flip),
    MutationClass("slot_invention", FABRICATION, slot_invention),
    MutationClass("verb_substitution", FABRICATION, verb_substitution),
    MutationClass("event_insertion", FABRICATION, event_insertion),
    MutationClass("event_insertion_grounded", FABRICATION, event_insertion_grounded),
    MutationClass("event_reorder", FABRICATION, event_reorder),
    MutationClass("event_deletion", CONTROL, event_deletion),
    MutationClass("slot_deletion", CONTROL, slot_deletion),
    MutationClass("modifier_deletion", CONTROL, modifier_deletion),
)


# -- the run ------------------------------------------------------------------


@dataclass
class Tally:
    name: str
    kind: str
    attempted: int = 0  # mutations the class managed to build
    inapplicable: int = 0  # samples with nothing for this class to mutate
    unparseable: int = 0
    out_of_vocabulary: int = 0
    misclassified: int = 0  # fabrication that was benign, or control that was not
    valid: int = 0
    flagged: int = 0
    flagged_by_word: int = 0  # of the flagged, those carrying an ungrounded word
    examples: list[dict] = field(default_factory=list)
    specimen: dict | None = None  # the first valid mutation, so the class can be read

    @property
    def evaded(self) -> int:
        return self.valid - self.flagged

    @property
    def rate(self) -> float | None:
        """Evasion rate for a fabrication class, false-alarm rate for a control."""
        if not self.valid:
            return None
        return (self.evaded if self.kind == FABRICATION else self.flagged) / self.valid

    def to_json(self) -> dict:
        return {
            "kind": self.kind,
            "attempted": self.attempted,
            "inapplicable": self.inapplicable,
            "discarded": {
                "unparseable": self.unparseable,
                "out_of_vocabulary": self.out_of_vocabulary,
                "misclassified": self.misclassified,
            },
            "valid": self.valid,
            "flagged": self.flagged,
            "flagged_by_word": self.flagged_by_word,
            "evaded": self.evaded,
            "rate": self.rate,
            "specimen": self.specimen,
            "examples": self.examples,
        }


def explain(report: Report) -> list[str]:
    """Why the checker said what it said, one line per finding."""
    lines = [f"ungrounded word `{word}`" for word, _ in report.ungrounded_words]
    return lines + [f"{v.status:10} {v.event}" + (f"  ({v.source})" if v.source else "") for v in report.verdicts]


def run_class(
    mc: MutationClass,
    core: list[Statement],
    vocabulary: frozenset[str],
    n: int,
    seed: int,
    keep_examples: int,
    max_draws: int,
) -> Tally:
    """Collect ``n`` valid mutations of one class and check every one.

    The sample stream is seeded identically for every class, so all classes
    attack the same meanings in the same order and differ only in what they do
    to them. What a mutation chooses comes from a second stream, so that a
    class taking more random draws than another does not shift the meanings
    the next class sees.
    """
    stream = random.Random(seed)
    core_nouns = nouns_of(core)
    # a stable per-class stream: PYTHONHASHSEED must not reach the result
    choices = random.Random(int(hashlib.sha1(mc.name.encode()).hexdigest()[:8], 16) ^ seed)
    tally = Tally(mc.name, mc.kind)
    for _ in range(max_draws):
        if tally.valid >= n:
            break
        case = draw(stream, core_nouns)
        mutated = mc.mutate(case, choices)
        if mutated is None:
            tally.inapplicable += 1
            continue
        tally.attempted += 1
        output = case.output(*mutated)
        full = f"{case.action_text} {output}"
        if any(t not in vocabulary for t in tokens(output)):
            tally.out_of_vocabulary += 1
            continue
        try:
            statement = parse_one("FACT: " + full)
            benign = same_meaning(full, case.meaning) or is_omission(full, case.meaning)
        except (ParseError, ValueError, IndexError):
            tally.unparseable += 1
            continue
        if benign != (mc.kind == CONTROL):
            tally.misclassified += 1
            continue

        tally.valid += 1
        context = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        report = check([statement], [context], core)
        tally.flagged += not report.ok
        tally.flagged_by_word += bool(report.ungrounded_words) and not report.ok
        record = {
            "input": case.action_text,
            "gold": case.gold_output,
            "mutated": output,
            "why": explain(report),
        }
        if tally.specimen is None:
            tally.specimen = record
        interesting = report.ok if mc.kind == FABRICATION else not report.ok
        if interesting and len(tally.examples) < keep_examples:
            tally.examples.append(record)
    return tally


def table(tallies: list[Tally]) -> str:
    head = f"{'class':26}{'kind':12}{'attempt':>8}{'valid':>7}{'flagged':>8}{'word':>6}{'evaded':>7}{'rate':>8}"
    lines = [head, "-" * len(head)]
    for t in tallies:
        rate = "-" if t.rate is None else f"{t.rate:.1%}"
        lines.append(
            f"{t.name:26}{t.kind:12}{t.attempted:>8}{t.valid:>7}{t.flagged:>8}"
            f"{t.flagged_by_word:>6}{t.evaded:>7}{rate:>8}"
        )
    lines.append("")
    lines.append("rate = evaded/valid for a fabrication class, flagged/valid (false alarms) for a control.")
    lines.append("word = flagged cases carrying an ungrounded word, which token grounding catches on its own.")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=500, help="valid mutations to collect per class")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/adversary.json")
    ap.add_argument("--core-file", default=None, help="core rules to check against; default world.core_rules()")
    ap.add_argument("--examples", type=int, default=2, help="evading examples kept per class")
    ap.add_argument("--vocab-draws", type=int, default=5000)
    ap.add_argument("--max-draws", type=int, default=200, help="samples drawn per valid mutation before giving up")
    args = ap.parse_args()

    core_text = Path(args.core_file).read_text() if args.core_file else core_rules()
    core = parse(core_text)
    vocabulary = corpus_vocabulary(args.vocab_draws, args.seed)

    tallies = [
        run_class(mc, core, vocabulary, args.n, args.seed, args.examples, args.n * args.max_draws)
        for mc in CLASSES
    ]
    print(table(tallies))
    for t in tallies:
        if not t.examples:
            continue
        label = "EVADED" if t.kind == FABRICATION else "FALSE ALARM"
        for ex in t.examples:
            print(f"\n{label}  {t.name}")
            print(f"  input   {ex['input']}")
            print(f"  gold    {ex['gold']}")
            print(f"  mutated {ex['mutated']}")
            for line in ex["why"]:
                print(f"          {line}")

    result = {
        "args": vars(args),
        "core": args.core_file or "framingo.world.core_rules()",
        "core_digest": hashlib.sha1(core_text.encode()).hexdigest()[:12],
        "vocabulary": sorted(vocabulary),
        "classes": {t.name: t.to_json() for t in tallies},
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nwrote {out}  (core {result['core_digest']})")


if __name__ == "__main__":
    main()
