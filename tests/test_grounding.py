from __future__ import annotations

import random

from framingo import parse, parse_one
from framingo.grounding import check, entails, memberships
from framingo.parser import parse_concept
from framingo.syntax import Concept, Event, Pipeline, Statement
from framingo.world import Sample, core_rules, sample

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


# -- the world's minimal core ------------------------------------------------
#
# Soundness (the core derives every true result) and completeness (it derives
# nothing else) are two claims, and only the pair is worth anything: a core
# that derives everything is sound and useless. The two tests below are the
# pair, taken over the same draws.

WORLD = parse(core_rules())


def graded(meaning: Pipeline, action: Event):
    """Grade a meaning with the action in context, as the corpus is graded."""
    return check(
        [Statement(meaning, prefix="FACT")],
        [Statement(Pipeline((action,)), prefix="FACT")],
        WORLD,
    )


def copy_error(s: Sample) -> Pipeline | None:
    """The sample's meaning with the whole target copied through a division.

    ``Cut tgt:Big.Red.Apple`` makes ``Red.Apple.Slice``; this claims
    ``Big.Red.Apple.Slice``, keeping the structural modifier the world
    destroys. None when the sample divides nothing, or divides a target that
    carried no structural modifier to keep.
    """
    (target,) = s.action.get("tgt")
    events, forged = [], False
    for event in s.result.events:
        parts = event.get("agt")
        if event.verb.segments == ("Become",) and parts:
            whole = Concept(target.segments + parts[0].segments[-1:])
            if whole != parts[0]:
                event = Event(event.verb, frozenset({("agt", whole)}), event.label)
                forged = True
        events.append(event)
    if not forged:
        return None
    return Pipeline((s.action,) + tuple(events), (s.connector,) + s.result.connectors)


def test_the_core_derives_every_result_the_world_produces():
    rng = random.Random(5)
    for _ in range(300):
        s = sample(rng)
        report = graded(s.meaning(), s.action)
        assert report.ok, f"{s.meaning()}\n{report}"


def test_a_modifier_that_did_not_survive_the_division_is_not_grounded():
    # The core once accepted this in every single case: `Become agt:It.Slice`
    # made `It` the whole target, so `Big.Red.Apple.Slice` followed from the
    # core as readily as `Red.Apple.Slice` did, and a fabrication that keeps
    # a destroyed property was invisible to the verifier.
    rng = random.Random(5)
    forged = 0
    for _ in range(300):
        s = sample(rng)
        wrong = copy_error(s)
        if wrong is None:
            continue
        forged += 1
        report = graded(wrong, s.action)
        assert not report.ok, f"{wrong}\n{report}"
    assert forged > 50, "the draw produced too few divisions to say anything"


def test_cutting_a_big_red_apple_yields_red_apple_slices_and_nothing_bigger():
    context = [parse_one("FACT: Action: Cut agt:John tgt:Big.Red.Apple tool:Knife")]
    good = check(parse("FACT: Result: Become agt:Red.Apple.Slice"), context, WORLD)
    bad = check(parse("FACT: Result: Become agt:Big.Red.Apple.Slice"), context, WORLD)
    assert statuses(good) == ["derived"], str(good)
    assert statuses(bad) == ["ungrounded"], str(bad)
    # the fall keeps everything, so there the whole target is the right answer
    dropped = [parse_one("FACT: Action: Drop agt:Mary tgt:Tall.Blue.Vase")]
    fell = check(parse("FACT: Result: Fall tgt:Tall.Blue.Vase dst:Floor"), dropped, WORLD)
    assert statuses(fell) == ["derived"], str(fell)

# -- order (spec ch.4 §1.1) --------------------------------------------------

CHAIN = parse("RULE: Action: Push tgt:Every.Thing -> Move tgt:It -> Fall tgt:It")


def test_a_result_told_backwards_is_not_grounded():
    # `->` asserts that the left event brought the right one about, so the
    # two orders are not two ways of saying one thing: one of them is false.
    context = parse("FACT: Action: Push agt:Cat tgt:Ball")
    forwards = check(parse("FACT: Move tgt:Ball -> Fall tgt:Ball"), context, CHAIN)
    backwards = check(parse("FACT: Fall tgt:Ball -> Move tgt:Ball"), context, CHAIN)
    assert statuses(forwards) == ["derived", "derived"], str(forwards)
    assert statuses(backwards) == ["misordered", "derived"], str(backwards)
    assert not backwards.ok


def test_skipping_a_link_of_the_chain_is_still_grounded():
    # The core derives Push -> Move -> Fall; saying Push -> Fall leaves the
    # middle out but inverts nothing. Abstraction is the gradient the
    # language is built for (spec ch.2 §3), not a fabrication.
    context = parse("FACT: Action: Push agt:Cat tgt:Ball")
    report = check(parse("FACT: Action: Push tgt:Ball -> Fall tgt:Ball"), context, CHAIN)
    assert report.ok, str(report)
    assert statuses(report) == ["known", "derived"]


