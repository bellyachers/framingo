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
- Carry moves the target to a place: ``Carry agt:A tgt:Y dst:P`` gives
  ``At tgt:Y loc:P``.
- Push and Carry can target animates as well as objects. This is what gives
  the role-swap split something to test: an animate that is only ever an
  agent in training must be recognised as a target at test time.
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
PLACES = ("Kitchen", "Garden", "Hall")
SOURCES = (("On", "Table"), ("On", "Chair"), ("On", "Shelf"))
ANIMATE_TARGET_VERBS = ("Push", "Carry")


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
        return Pipeline((ev("At", tgt=target, loc=place),))
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


def core_rules() -> str:
    """The same physics written as Framingo RULEs, for the grounding checker.

    One rule per kind rather than one per class, because the checker does not
    infer class membership (grounding.LIMITS). Writing them out is the
    minimal core doing its job: the checker must be able to derive every
    result the generator claims.
    """
    lines = []
    for k in KINDS:
        if k.cuttable:
            lines.append(f"RULE: Action: Cut tgt:{k.base} tool:Knife -> Result: Become agt:It.Slice")
            lines.append(
                f"RULE: Action: Cut tgt:{k.base} tool:Ruler !> Result: Become agt:It.Slice"
                " -> Result: Deform tgt:It reason:Inappropriate.Tool"
            )
    targets = [(k.base, k.break_prone) for k in KINDS] + [(a, False) for a in ANIMATES]
    for base, break_prone in targets:
        verbs = ("Drop", "Push") if base in KIND else ("Push",)
        for verb in verbs:
            for src in [None] + [".".join(s) for s in SOURCES]:
                src_slot = f" src:{src}" if src else ""
                fall = f"Fall tgt:It dst:Floor{src_slot}"
                then = " -> Result: Become agt:It.Piece" if break_prone else ""
                lines.append(f"RULE: Action: {verb} tgt:{base}{src_slot} -> {fall}{then}")
        for place in PLACES:
            lines.append(f"RULE: Action: Carry tgt:{base} dst:{place} -> At tgt:It loc:{place}")
    return "\n".join(lines)
