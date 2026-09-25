"""The corpus with no physics in it: is it really only asking for instantiation?

Two things have to hold or the experiment measures something else. The
conclusion the corpus claims must be exactly what the checker derives from the
rule and the fact — the corpus writes it out, the checker derives it, and only
a test keeps the two in step. And the held-out rules must be genuinely held
out: a shared verb, entity or modifier would let a model answer from a habit
rather than from the rule in front of it.
"""

from __future__ import annotations

import random

import pytest

from framingo import parse_one
from framingo.grounding import check
from framingo.instantiation import (
    ENTITIES,
    MODIFIERS,
    TRAIN_SHARE,
    UNSEEN_SHARE,
    VERBS,
    build,
    make_fact,
    make_rule,
    store_of,
)
from framingo.render import tokens
from framingo.syntax import Pipeline, Statement


def corpus():
    return build(n_rules=40, n_unseen_rules=10, facts_per_rule=6, n_iid=3, n_unseen_facts=5, seed=0)


def grounds(meaning: str, rule) -> bool:
    statement = parse_one("FACT: " + meaning)
    fact = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
    return check([statement], [fact, rule], ()).ok


@pytest.mark.parametrize("seed", (0, 1, 2))
def test_the_conclusion_written_is_the_conclusion_derived(seed):
    """With an empty core: the rule and the fact are all there is."""
    rng = random.Random(seed)
    for i in range(30):
        rule = make_rule(rng, i, TRAIN_SHARE)
        for _ in range(3):
            drawn = make_fact(rule, rng, TRAIN_SHARE)
            assert grounds(str(drawn.meaning()), drawn.rule), f"{drawn.rule}\n{drawn.meaning()}"


def test_a_query_returns_that_record_s_own_rule_and_nothing_else():
    """Every rule has a verb of its own, so an answer is never a choice of rules."""
    records = corpus()
    store = store_of(records)
    for r in records:
        answer = store.answer(parse_one(r.query))
        assert [str(s) for s in answer.statements] == [r.answer], r.query


def test_the_held_out_rules_share_no_word_with_training():
    """Otherwise a model could be answering from a habit about a word."""
    records = corpus()
    trained = {
        t
        for r in records
        if r.split == "train"
        for f in ("tagged_in", "tagged_out", "query", "answer")
        for t in tokens(getattr(r, f))
    }
    invented = set(VERBS) | set(ENTITIES) | set(MODIFIERS)
    for r in records:
        if r.split != "test_unseen":
            continue
        used = {t for f in ("tagged_in", "tagged_out", "answer") for t in tokens(getattr(r, f))}
        assert not (used & invented & trained), sorted(used & invented & trained)


def test_the_shares_do_not_overlap():
    for pool in (VERBS, ENTITIES, MODIFIERS):
        lo = set(pool[int(len(pool) * TRAIN_SHARE[0]) : int(len(pool) * TRAIN_SHARE[1])])
        hi = set(pool[int(len(pool) * UNSEEN_SHARE[0]) : int(len(pool) * UNSEEN_SHARE[1])])
        assert not lo & hi


def test_the_iid_split_reuses_the_rules_and_not_the_facts():
    records = corpus()
    by = {"train": set(), "test_iid": set(), "test_unseen": set()}
    rules = {"train": set(), "test_iid": set(), "test_unseen": set()}
    for r in records:
        by[r.split].add(r.meaning)
        rules[r.split].add(r.answer)
    assert not by["train"] & by["test_iid"], "a test fact also occurs in training"
    assert rules["test_iid"] <= rules["train"], "the IID split is meant to reuse trained rules"
    assert not rules["test_unseen"] & rules["train"]


def test_every_record_is_gradeable_from_its_own_answer():
    """What the corpus hands a model is enough to answer with, and no more."""
    for r in corpus():
        assert grounds(r.meaning, parse_one(r.answer)), r.meaning
