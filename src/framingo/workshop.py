"""A world that uses the case frame it was given.

The three worlds before this one all derive the same way:

    (verb, class of target) -> outcome word -> its state -> tail

`(verb, class)` names exactly one rule and the class arrives from the
dictionary before anything is written, so nothing is ever *found*: the
derivation is one road followed to its end. Raising the class count to three
hundred and twenty made the road longer to look up and changed nothing else,
which is why every measurement of what the separation buys came out as a
constant factor. The thing being externalised was one flat table.

The language was never the constraint. `syntax.SLOT_KEYS` has sixteen slots and
the worlds above used seven; the verifier was probed against the rest and takes
`goal:`, `reason:`, `mod:`, `count:`, `iter:`, `freq:`, `tense:` and `asp:` in a
premise, several slots in one premise, `when:` over two states or over an event,
a slot carried into the consequent by index, and `!>` and `->` in one rule. So
the caution that built one narrow world at a time was not forced by the tools.
It was not checking.

**What decides an outcome here.** Five things, four of them fetched:

| | where it comes from |
|---|---|
| the material's class, on one of two axes | the dictionary |
| the condition it is already in | the situation states it |
| what the tool is | the dictionary |
| where the work happens | the dictionary |
| what it is for (`goal:`) | the dictionary |
| whether it is finished (`asp:`) | the situation states it |
| whether it happens at all (`mod:`) | the situation states it |
| how many times (`iter:`) | the situation states it |

and they do different jobs. The **place** gates whether anything happens at
all, and `mod:Cannot` gates it for a different reason, which a model has to
tell apart. The **tool** decides whether the effect happens or is blocked, and
a blocked rule says so with `!>` and puts something else in its place. The
**goal** chooses between two effects that are both available. The **condition**
and the **material** name which effect those are. The **aspect** decides
whether the result obtains at all or only the process does. And **`iter:`
decides how many times the effect applies**, each time from the condition the
last one left — which is why this world needs the harness to stop for a lookup
more than once.

**On `tense:`.** It parses, and it is left out. Every situation here is one
action; there is no earlier and no later for a tense to point at, and variable
normalisation actively forbids anything persisting between examples. A slot
that changes nothing would make the world look richer and be no richer, which
is the same error as inventing a word. Making tense real needs a corpus with
more than one moment in it, and that is the same problem as the dialogue layer
and cross-turn identity.

So a rule cannot be indexed, it has to be found: several have premises that
match on the material and differ elsewhere, and none of the differences can be
seen before the lookups come back.

**Three things a model has never had to do here.** Write nothing, because no
rule fires. Write a result the rule says did *not* happen. And read five
premises from four places before writing anything at all.

**What is still missing.** Time, for the reason above. And the verifier does
not ask for completeness: writing the first of two applications and stopping
grounds perfectly well, because the Grounding Constraint is that every token
written can be traced and not that nothing was left out. What catches a short
derivation is the accuracy, not the checker.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .syntax import Concept, Event, Pipeline

# -- what things are made of --------------------------------------------------
#
# Two axes, and every material sits on both, one parent from each. A rule about
# `Workable` and a rule about `Fibrous` therefore both match timber; which one
# is under consideration depends on the verb, and which one *fires* depends on
# everything else.

PARENTS: dict[str, tuple[str, ...]] = {
    "Timber": ("Workable", "Fibrous"),
    "Iron": ("Workable", "Dense"),
    "Cloth": ("Yielding", "Fibrous"),
    "Clay": ("Yielding", "Dense"),
    "Glass": ("Brittle", "Dense"),
    "Shell": ("Brittle", "Fibrous"),
}

NAMES: dict[str, tuple[str, ...]] = {
    "Timber": ("'Beam", "'Plank", "'Log", "'Stave", "'Batten", "'Rafter",
               "'Joist", "'Dowel", "'Lath", "'Spar", "'Slat", "'Strut"),
    "Iron": ("'Nail", "'Rod", "'Hoop", "'Rivet", "'Spike", "'Hinge",
             "'Clasp", "'Stud", "'Tack", "'Brace", "'Latch", "'Anvil"),
    "Cloth": ("'Sail", "'Veil", "'Sash", "'Braid", "'Twine", "'Rag",
              "'Shroud", "'Gauze", "'Linen", "'Serge", "'Tulle", "'Wadding"),
    "Clay": ("'Crock", "'Brick", "'Tile", "'Urn", "'Flue", "'Pipkin",
             "'Bisque", "'Slipware", "'Tessera", "'Grog", "'Engobe", "'Daub"),
    "Glass": ("'Pane", "'Phial", "'Lens", "'Bead", "'Prism", "'Retort",
              "'Cullet", "'Alembic", "'Bulb", "'Rondel", "'Crown", "'Frit"),
    "Shell": ("'Nacre", "'Whelk", "'Cowrie", "'Conch", "'Limpet", "'Auger",
              "'Cockle", "'Murex", "'Abalone", "'Tellin", "'Scallop", "'Nautilus"),
}

HANDS: tuple[str, ...] = (
    "'Ada", "'Bram", "'Cleo", "'Dov", "'Esme", "'Finn", "'Gwen", "'Hugo",
    "'Ida", "'Jory", "'Kit", "'Lune", "'Mabel", "'Nero", "'Odie", "'Pim",
)

# The other three arguments, each with a class the rules speak of and names
# they never do.
TOOLS: dict[str, tuple[str, ...]] = {
    "Keen": ("'Adze", "'Chisel", "'Rasp", "'Awl", "'Burin", "'Scriber"),
    "Blunt": ("'Maul", "'Mallet", "'Peen", "'Beetle", "'Drift", "'Fid"),
}
PLACES: dict[str, tuple[str, ...]] = {
    "Dry": ("'Loft", "'Shed", "'Bench", "'Gallery", "'Attic", "'Stall"),
    "Damp": ("'Trough", "'Cellar", "'Sluice", "'Washhouse", "'Sump", "'Culvert"),
}
GOALS: dict[str, tuple[str, ...]] = {
    "Shaping": ("'Fitting", "'Truing", "'Joinery", "'Turnery"),
    "Breaking": ("'Salvage", "'Demolition", "'Reclaim", "'Scrapping"),
}

# The conditions a situation may state. Only these: what a derivation produces
# is listed separately, so that nothing a thing decays into can also be offered
# as a stable starting point.
STATED: tuple[str, ...] = ("Raw", "Scored", "Parted", "Dented", "Frayed", "Swollen")

VERBS: tuple[str, ...] = ("Score", "Fire", "Strike", "Soak")

# Tense-aspect-modality, minus the tense. Each of these is in the premise and
# each changes what follows, which is the only reason any of them is here.
ASPECTS: tuple[str, ...] = ("Done", "Ongoing")
MODALS: tuple[str, ...] = ("Must", "May", "Cannot")
ITERS: tuple[str, ...] = ("Once", "Twice")

# Which axis each verb reads, and which place it needs. Two verbs per axis, and
# every material has one parent on each axis, so a verb and a material together
# name exactly one class: the world stays unambiguous while the material alone
# stays uninformative.
AXIS: dict[str, tuple[str, ...]] = {
    "Score": ("Workable", "Yielding", "Brittle"),
    "Fire": ("Workable", "Yielding", "Brittle"),
    "Strike": ("Dense", "Fibrous"),
    "Soak": ("Dense", "Fibrous"),
}
NEEDS_PLACE: dict[str, str] = {
    "Score": "Dry", "Fire": "Dry", "Strike": "Dry", "Soak": "Damp",
}
NEEDS_TOOL: dict[str, str] = {
    "Score": "Keen", "Fire": "Blunt", "Strike": "Blunt", "Soak": "Keen",
}

PRODUCED: tuple[str, ...] = (
    "Scored", "Parted", "Dented", "Frayed", "Swollen", "Crazed", "Pulped",
)
OUTCOME: dict[str, str] = {c: f"'{c}" for c in PRODUCED}

# Settling states carry on by themselves; stable ones do not.
OUTCOME_STATE: dict[str, str] = {
    "'Scored": "Stable", "'Parted": "Stable", "'Dented": "Stable",
    "'Frayed": "Stable", "'Swollen": "Stable",
    "'Crazed": "Shedding", "'Pulped": "Slumping",
}
TAIL: dict[str, tuple[str, ...]] = {
    "Stable": (),
    "Shedding": ("Flake", "Powder"),
    "Slumping": ("Sag",),
}


def effects(density: float = 0.8, seed: int = 0) -> dict[tuple[str, str, str, str], str]:
    """What each verb does, per (verb, axis class, condition, purpose).

    Generated, not written out. The readable part of this world is its
    structure — two axes, six materials, the conditions, what gates what — and
    that is hand-written above, because reading a world is how three design
    errors were caught here. What a particular verb does to a particular class
    in a particular condition for a particular purpose is arbitrary, and
    arbitrary content is what should not be hand-tuned: written by hand it
    acquires whatever balance the writer did not notice they were choosing. A
    first hand-written table left 68% of situations doing nothing at all, where
    a model that always writes nothing scores 0.68.

    `density` is the share of cells that do anything. The rest are the cases
    where the right answer is to write nothing, and they are drawn as often as
    any other.
    """
    rng = random.Random(f"{seed}-effects")
    out: dict[tuple[str, str, str, str], str] = {}
    for verb in VERBS:
        for klass in AXIS[verb]:
            for condition in STATED:
                for purpose in sorted(GOALS):
                    if rng.random() < density:
                        choices = [c for c in PRODUCED if c != condition]
                        out[(verb, klass, condition, purpose)] = rng.choice(choices)
    return out


EFFECT = effects()


def class_of(name: str, groups: dict[str, tuple[str, ...]]) -> str:
    for klass, members in groups.items():
        if name in members:
            return klass
    raise KeyError(name)


def axis_class(verb: str, material: str) -> str:
    (klass,) = [p for p in PARENTS[material] if p in AXIS[verb]]
    return klass


def outcome_of(verb: str, klass: str, condition: str, purpose: str) -> str | None:
    word = EFFECT.get((verb, klass, condition, purpose))
    return OUTCOME[word] if word else None


def applications(verb: str, klass: str, condition: str, purpose: str, times: str) -> list[str]:
    """The outcome words the effect leaves, applied `times` times in turn.

    Each application starts from the condition the last one left, and stops
    early where no rule covers it — either because the table is empty there or
    because what was left is not a condition a situation can be in.

    Written once and read by both `core_rules` and `sample`, which is the
    invariant that makes this a world rather than a dataset with a checker
    beside it: the rules and the corpus cannot disagree because they are the
    same computation.
    """
    out: list[str] = []
    here = condition
    for _ in range(ITERS.index(times) + 1):
        word = outcome_of(verb, klass, here, purpose)
        if word is None:
            break
        out.append(word)
        here = word[1:]
        if here not in STATED:
            break
    return out


# -- the three projections ----------------------------------------------------


def names() -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {"Human": HANDS}
    for group in (NAMES, TOOLS, PLACES, GOALS):
        out.update(group)
    return out


def dictionary() -> str:
    """The knowledge layer: what class each name is in, and nothing else.

    Not the condition, which is a fact about the situation rather than about
    the name, and is stated by the situation. The outcome words' states are
    here because they are marked and so are fetched when they appear, exactly
    as in `basics`.
    """
    lines = [
        f"FACT: State tgt:{name} is:{klass}"
        for klass, members in names().items()
        for name in members
    ]
    lines += [
        f"FACT: State tgt:{word} is:{state}" for word, state in OUTCOME_STATE.items()
    ]
    return "\n".join(lines)


def core_rules() -> str:
    """The instinct. No name appears in it.

    Four kinds of rule. One per cell of the effect table, carrying the place,
    the tool, the purpose and the aspect in its premise. One per (verb, class)
    for the wrong tool — `!>` for the effect that is blocked and `->` for what
    takes its place. One per (verb, class) for an unfinished action, which
    blocks the effect the same way and leaves the process instead. And the
    cascade, keyed on the state of what was produced.

    Nothing says what happens in the wrong place, or under `mod:Cannot`. That
    is the point: the rule set is silent there, so nothing is licensed, and the
    derivation is empty — for two different reasons that look the same from
    outside and have to be told apart from the input.
    """
    lines = ["FACT: State tgt:Human is:Animate"]
    lines += [
        f"FACT: State tgt:{material} is:{parent}"
        for material, parents in PARENTS.items()
        for parent in parents
    ]
    for (verb, klass, condition, purpose) in sorted(EFFECT):
        for times in ITERS:
            words = applications(verb, klass, condition, purpose, times)
            if not words:
                continue
            # `iter:Twice` licenses both applications in one rule. The second
            # cannot be a rule of its own keyed on the condition the first
            # left: that condition is nowhere stated — the situation states
            # the condition the thing *started* in, and `Become agt:X.'Scored`
            # is an event and not a `State`. Thirteen derivations in four
            # hundred failed to ground on exactly that before this was noticed.
            grown = "It"
            chain = []
            for word in words:
                grown = f"{grown}.{word}"
                chain.append(f"Result: Become agt:{grown}")
            for modal in ("Must", "May"):
                lines.append(
                    f"RULE: when:(State tgt:Every.{klass}.Thing<T> is:{condition})"
                    f" Action: {verb} agt:Every.Animate.Thing tgt:It<T>"
                    f" tool:Every.{NEEDS_TOOL[verb]}.Thing"
                    f" loc:Every.{NEEDS_PLACE[verb]}.Thing"
                    f" goal:Every.{purpose}.Thing asp:Done mod:{modal}"
                    f" iter:{times} -> " + " -> ".join(chain)
                )
    wrong = {"Keen": "Blunt", "Blunt": "Keen"}
    for verb in VERBS:
        for klass in AXIS[verb]:
            lines.append(
                f"RULE: Action: {verb} agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
                f" tool:Every.{wrong[NEEDS_TOOL[verb]]}.Thing"
                f" loc:Every.{NEEDS_PLACE[verb]}.Thing"
                f" !> Result: Become agt:It.Changed"
                f" -> Result: Deform tgt:It reason:Wrong.Tool"
            )
            lines.append(
                f"RULE: Action: {verb} agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
                f" tool:Every.{NEEDS_TOOL[verb]}.Thing"
                f" loc:Every.{NEEDS_PLACE[verb]}.Thing asp:Ongoing"
                f" !> Result: Become agt:It.Changed"
                f" -> Result: Underway tgt:It"
            )
    for state, steps in TAIL.items():
        for i, step in enumerate(steps):
            before = (
                f"Become agt:Every.{state}.Thing" if i == 0
                else f"{steps[i - 1]} tgt:Every.Thing"
            )
            lines.append(f"RULE: Action: {before} -> Result: {step} tgt:It")
    return "\n".join(lines)


# -- drawing a situation ------------------------------------------------------


def C(*segments: str, index: str | None = None) -> Concept:
    return Concept(tuple(segments), index=index)


def ev(verb: str, **slots: Concept) -> Event:
    return Event(C(verb), frozenset(slots.items()))


@dataclass(frozen=True)
class Sample:
    action: Event
    condition: str
    # why the derivation looks as it does. Reported apart, because an accuracy
    # averaged over these says almost nothing: the empty ones can be had for
    # free by writing nothing, and there are three unrelated ways to earn one.
    why: str   # effect | blocked | unfinished | no-rule | wrong-place | forbidden
    result: Pipeline | None

    def meaning(self) -> Pipeline:
        if self.result is None:
            return Pipeline((self.action,), ())
        return Pipeline(
            (self.action,) + self.result.events, ("->",) + self.result.connectors
        )

    def words(self) -> list[str]:
        out = [self.action.verb.segments[-1]]
        for _, value in sorted(self.action.slots, key=lambda kv: kv[0]):
            if isinstance(value, Concept):
                out += list(value.segments)
        return out


def sample(rng: random.Random, pool: set[str] | None = None) -> Sample:
    """One situation, with the gates set so that no single answer is cheap.

    The right place and the right tool are drawn three times in four rather
    than one in two. Left even, three quarters of the corpus does nothing and a
    model that writes nothing scores three quarters of it, which is a corpus
    that measures the prior and not the model.
    """
    def pick(members):
        allowed = [n for n in members if pool is None or n in pool]
        return rng.choice(allowed or list(members))

    def gate(right: str, groups) -> str:
        other = [k for k in groups if k != right]
        return right if rng.random() < 0.82 else rng.choice(other)

    verb = rng.choice(VERBS)
    material = rng.choice(tuple(NAMES))
    condition = rng.choice(STATED)
    tool_class = gate(NEEDS_TOOL[verb], TOOLS)
    place_class = gate(NEEDS_PLACE[verb], PLACES)
    purpose = rng.choice(tuple(GOALS))
    aspect = "Done" if rng.random() < 0.75 else "Ongoing"
    modal = rng.choices(MODALS, weights=(5, 5, 2))[0]
    times = "Twice" if rng.random() < 0.35 else "Once"

    target = pick(NAMES[material])
    action = ev(
        verb,
        agt=C(pick(HANDS)), tgt=C(target), tool=C(pick(TOOLS[tool_class])),
        loc=C(pick(PLACES[place_class])), goal=C(pick(GOALS[purpose])),
        asp=C(aspect), mod=C(modal), iter=C(times),
    )
    nothing = lambda why: Sample(action, condition, why, None)  # noqa: E731
    if modal == "Cannot":
        return nothing("forbidden")
    if place_class != NEEDS_PLACE[verb]:
        return nothing("wrong-place")
    if tool_class != NEEDS_TOOL[verb]:
        blocked = ev("Deform", tgt=C(target), reason=C("Wrong", "Tool"))
        return Sample(action, condition, "blocked", Pipeline((blocked,), ()))
    if aspect == "Ongoing":
        return Sample(action, condition, "unfinished",
                      Pipeline((ev("Underway", tgt=C(target)),), ()))

    words = applications(verb, axis_class(verb, material), condition, purpose, times)
    if not words:
        return nothing("no-rule")
    events: list[Event] = []
    grown: tuple[str, ...] = (target,)
    for word in words:
        grown = grown + (word,)
        events.append(ev("Become", agt=C(*grown)))
    steps = TAIL[OUTCOME_STATE[grown[-1]]]
    events += [ev(step, tgt=C(*grown)) for step in steps]
    return Sample(action, condition, "effect",
                  Pipeline(tuple(events), ("->",) * (len(events) - 1)))
