"""Basic information about basic vocabulary, and a dictionary that holds names.

`world.py` gives a model nine kinds and asks it to learn what happens to them.
With so few names a model can learn the names themselves and never form the
class, and nothing distinguishes the two. This world is built the other way
round: **many names, each seen rarely, and every consequence stated about the
class rather than the name.** The only way to be right about a name seen twice
is to have learnt what its class does.

The split the maintainer drew (2026-09-25) decides what goes where:

- **Binding a name to a class is knowledge.** It is arbitrary, unbounded and
  particular — no amount of reasoning yields "John is a human" — so it lives in
  the dictionary and is fetched. `dictionary()` is that, and nothing else.
- **What follows from belonging to a class is the minimal core's.** It is
  general and finite, so a model can hold it. `core_rules()` is that, and
  nothing else. It is written about classes and mentions no name at all.

A word that is already general has nothing to fetch: asking about `Big` returns
nothing, because `Big` is not a name of anything, it is a way things are. The
model is not asked to know that in advance. It asks about every word, and some
answers are empty — which costs a lookup in a table and no judgement, and
judgement is the thing being kept out.

**The test this world exists for**: a name held out of training entirely. Its
class is fetched like any other, and a model that has learnt what the class
does should be right about a word it has never seen.

Modifiers survive everything here, unlike in `world.py` where a division keeps
the intrinsic ones and destroys the structural ones. That distinction cannot be
written as a class rule — `Become agt:It.Slice` carries the whole antecedent
across, and the language has no way to say "keep only the parts of it that are
intrinsic". Saying it per word is what forced `world.core_rules` to enumerate,
from 150 rules to 440. It is the same kind of gap as the one `&>` closed, it is
recorded as such, and this world steps around it rather than paying for it.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .render import tagged_event, tagged_pipeline
from .syntax import Concept, Event, Pipeline, Statement, is_instinct

# -- what there is to be ------------------------------------------------------
#
# Each class names its parents. The checker closes the relation transitively,
# so a rule about `Animate.Thing` fires on a cat by way of `Creature`.

PARENTS: dict[str, tuple[str, ...]] = {
    "Human": ("Animate",),
    "Creature": ("Animate",),
    "Fruit": ("Edible", "Cuttable"),
    "Staple": ("Edible", "Cuttable"),
    "Vessel": ("Break-prone", "Container"),
    "Blade": ("Sharp", "Tool"),
    "Club": ("Blunt", "Tool"),
    "Garment": ("Wearable",),
    "Opening": ("Openable",),
    "Liquid": ("Pourable",),
    "Place": (),
}

# -- what the names are -------------------------------------------------------
#
# Deliberately many. A name is meant to be met a handful of times, so that
# nothing about it can be learnt except through its class.

# Every name carries the mark: it is not a word the model holds. Classes and
# modifiers do not, because they are what the model reasons in.
NAMES: dict[str, tuple[str, ...]] = {
    "Human": (
        "'John", "'Mary", "'Anna", "'Ben", "'Carl", "'Dana", "'Emma", "'Frank", "'Grace",
        "'Henry", "'Iris", "'Jack", "'Kate", "'Leo", "'Mia", "'Noah", "'Olive", "'Paul",
        "'Quinn", "'Rose", "'Sam", "'Tina", "'Uma", "'Victor", "'Wendy", "'Zack",
    ),
    "Creature": ("'Cat", "'Dog", "'Bird", "'Fish", "'Mouse", "'Horse", "'Sheep", "'Goat", "'Duck", "'Frog"),
    "Fruit": ("'Apple", "'Pear", "'Plum", "'Peach", "'Grape", "'Melon", "'Lemon", "'Mango", "'Cherry", "'Fig"),
    "Staple": ("'Bread", "'Cheese", "'Cake", "'Meat", "'Yam", "'Bean", "'Corn", "'Onion"),
    "Vessel": ("'Glass", "'Cup", "'Bottle", "'Plate", "'Bowl", "'Jar", "'Vase", "'Mug", "'Dish", "'Flask"),
    "Blade": ("'Knife", "'Razor", "'Shears", "'Axe", "'Saw", "'Chisel"),
    "Club": ("'Ruler", "'Spoon", "'Stick", "'Rod", "'Hammer", "'Brick"),
    "Garment": ("'Shirt", "'Shoe", "'Hat", "'Sock", "'Coat", "'Glove", "'Scarf", "'Belt"),
    "Opening": ("'Door", "'Window", "'Box", "'Gate", "'Lid", "'Drawer"),
    "Liquid": ("'Water", "'Milk", "'Juice", "'Oil", "'Tea", "'Wine"),
    "Place": ("'Kitchen", "'Garden", "'Hall", "'Yard", "'Attic", "'Cellar", "'Porch", "'Study"),
}

# Ways things are, rather than things there are. Nothing to look up.
MODIFIERS = ("Red", "Green", "Blue", "White", "Brown", "Big", "Small", "Tall", "Round", "Soft", "Hard")

VERBS = ("Cut", "Eat", "Drop", "Carry")

# What a verb leaves behind, per class of target. **Every verb's outcome turns
# on the class**, and that is the whole point of the table.
#
# A first version let the verb decide almost everything — cutting made slices
# whatever was cut, eating left nothing, opening opened — and the class only
# mattered for whether a dropped thing broke. A model then learnt the physics
# without consulting the dictionary at all, and was right to: lying in the
# dictionary cost it 8.5% of its accuracy, which is how little of the world
# turned on what the dictionary knew. Verbs whose target class is fixed by the
# verb were removed for the same reason: `Wear` only ever took a garment, so
# knowing it was a garment told a model nothing it could not read off `Wear`.
#
# If the class is to be fetched, the class has to matter.
# Some outcomes are marked. They are words the model does not hold, and —
# unlike a marked word in the input — they cannot have been fetched in advance,
# because they were not there to fetch: they come into existence only once the
# first step has been taken. This is the case the maintainer named, where what
# has to be looked up is only knowable after thinking.
#
# Nothing about that requires a judgement. The rule is the same as for a marked
# word in the input: if it carries the mark, look it up. Whether it arrived from
# outside or was just derived makes no difference to its shape.
OUTCOMES: dict[str, dict[str, str]] = {
    "Cut": {"Fruit": "Slice", "Staple": "Chunk", "Garment": "'Scrap"},
    "Eat": {"Fruit": "Core", "Staple": "'Crumb"},
    "Drop": {
        "Vessel": "'Shard", "Fruit": "Bruise", "Staple": "'Crumb", "Garment": "Heap",
        "Opening": "Bang", "Liquid": "'Splash", "Blade": "Clatter", "Club": "Thud",
        "Human": "Stumble", "Creature": "Startle",
    },
    "Carry": {
        "Human": "Held", "Creature": "Held", "Vessel": "'Rattle", "Fruit": "Cradled",
        "Staple": "Cradled", "Garment": "Draped", "Opening": "Hauled",
        "Liquid": "'Sloshed", "Blade": "Sheathed", "Club": "Shouldered",
    },
}

# What kind of state an outcome leaves a thing in, and what then happens to it.
#
# This is the second hop. A first world stopped at the outcome, so every answer
# was one rule applied once and nothing had to be derived in order to derive
# something else. Here the outcome's own class decides what follows, so a model
# that gets the first step wrong gets the whole tail wrong — which is what makes
# the chain a chain rather than a longer template.
#
# Each step uses a *different* verb. Appending to the same concept instead
# (`X.Piece` then `X.Piece.Swept`) leaves the first rule's premise still
# matching its own conclusion, and it fires again on what it just produced.
OUTCOME_CLASS: dict[str, str] = {
    "'Shard": "Broken", "'Crumb": "Broken", "Clatter": "Broken",
    "Slice": "Divided", "Chunk": "Divided", "Core": "Divided", "'Scrap": "Divided",
    "Bruise": "Marked", "Heap": "Marked", "'Splash": "Marked", "Thud": "Marked",
    "Bang": "Marked", "Stumble": "Marked", "Startle": "Marked",
    "Held": "Moved", "Cradled": "Moved", "Draped": "Moved", "Sheathed": "Moved",
    "Shouldered": "Moved", "Hauled": "Moved", "'Rattle": "Moved", "'Sloshed": "Moved",
}

# The tail each state leads to, as verbs applied in turn to the same thing.
TAIL: dict[str, tuple[str, ...]] = {
    "Broken": ("Sweep", "Discard"),
    "Divided": ("Dry", "Store"),
    "Marked": ("Wipe",),
    "Moved": (),
}

# What each verb may take, and so which names the sampler may draw.
TAKES: dict[str, tuple[str, ...]] = {verb: tuple(table) for verb, table in OUTCOMES.items()}


def outcome(verb: str, name: str) -> str | None:
    """The word a verb leaves on a thing of that name's class."""
    table = OUTCOMES[verb]
    for klass in classes_of(name):
        if klass in table:
            return table[klass]
    return None


