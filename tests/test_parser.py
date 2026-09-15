from __future__ import annotations

import pytest

from framingo import Concept, ParseError, Pipeline, Placeholder, parse, parse_concept, parse_one


def test_slot_order_does_not_change_meaning():
    # spec ch.2 §2.1: the three patterns are one event
    a = parse_one("Action: Cut agt:John tgt:Bread tool:Knife")
    b = parse_one("Action: Cut tgt:Bread tool:Knife agt:John")
    c = parse_one("Action: Cut tool:Knife agt:John tgt:Bread")
    assert a == b == c


def test_dropping_a_slot_changes_the_event():
    assert parse_one("Action: Cut tgt:Bread") != parse_one("Action: Cut tgt:Bread tool:Knife")


def test_concept_parts():
    c = parse_concept("!Every.Break-prone.Glass.Piece<A>")
    assert c == Concept(("Break-prone", "Glass", "Piece"), determiner="Every", negated=True, index="A")
    assert parse_concept("Bread[1]").instance == "1"
    assert parse_concept("Bread#402").instance == "402"
    # a lone determiner word is a concept, not a determiner
    assert parse_concept("This").segments == ("This",)


def test_statements_split_where_the_pipeline_ends():
    stmts = parse(
        """
        // two statements in one block
        Action: Move agt:Cat src:Under.Table dst:On.Chair
        Action: Put agt:John tgt:Apple src:On.Counter dst:In.Box
        """
    )
    assert [s.pipeline.events[0].verb.segments for s in stmts] == [("Move",), ("Put",)]


def test_statement_spans_blank_lines_while_connectors_continue():
    s = parse_one(
        """
        FACT:
          Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)
          !> Result: State tgt:Door is:Open

          -> Action: Pull agt:Robot tgt:Door
        """
    )
    assert s.prefix == "FACT"
    assert s.pipeline.connectors == ("!>", "->")


def test_nested_goal_and_block_condition():
    s = parse_one(
        "RULE: when:(State tgt:Door is:Open) Action: Pass agt:Human tgt:Door "
        "-> Result: At agt:Human dst:Room.Inside"
    )
    assert s.condition == parse_one("State tgt:Door is:Open").pipeline
    goal = parse_one("Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)").pipeline.events[0]
    (value,) = goal.get("goal")
    assert isinstance(value, Pipeline)


def test_placeholders():
    s = parse_one("QUERY: Action: ? -> Result: Become agt:Apple.Half count:2")
    assert isinstance(s.pipeline.events[0].verb, Placeholder)
    s = parse_one("QUERY: Action: Drop tgt:Glass.Cup -> Result: ?")
    assert isinstance(s.pipeline.events[1].verb, Placeholder)


def test_round_trip_is_stable():
    src = "FACT: when:(State tgt:Floor is:Wet) Action: Run agt:John dst:Exit !> Result: At agt:John dst:Exit"
    once = parse_one(src)
    assert parse_one(str(once)) == once


@pytest.mark.parametrize(
    "bad",
    [
        "Action: Cut tgt:",          # slot without value
        "Action: Cut tgt:Bread ->",  # dangling connector
        "RULE: when:(State tgt:Door is:Open Action: Pass",  # unclosed condition
        "Action: Cut tgt:Bread $",   # stray character
    ],
)
def test_errors_carry_a_position(bad):
    with pytest.raises(ParseError) as exc:
        parse(bad)
    assert exc.value.line >= 1 and exc.value.column >= 1
