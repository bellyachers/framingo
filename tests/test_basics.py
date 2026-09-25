"""Basic vocabulary, basic information: does the split hold up?

Two claims are worth pinning. The core mentions no name, so a name can only be
known by looking it up. And looking up exactly the marked words is enough to
ground everything the world produces, so the model needs no name in its
weights and no judgement about which words to fetch.
"""

from __future__ import annotations

import random

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


@pytest.mark.parametrize("seed", (0, 1, 2))
def test_looking_up_the_marked_words_grounds_everything(seed):
    entries, rng = book(), random.Random(seed)
    for _ in range(150):
        drawn = sample(rng)
        marked = [w for w in drawn.words() if not is_instinct(w)]
        looked = [s for w in marked for s in entries.get(w, [])]
        assert len(looked) == len(marked), f"a marked word has no entry: {drawn.action}"
        statement = parse_one("FACT: " + str(drawn.meaning()))
        action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        report = check([statement], [action] + looked, CORE)
        assert report.ok, f"{drawn.meaning()}\n{report}"


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