def C(*segments: str, determiner: str | None = None, index: str | None = None) -> Concept:
    return Concept(tuple(segments), determiner=determiner, index=index)


def ev(verb: str, **slots: Concept) -> Event:
    return Event(C(verb), frozenset(slots.items()))


def classes_of(name: str) -> tuple[str, ...]:
    """The class a name is directly a member of."""
    for klass, names in NAMES.items():
        if name in names:
            return (klass,)
    return ()


def ancestors(klass: str) -> set[str]:
    out: set[str] = set()
    stack = [klass]
    while stack:
        for parent in PARENTS.get(stack.pop(), ()):
            if parent not in out:
                out.add(parent)
                stack.append(parent)
    return out


def dictionary(names: tuple[str, ...] | None = None) -> str:
    """The knowledge layer: which class each name belongs to, and nothing more.

    One line per name, and that line is the only thing about a name that could
    not have been worked out. Not what the class implies — the core holds that
    — and **not the classes' own parents either**: "a human is animate" is not
    a fact about a name, it is the shape of the world, general and finite, so
    it belongs with the instinct rather than in the book. A dictionary that
    carried it would be answering a question nobody asked about `John`.
    """
    lines = []
    for klass, members in NAMES.items():
        for name in members:
            if names is None or name in names:
                lines.append(f"FACT: State tgt:{name} is:{klass}")
    # and the marked outcomes, which are looked up the same way although they
    # arrive from a derivation rather than from the input
    lines.append(outcome_classes(marked=True))
    return "\n".join(lines)


