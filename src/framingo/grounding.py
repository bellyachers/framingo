"""Grounding checker, v0.

Implements the Grounding Constraint of charter §2.2 at two levels.

**Token grounding.** Every identifier in the output must occur in the minimal
core or in the context. Closed-class words of the language itself (determiners,
``It``, TAM values, the meta-verbs) need no grounding, and a word formed with a
functional suffix (``Break-ed``) is grounded when its root is: suffixation is
logic, not knowledge (spec ch.3 §3).

**Relation grounding.** Every event the output asserts must be a known fact,
or be derivable from known facts by the RULE statements in core and context.
Known facts are the events of FACT (and unprefixed) statements, except those
introduced by ``!>``, which did *not* happen and are recorded as prevented.
A HYPO statement may assume its own ``when:`` condition and first event.

Entailment is deliberately narrow. An output concept is supported by a fact's
concept when it keeps the same head (last segment) and drops only modifiers:
``Red.Apple`` follows from ``Sweet.Red.Apple``, but ``Apple`` does not follow
from ``Apple.Slice``. Which words are modifiers is not declared anywhere (the
spec leaves ``Modifier`` / ``BaseEntity`` undefined), so it is read off the
core and context: a word that ever stands as the head of a concept there is a
noun and may not be dropped. Without this, ``Blue.Piece`` passed as grounded
by ``Blue.Plate.Piece``, which a trained model actually produced. In a RULE, a concept ending in ``Thing`` matches any
concept carrying its modifiers, and ``It`` refers to the target of the nearest
preceding event (spec ch.3 §5.1). Derivation is forward chaining to a fixpoint.

What v0 does not do is listed in ``LIMITS``; each item is a known way for a
hallucination to pass or a sound output to fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Iterable

from .syntax import DETERMINERS, SUFFIXES, Concept, Event, Pipeline, Placeholder, Statement

LIMITS = (
    "Class membership is not inferred: `Glass` does not match `Break-prone.Thing` unless the fact says `Break-prone.Glass`.",
    "Only `It` / `It<X>` anaphora is resolved; no other pronouns exist in v1.",
    "QUERY statements are not relation-checked, and RULE statements in the output are token-checked only.",
    "`mod:`, `freq:` and `asp:` carry no semantics; they are compared as plain slots.",
)

CLOSED_CLASS = frozenset(
    set(DETERMINERS)
    | {"It", "Thing", "State", "Become"}
    | {"past", "present", "future", "completed", "progressive", "iterative"}
    | {"can", "must", "may", "always", "often", "rarely", "never", "many", "Many"}
)

FACTUAL = (None, "FACT")


# -- vocabulary --------------------------------------------------------------


def root(word: str) -> str:
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix):
            return word[: -len(suffix)]
    return word


def _concepts_in(value: object) -> Iterable[Concept]:
    if isinstance(value, Concept):
        yield value
    elif isinstance(value, Pipeline):
        for event in value.events:
            yield from _concepts_in_event(event)


def _concepts_in_event(event: Event) -> Iterable[Concept]:
    if event.condition is not None:
        yield from _concepts_in(event.condition)
    if isinstance(event.verb, Concept):
        yield event.verb
    for _, value in event.slots:
        yield from _concepts_in(value)


def concepts(statement: Statement) -> Iterable[Concept]:
    if statement.condition is not None:
        yield from _concepts_in(statement.condition)
    yield from _concepts_in(statement.pipeline)


def words(statements: Iterable[Statement]) -> set[str]:
    return {root(seg) for s in statements for c in concepts(s) for seg in c.segments}


# -- anaphora ----------------------------------------------------------------


def _resolve(concept: Concept, antecedent: Concept | None, indexed: dict[str, Concept]) -> Concept:
    if not concept.segments or concept.segments[0] != "It":
        return concept
    target = indexed.get(concept.index) if concept.index else antecedent
    if target is None:
        return concept
    return Concept(
        segments=target.segments + concept.segments[1:],
        determiner=target.determiner,
        negated=concept.negated,
        instance=target.instance if len(concept.segments) == 1 else None,
    )


def _resolve_value(value: object, antecedent: Concept | None, indexed: dict[str, Concept]) -> object:
    if isinstance(value, Concept):
        return _resolve(value, antecedent, indexed)
    return value


def resolve_events(events: Iterable[Event]) -> list[Event]:
    """Replace ``It`` with the target of the nearest preceding event."""
    antecedent: Concept | None = None
    indexed: dict[str, Concept] = {}
    out = []
    for event in events:
        slots = frozenset((k, _resolve_value(v, antecedent, indexed)) for k, v in event.slots)
        resolved = Event(event.verb, slots, event.label, event.condition)
        out.append(resolved)
        for _, value in event.slots:
            if isinstance(value, Concept) and value.index and value.segments[0] != "It":
                indexed[value.index] = value
        targets = [v for v in resolved.get("tgt") if isinstance(v, Concept)]
        if targets:
            antecedent = targets[0]
    return out


# -- matching ----------------------------------------------------------------


def _dropped(fact: tuple[str, ...], claim: tuple[str, ...]) -> list[str] | None:
    """Segments removed if ``claim`` is an in-order subsequence of ``fact``, else None.

    Order and multiplicity both count: a set comparison let a model's
    ``Plate.Plate.Piece`` pass as grounded by ``Plate.Piece``.
    """
    dropped, i = [], 0
    for seg in fact:
        if i < len(claim) and claim[i] == seg:
            i += 1
        else:
            dropped.append(seg)
    return dropped if i == len(claim) else None


def entails(fact: Concept, claim: Concept, nouns: frozenset[str] = frozenset()) -> bool:
    """Does knowing ``fact`` support asserting ``claim``?

    ``nouns`` are words that may not be dropped (see the module docstring).
    """
    if fact == claim:
        return True
    dropped = _dropped(fact.segments, claim.segments)
    return (
        fact.negated == claim.negated
        and bool(claim.segments)
        and fact.segments[-1:] == claim.segments[-1:]
        and dropped is not None
        and not (set(dropped) & nouns)
        and (claim.instance is None or claim.instance == fact.instance)
        and claim.determiner in (None, fact.determiner)
    )


def _pattern_matches(pattern: Concept, concrete: Concept) -> bool:
    if pattern.negated != concrete.negated:
        return False
    segs = pattern.segments
    if segs and segs[-1] == "Thing":
        return set(segs[:-1]) <= set(concrete.segments)
    return entails(concrete, Concept(segs, negated=pattern.negated))


def _value_matches(pattern: object, concrete: object, binding: dict[Concept, Concept]) -> bool:
    if isinstance(pattern, Placeholder):
        return True
    if isinstance(pattern, Concept) and isinstance(concrete, Concept):
        if pattern in binding:
            return binding[pattern] == concrete
        if _pattern_matches(pattern, concrete):
            binding[pattern] = concrete
            return True
        return False
    return pattern == concrete


def _event_matches(pattern: Event, fact: Event, binding: dict[Concept, Concept]) -> bool:
    if pattern.verb != fact.verb:
        return False
    trial = dict(binding)
    for key, pv in pattern.slots:
        if not any(_value_matches(pv, fv, trial) for fv in fact.get(key)):
            return False
    binding.clear()
    binding.update(trial)
    return True


def _instantiate_concept(concept: Concept, binding: dict[Concept, Concept]) -> Concept:
    for pattern, concrete in binding.items():
        n = len(pattern.segments)
        if concept.segments[:n] == pattern.segments and concept.determiner == pattern.determiner:
            rest = concept.segments[n:]
            return Concept(
                concrete.segments + rest,
                determiner=concrete.determiner,
                negated=concept.negated,
                instance=concrete.instance if not rest else None,
            )
    return concept


def _instantiate(event: Event, binding: dict[Concept, Concept]) -> Event:
    slots = frozenset(
        (k, _instantiate_concept(v, binding) if isinstance(v, Concept) else v) for k, v in event.slots
    )
    return Event(event.verb, slots, event.label)


def supports(fact: Event, claim: Event, nouns: frozenset[str] = frozenset()) -> bool:
    if fact.verb != claim.verb:
        return False
    for key, cv in claim.slots:
        candidates = fact.get(key)
        if isinstance(cv, Concept):
            if not any(isinstance(fv, Concept) and entails(fv, cv, nouns) for fv in candidates):
                return False
        elif cv not in candidates:
            return False
    return True


# -- knowledge base ----------------------------------------------------------


def _bare(event: Event) -> Event:
    return Event(event.verb, event.slots)


@dataclass
class Knowledge:
    facts: dict[Event, str] = field(default_factory=dict)
    prevented: dict[Event, str] = field(default_factory=dict)
    rules: list[tuple[Statement, str]] = field(default_factory=list)
    nouns: frozenset[str] = frozenset()

    def add_statement(self, statement: Statement, source: str) -> None:
        if statement.prefix == "RULE":
            self.rules.append((statement, source))
            return
        if statement.prefix not in FACTUAL:
            return
        self._add_pipeline(statement, source)

    def _add_pipeline(self, statement: Statement, source: str, assume_first: bool = True) -> None:
        cond = list(statement.condition.events) if statement.condition else []
        events = resolve_events(cond + list(statement.pipeline.events))
        for event in events[: len(cond)]:
            self.facts.setdefault(_bare(event), source)
        body = events[len(cond):]
        connectors = ("->",) + statement.pipeline.connectors
        for connector, event in zip(connectors, body):
            target = self.prevented if connector == "!>" else self.facts
            target.setdefault(_bare(event), source)

    def lookup(self, claim: Event, table: dict[Event, str]) -> str | None:
        for fact, source in table.items():
            if supports(fact, claim, self.nouns):
                return source
        return None

    def saturate(self, limit: int = 32) -> None:
        """Forward-chain every RULE until nothing new follows."""
        for _ in range(limit):
            before = (len(self.facts), len(self.prevented))
            for rule, source in self.rules:
                self._apply(rule, source)
            if (len(self.facts), len(self.prevented)) == before:
                return

    def _apply(self, rule: Statement, source: str) -> None:
        cond = list(rule.condition.events) if rule.condition else []
        events = resolve_events(cond + list(rule.pipeline.events))
        premises = events[: len(cond) + 1]
        conclusions = list(zip(rule.pipeline.connectors, events[len(cond) + 1 :]))
        facts = list(self.facts)
        for chosen in product(facts, repeat=len(premises)):
            binding: dict[Concept, Concept] = {}
            if all(_event_matches(p, f, binding) for p, f in zip(premises, chosen)):
                label = f"derived by {source}"
                for connector, conclusion in conclusions:
                    table = self.prevented if connector == "!>" else self.facts
                    table.setdefault(_bare(_instantiate(conclusion, binding)), label)


# -- report ------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    event: Event
    status: str  # "known", "derived", "assumed", "prevented", "ungrounded"
    source: str = ""


@dataclass
class Report:
    ungrounded_words: list[tuple[str, int]] = field(default_factory=list)
    verdicts: list[Verdict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.ungrounded_words and all(v.status != "ungrounded" for v in self.verdicts)

    def __str__(self) -> str:
        lines = []
        for word, line in self.ungrounded_words:
            lines.append(f"line {line}: ungrounded word `{word}`")
        for v in self.verdicts:
            tail = f" ({v.source})" if v.source else ""
            lines.append(f"{v.status:10} {v.event}{tail}")
        lines.append("grounded" if self.ok else "NOT GROUNDED")
        return "\n".join(lines)


def check(
    output: Iterable[Statement],
    context: Iterable[Statement],
    core: Iterable[Statement] = (),
) -> Report:
    output, context, core = list(output), list(context), list(core)
    report = Report()

    vocabulary = words(core) | words(context) | CLOSED_CLASS
    for statement in output:
        for concept in concepts(statement):
            for seg in concept.segments:
                if root(seg) not in vocabulary and seg not in CLOSED_CLASS:
                    report.ungrounded_words.append((seg, statement.line))

    nouns = frozenset(
        c.segments[-1] for s in core + context for c in concepts(s) if c.segments and c.segments[-1] != "It"
    ) - {"Thing"}
    base = Knowledge(nouns=nouns)
    for statement in core:
        base.add_statement(statement, f"core line {statement.line}")
    for statement in context:
        base.add_statement(statement, f"context line {statement.line}")

    for statement in output:
        if statement.prefix in ("RULE", "QUERY"):
            continue
        kb = Knowledge(dict(base.facts), dict(base.prevented), list(base.rules), base.nouns)
        assumed: set[Event] = set()
        if statement.prefix == "HYPO":
            cond = list(statement.condition.events) if statement.condition else []
            first = resolve_events(cond + [statement.pipeline.events[0]])
            for event in first:
                kb.facts.setdefault(_bare(event), "assumed")
                assumed.add(_bare(event))
        kb.saturate()

        cond = list(statement.condition.events) if statement.condition else []
        events = resolve_events(cond + list(statement.pipeline.events))
        connectors = ("->",) * len(cond) + ("->",) + statement.pipeline.connectors
        for connector, event in zip(connectors, events):
            bare = _bare(event)
            if bare in assumed:
                report.verdicts.append(Verdict(event, "assumed"))
                continue
            table = kb.prevented if connector == "!>" else kb.facts
            source = kb.lookup(bare, table)
            if source is None:
                report.verdicts.append(Verdict(event, "ungrounded"))
            elif connector == "!>":
                report.verdicts.append(Verdict(event, "prevented", source))
            else:
                status = "derived" if source.startswith("derived") else "known"
                report.verdicts.append(Verdict(event, status, source))
    return report
