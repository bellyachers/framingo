"""Basic vocabulary, basic information: does the split hold up?

Two claims are worth pinning. The core mentions no name, so a name can only be
known by looking it up. And looking up exactly the marked words is enough to
ground everything the world produces, so the model needs no name in its
weights and no judgement about which words to fetch.
"""

from __future__ import annotations

import random
import re

import pytest

from framingo import parse, parse_one
from framingo.basics import NAMES, PARENTS, core_rules, dictionary, sample
from framingo.grounding import check
from framingo.syntax import Pipeline, Statement, is_instinct

CORE = parse(core_rules())


def book() -> dict[str, list[Statement]]:
    out: dict[str, list[Statement]] = {}
    for statement in parse(dictionary()):
        word = [v for v in statement.pipeline.events[0].get("tgt")][0].segments[-1]
        out.setdefault(word, []).append(statement)
    return out


def test_every_name_is_marked_and_every_class_is_not():
    assert not [n for names in NAMES.values() for n in names if is_instinct(n)]
    assert not [k for k in NAMES if not is_instinct(k)]
    assert not [k for k in PARENTS if not is_instinct(k)]


def test_the_core_mentions_no_name():
    """If it did, that name could be known without looking it up."""
    text = core_rules()
    named = [n for names in NAMES.values() for n in names if n in text]
    assert not named, named


def test_the_dictionary_says_only_which_class_a_name_is_in():
    """Not what the class implies, and not the class hierarchy either."""
    for statement in parse(dictionary()):
        (event,) = statement.pipeline.events
        assert str(event.verb) == "State"
        assert {k for k, _ in event.slots} == {"tgt", "is"}
        (target,) = event.get("tgt")
        (klass,) = event.get("is")
        assert not is_instinct(target.segments[-1]), str(statement)
        assert is_instinct(klass.segments[-1]), str(statement)


MARK = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")


def looked(entries, words):
    return [s for w in dict.fromkeys(words) for s in entries.get(w, [])]


@pytest.mark.parametrize("seed", (0, 1, 2))
def test_looking_up_what_was_given_and_what_was_derived_grounds_everything(seed):
    entries, rng = book(), random.Random(seed)
    for _ in range(150):
        drawn = sample(rng)
        meaning = str(drawn.meaning())
        given = [w for w in drawn.words() if not is_instinct(w)]
        derived = [w for w in MARK.findall(meaning) if w not in given]
        statement = parse_one("FACT: " + meaning)
        action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        context = [action] + looked(entries, given) + looked(entries, derived)
        assert check([statement], context, CORE).ok, f"{meaning}\n{check([statement], context, CORE)}"


def test_a_word_the_derivation_brings_in_has_to_be_looked_up_too():
    """The lookup a parser cannot do in advance.

    `Drop` a vessel and it becomes `'Shard`, a word the model does not hold and
    which was nowhere in the input to be fetched. Where a chain then turns on
    what that word is a kind of, looking up only what was given is not enough.
    """
    entries, rng = book(), random.Random(3)
    needed = enough = 0
    for _ in range(400):
        drawn = sample(rng)
        meaning = str(drawn.meaning())
        given = [w for w in drawn.words() if not is_instinct(w)]
        derived = [w for w in MARK.findall(meaning) if w not in given]
        if not derived:
            continue
        statement = parse_one("FACT: " + meaning)
        action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        given_only = check([statement], [action] + looked(entries, given), CORE).ok
        both = check([statement], [action] + looked(entries, given + derived), CORE).ok
        assert both, meaning
        needed += 1
        enough += given_only
    assert needed, "no derivation brought in a marked word"
    # some chains end at the derived word and never use its class; the rest do
    assert enough < needed, "looking up only what was given was always enough"


def test_without_the_lookup_nothing_is_grounded():
    """The entries are doing the work, not the core on its own."""
    rng = random.Random(9)
    for _ in range(40):
        drawn = sample(rng)
        statement = parse_one("FACT: " + str(drawn.meaning()))
        action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        assert not check([statement], [action], CORE).ok, str(drawn.meaning())


def test_a_name_never_handed_over_cannot_be_grounded():
    """The half of the Grounding Constraint that a vocabulary mask would make
    impossible rather than merely detectable."""
    entries, rng = book(), random.Random(4)
    drawn = sample(rng)
    looked = [s for w in drawn.words() if not is_instinct(w) for s in entries.get(w, [])]
    statement = parse_one("FACT: " + str(drawn.meaning()))
    action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
    invented = parse("FACT: Become agt:'Quokka.Slice")
    assert not check(invented, [action] + looked, CORE).ok