def outcome_classes(marked: bool) -> str:
    """What state each outcome leaves behind.

    Split by the mark, as everything else is. An unmarked outcome is a word the
    model holds, so what it is a kind of belongs to the core. A marked one it
    does not hold, so that belongs to the dictionary — and cannot be fetched
    before the model has taken the step that produces it.
    """
    return "\n".join(
        f"FACT: State tgt:{word} is:{state}"
        for word, state in OUTCOME_CLASS.items()
        if is_instinct(word) is not marked
    )


def hierarchy() -> str:
    """Which class is a kind of which. Part of the core, not of the dictionary.

    Arbitrary bindings are fetched; the structure they are bound into is held.
    """
    return "\n".join(
        f"FACT: State tgt:{klass} is:{parent}"
        for klass, parents in PARENTS.items()
        for parent in parents
    )


# -- what follows from being a thing of that kind -----------------------------
#
# The minimal core. Every rule is about a class; not one mentions a name. That
# is what makes the dictionary the only place a name can be known, and it is
# why this core is short where `world.core_rules` had to enumerate.

def _core_lines() -> list[str]:
    """The core, written out of the same table the world uses.

    One rule per verb and class, which is what a class-level rule language buys:
    the same physics needed 440 rules when it had to be stated per name.
    """
    lines = []
    for klass, left in OUTCOMES["Cut"].items():
        lines.append(
            f"RULE: Action: Cut agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
            f" tool:Every.Sharp.Thing -> Result: Become agt:It.{left}"
        )
        lines.append(
            f"RULE: Action: Cut agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
            f" tool:Every.Blunt.Thing !> Result: Become agt:It.{left}"
            " -> Result: Deform tgt:It reason:Inappropriate.Tool"
        )
    for klass, left in OUTCOMES["Eat"].items():
        lines.append(
            f"RULE: Action: Eat agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
            f" -> Result: Become agt:It.{left}"
        )
    for klass, left in OUTCOMES["Drop"].items():
        lines.append(
            f"RULE: Action: Drop agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
            f" -> Result: Fall tgt:It dst:Floor -> Result: Become agt:It.{left}"
        )
        lines.append(
            f"RULE: Action: Drop agt:Every.Animate.Thing tgt:Every.{klass}.Thing"
            f" src:Every.Thing<S> -> Result: Fall tgt:It dst:Floor src:It<S>"
            f" -> Result: Become agt:It.{left}"
        )
    for state, steps in TAIL.items():
        previous = f"Every.{state}.Thing"
        for i, step in enumerate(steps):
            if i == 0:
                lines.append(f"RULE: Action: Become agt:{previous} -> Result: {step} tgt:It")
            else:
                lines.append(f"RULE: Action: {steps[i - 1]} tgt:Every.Thing -> Result: {step} tgt:It")
    for klass, left in OUTCOMES["Carry"].items():
        # The outcome comes first, which is both the natural order — a thing is
        # taken up before it arrives anywhere — and the only order the language
        # can express. A bare `It` resolves to the target of the nearest
        # preceding event (spec ch.3 §5.1), so after the carrier's arrival it
        # would name the carrier; and `It<T>.Held`, which would say what is
        # meant, is not writable: a concept's index comes after its whole dot
        # chain, so nothing may follow it. That is a gap in the language, of
        # the same kind as the one `&>` closed, and it is recorded as one.
        lines.append(
            f"RULE: Action: Carry agt:Every.Animate.Thing<A> tgt:Every.{klass}.Thing"
            f" dst:Every.Place.Thing<P> -> Result: Become agt:It.{left}"
            f" -> Result: At tgt:It loc:It<P> &> Result: At tgt:It<A> loc:It<P>"
        )
    return lines


