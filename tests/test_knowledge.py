"""The knowledge layer: is a query enough, and is an empty answer visible?

The claim under test is charter chapter 3's arrangement, not a model's skill at
it: with the minimal core empty, does what a query brings back suffice for the
Grounding Constraint? No model appears in this file.
"""

from __future__ import annotations

import random

import pytest

from framingo import parse, parse_one
from framingo.grounding import check
from framingo.knowledge import Answer, Store, asked_about, query_for
from framingo.syntax import Event, Pipeline, Placeholder, Statement
from framingo.world import C, core_rules, ev, sample

CORE = parse(core_rules())


def store() -> Store:
    return Store(CORE, "core")


def as_fact(meaning: str) -> Statement:
    return parse_one("FACT: " + meaning)


def action_of(statement: Statement) -> Statement:
    return Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")


# -- the query ---------------------------------------------------------------


def test_a_query_is_built_from_the_action_alone_and_parses_back():
    """Query formation is a structural operation, so it round-trips as text."""
    action = ev("Cut", agt=C("John"), tgt=C("Big", "Red", "Apple"), tool=C("Knife"))
    query = query_for(action)
    assert query.prefix == "QUERY"
    assert parse_one(str(query)) == query
    assert "?" in str(query)


def test_the_subject_of_a_query_is_whichever_end_is_given():
    action = ev("Cut", tgt=C("Apple"), tool=C("Knife"))
    assert asked_about(query_for(action)).verb == action.verb

    # working back to a cause: the action is the unknown, the result is given
    abductive = Statement(
        Pipeline(
            (
                Event(Placeholder(), frozenset(), label="Action"),
                ev("Become", agt=C("Apple", "Slice")),
            ),
            ("->",),
        ),
        prefix="QUERY",
    )
    assert asked_about(abductive).verb == C("Become")

    nothing_asked = Statement(
        Pipeline((Event(Placeholder(), frozenset()),)), prefix="QUERY"
    )
    assert asked_about(nothing_asked) is None


# -- the answer --------------------------------------------------------------


def test_an_answer_is_narrow_and_not_the_whole_store():
    """Bounded by the action, not by the size of the store: that bound is what
    keeps asking about everything affordable in context."""
    answer = store().answer(query_for(ev("Cut", tgt=C("Apple"), tool=C("Knife"))))
    assert not answer.empty
    assert len(answer.statements) < 10 < len(CORE)
    assert all(s.prefix == "RULE" for s in answer.statements)
    assert len(answer.sources) == len(answer.statements)


def test_an_empty_answer_is_a_result_and_says_so():
    """A gap in the store must be visible, not something to fall through."""
    answer = store().answer(query_for(ev("Sing", agt=C("John"))))
    assert answer.empty
    assert answer.statements == ()
    assert str(answer) == "(nothing)"
    assert Answer().empty


def test_an_answer_is_one_hop_so_the_next_question_is_the_model_s_to_ask():
    """Chaining to a fixpoint here would hand back a finished derivation.

    The rules that come back are the ones the action fires; a rule that fires
    on one of *their* conclusions is a second query.
    """
    answer = store().answer(query_for(ev("Drop", tgt=C("Tall", "Blue", "Vase"))))
    assert not answer.empty
    for statement in answer.statements:
        first = statement.pipeline.events[0]
        assert first.verb == C("Drop"), f"not fired by the action asked about: {statement}"


def test_a_stored_fact_comes_back_for_a_question_about_its_predicate():
    facts = parse("FACT: At tgt:Kettle loc:Kitchen")
    answer = Store(facts, "context").answer(query_for(ev("At", tgt=C("Kettle"))))
    assert not answer.empty
    assert answer.statements[0].prefix == "FACT"


# -- the arrangement ---------------------------------------------------------


@pytest.mark.parametrize("seed", (0, 1, 2))
def test_what_a_query_returns_grounds_the_world_with_an_empty_core(seed):
    """Charter ch.3, mechanically: the core may hold nothing.

    Context is the action plus what came back, the core is empty, and every
    consequence the world produces still satisfies the Grounding Constraint.
    This says the arrangement works; it says nothing about whether a model can
    use it, which needs a model trained to ask.
    """
    knowledge, rng = store(), random.Random(seed)
    for _ in range(120):
        drawn = sample(rng)
        answer = knowledge.answer(query_for(drawn.action))
        assert not answer.empty, f"nothing came back for {drawn.action}"
        gold = as_fact(str(drawn.meaning()))
        report = check([gold], [action_of(gold)] + list(answer.statements), ())
        assert report.ok, f"{drawn.meaning()}\n{report}"


def test_without_the_answer_the_same_gold_is_not_grounded():
    """The retrieved statements are doing the work, not the action alone."""
    rng = random.Random(7)
    ungrounded = 0
    for _ in range(60):
        gold = as_fact(str(sample(rng).meaning()))
        if not check([gold], [action_of(gold)], ()).ok:
            ungrounded += 1
    assert ungrounded == 60
