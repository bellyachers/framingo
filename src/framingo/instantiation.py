"""A corpus with no physics in it: only the act of applying a rule.

`world.py` builds a world and asks a model to learn what happens in it. That
conflates two things. A model can score well there by learning the world — the
shapes of its actions and their results — without ever learning the operation
the charter actually assigns to the logic core: given a rule and a fact the
rule fires on, state the conclusion (charter ch.1, "the operation of drawing
valid conclusions from the propositions placed there").

Here there is nothing to learn but that operation. Predicates, entities and
modifiers are drawn from a pool of meaningless names, every rule has a verb of
its own, and the conclusion is whatever the rule says it is. Nothing about a
rule can be guessed from the world, because there is no world; a model that
gets the conclusion right either applied the rule or was lucky.

The split that matters is `test_unseen`: rules whose verbs, entities and
modifiers never occur in any training example. Their tokens are in the
vocabulary — the embeddings exist and are untrained, which is the honest
condition for a model asked to carry a symbol it has no habits about — and
applying such a rule requires treating its parts as variables rather than as
words with learned behaviour. That is the whole question, and this corpus is
the narrowest way to ask it.

The patterns a conclusion can take are deliberately few. Varying them without
limit would test whether a model can learn an unbounded grammar of rules, which
is a different and larger question; varying only the *content* asks whether the
operation generalises over symbols, which is the one the architecture rests on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .syntax import Concept, Event, Pipeline, Statement

# Names with nothing behind them. Three pools rather than one, so that a rule
# cannot be applied by guessing which position a familiar word belongs in.
VERBS = tuple(f"Vb{i:03}" for i in range(240))
ENTITIES = tuple(f"En{i:03}" for i in range(240))
MODIFIERS = tuple(f"Md{i:03}" for i in range(120))

PERIPHERAL = ("loc", "src", "dst", "tool", "reason")

# How a conclusion may be built out of what the premise bound. Each is a way of
# saying "carry this across", which is what instantiation is.
PATTERNS = (
    "copy_target",        # W tgt:It            — the target, unchanged
    "append_to_target",   # W agt:It.Md         — the target with a suffix
    "copy_agent",         # W tgt:It<A>         — the agent, which `It` alone cannot reach
    "both",               # W tgt:It -> W2 tgt:It<A>
)


def C(*segments: str, determiner: str | None = None, index: str | None = None) -> Concept:
    return Concept(tuple(segments), determiner=determiner, index=index)


@dataclass(frozen=True)
class Rule:
    """A rule, kept with the pieces needed to build facts that fire it.

    Rule and fact are made separately so that a split can hold one fixed while
    varying the other: `test_iid` asks for a rule the model has applied before
    on an instance it has not seen, and `test_unseen` asks for a rule it has
    never seen at all. Reading the pieces back out of the statement would work
    too, and would be one more place for the corpus and the checker to drift
    apart.
    """

    statement: Statement
    verb: str
    pattern: str
    target_base: str
    suffix: str
    out_verbs: tuple[str, ...]
    peripheral: tuple[str, str] | None


@dataclass(frozen=True)
class Drawn:
    """One rule, one fact it fires on, and what follows."""

    rule: Statement
    fact: Event
    conclusion: Pipeline

    def meaning(self) -> Pipeline:
        return Pipeline((self.fact,) + self.conclusion.events, ("->",) + self.conclusion.connectors)


def _names(rng: random.Random, pool: tuple[str, ...], share: tuple[float, float], n: int) -> list[str]:
    lo, hi = int(len(pool) * share[0]), int(len(pool) * share[1])
    return rng.sample(pool[lo:hi], n)


def make_rule(rng: random.Random, verb_index: int, share: tuple[float, float]) -> Rule:
    """A rule with a verb of its own.

    ``share`` is the stretch of each pool this rule may use, as a fraction, so
    that pools of different sizes are held back in the same proportion. It is
    how a split keeps names out of training: a rule built from the held-out
    stretch shares no verb, no entity and no modifier with anything a model has
    seen.
    """
    verb = VERBS[verb_index]
    pattern = rng.choice(PATTERNS)
    (target_base,) = _names(rng, ENTITIES, share, 1)
    (suffix,) = _names(rng, MODIFIERS, share, 1)
    out_verbs = tuple(_names(rng, VERBS, share, 2))
    peripheral = None
    if rng.random() < 0.5:
        key = rng.choice(PERIPHERAL)
        (value,) = _names(rng, ENTITIES, share, 1)
        peripheral = (key, value)

    slots: dict[str, Concept] = {
        "agt": C("Thing", determiner="Every", index="A"),
        "tgt": C(target_base, determiner="Every"),
    }
    if peripheral:
        slots[peripheral[0]] = C(peripheral[1])
    premise = Event(C(verb), frozenset(slots.items()), label="Action")

    it, it_a = C("It"), C("It", index="A")
    if pattern == "copy_target":
        conclusions = (Event(C(out_verbs[0]), frozenset({("tgt", it)}), label="Result"),)
    elif pattern == "append_to_target":
        conclusions = (Event(C(out_verbs[0]), frozenset({("agt", C("It", suffix))}), label="Result"),)
    elif pattern == "copy_agent":
        conclusions = (Event(C(out_verbs[0]), frozenset({("tgt", it_a)}), label="Result"),)
    else:
        conclusions = (
            Event(C(out_verbs[0]), frozenset({("tgt", it)}), label="Result"),
            Event(C(out_verbs[1]), frozenset({("tgt", it_a)}), label="Result"),
        )
    connectors = ("->",) * (len(conclusions) - 1)
    statement = Statement(Pipeline((premise,) + conclusions, ("->",) + connectors), prefix="RULE")
    return Rule(statement, verb, pattern, target_base, suffix, out_verbs, peripheral)


def make_fact(rule: Rule, rng: random.Random, share: tuple[float, float]) -> Drawn:
    """An instance the rule fires on, and the conclusion it licenses.

    The conclusion is written out here rather than derived, and a test asserts
    that the checker derives exactly this from the rule and the fact. Two ways
    of saying the same thing, kept in step by a test, is the arrangement the
    minimal core already uses on `world.py`.
    """
    agent, = _names(rng, ENTITIES, share, 1)
    (modifier,) = _names(rng, MODIFIERS, share, 1)
    target = C(modifier, rule.target_base) if rng.random() < 0.5 else C(rule.target_base)

    slots: dict[str, Concept] = {"agt": C(agent), "tgt": target}
    if rule.peripheral:
        slots[rule.peripheral[0]] = C(rule.peripheral[1])
    fact = Event(C(rule.verb), frozenset(slots.items()))

    if rule.pattern == "copy_target":
        events = (Event(C(rule.out_verbs[0]), frozenset({("tgt", target)})),)
    elif rule.pattern == "append_to_target":
        events = (Event(C(rule.out_verbs[0]), frozenset({("agt", C(*target.segments, rule.suffix))})),)
    elif rule.pattern == "copy_agent":
        events = (Event(C(rule.out_verbs[0]), frozenset({("tgt", C(agent))})),)
    else:
        events = (
            Event(C(rule.out_verbs[0]), frozenset({("tgt", target)})),
            Event(C(rule.out_verbs[1]), frozenset({("tgt", C(agent))})),
        )
    return Drawn(rule.statement, fact, Pipeline(events, ("->",) * (len(events) - 1)))


# -- the corpus --------------------------------------------------------------

TRAIN_SHARE = (0.0, 0.75)
UNSEEN_SHARE = (0.75, 1.0)


def build(
    n_rules: int = 150,
    n_unseen_rules: int = 40,
    facts_per_rule: int = 14,
    n_iid: int = 4,
    n_unseen_facts: int = 12,
    seed: int = 0,
) -> list["Record"]:
    """Records in the shape `experiments/train.py --ask` already reads.

    Three splits:

    - ``train``          facts of rules the model is trained on
    - ``test_iid``       further facts of *those same* rules, none of them seen
    - ``test_unseen``    facts of rules whose verb, entities and modifiers
                         occur in no training example at all

    The store the experiment queries holds every rule, seen and unseen alike,
    so a question about an unseen rule is answered — with a rule the model is
    meeting for the first time. Whether it can then apply it is the question
    the whole corpus exists to ask.
    """
    from .corpus import Record  # noqa: PLC0415  (Record lives with the world corpus)
    from .knowledge import query_for  # noqa: PLC0415
    from .render import tagged_event  # noqa: PLC0415

    # A rule's own verb has to come from its own stretch of the pool, not just
    # the words it mentions. Numbering the held-out rules straight on from the
    # trained ones put their verbs inside the training stretch, where a trained
    # rule could draw one as the verb of *its* conclusion — and then a model
    # meeting a "new" rule would already have a habit about its verb. A test
    # catches this (`test_the_held_out_rules_share_no_word_with_training`).
    first_unseen = int(len(VERBS) * UNSEEN_SHARE[0])
    assert n_rules <= first_unseen, f"at most {first_unseen} rules fit the training stretch"
    assert n_unseen_rules <= len(VERBS) - first_unseen, "not enough held-out verbs"
    rng = random.Random(seed)
    trained = [make_rule(rng, i, TRAIN_SHARE) for i in range(n_rules)]
    unseen = [make_rule(rng, first_unseen + i, UNSEEN_SHARE) for i in range(n_unseen_rules)]

    def record(drawn: Drawn, split: str) -> Record:
        action = tagged_event(drawn.fact, rng)
        return Record(
            split=split,
            meaning=str(drawn.meaning()),
            tagged_in=action,
            tagged_out=f"-> {drawn.conclusion}",
            word_order_in=action,
            word_order_out=f"-> {drawn.conclusion}",
            passive=False,
            query=str(query_for(drawn.fact)),
            answer=str(drawn.rule),
        )

    out: list[Record] = []
    for rule, split_counts in [(r, (facts_per_rule, n_iid)) for r in trained]:
        seen: set[str] = set()
        for split, count in zip(("train", "test_iid"), split_counts):
            made = 0
            while made < count:
                drawn = make_fact(rule, rng, TRAIN_SHARE)
                key = str(drawn.meaning())
                if key in seen:
                    continue
                seen.add(key)
                out.append(record(drawn, split))
                made += 1
    for rule in unseen:
        seen = set()
        made = 0
        while made < n_unseen_facts:
            drawn = make_fact(rule, rng, UNSEEN_SHARE)
            key = str(drawn.meaning())
            if key in seen:
                continue
            seen.add(key)
            out.append(record(drawn, "test_unseen"))
            made += 1
    return out


def store_of(records: list["Record"]) -> "Store":
    """A store holding every rule the corpus used, seen and unseen alike."""
    from . import parse  # noqa: PLC0415
    from .knowledge import Store  # noqa: PLC0415

    rules, ordered = set(), []
    for r in records:
        if r.answer not in rules:
            rules.add(r.answer)
            ordered.append(r.answer)
    return Store(parse("\n".join(ordered)), "store")