def core_rules() -> str:
    """The instinct: the shape of the world, and what follows from it.

    The class hierarchy is part of it, for the reason `hierarchy` gives.
    """
    return hierarchy() + "\n" + outcome_classes(marked=False) + "\n" + "\n".join(_core_lines())


# -- drawing a situation ------------------------------------------------------


@dataclass(frozen=True)
class Sample:
    action: Event
    result: Pipeline
    connector: str

    def meaning(self) -> Pipeline:
        return Pipeline(
            (self.action,) + self.result.events, (self.connector,) + self.result.connectors
        )

    def words(self) -> list[str]:
        """Every word of the action, in the order it is written.

        What a model is asked to look up: all of them, including the ones with
        nothing behind them.
        """
        out: list[str] = [self.action.verb.segments[-1]]
        for _, value in sorted(self.action.slots, key=lambda kv: kv[0]):
            if isinstance(value, Concept):
                out += list(value.segments)
        return out


def _members(klass: str) -> list[str]:
    """Every name that is a member of a class, directly or by inheritance.

    ``Thing`` is the universal class. It is never declared as a parent because
    a pattern ending in ``Thing`` with no modifiers already matches anything
    (`grounding._pattern_matches`), so nothing has to say that a cup is a
    thing.
    """
    if klass == "Thing":
        return [name for names in NAMES.values() for name in names]
    return [
        name
        for own, names in NAMES.items()
        if own == klass or klass in ancestors(own)
        for name in names
    ]


def thing(rng: random.Random, klass: str, pool: set[str] | None = None) -> Concept:
    names = [n for n in _members(klass) if pool is None or n in pool]
    name = rng.choice(names)
    return C(rng.choice(MODIFIERS), name) if rng.random() < 0.5 else C(name)


