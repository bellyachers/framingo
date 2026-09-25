"""The same world at whatever size: does the structure survive being generated?

The hand-written world is checked by reading it. A generated one cannot be, so
the properties that reading would have caught are asserted instead: the core
names nothing, the dictionary says only what class a name is in, and what the
world claims follows is what the checker derives — at more than one size,
because a table that happens to work at ten classes is not evidence about forty.
"""

from __future__ import annotations

import random
import re

import pytest

from framingo import parse, parse_one, scaled
from framingo.grounding import check
from framingo.syntax import Pipeline, Statement

MARK = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")
SIZES = (6, 20, 50)


def entries(w):
    out = {}
    for line in scaled.dictionary(w).splitlines():
        out[line.split("tgt:")[1].split()[0]] = parse_one(line)
    return out


@pytest.mark.parametrize("n", SIZES)
def test_what_the_world_claims_is_what_the_checker_derives(n):
    w = scaled.make(n_classes=n, seed=0)
    core, book, rng = parse(scaled.core_rules(w)), entries(w), random.Random(n)
    for _ in range(80):
        drawn = scaled.sample(w, rng)
        meaning = str(drawn.meaning())
        looked = [book[x] for x in dict.fromkeys(MARK.findall(meaning)) if x in book]
        statement = parse_one("FACT: " + meaning)
        action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
        report = check([statement], [action] + looked, core)
        assert report.ok, f"{meaning}\n{report}"


@pytest.mark.parametrize("n", SIZES)
def test_the_core_names_nothing(n):
    """If it did, that name could be known without looking it up."""
    w = scaled.make(n_classes=n, seed=0)
    text = scaled.core_rules(w)
    named = [x for members in w.names.values() for x in members if x in text]
    assert not named, named[:3]


@pytest.mark.parametrize("n", SIZES)
def test_the_dictionary_says_only_what_class_something_is_in(n):
    w = scaled.make(n_classes=n, seed=0)
    for statement in parse(scaled.dictionary(w)):
        (event,) = statement.pipeline.events
        assert str(event.verb) == "State"
        assert {k for k, _ in event.slots} == {"tgt", "is"}
        (target,) = event.get("tgt")
        assert scaled.is_marked(target.segments[-1]), str(statement)


def test_the_size_dial_moves_the_number_of_rules():
    small, large = scaled.make(n_classes=10, seed=0), scaled.make(n_classes=40, seed=0)
    assert large.n_rules > small.n_rules * 3


def test_a_derivation_keeps_bringing_in_words_the_model_does_not_hold():
    """The stop is what the whole arrangement turns on, so it has to happen."""
    w = scaled.make(n_classes=20, seed=0)
    records = scaled.build(w, n_train=200, n_iid=20, n_unseen=20, seed=0)
    stopped = [r for r in records if r.handed]
    assert stopped, "no derivation ever brought in a marked word"
    assert len(stopped) > len(records) // 20


def test_held_back_names_never_train():
    w = scaled.make(n_classes=12, seed=0)
    train_pool, unseen_pool = scaled.pools(w, 0)
    assert not train_pool & unseen_pool
    records = scaled.build(w, n_train=200, n_iid=20, n_unseen=20, seed=0)
    trained = {
        w.names and n
        for r in records
        if r.split == "train"
        for n in r.names.values()
    }
    assert not (trained & unseen_pool)
