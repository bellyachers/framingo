"""A world where what the derivation needs is not in the sentence.

The properties worth asserting are the ones that make the question real. The
sentence must not name a container — otherwise there is nothing to ask for.
The core must not name one either — otherwise the answer could be guessed. And
the material, which is the only thing the answer is good for, must decide what
follows, or the lookup would be a habit rather than a necessity.

The last three are the guarantee itself: a container nobody handed over, a
container of the wrong kind, and a store with nothing in it must all fail to
ground, and they must fail for want of a licence rather than by the rule's
objection — the rule only ever asked for *a* container.
"""

from __future__ import annotations

import random
import re

from framingo import parse, parse_one, vessels
from framingo.grounding import check
from framingo.syntax import Pipeline, Statement

MARK = re.compile(r"'[A-Za-z][A-Za-z0-9-]*")
CORE = parse(vessels.core_rules())


def book():
    out = {}
    for line in vessels.dictionary().splitlines():
        out[line.split("tgt:")[1].split()[0]] = line
    return out


def grade(meaning: str, context: list[str]):
    statement = parse_one("FACT: " + meaning)
    action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
    given = [action]
    for text in context:
        given += list(parse(text))
    return check([statement], given, CORE)


def drawn(n=60, seed=0):
    entries, rng = book(), random.Random(seed)
    for _ in range(n):
        one = vessels.sample(rng)
        meaning = str(one.meaning())
        handed = [entries[x] for x in one.words() if x in entries]
        yield one, meaning, handed, entries


def test_what_the_world_claims_is_what_the_checker_derives():
    for one, meaning, handed, entries in drawn():
        report = grade(meaning, handed + [entries[one.vessel]])
        assert report.ok, f"{meaning}\n{report}"


def test_the_sentence_never_names_the_container():
    """If it did there would be nothing to ask for."""
    for one, _, _, _ in drawn():
        assert one.vessel not in one.words()


def test_the_core_names_no_individual():
    text = vessels.core_rules()
    named = [n for members in vessels.names().values() for n in members if n in text]
    assert not named, named[:3]


def test_the_material_decides_what_follows():
    """The one thing the answer is good for. Without this the question could be
    asked and the answer thrown away."""
    seen = {}
    for one, _, _, _ in drawn(120):
        seen.setdefault(one.material, set()).add(
            tuple(str(e.verb) for e in one.result.events[1:])
        )
    assert len(seen) > 1
    assert all(len(tails) == 1 for tails in seen.values()), seen
    assert len({next(iter(t)) for t in seen.values()}) == len(seen), seen


def test_a_container_nobody_handed_over_grounds_nothing():
    """The guarantee. Not the rule's objection — it asked only for *a*
    container — but the absence of anything that licensed a fact of that
    shape."""
    for one, meaning, handed, entries in drawn(30):
        invented = meaning.replace(one.vessel, "'Nowhere")
        assert not grade(invented, handed + [entries[one.vessel]]).ok


def test_a_container_of_the_wrong_kind_grounds_nothing():
    for one, meaning, handed, entries in drawn(30):
        wrong = next(
            n
            for kind, members in vessels.VESSEL_NAMES.items()
            if kind not in vessels.CONTAINERS[one.wanted]
            for n in members
        )
        swapped = meaning.replace(one.vessel, wrong)
        assert not grade(swapped, handed + [entries[wrong]]).ok


def test_an_empty_store_grounds_nothing():
    for _, meaning, handed, _ in drawn(30):
        assert not grade(meaning, handed).ok


def test_the_query_asks_about_a_class_and_never_about_a_name():
    records = vessels.build(n_train=120, n_iid=10, n_unseen=10, seed=0)
    for r in records:
        assert r.head.startswith("-> QUERY: State tgt:? is:")
        assert not MARK.findall(r.head), r.head
        assert r.query in vessels.CONTAINERS


def test_held_back_containers_never_train():
    _, _, vessel_train, vessel_unseen = vessels.pools(0)
    assert not vessel_train & vessel_unseen
    records = vessels.build(n_train=200, n_iid=20, n_unseen=20, seed=0)
    trained = {n for r in records if r.split == "train" for n in r.names.values()}
    assert not (trained & vessel_unseen)


def test_a_kind_of_container_is_not_itself_a_container():
    """`Any.Vessel.Thing` asks for one chosen from the set, and `Clay-Vessel`
    is what a vessel is, not a vessel."""
    for one, meaning, handed, entries in drawn(20):
        kind = meaning.replace(one.vessel, one.vessel_class)
        assert not grade(kind, handed + [entries[one.vessel]]).ok