def consequence(action: Event) -> tuple[Pipeline, str]:
    """What follows, and whether the first step happened or was prevented.

    Every branch reads the outcome out of `OUTCOMES`, so nothing here can be
    predicted from the verb alone.
    """
    verb = action.verb.segments[0]
    (target,) = action.get("tgt")
    (agent,) = action.get("agt")
    left = outcome(verb, target.segments[-1])
    assert left is not None, f"{verb} has no outcome for {target}"
    left_concept = C(*target.segments, left)
    became = ev("Become", agt=left_concept)
    tail = tuple(ev(step, tgt=left_concept) for step in TAIL[OUTCOME_CLASS[left]])
    if verb == "Cut":
        (tool,) = action.get("tool")
        if "Sharp" in _all_classes(tool.segments[-1]):
            return Pipeline((became,) + tail, ("->",) * len(tail)), "->"
        # nothing was divided, so nothing follows from having been divided
        deformed = ev("Deform", tgt=target, reason=C("Inappropriate", "Tool"))
        return Pipeline((became, deformed), ("->",)), "!>"
    if verb == "Eat":
        return Pipeline((became,) + tail, ("->",) * len(tail)), "->"
    if verb == "Drop":
        src = {"src": s for s in action.get("src")}
        fall = ev("Fall", tgt=target, dst=C("Floor"), **src)
        return Pipeline((fall, became) + tail, ("->",) * (1 + len(tail))), "->"
    if verb == "Carry":
        # taken up, then both arrive at once (see `_core_lines` on the order)
        (place,) = action.get("dst")
        arrive = (ev("At", tgt=target, loc=place), ev("At", tgt=agent, loc=place))
        return Pipeline((became,) + arrive + tail, ("->", "&>") + ("->",) * len(tail)), "->"
    raise ValueError(f"no physics for {verb}")


def _all_classes(name: str) -> set[str]:
    own = classes_of(name)
    return set(own) | {a for k in own for a in ancestors(k)}


def sample(rng: random.Random, pool: set[str] | None = None) -> Sample:
    """One situation, drawn from the names available."""
    verb = rng.choice(VERBS)
    klass = rng.choice(TAKES[verb])
    slots: dict[str, Concept] = {"agt": thing(rng, "Animate", pool), "tgt": thing(rng, klass, pool)}
    if verb == "Cut":
        slots["tool"] = thing(rng, "Tool", pool)
    elif verb == "Carry":
        slots["dst"] = thing(rng, "Place", pool)
    elif verb == "Drop" and rng.random() < 0.4:
        slots["src"] = thing(rng, "Opening", pool)
    action = ev(verb, **slots)
    result, connector = consequence(action)
    return Sample(action, result, connector)


# -- the corpus ---------------------------------------------------------------

HELD_BACK = 0.25
_MARKED = re.compile(r"'[A-Za-z][A-Za-z0-9_-]*")


def normalise(texts: list[str]) -> tuple[list[str], dict[str, str]]:
    """Rewrite every marked word as a variable, the same way across one example.

    `'John` becomes `'A`, the next new name `'B`, and so on in the order they
    are first written. Two things follow.

    A model's vocabulary stops growing with the world's — it holds `'A`..`'H`
    and nothing else — so no name ever arrives with an untrained embedding.
    Measured before this existed: a model got the physics of a held-out name
    exactly right and then wrote a *different*, familiar name in the answer,
    because it could not carry the unfamiliar token across. That was a failure
    of the tokeniser's making, not of reasoning, and it hid whatever the
    experiment was meant to see.

    And a model can learn **nothing** about a name, because `'A` is a different
    thing in every example. "The model holds no names" stops being an intention
    and becomes a fact about what it was shown.

    Returns the rewritten texts and the way back. Grading needs the way back:
    the core is written in the world's own words, so `Become agt:It.'Crumb`
    cannot derive a model's `Become agt:'A.'C` until the renaming is undone.
    That was not visible until an outcome carried the mark, because until then
    only names were renamed and the core names none.

    The price is that a name's identity cannot outlive the example. Anything
    that tracks the same individual across turns will need this revisited.
    """
    seen: dict[str, str] = {}

    def swap(m: re.Match[str]) -> str:
        word = m.group(0)
        if word not in seen:
            seen[word] = f"'{chr(ord('A') + len(seen))}"
        return seen[word]

    return [_MARKED.sub(swap, t) for t in texts], {v: k for k, v in seen.items()}