def test_events_no_chain_sequences_pass_in_either_order():
    # Two rules, one premise: the carried and the carrier arrive at one and
    # the same moment, and nothing in the core puts one before the other.
    # An order the knowledge does not license is not an order it forbids.
    core = parse(
        """
        RULE: Action: Carry agt:Every.Thing<A> tgt:Box dst:Hall -> At tgt:It loc:Hall
        RULE: Action: Carry agt:Every.Thing<A> tgt:Box dst:Hall -> At tgt:It<A> loc:Hall
        """
    )
    context = parse("FACT: Action: Carry agt:John tgt:Box dst:Hall")
    carried_first = check(parse("FACT: At tgt:Box loc:Hall -> At tgt:John loc:Hall"), context, core)
    carrier_first = check(parse("FACT: At tgt:John loc:Hall -> At tgt:Box loc:Hall"), context, core)
    assert carried_first.ok, str(carried_first)
    assert carrier_first.ok, str(carrier_first)


def test_the_vase_shatters_after_it_falls_and_not_before():
    # The case the order check was written for: every event of the reversed
    # pipeline is derivable on its own, so token and relation grounding both
    # pass it, and the reading is still false — the vase became pieces and
    # then fell to the floor.
    core = parse("RULE: Action: Drop tgt:Vase -> Fall tgt:It dst:Floor -> Result: Become agt:It.Piece")
    context = parse("FACT: Action: Drop agt:Robot tgt:Tall.White.Vase")
    gold = check(
        parse(
            "FACT: Action: Drop tgt:Tall.White.Vase"
            " -> Fall dst:Floor tgt:Tall.White.Vase -> Become agt:White.Vase.Piece"
        ),
        context,
        core,
    )
    reversed_ = check(
        parse(
            "FACT: Action: Drop tgt:Tall.White.Vase"
            " -> Become agt:White.Vase.Piece -> Fall dst:Floor tgt:Tall.White.Vase"
        ),
        context,
        core,
    )
    assert gold.ok, str(gold)
    assert statuses(reversed_) == ["known", "misordered", "derived"], str(reversed_)


# -- class membership --------------------------------------------------------
#
# The boundary the architecture runs on. Binding a name to a class is
# arbitrary and unbounded, so it is knowledge and arrives from outside; what
# follows from belonging to a class is general, so the core holds it. These
# tests pin that a rule written about a class fires on a member, and — the
# pair that matters — that it fires *only* when something said so.

CLASSES = parse(
    """
    FACT: State tgt:Human is:Animate
    RULE: Action: Drop tgt:Every.Break-prone.Thing -> Result: Become agt:Broken.Thing
    RULE: Action: Feed tgt:Every.Animate.Thing -> Result: Full tgt:It
    """
)


def test_memberships_are_read_off_stated_facts_and_closed_transitively():
    told = memberships(parse("FACT: State tgt:John is:Human\nFACT: State tgt:Human is:Animate"))
    assert told["John"] == frozenset({"Human", "Animate"})
    assert told["Human"] == frozenset({"Animate"})


def test_a_rule_about_a_class_fires_on_a_member():
    context = parse("FACT: Drop tgt:Glass\nFACT: State tgt:Glass is:Break-prone")
    report = check(parse("FACT: Become agt:Broken.Thing"), context, CLASSES)
    assert report.ok, str(report)


def test_membership_carries_through_a_chain():
    context = parse("FACT: Feed tgt:John\nFACT: State tgt:John is:Human")
    report = check(parse("FACT: Full tgt:John"), context, CLASSES)
    assert report.ok, str(report)


def test_a_rule_about_a_class_does_not_fire_on_a_non_member():
    context = parse("FACT: Feed tgt:Knife\nFACT: State tgt:Knife is:Tool")
    assert not check(parse("FACT: Full tgt:Knife"), context, CLASSES).ok


def test_the_same_output_is_grounded_only_when_the_class_was_looked_up():
    """The architecture in one test.

    The core holds what follows from being animate. The context holds what a
    lookup returned. Identical output, identical core: grounded when the
    lookup told the checker that Mary is a human, ungrounded when it did not.
    A word not looked up is a word the output cannot be traced to.
    """
    output = parse("FACT: Full tgt:Mary")
    asked = parse("FACT: Feed tgt:Mary\nFACT: State tgt:Mary is:Human")
    unasked = parse("FACT: Feed tgt:Mary")
    assert check(output, asked, CLASSES).ok
    assert not check(output, unasked, CLASSES).ok
