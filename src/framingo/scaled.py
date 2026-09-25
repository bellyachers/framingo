"""The same world, at whatever size is asked for.

`basics.py` is written out by hand, which is worth keeping: eleven classes with
names one recognises are readable, and reading them is how three separate
design errors were caught. But it cannot answer the question it raises. Four
verbs and ten classes make forty outcomes, and forty outcomes fit in the
weights, so nothing there distinguishes a model that looks a name's class up
and applies a rule from one that has memorised the whole table.

Here the tables are generated, so the number of classes is a dial. The content
is arbitrary — outcome words are `Ou007`, classes are `Cl012` — and that is
fine, because **what is being varied is the size of the structure, not its
shape.** Names still belong to classes, a dictionary still holds only the
binding, the core still speaks of classes and names nothing.

That is what separates this from `instantiation.py`, which removed the world
rather than enlarging it. Nothing is taken away here.

**What the dial is for.** Raise the number of classes and the table of
(verb, class) outcomes grows past what a model of a given size can hold. A
model that reads a name's class from the dictionary and applies a rule should
survive that, since it never held the table; one that memorised the composite
should not. So the curve of accuracy against class count is the measurement
that tells the two apart — the one the hand-written world is too small to make.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .syntax import Concept, Event, Pipeline


@dataclass(frozen=True)
class World:
    """Everything the generators need, at one size."""

    parents: dict[str, tuple[str, ...]]
    names: dict[str, tuple[str, ...]]
    modifiers: tuple[str, ...]
    verbs: tuple[str, ...]
    takes: dict[str, tuple[str, ...]]
    outcomes: dict[str, dict[str, str]]
    outcome_class: dict[str, str]
    tail: dict[str, tuple[str, ...]]
    # How often a thing wears the modifier that goes with its class. At 0 the
    # modifiers say nothing and the dictionary is the only way to know what
    # something is; above 0 they leak, and a model can pick the class up from
    # use, as a language model picks up that `Big` goes with mountains and not
    # with ants. That knowledge is in no dictionary and in no rule, so nothing
    # can trace an output to it — the point of the dial is to find out whether
    # a model takes it, and how much of the lookup it then stops doing.
    leak: float = 0.0
    signature: dict[str, str] = None  # type: ignore[assignment]

    @property
    def n_rules(self) -> int:
        chain = sum(len(steps) for steps in self.tail.values())
        return sum(len(table) for table in self.outcomes.values()) + chain


def make(
    n_classes: int = 10,
    n_verbs: int = 4,
    names_per_class: int = 10,
    n_states: int = 4,
    seed: int = 0,
    leak: float = 0.0,
    marked: float = 0.25,
) -> World:
    """A world of the given size.

    Classes are grouped under a few parents so that membership still has to be
    closed transitively, as it does in the hand-written world; without that the
    checker's class inference would go untested at every size.
    """
    rng = random.Random(f"{seed}-world-{n_classes}-{n_verbs}")
    classes = tuple(f"Cl{i:03}" for i in range(n_classes))
    supers = tuple(f"Su{i:02}" for i in range(max(2, n_classes // 4)))
    parents = {k: (rng.choice(supers),) for k in classes}

    names = {
        k: tuple(f"'Nm{i * names_per_class + j:04}" for j in range(names_per_class))
        for i, k in enumerate(classes)
    }
    # at least one per class, so a signature is not shared and the leak is
    # a clean dial rather than a muddy one
    modifiers = tuple(f"Md{i:03}" for i in range(max(8, n_classes)))
    verbs = tuple(f"Vb{i:02}" for i in range(n_verbs))

    # Each verb takes some classes and leaves its own outcome on each. Some
    # share of the outcomes carries the mark, so that a derivation keeps
    # bringing in words the model does not hold and has to stop for. The share
    # is a dial because it sets how many examples exercise the mid-derivation
    # lookup at all: at the natural 0.25 only about one in nine does, once a
    # tail is needed too, and a control scored over the other eight says
    # nothing. Turn it to 1 to measure the lookup; leave it low to keep the
    # mixture a vocabulary really has.
    words = iter(range(10_000))
    outcomes: dict[str, dict[str, str]] = {}
    takes: dict[str, tuple[str, ...]] = {}
    for verb in verbs:
        taken = tuple(rng.sample(classes, max(2, len(classes) * 3 // 4)))
        takes[verb] = taken
        table = {}
        for klass in taken:
            word = f"Ou{next(words):04}"
            table[klass] = f"'{word}" if rng.random() < marked else word
        outcomes[verb] = table

    states = tuple(f"St{i:02}" for i in range(n_states))
    outcome_class = {
        word: rng.choice(states) for table in outcomes.values() for word in table.values()
    }
    steps = tuple(f"Vc{i:02}" for i in range(n_states * 2))
    tail: dict[str, tuple[str, ...]] = {}
    for i, state in enumerate(states):
        # One or two further events, never none. A state whose tail is empty
        # cannot test whether the model read what it was told that state was:
        # there is nothing left to write either way. The hand-written world has
        # the same property, and keeping it here is what makes the two
        # comparable rather than a kindness to the model.
        length = 1 + i % 2
        tail[state] = tuple(steps[i * 2 : i * 2 + length])
    # one modifier per class, for the leak
    signature = {k: modifiers[i % len(modifiers)] for i, k in enumerate(classes)}
    return World(
        parents, names, modifiers, verbs, takes, outcomes, outcome_class, tail,
        leak, signature,
    )


# -- the same four functions the hand-written world has -----------------------


def C(*segments: str, determiner: str | None = None, index: str | None = None) -> Concept:
    return Concept(tuple(segments), determiner=determiner, index=index)


def ev(verb: str, **slots: Concept) -> Event:
    return Event(C(verb), frozenset(slots.items()))


def classes_of(w: World, name: str) -> tuple[str, ...]:
    for klass, members in w.names.items():
        if name in members:
            return (klass,)
    return ()


def ancestors(w: World, klass: str) -> set[str]:
    out: set[str] = set()
    stack = [klass]
    while stack:
        for parent in w.parents.get(stack.pop(), ()):
            if parent not in out:
                out.add(parent)
                stack.append(parent)
    return out


def is_marked(word: str) -> bool:
    return word.startswith("'")


def dictionary(w: World) -> str:
    """Name to class, and the class of every marked outcome. Nothing else."""
    lines = [
        f"FACT: State tgt:{name} is:{klass}"
        for klass, members in w.names.items()
        for name in members
    ]
    lines += [
        f"FACT: State tgt:{word} is:{state}"
        for word, state in w.outcome_class.items()
        if is_marked(word)
    ]
    return "\n".join(lines)


def core_rules(w: World) -> str:
    """The class hierarchy, the unmarked outcomes' states, and one rule per
    (verb, class) and per step of each tail. No name appears anywhere."""
    lines = [
        f"FACT: State tgt:{klass} is:{parent}"
        for klass, parents in w.parents.items()
        for parent in parents
    ]
    lines += [
        f"FACT: State tgt:{word} is:{state}"
        for word, state in w.outcome_class.items()
        if not is_marked(word)
    ]
    for verb, table in w.outcomes.items():
        for klass, word in table.items():
            lines.append(
                f"RULE: Action: {verb} agt:Every.Thing tgt:Every.{klass}.Thing"
                f" -> Result: Become agt:It.{word}"
            )
    for state, steps in w.tail.items():
        for i, step in enumerate(steps):
            before = f"Become agt:Every.{state}.Thing" if i == 0 else f"{steps[i - 1]} tgt:Every.Thing"
            lines.append(f"RULE: Action: {before} -> Result: {step} tgt:It")
    return "\n".join(lines)


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
        out = [self.action.verb.segments[-1]]
        for _, value in sorted(self.action.slots, key=lambda kv: kv[0]):
            if isinstance(value, Concept):
                out += list(value.segments)
        return out


def thing(w: World, rng: random.Random, klass: str, pool: set[str] | None) -> Concept:
    members = [n for n in w.names[klass] if pool is None or n in pool]
    name = rng.choice(members)
    if rng.random() >= 0.5:
        return C(name)
    if w.leak and rng.random() < w.leak:
        return C(w.signature[klass], name)
    return C(rng.choice(w.modifiers), name)


def any_thing(w: World, rng: random.Random, pool: set[str] | None) -> Concept:
    return thing(w, rng, rng.choice(tuple(w.names)), pool)


def sample(w: World, rng: random.Random, pool: set[str] | None = None) -> Sample:
    verb = rng.choice(w.verbs)
    klass = rng.choice(w.takes[verb])
    action = ev(verb, agt=any_thing(w, rng, pool), tgt=thing(w, rng, klass, pool))
    (target,) = action.get("tgt")
    word = w.outcomes[verb][klass]
    became = ev("Become", agt=C(*target.segments, word))
    steps = w.tail[w.outcome_class[word]]
    rest = tuple(ev(step, tgt=C(*target.segments, word)) for step in steps)
    return Sample(action, Pipeline((became,) + rest, ("->",) * len(rest)), "->")


# -- the corpus ---------------------------------------------------------------

HELD_BACK = 0.25
_MARKED = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")


def pools(w: World, seed: int) -> tuple[set[str], set[str]]:
    """Names to train on, and names held back — a quarter of every class."""
    rng = random.Random(f"{seed}-names")
    train: set[str] = set()
    unseen: set[str] = set()
    for members in w.names.values():
        shuffled = list(members)
        rng.shuffle(shuffled)
        cut = max(1, round(len(shuffled) * HELD_BACK))
        unseen |= set(shuffled[:cut])
        train |= set(shuffled[cut:])
    return train, unseen


def build(
    w: World,
    n_train: int = 8000,
    n_iid: int = 1000,
    n_unseen: int = 1000,
    seed: int = 0,
):
    """Records in the shape `experiments/train.py --corpus scaled` reads.

    The same four stretches the hand-written world uses: what the parser handed
    over, what the model writes before it has to stop, what comes back, and the
    rest. Marked words are renumbered per example, and the way back is kept so
    that grading can undo it before asking the core anything.
    """
    from .basics import normalise  # noqa: PLC0415
    from .corpus import Record  # noqa: PLC0415
    from .render import tagged_event, tagged_pipeline  # noqa: PLC0415

    entries = {}
    for line in dictionary(w).splitlines():
        entries[line.split("tgt:")[1].split()[0]] = line
    train_pool, unseen_pool = pools(w, seed)
    rng = random.Random(seed)

    def record(drawn: Sample, split: str) -> Record:
        given = [x for x in drawn.words() if is_marked(x)]
        handed_in = " ".join(entries[x] for x in dict.fromkeys(given) if x in entries)
        action = tagged_event(drawn.action, rng)
        events = list(drawn.result.events)
        connectors = drawn.result.connectors

        seen = set(given)
        cut = len(events)
        for i, event in enumerate(events):
            fresh = {x for x in _MARKED.findall(str(event)) if x not in seen}
            if fresh:
                cut, seen = i + 1, seen | fresh
                break
        handed_mid = " ".join(
            entries[x] for x in sorted(seen - set(given)) if x in entries
        )

        head = f"{drawn.connector} {tagged_pipeline(Pipeline(tuple(events[:cut]), connectors[: cut - 1]))}"
        tail = (
            f"{connectors[cut - 1]} {tagged_pipeline(Pipeline(tuple(events[cut:]), connectors[cut:]))}"
            if cut < len(events)
            else ""
        )
        out = f"{drawn.connector} {tagged_pipeline(drawn.result)}"
        meaning = str(drawn.meaning())
        (action, handed_in, out, meaning, head, handed_mid, tail), names = normalise(
            [action, handed_in, out, meaning, head, handed_mid, tail]
        )
        return Record(
            split=split, meaning=meaning, tagged_in=action, tagged_out=out,
            word_order_in=action, word_order_out=out, passive=False,
            query="", answer=handed_in, head=head, handed=handed_mid, tail=tail,
            names=names,
        )

    def draw(pool: set[str], seen: set[str], count: int, split: str):
        out = []
        while len(out) < count:
            drawn = sample(w, rng, pool)
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
