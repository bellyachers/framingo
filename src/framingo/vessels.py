"""A world where the thing you need is not in the sentence.

`basics.py` and `scaled.py` cover two of the three ways a model reaches for
knowledge, and both are settled by **form**: a marked word in the input, which
the parser resolves before the model thinks, and a marked word the model has
just derived, which the harness resolves when the model stops. Neither calls
for a judgement. The word carries the mark, so it gets looked up.

The third way cannot be settled by form, and it is the only one that is really
a function call. The maintainer put it this way (2026-09-25):

    Function Calling is something you only discover by trying to think.
    (...) The question then is not "what is a Quokka" — this model does not
    know Quokkas, so it could not even conceive of the question. But "what
    marsupials are there other than kangaroos" it *can* ask.

So the question is about a **class**, never about a name, and it arises only
after a derivation has got far enough to want something it was never given.

**What makes it arise here.** Carrying a liquid takes a vessel. The sentence
names a carrier, a liquid and a destination, and says nothing whatever about a
vessel. The rule says what is wanted and does not say which:

    RULE: Action: Carry agt:Every.Animate.Thing tgt:Every.Liquid.Thing
          -> Result: In tgt:It loc:Any.Vessel.Thing

`Any.` is the spec's own word for "one chosen arbitrarily from the set"
(ch.3 §4.1). Nothing is added to the language to express a gap; the determiner
system has had the word for it since the first draft. What the model does with
it is ask:

    QUERY: State tgt:? is:Vessel

and the store answers with a member — under the mark, and with its class, so
the answer comes back down the very path the other two lookups use. The loop
closes.

**Why the answer has to be read.** A vessel is of some material, and the
material decides what follows: a fragile one is cushioned and steadied, a tough
one is slung. The model cannot know which until it has asked, and it cannot
write the tail until it knows. That is the difference from `scaled.py`, where
the tail was a function of the input and the lookup, though always performed,
was never needed. Here it is needed, and the reason it is needed is that **the
world holds something the sentence does not reveal** — which is the second of
the two conditions under which a lookup can matter at all.

**What this is for.** Three things, in rising order of what they settle:

1. does the derivation ask for the right class — a liquid wants a vessel, not
   a sack;
2. does it use what comes back, which the lying control answers as before;
3. **what does it do when the store has nothing.** A model that needs a vessel
   and is given none is in exactly the position a language model is in when it
   needs a citation and has none. Here it cannot invent one and be believed:
   `grounding._supply` fills an `Any.` gap only from what was handed over, so a
   vessel from nowhere grounds nothing. Whether it nonetheless *tries* is worth
   a number, and this world is where that number comes from.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .syntax import Concept, Event, Pipeline

# -- what there is ------------------------------------------------------------
#
# Three things that cannot be carried bare, and the kind of container each one
# calls for. The pairing is arbitrary, which is the point: it is knowledge
# about classes, so it belongs in the core, and nothing about the word `Liquid`
# tells you it is a vessel rather than a sack that is wanted.

NEEDS: dict[str, str] = {"Liquid": "Vessel", "Grain": "Sack", "Ember": "Pan"}

CARRIED: dict[str, tuple[str, ...]] = {
    "Liquid": tuple(f"'Lq{i:02}" for i in range(12)),
    "Grain": tuple(f"'Gr{i:02}" for i in range(12)),
    "Ember": tuple(f"'Em{i:02}" for i in range(12)),
}

# Each kind of container comes in two materials, and the material is what the
# tail turns on. A model that asked and did not read the answer knows the
# container's name and not its material, so it cannot write the tail — which is
# how this world makes the lookup necessary rather than merely habitual.
CONTAINERS: dict[str, dict[str, str]] = {
    "Vessel": {"Clay-Vessel": "Fragile", "Hide-Vessel": "Tough"},
    "Sack": {"Mesh-Sack": "Fragile", "Canvas-Sack": "Tough"},
    "Pan": {"Tin-Pan": "Fragile", "Iron-Pan": "Tough"},
}

VESSEL_NAMES: dict[str, tuple[str, ...]] = {
    kind: tuple(f"'Cn{i:02}{j}" for j in range(8))
    for i, kind in enumerate(k for kinds in CONTAINERS.values() for k in kinds)
}

CARRIERS: tuple[str, ...] = tuple(f"'Pn{i:02}" for i in range(12))
PLACES: tuple[str, ...] = tuple(f"'Pl{i:02}" for i in range(8))

TAIL: dict[str, tuple[str, ...]] = {
    "Fragile": ("Cushion", "Steady"),
    "Tough": ("Sling",),
}

_MARKED = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")


def names() -> dict[str, tuple[str, ...]]:
    """Every name in the world, under the class the dictionary binds it to."""
    out: dict[str, tuple[str, ...]] = {"Human": CARRIERS, "Place": PLACES}
    out.update(CARRIED)
    out.update(VESSEL_NAMES)
    return out


def dictionary() -> str:
    """Name to class, and nothing else — as everywhere else in this repository.

    A container's line says its *material* class (`Clay-Vessel`), not the kind
    that was asked for (`Vessel`). That the one is a kind of the other is the
    shape of the world and lives in the core. So the answer to a question about
    vessels tells the model two things at once: which individual, and what it
    is made of — and only the second is of any use.
    """
    return "\n".join(
        f"FACT: State tgt:{name} is:{klass}"
        for klass, members in names().items()
        for name in members
    )


def core_rules() -> str:
    """The instinct. No name appears in it, and no individual container."""
    lines = [f"FACT: State tgt:{klass} is:Carriable" for klass in NEEDS]
    for kind, materials in CONTAINERS.items():
        for klass, material in materials.items():
            lines.append(f"FACT: State tgt:{klass} is:{kind}")
            lines.append(f"FACT: State tgt:{klass} is:{material}")
    for carried, kind in NEEDS.items():
        # What is wanted, and the language's own way of not saying which.
        lines.append(
            f"RULE: Action: Carry agt:Every.Animate.Thing tgt:Every.{carried}.Thing"
            f" -> Result: In tgt:It loc:Any.{kind}.Thing"
        )
    lines.append("FACT: State tgt:Human is:Animate")
    for material, steps in TAIL.items():
        for i, step in enumerate(steps):
            before = (
                f"In tgt:Every.Carriable.Thing loc:Every.{material}.Thing<Q>"
                if i == 0
                else f"{steps[i - 1]} tgt:Every.{material}.Thing<Q>"
            )
            lines.append(f"RULE: Action: {before} -> Result: {step} tgt:It<Q>")
    return "\n".join(lines)


# -- drawing a situation ------------------------------------------------------


def C(*segments: str, index: str | None = None) -> Concept:
    return Concept(tuple(segments), index=index)


def ev(verb: str, **slots: Concept) -> Event:
    return Event(C(verb), frozenset(slots.items()))


@dataclass(frozen=True)
class Sample:
    action: Event
    wanted: str          # the class the derivation has to ask for
    vessel: str          # the individual the store will answer with
    material: str        # what that individual is made of
    vessel_class: str    # the class its dictionary line gives
    result: Pipeline

    def meaning(self) -> Pipeline:
        return Pipeline((self.action,) + self.result.events, ("->",) + self.result.connectors)

    def words(self) -> list[str]:
        out = [self.action.verb.segments[-1]]
        for _, value in sorted(self.action.slots, key=lambda kv: kv[0]):
            if isinstance(value, Concept):
                out += list(value.segments)
        return out


def sample(w_rng: random.Random, pool: set[str] | None = None, vessels: set[str] | None = None) -> Sample:
    carried_class = w_rng.choice(tuple(CARRIED))
    kind = NEEDS[carried_class]
    vessel_class = w_rng.choice(tuple(CONTAINERS[kind]))
    material = CONTAINERS[kind][vessel_class]

    def pick(members, held):
        allowed = [n for n in members if held is None or n in held]
        return w_rng.choice(allowed)

    carrier = pick(CARRIERS, pool)
    carried = pick(CARRIED[carried_class], pool)
    vessel = pick(VESSEL_NAMES[vessel_class], vessels)
    action = ev("Carry", agt=C(carrier), tgt=C(carried))
    events = [ev("In", tgt=C(carried), loc=C(vessel))]
    events += [ev(step, tgt=C(vessel)) for step in TAIL[material]]
    return Sample(
        action, kind, vessel, material, vessel_class,
        Pipeline(tuple(events), ("->",) * (len(events) - 1)),
    )


# -- the corpus ---------------------------------------------------------------

HELD_BACK = 0.25


def pools(seed: int) -> tuple[set[str], set[str], set[str], set[str]]:
    """Names to train on and names held back, for the things carried and for
    the containers separately.

    The containers are split apart because they are the ones a model never sees
    in an input: they arrive only as an answer. A container held out of
    training tests whether the answer is read, rather than whether the word is
    familiar, and it is the sharper of the two tests.
    """
    rng = random.Random(f"{seed}-vessel-names")

    def split(groups):
        train: set[str] = set()
        unseen: set[str] = set()
        for members in groups:
            shuffled = list(members)
            rng.shuffle(shuffled)
            cut = max(1, round(len(shuffled) * HELD_BACK))
            unseen |= set(shuffled[:cut])
            train |= set(shuffled[cut:])
        return train, unseen

    thing_train, thing_unseen = split(list(CARRIED.values()) + [CARRIERS, PLACES])
    vessel_train, vessel_unseen = split(VESSEL_NAMES.values())
    return thing_train, thing_unseen, vessel_train, vessel_unseen


def build(n_train: int = 8000, n_iid: int = 1000, n_unseen: int = 1000, seed: int = 0):
    """Records shaped for `experiments/train.py --corpus vessels`.

    The four stretches are the same as everywhere: what the parser handed over,
    what the model writes before it has to stop, what comes back, and the rest.
    Only the middle one differs in kind — it is the model's own question rather
    than a word the harness spotted, and `query` holds the class it should have
    asked about so that grading can say whether it did.
    """
    from .basics import normalise  # noqa: PLC0415
    from .corpus import Record  # noqa: PLC0415
    from .render import tagged_event, tagged_pipeline  # noqa: PLC0415

    entries = {}
    for line in dictionary().splitlines():
        entries[line.split("tgt:")[1].split()[0]] = line
    thing_train, thing_unseen, vessel_train, vessel_unseen = pools(seed)
    rng = random.Random(seed)

    def record(drawn: Sample, split: str) -> Record:
        given = [x for x in drawn.words() if x.startswith("'")]
        handed_in = " ".join(entries[x] for x in dict.fromkeys(given) if x in entries)
        action = tagged_event(drawn.action, rng)
        head = f"-> QUERY: State tgt:? is:{drawn.wanted}"
        handed_mid = entries[drawn.vessel]
        tail = f"-> {tagged_pipeline(drawn.result)}"
        meaning = str(drawn.meaning())
        texts = [action, handed_in, meaning, head, handed_mid, tail]
        (action, handed_in, meaning, head, handed_mid, tail), renamed = normalise(texts)
        # The container is always the third marked word, so `normalise` would
        # always call it `'C` and a model could write `'C` without having read
        # anything. Which letter it gets is drawn instead, out of a range the
        # carrier and the thing carried never reach. Now the only way to know
        # what the answer was called is to have read the answer, and a model
        # asked with an empty store has to invent a letter to write at all —
        # which is the number the whole arm is for.
        letter = f"'{rng.choice('DEFGHIJK')}"
        swap = {"'C": letter}
        action, handed_in, meaning, head, handed_mid, tail = (
            _MARKED.sub(lambda m: swap.get(m.group(0), m.group(0)), t)
            for t in (action, handed_in, meaning, head, handed_mid, tail)
        )
        renamed = {swap.get(k, k): v for k, v in renamed.items()}
        return Record(
            split=split, meaning=meaning, tagged_in=action, tagged_out=tail,
            word_order_in=action, word_order_out=tail, passive=False,
            query=drawn.wanted, answer=handed_in,
            head=head, handed=handed_mid, tail=tail, names=renamed,
        )

    def draw(things: set[str], vessels: set[str], seen: set[str], count: int, split: str):
        out = []
        while len(out) < count:
            drawn = sample(rng, things, vessels)
            key = str(drawn.meaning())
            if key in seen:
                continue
            seen.add(key)
            out.append(record(drawn, split))
        return out

    seen: set[str] = set()
    out = draw(thing_train, vessel_train, seen, n_train, "train")
    out += draw(thing_train, vessel_train, seen, n_iid, "test_iid")
    # A container the model has never met, offered as the answer to its own
    # question. Nothing about the word can help; only its class can.
    out += draw(thing_train, vessel_unseen, set(), n_unseen, "test_unseen_vessel")
    out += draw(thing_unseen, vessel_train, set(), n_unseen, "test_unseen_thing")
    return out