def _pools(seed: int) -> tuple[set[str], set[str]]:
    """The names a model may be trained on, and the ones kept from it.

    Held back per class, so every class is still represented at test time and a
    failure is about the name rather than about a class never met.
    """
    rng = random.Random(f"{seed}-names")
    train: set[str] = set()
    unseen: set[str] = set()
    for names in NAMES.values():
        shuffled = list(names)
        rng.shuffle(shuffled)
        cut = max(1, round(len(shuffled) * HELD_BACK))
        unseen |= set(shuffled[:cut])
        train |= set(shuffled[cut:])
    return train, unseen


def build(
    n_train: int = 4000,
    n_iid: int = 1000,
    n_unseen: int = 1000,
    seed: int = 0,
    variables: bool = True,
):
    """Records in the shape `experiments/train.py --corpus basics` reads.

    What the parser hands over is in `answer`: the dictionary entry for every
    marked word of the action, and nothing else. There is no query turn,
    because there is no decision to make — the mark is visible before the word
    is understood, so the lookup has already happened by the time a model sees
    anything.

    - ``train``         names the model is trained on
    - ``test_iid``      those same names, situations it has not seen
    - ``test_unseen``   names held out of training entirely

    With ``variables`` the split between the last two is invisible to the
    model, which is the point of it: a name it has never met should be no
    harder than one it has met a thousand times, and if that holds the two
    figures are the same. What is then being tested is whether the class the
    dictionary supplies is used at all, which is what the scrambled control in
    `experiments/train.py` measures.
    """
    from .corpus import Record  # noqa: PLC0415

    entries = {}
    for line in dictionary().splitlines():
        entries[line.split("tgt:")[1].split()[0]] = line
    train_pool, unseen_pool = _pools(seed)
    rng = random.Random(seed)

    def record(drawn: Sample, split: str) -> Record:
        marked = [w for w in drawn.words() if not is_instinct(w)]
        handed_in = " ".join(entries[w] for w in dict.fromkeys(marked))
        action = tagged_event(drawn.action, rng)
        events = list(drawn.result.events)
        connectors = drawn.result.connectors

        # Where the derivation has to stop and look something up: the first
        # event that brings in a marked word the input did not carry. There is
        # no judgement in finding it — the mark is on the word. If nothing is
        # brought in, the stop is at the end, because the lookup happens either
        # way and only its answer is empty.
        seen = set(marked)
        cut = len(events)
        for i, event in enumerate(events):
            fresh = {w for w in _MARKED.findall(str(event)) if w not in seen}
            if fresh:
                cut = i + 1
                seen |= fresh
                break
        derived = sorted(seen - set(marked))
        handed_mid = " ".join(entries[w] for w in derived if w in entries)

        head = f"{drawn.connector} {tagged_pipeline(Pipeline(tuple(events[:cut]), connectors[: cut - 1]))}"
        tail = (
            f"{connectors[cut - 1]} {tagged_pipeline(Pipeline(tuple(events[cut:]), connectors[cut:]))}"
            if cut < len(events)
            else ""
        )
        out = f"{drawn.connector} {tagged_pipeline(drawn.result)}"
        meaning = str(drawn.meaning())
        names: dict[str, str] = {}
        if variables:
            # the action first, so the variables are numbered as they are read
            (action, handed_in, out, meaning, head, handed_mid, tail), names = normalise(
                [action, handed_in, out, meaning, head, handed_mid, tail]
            )
        handed = handed_in
        return Record(
            head=head,
            handed=handed_mid,
            tail=tail,
            names=names,
            split=split,
            meaning=meaning,
            tagged_in=action,
            tagged_out=out,
            word_order_in=action,
            word_order_out=out,
            passive=False,
            query="",
            answer=handed,
        )

    def draw(pool: set[str], seen: set[str], count: int, split: str) -> list[Record]:
        out = []
        while len(out) < count:
            drawn = sample(rng, pool)
            key = str(drawn.meaning())
            if key in seen:
                continue
            seen.add(key)
            out.append(record(drawn, split))
        return out

    seen: set[str] = set()
    out = draw(train_pool, seen, n_train, "train")
    out += draw(train_pool, seen, n_iid, "test_iid")
    out += draw(unseen_pool, set(), n_unseen, "test_unseen")
    return out
