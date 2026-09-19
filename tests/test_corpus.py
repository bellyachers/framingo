from __future__ import annotations

import random
from collections import Counter

import pytest

from framingo import parse, parse_one
from framingo.corpus import COMBOS_HELD_OUT, ROLE_HELD_OUT, build
from framingo.grounding import check
from framingo.render import tokens, word_order_event
from framingo.syntax import Pipeline, Statement
from framingo.world import C, core_rules, ev, sample

CORE = parse(core_rules())


@pytest.fixture(scope="module")
def records():
    return build(n_train=3000, n_iid=300, n_held=100, seed=1)


def test_every_generated_result_is_grounded_by_the_core():
    # The generator and the checker are separate implementations of the
    # same physics; each must agree with the other on every sample.
    rng = random.Random(7)
    for _ in range(150):
        s = sample(rng)
        context = [Statement(Pipeline((s.action,)), prefix="FACT")]
        output = [Statement(s.meaning(), prefix="FACT")]
        report = check(output, context, CORE)
        assert report.ok, f"{s.meaning()}\n{report}"
        assert [v.status for v in report.verdicts][0] == "known"


def test_ruler_prevents_slicing():
    s = parse_one("Cut agt:John tgt:Red.Apple tool:Ruler").pipeline.events[0]
    from framingo.world import consequence, outcome_connector

    assert outcome_connector(s) == "!>"
    assert [e.verb.segments[0] for e in consequence(s).events] == ["Become", "Deform"]


def test_tagged_form_parses_back_to_the_meaning(records):
    for r in records[:500]:
        meaning = parse_one(r.meaning).pipeline
        rendered = parse_one(f"{r.tagged_in} {r.tagged_out}").pipeline
        assert [e.slots for e in rendered.events] == [e.slots for e in meaning.events]
        assert rendered.connectors == meaning.connectors


def test_forms_share_all_content_tokens(records):
    # The only difference allowed between the two forms is role marking.
    role_marks = {"agt:", "tgt:", "tool:", "src:", "dst:", "loc:", "reason:"}
    word_order_marks = {"with", "from", "onto", "in", "because", "was", "by"}
    for r in records[:500]:
        f = Counter(t for t in tokens(f"{r.tagged_in} {r.tagged_out}") if t not in role_marks)
        w = Counter(t for t in tokens(f"{r.word_order_in} {r.word_order_out}") if t not in word_order_marks)
        assert f == w, r


def test_word_order_form_marks_core_roles_by_position_only():
    e = ev("Push", agt=C("Cat"), tgt=C("Blue", "Vase"), tool=C("Knife"))
    assert word_order_event(e) == "Cat Push Blue.Vase with Knife"
    assert word_order_event(e, passive=True) == "Blue.Vase was Push by Cat with Knife"
    assert word_order_event(ev("Fall", tgt=C("Vase"), dst=C("Floor"))) == "Vase Fall onto Floor"


def test_held_out_role_never_appears_as_target_in_training_inputs(records):
    def action_targets(r):
        return [str(v) for v in parse_one(r.tagged_in).pipeline.events[0].get("tgt")]

    train = [r for r in records if r.split == "train"]
    assert not any(ROLE_HELD_OUT in action_targets(r) for r in train)
    assert any(f"agt:{ROLE_HELD_OUT}" in r.tagged_in for r in train)
    role = [r for r in records if r.split == "test_role"]
    assert role and all(action_targets(r) == [ROLE_HELD_OUT] for r in role)


def test_held_out_animate_is_a_familiar_output_token(records):
    # Otherwise the role-swap test only measures whether a model can emit a
    # word it never emitted in training, whatever the input form (world.py).
    train_outputs = " ".join(r.tagged_out for r in records if r.split == "train")
    assert f"tgt:{ROLE_HELD_OUT}" in train_outputs


def test_held_out_combinations_never_appear_in_training(records):
    for r in records:
        if r.split != "train":
            continue
        for mod, base in COMBOS_HELD_OUT:
            for word in r.meaning.split():
                segs = word.split(":")[-1].split(".")
                assert not (mod in segs and base in segs), r.meaning
    # but each word does occur in training on its own
    train_text = " ".join(r.meaning for r in records if r.split == "train")
    for mod, base in COMBOS_HELD_OUT:
        assert mod in train_text and base in train_text


def test_iid_test_meanings_are_disjoint_from_training(records):
    train = {r.meaning for r in records if r.split == "train"}
    iid = [r.meaning for r in records if r.split == "test_iid"]
    assert iid and not (set(iid) & train)


def test_split_sizes(records):
    sizes = Counter(r.split for r in records)
    assert sizes["train"] == 3000
    assert sizes["test_iid"] == 300
    assert sizes["test_role"] == 100 and sizes["test_combo"] == 100


def test_build_is_deterministic():
    a = build(n_train=200, n_iid=20, n_held=10, seed=3)
    b = build(n_train=200, n_iid=20, n_held=10, seed=3)
    assert [r.to_json() for r in a] == [r.to_json() for r in b]


def test_division_keeps_intrinsic_and_drops_structural_modifiers():
    # spec ch.3 §2: colour and taste survive a cut, shape and size do not.
    # The grounding checker cannot catch a violation of this (it accepts any
    # modifier drop), so the world model is tested directly.
    from framingo.world import consequence

    cut = ev("Cut", agt=C("John"), tgt=C("Round", "Red", "Apple"), tool=C("Knife"))
    (become,) = consequence(cut).events
    assert become.get("agt") == [C("Red", "Apple", "Slice")]
    drop = ev("Drop", agt=C("Cat"), tgt=C("Tall", "Blue", "Vase"))
    assert consequence(drop).events[-1].get("agt") == [C("Blue", "Vase", "Piece")]
