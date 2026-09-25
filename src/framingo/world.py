"""A small deterministic world: the generator for charter proposition 3.

The world decides what happens; renderers (``render.py``) only decide how it
is written. Keeping the two apart is what lets the experiment hold meaning
fixed while varying form.

Meaning is represented with the same syntax tree as the parser produces
(``Event`` / ``Pipeline``), so a generated sample can be checked by the
grounding checker without a translation step.

Physics, deliberately tiny:
- Cut with a Knife turns a cuttable target into slices; intrinsic modifiers
  (colour, taste) survive, structural ones (shape, size, wholeness) do not
  (spec ch.3 §2). Cut with a Ruler fails: the slicing is prevented and the
  target is deformed instead (spec ch.4 §4.1).
- Drop and Push make the target fall; a break-prone target then becomes pieces.
- Drop and Push may name where the target fell from (``src:``); the fall
  keeps that source.
- Carry moves both the target and the carrier: ``Carry agt:A tgt:Y dst:P``
  gives ``At tgt:Y loc:P &> At tgt:A loc:P`` — joined by the connective for
  results that hold at once, because neither arrival causes the other.
- Carry can target animates as well as objects. This is what gives the
  role-swap split something to test: an animate that is only ever a carrier
  in training must be recognised as the carried at test time.

Why the carrier appears in the result: the first version named only the
target in results, so an animate held out as a target never occurred in any
training output at all. A model then fails the role-swap test simply
because it has never emitted that word, whatever the input form, and the
test measures output-vocabulary priors instead of role binding (the same
trap as SCAN's held-out primitive). With the carrier in the result, the
held-out animate is a familiar output token, and only its role is new.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .syntax import Concept, Event, Pipeline


@dataclass(frozen=True)
class Kind:
    base: str
    intrinsic: tuple[str, ...]
    structural: tuple[str, ...]
    cuttable: bool = False
    break_prone: bool = False


ANIMATES = ("John", "Mary", "Cat", "Robot", "Chef")

KINDS = (
    Kind("Apple", ("Red", "Green", "Sweet", "Sour"), ("Round", "Whole", "Big"), cuttable=True),
    Kind("Bread", ("Soft", "Hard"), ("Whole", "Big", "Small"), cuttable=True),
    Kind("Tomato", ("Red", "Green"), ("Round", "Big", "Small"), cuttable=True),
    Kind("Melon", ("Green", "Sweet"), ("Round", "Whole"), cuttable=True),
    Kind("Glass", ("Blue", "Clear"), ("Tall", "Whole"), break_prone=True),
    Kind("Vase", ("Blue", "White"), ("Tall", "Whole"), break_prone=True),
    Kind("Plate", ("White", "Blue"), ("Round", "Whole"), break_prone=True),
    Kind("Ball", ("Red", "Blue"), ("Round", "Big")),
    Kind("Box", ("Brown", "White"), ("Big", "Small")),
)
KIND = {k.base: k for k in KINDS}

TOOLS = ("Knife", "Ruler")
PLACES = ("Kitchen", "Garden", "Hall", "Yard", "Attic")
SOURCES = (("On", "Table"), ("On", "Chair"), ("On", "Shelf"))
ANIMATE_TARGET_VERBS = ("Carry",)


def C(*segments: str) -> Concept:
    return Concept(tuple(segments))


def ev(verb: str, **slots: Concept) -> Event:
    return Event(C(verb), frozenset(slots.items()))


def thing(kind: Kind, intrinsic: str | None, structural: str | None) -> Concept:
    mods = [m for m in (structural, intrinsic) if m]
    return C(*mods, kind.base)


def keep_intrinsic(target: Concept, part: str) -> Concept:
    """The target after it has been divided: structural modifiers are lost."""
    kind = KIND[target.segments[-1]]
    mods = [m for m in target.segments[:-1] if m in kind.intrinsic]
    return C(*mods, kind.base, part)


def consequence(action: Event) -> Pipeline:
    """What the world does in response to ``action``. Deterministic."""
    verb = action.verb.segments[0]
    (target,) = action.get("tgt")
    if verb == "Cut":
        (tool,) = action.get("tool")
        slices = ev("Become", agt=keep_intrinsic(target, "Slice"))
        if tool.segments == ("Knife",):
            return Pipeline((slices,))
        deformed = ev("Deform", tgt=target, reason=C("Inappropriate", "Tool"))
        return Pipeline((slices, deformed), ("->",))
    if verb == "Carry":
        (place,) = action.get("dst")
        (agent,) = action.get("agt")
        # `&>`, not `->`: the carrier and the carried arrive at one and the
        # same moment, and neither arrival brought the other about. Writing
        # this chain with `->` asserted that the carried thing's arrival
        # caused the carrier's, which is false, and the verifier enforced it
        # as physics once it began to read order (spec ch.4 §1.1, §1.3).
        return Pipeline((ev("At", tgt=target, loc=place), ev("At", tgt=agent, loc=place)), ("&>",))
    if verb in ("Drop", "Push"):
        src = {"src": s for s in action.get("src")}
        fall = ev("Fall", tgt=target, dst=C("Floor"), **src)
        base = target.segments[-1]
        if base in KIND and KIND[base].break_prone:
            pieces = ev("Become", agt=keep_intrinsic(target, "Piece"))
            return Pipeline((fall, pieces), ("->",))
        return Pipeline((fall,))
    raise ValueError(f"no physics for {verb}")


def outcome_connector(action: Event) -> str:
    """Cut with a Ruler prevents the slicing; everything else just happens."""
    if action.verb.segments[0] == "Cut" and action.get("tool")[0].segments == ("Ruler",):
        return "!>"
    return "->"


@dataclass(frozen=True)
class Sample:
    action: Event
    result: Pipeline
    connector: str  # joins action to the first result event

    def meaning(self) -> Pipeline:
        return Pipeline(
            (self.action,) + self.result.events,
            (self.connector,) + self.result.connectors,
        )


def random_object(rng: random.Random, kinds: tuple[Kind, ...] = KINDS) -> Concept:
    kind = rng.choice(kinds)
    intrinsic = rng.choice((None,) + kind.intrinsic)
    structural = rng.choice((None,) + kind.structural)
    return thing(kind, intrinsic, structural)


def random_action(rng: random.Random) -> Event:
    verb = rng.choice(("Cut", "Drop", "Push", "Carry"))
    agent = C(rng.choice(ANIMATES))
    slots: dict[str, Concept] = {"agt": agent}
    if verb == "Cut":
        slots["tgt"] = random_object(rng, tuple(k for k in KINDS if k.cuttable))
        slots["tool"] = C(rng.choice(TOOLS))
    elif verb in ANIMATE_TARGET_VERBS and rng.random() < 0.3:
        slots["tgt"] = C(rng.choice([a for a in ANIMATES if a != agent.segments[0]]))
    else:
        slots["tgt"] = random_object(rng)
    if verb == "Carry":
        slots["dst"] = C(rng.choice(PLACES))
    if verb in ("Drop", "Push") and rng.random() < 0.5:
        slots["src"] = C(*rng.choice(SOURCES))
    if rng.random() < 0.3:
        slots["loc"] = C(rng.choice(PLACES))
    return ev(verb, **slots)


def sample(rng: random.Random) -> Sample:
    action = random_action(rng)
    return Sample(action, consequence(action), outcome_connector(action))


def _divisions(kind: Kind) -> list[tuple[str, str]]:
    """Every target ``thing()`` can build for this kind, paired with what is
    left of it once it has been divided.

    ``thing()`` writes ``[structural].[intrinsic].Base`` with at most one of
    each and either one free to be absent, so the combinations are exactly the
    product of the two modifier lists, each widened with "absent". The
    structural modifier does not survive the division and the intrinsic one
    does (``keep_intrinsic``); this states that a second time, in the shape a
    rule needs, so that the checker really is a second opinion on the physics.
    """
    out = []
    for structural in (None,) + kind.structural:
        for intrinsic in (None,) + kind.intrinsic:
            target = ".".join(m for m in (structural, intrinsic, kind.base) if m)
            out.append((target, ".".join(m for m in (intrinsic, kind.base) if m)))
    return out


def core_rules() -> str:
    """The same physics written as Framingo RULEs, for the grounding checker.

    One rule per kind rather than one per class, because the checker does not
    infer class membership (grounding.LIMITS). Writing them out is the
    minimal core doing its job: the checker must be able to derive every
    result the generator claims — and nothing beyond it, or a fabrication the
    core happens to license passes unflagged.

    Division is enumerated over modifier combinations, which is why the core
    is long. The rule language has no "drop segment M from the target"
    operation, and ``It`` necessarily stands for the whole antecedent, so
    ``Cut tgt:Apple -> Become agt:It.Slice`` derives ``Big.Red.Apple.Slice``
    from ``Cut tgt:Big.Red.Apple``: the structural modifier the world destroys
    survives in the core, which then accepts the copy error exactly as readily
    as the truth. The distinction between intrinsic and structural can only be
    carried by naming the combinations and writing the surviving concept out.

    That in turn is why the enumerated premises are marked ``Every.``. The
    reading is universal, so the mark belongs there anyway, but it is also
    load-bearing: ``It`` copies its antecedent's determiner, so the mark is
    what separates the concepts that stand for the matched target (``Fall
    tgt:It``, still the whole thing) from the one written out (``Become
    agt:Red.Apple.Slice``, only what survived). Without it the checker expands
    the written-out concept back into the matched target and the enumeration
    buys nothing.

    Conservation keeps ``It`` and needs no enumeration: falling, being
    deformed and being carried lose nothing, so the whole antecedent is the
    right answer there.
    """
    lines = []
    for k in KINDS:
        if k.cuttable:
            for target, slices in _divisions(k):
                lines.append(
                    f"RULE: Action: Cut tgt:Every.{target} tool:Knife"
                    f" -> Result: Become agt:{slices}.Slice"
                )
                lines.append(
                    f"RULE: Action: Cut tgt:Every.{target} tool:Ruler"
                    f" !> Result: Become agt:{slices}.Slice"
                    " -> Result: Deform tgt:It reason:Inappropriate.Tool"
                )
    targets = [(k.base, k.break_prone) for k in KINDS] + [(a, False) for a in ANIMATES]
    for base, break_prone in targets:
        verbs = ("Drop", "Push") if base in KIND else ()
        for verb in verbs:
            for src in [None] + [".".join(s) for s in SOURCES]:
                src_slot = f" src:{src}" if src else ""
                fall = f"Fall tgt:It dst:Floor{src_slot}"
                if not break_prone:
                    # nothing is divided, so the fall may keep the whole target
                    lines.append(f"RULE: Action: {verb} tgt:{base}{src_slot} -> {fall}")
                    continue
                for target, pieces in _divisions(KIND[base]):
                    lines.append(
                        f"RULE: Action: {verb} tgt:Every.{target}{src_slot}"
                        f" -> {fall} -> Result: Become agt:{pieces}.Piece"
                    )
        for place in PLACES:
            # <A> carries the carrier across to the second event (spec ch.3
            # §5.2), and `&>` says the two arrivals hold at once rather than
            # one causing the other (spec ch.4 §1.3).
            lines.append(
                f"RULE: Action: Carry agt:Every.Thing<A> tgt:{base} dst:{place}"
                f" -> At tgt:It loc:{place} &> At tgt:It<A> loc:{place}"
            )
    return "\n".join(lines)
