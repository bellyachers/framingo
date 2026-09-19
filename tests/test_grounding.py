from __future__ import annotations

from framingo import parse
from framingo.grounding import check, entails
from framingo.parser import parse_concept

CORE = parse(
    """
    RULE: Action: Drop tgt:Every.Break-prone.Thing -> Result: Become agt:It.Piece
    RULE: when:(State tgt:Door is:Lock-ed)
          Action: Pass agt:Human tgt:Door
          !> Result: At agt:Human dst:Room.Inside
          -> Result: Bump agt:Human tgt:Door
    """
)


def statuses(report):
    return [v.status for v in report.verdicts]


def test_restating_the_context_is_grounded():
    context = parse("FACT: Action: Cut agt:John tgt:Bread tool:Knife")
    report = check(parse("FACT: Action: Cut tgt:Bread agt:John"), context)
    assert report.ok
    assert statuses(report) == ["known"]


def test_an_invented_entity_is_caught_by_string_matching():
    # the charter's central example: a token traceable to nothing
    context = parse("FACT: Action: Cut agt:John tgt:Bread tool:Knife")
    report = check(parse("FACT: Action: Cut agt:Mary tgt:Bread"), context)
    assert not report.ok
    assert ("Mary", 1) in report.ungrounded_words


def test_a_miscombination_of_known_words_is_caught_at_relation_level():
    # charter ch.8 proposition 2's falsifier: every token is known,
    # but the relation was never stated or derived
    context = parse(
        """
        FACT: Action: Cut agt:John tgt:Bread tool:Knife
        FACT: Action: Cut agt:Mary tgt:Apple tool:Knife
        """
    )
    report = check(parse("FACT: Action: Cut agt:John tgt:Apple"), context)
    assert report.ungrounded_words == []
    assert statuses(report) == ["ungrounded"]
    assert not report.ok


def test_dropping_modifiers_is_allowed_but_changing_the_head_is_not():
    assert entails(parse_concept("Sweet.Red.Apple"), parse_concept("Red.Apple"))
    assert not entails(parse_concept("Apple.Slice"), parse_concept("Apple"))
    assert not entails(parse_concept("Red.Apple"), parse_concept("Sweet.Red.Apple"))


def test_a_consequence_derived_by_a_rule_is_grounded():
    context = parse("FACT: Action: Drop agt:John tgt:Break-prone.Glass")
    output = parse("FACT: Action: Drop tgt:Break-prone.Glass -> Result: Become agt:It.Piece")
    report = check(output, context, CORE)
    assert report.ok, str(report)
    assert statuses(report) == ["known", "derived"]


def test_rules_do_not_fire_without_their_premise():
    # the glass is not stated to be break-prone; the rule must not apply
    context = parse("FACT: Action: Drop agt:John tgt:Glass")
    output = parse("FACT: Action: Drop tgt:Glass -> Result: Become agt:It.Piece")
    assert statuses(check(output, context, CORE)) == ["known", "ungrounded"]


def test_prevented_events_are_not_facts():
    context = parse(
        """
        FACT: when:(State tgt:Door is:Lock-ed) Action: Pass agt:Human tgt:Door
        """
    )
    # claiming the human got inside contradicts the rule's !>
    wrong = check(parse("FACT: Result: At agt:Human dst:Room.Inside"), context, CORE)
    assert statuses(wrong) == ["ungrounded"]
    # claiming it was prevented, and that they bumped the door, is grounded
    right = check(
        parse(
            "FACT: Action: Pass agt:Human tgt:Door "
            "!> Result: At agt:Human dst:Room.Inside -> Result: Bump agt:Human tgt:Door"
        ),
        context,
        CORE,
    )
    assert statuses(right) == ["known", "prevented", "derived"], str(right)


def test_a_fact_pipeline_records_what_did_not_happen():
    context = parse(
        "FACT: Action: Push agt:John tgt:Locked.Door !> Result: Become agt:Open.Door"
    )
    assert statuses(check(parse("FACT: Result: Become agt:Open.Door"), context)) == ["ungrounded"]


def test_hypo_may_assume_its_own_premises():
    output = parse("HYPO: Action: Drop tgt:Break-prone.Vase -> Result: Become agt:It.Piece")
    context = parse("FACT: State tgt:Break-prone.Vase loc:Table")
    report = check(output, context, CORE)
    assert statuses(report) == ["assumed", "derived"], str(report)


def test_suffixed_words_are_grounded_by_their_root():
    context = parse("FACT: Action: Lock agt:John tgt:Door")
    report = check(parse("FACT: State tgt:Door is:Lock-ed"), context)
    assert report.ungrounded_words == []


def test_chained_rules_reach_a_fixpoint():
    core = parse(
        """
        RULE: Action: Push tgt:Every.Thing -> Fall tgt:It
        RULE: Fall tgt:Every.Break-prone.Thing -> Result: Become agt:It.Piece
        """
    )
    context = parse("FACT: Action: Push agt:Cat tgt:Break-prone.Vase")
    report = check(parse("FACT: Result: Become agt:Break-prone.Vase.Piece"), context, core)
    assert statuses(report) == ["derived"], str(report)


def test_a_noun_may_not_be_dropped_even_when_the_head_survives():
    # A trained model produced `Blue.Piece` for `Blue.Plate.Piece`.
    context = parse("FACT: Action: Drop agt:Mary tgt:Break-prone.Blue.Plate")
    good = check(parse("FACT: Result: Become agt:Blue.Plate.Piece"), context, CORE)
    bad = check(parse("FACT: Result: Become agt:Blue.Piece"), context, CORE)
    assert statuses(good) == ["derived"]
    assert statuses(bad) == ["ungrounded"]


def test_omitting_a_slot_is_not_a_hallucination():
    # Leaving out where something fell from fabricates nothing; the
    # Grounding Constraint accepts it by design (abstraction, spec ch.2 §3).
    context = parse("FACT: Action: Drop agt:Mary tgt:Vase src:On.Table")
    core = parse("RULE: Action: Drop tgt:Vase src:On.Table -> Fall tgt:It src:On.Table dst:Floor")
    assert check(parse("FACT: Fall tgt:Vase dst:Floor"), context, core).ok


def test_a_repeated_word_is_not_grounded():
    # A trained model produced `Plate.Plate.Piece` and `Red.Red.Tomato`.
    assert not entails(parse_concept("Plate.Piece"), parse_concept("Plate.Plate.Piece"))
    assert not entails(parse_concept("Red.Tomato"), parse_concept("Red.Red.Tomato"))
    assert not entails(parse_concept("Round.Red.Apple"), parse_concept("Red.Round.Apple"))
    assert entails(parse_concept("Round.Red.Apple"), parse_concept("Round.Apple"))
