"""Grounding checker, v0.

Implements the Grounding Constraint of charter §2.2 at three levels.

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

**Order grounding.** ``->`` is not a list separator: it asserts that the left
event "directly brought about, temporally and mechanically" the right one
(spec ch.4 §1.1). An output that names the right events in the wrong sequence
therefore asserts a causal chain that never held — the vase becomes pieces and
then falls — and event-by-event derivability cannot see it, because each event
on its own is derivable. So every pipeline that licenses a fact also records
what it places after it, and a claimed ``X -> Y`` is rejected when everything
that licenses ``Y`` is placed before everything that licenses ``X``. Skipping
a link is not rejected: the chain ``A -> B -> C`` licenses the claim
``A -> C``, because the Grounding Constraint accepts abstraction by design
(spec ch.2 §3), and only the sequence it does not license is a fabrication.
Events that no pipeline chains are unordered, and pass in either sequence.

What v0 does not do is listed in ``LIMITS``; each item is a known way for a
hallucination to pass or a sound output to fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Iterable

from .syntax import DETERMINERS, SUFFIXES, Concept, Event, Pipeline, Placeholder, Statement

LIMITS = (
    "Class membership is read off `State tgt:X is:C` facts and closed transitively, but only a pattern ending in `Thing` consults it: `Break-prone.Thing` matches `Glass`, `Break-prone` alone does not.",
    "Only `It` / `It<X>` anaphora is resolved; no other pronouns exist in v1.",
    "QUERY statements are not relation-checked, and RULE statements in the output are token-checked only.",
    "`mod:`, `freq:` and `asp:` carry no semantics; they are compared as plain slots.",
    "Only `It` should stand for the matched target, but a conclusion that repeats a premise's segments and determiner is expanded into it too: `tgt:Red.Apple -> Become agt:Red.Apple.Slice` derives `Big.Red.Apple.Slice`. Writing the premise `tgt:Every.Red.Apple` is what keeps such a conclusion literal (world.core_rules).",
    "Order comes from the connectives alone: `when:` states are not placed before the action they condition, and events chained by no pipeline pass in either sequence.",
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


# -- class membership --------------------------------------------------------


def memberships(statements: Iterable[Statement]) -> dict[str, frozenset[str]]:
    """What each word is a kind of, according to what has been stated.

    A fact of the shape ``State tgt:John is:Human`` says that the word ``John``
    belongs to the class ``Human``. Reading these lets a rule be written about
    a class — ``Action: Drop tgt:Every.Break-prone.Thing`` — and still fire on
    ``Glass``, provided something says that a glass is break-prone. Without it
    a rule can only be written per word, which is what forced `world.core_rules`
    to enumerate and is why the core grew from 150 rules to 440.

    This is the half of the architecture that decides where the boundary runs.
    Binding a name to a class is arbitrary, unbounded and particular, so it is
    knowledge and belongs outside the model; what follows from belonging to a
    class is general, so it is the minimal core's to hold. A model that is told
    "John is a human" and can then apply everything it knows about humans is
    the arrangement charter chapter 1 describes.

    The relation is closed transitively: told that John is a human and that a
    human is animate, a rule about animates fires on John.
    """
    direct: dict[str, set[str]] = {}
    for statement in statements:
        if statement.prefix not in FACTUAL:
            continue
        for event in statement.pipeline.events:
            targets = [v for v in event.get("tgt") if isinstance(v, Concept)]
            classes = [v for v in event.get("is") if isinstance(v, Concept)]
            if not targets or not classes:
                continue
            for target in targets:
                if not target.segments:
                    continue
                key = target.segments[-1]
                direct.setdefault(key, set()).update(
                    segment for c in classes for segment in c.segments
                )
    closed: dict[str, frozenset[str]] = {}
    for key in direct:
        seen: set[str] = set()
        stack = [key]
        while stack:
            for name in direct.get(stack.pop(), ()):
                if name not in seen:
                    seen.add(name)
                    stack.append(name)
        closed[key] = frozenset(seen)
    return closed


def _classes_of(concept: Concept, classes: dict[str, frozenset[str]]) -> set[str]:
    """Everything the words of a concept are known to be a kind of."""
    out: set[str] = set()
    for segment in concept.segments:
        out |= classes.get(segment, frozenset())
    return out


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
        # The resolved concept stands for the antecedent, so it carries the
        # antecedent's index. Without it, two premise patterns that differ only
        # by index — `tgt:Every.Thing` beside `src:Every.Thing<S>` — become
        # indistinguishable when a conclusion is instantiated, and the source
        # of a fall is filled in with the thing that fell.
        index=target.index,
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


def _pattern_matches(
    pattern: Concept, concrete: Concept, classes: dict[str, frozenset[str]] | None = None
) -> bool:
    if pattern.negated != concrete.negated:
        return False
    segs = pattern.segments
    if segs and segs[-1] == "Thing":
        # a class pattern: the concrete concept must carry each of the
        # pattern's words, either in its own segments or by membership
        known = set(concrete.segments) | _classes_of(concrete, classes or {})
        return set(segs[:-1]) <= known
    return entails(concrete, Concept(segs, negated=pattern.negated))


def _value_matches(
    pattern: object,
    concrete: object,
    binding: dict[Concept, Concept],
    classes: dict[str, frozenset[str]] | None = None,
) -> bool:
    if isinstance(pattern, Placeholder):
        return True
    if isinstance(pattern, Concept) and isinstance(concrete, Concept):
        if pattern in binding:
            return binding[pattern] == concrete
        if _pattern_matches(pattern, concrete, classes):
            binding[pattern] = concrete
            return True
        return False
    return pattern == concrete


def _event_matches(
    pattern: Event,
    fact: Event,
    binding: dict[Concept, Concept],
    classes: dict[str, frozenset[str]] | None = None,
) -> bool:
    if pattern.verb != fact.verb:
        return False
    trial = dict(binding)
    for key, pv in pattern.slots:
        if not any(_value_matches(pv, fv, trial, classes) for fv in fact.get(key)):
            return False
    binding.clear()
    binding.update(trial)
    return True


def _instantiate_concept(concept: Concept, binding: dict[Concept, Concept]) -> Concept:
    for pattern, concrete in binding.items():
        n = len(pattern.segments)
        if (
            concept.segments[:n] == pattern.segments
            and concept.determiner == pattern.determiner
            and concept.index == pattern.index
        ):
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


def _first_premise(rule: Statement) -> Event:
    return rule.condition.events[0] if rule.condition is not None else rule.pipeline.events[0]


def _demanded(premise: Event) -> tuple[object, str | None]:
    """What a rule's first premise demands of a fact, as an index key.

    A rule can fire only if some fact matches that premise, and
    ``_event_matches`` demands the verb exactly. Where the premise also fixes
    a single ``tgt:`` concept, matching it falls through to ``entails``, which
    demands the same head segment — so the head joins the key and a core that
    names one rule per kind skips almost all of itself per fact. A pattern
    ending in ``Thing`` is a class pattern and matches any head; a premise
    naming no target demands nothing of one. Both keep ``None`` there and stay
    in the catch-all bucket, tried against every fact carrying their verb.
    """
    targets = premise.get("tgt")
    if len(targets) == 1 and isinstance(targets[0], Concept):
        segments = targets[0].segments
        if segments and segments[-1] != "Thing":
            return (premise.verb, segments[-1])
    return (premise.verb, None)


def _offered(fact: Event) -> set[tuple[object, str | None]]:
    """The index keys this fact can answer."""
    keys = {(fact.verb, None)}
    for value in fact.get("tgt"):
        if isinstance(value, Concept) and value.segments:
            keys.add((fact.verb, value.segments[-1]))
    return keys


@dataclass
class Knowledge:
    facts: dict[Event, str] = field(default_factory=dict)
    prevented: dict[Event, str] = field(default_factory=dict)
    rules: list[tuple[Statement, str]] = field(default_factory=list)
    nouns: frozenset[str] = frozenset()
    # what each word is a kind of, so a rule about a class fires on a member
    classes: dict[str, frozenset[str]] = field(default_factory=dict)
    # `after[P]` are the events some pipeline places immediately after P. The
    # relation is kept beside the facts rather than inside them because the
    # same event can be licensed by several pipelines, each with its own
    # neighbours, and a fact is one thing however many chains lead to it.
    after: dict[Event, set[Event]] = field(default_factory=dict)
    _keyed: list[tuple[tuple[object, str | None], Statement, str]] = field(
        default_factory=list, repr=False, compare=False
    )

    def keyed_rules(self) -> list[tuple[tuple[object, str | None], Statement, str]]:
        """``rules`` paired with their index keys, in their original order.

        Built once and handed to the per-statement copies, so a core of a few
        hundred rules is keyed once per check rather than once per statement.
        """
        if len(self._keyed) != len(self.rules):
            self._keyed = [(_demanded(_first_premise(r)), r, s) for r, s in self.rules]
        return self._keyed

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
        self.sequence(body, statement.pipeline.connectors)

    def sequence(self, chain: Iterable[Event], connectors: tuple[str, ...] = ()) -> None:
        """Record what each event of ``chain`` is licensed after.

        A prevented event keeps its place in the chain: ``A !> B -> C`` still
        says where C stands relative to B, and the claim that C came first is
        as wrong as it would be had B happened.

        ``&>`` places nothing. It joins its two sides into one group of events
        that hold at once, neither having brought the other about (spec ch.4
        §1.3), so the group is unordered within itself and every member of one
        group precedes every member of the next. Passing no connectors reads
        the chain as all ``->``, which is what every caller meant before the
        connective existed.
        """
        events = [_bare(e) for e in chain]
        if not events:
            return
        groups: list[list[Event]] = [[events[0]]]
        for connector, event in zip(connectors + ("->",) * len(events), events[1:]):
            if connector != "&>":
                groups.append([])
            groups[-1].append(event)
        for earlier, later in zip(groups, groups[1:]):
            for event in earlier:
                self.after.setdefault(event, set()).update(later)

    def lookup(self, claim: Event, table: dict[Event, str]) -> str | None:
        for fact, source in table.items():
            if supports(fact, claim, self.nouns):
                return source
        return None

    def supporters(self, claim: Event, table: dict[Event, str]) -> set[Event]:
        """Every fact that licenses ``claim``, not just the first.

        ``lookup`` answers whether the claim is derivable at all; the order
        check needs all the candidates, because the claim inherits a position
        from each of them and one consistent position is enough.
        """
        return {fact for fact in table if supports(fact, claim, self.nouns)}

    def licensed_after(self, event: Event) -> set[Event]:
        """Every event placed after ``event``, transitively.

        Transitively, because skipping a link is not a fabrication: from
        ``A -> B -> C`` the claim ``A -> C`` states a real order, coarsely.
        """
        seen: set[Event] = set()
        stack = [event]
        while stack:
            for nxt in self.after.get(stack.pop(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def misordered(self, earlier: set[Event], later: set[Event]) -> bool:
        """Is claiming ``earlier -> later`` an inversion of the licensed order?

        Only when *every* way of licensing the two puts them the other way
        round. If some pair is chained in the claimed direction, or chained
        in neither — the carrier and the carried arriving at one and the same
        moment — the claim asserts nothing the knowledge contradicts.
        """
        return bool(earlier) and bool(later) and all(
            e in self.licensed_after(l) and l not in self.licensed_after(e)
            for e in earlier
            for l in later
        )

    def saturate(self, limit: int = 32) -> None:
        """Forward-chain every RULE until nothing new follows.

        A rule whose first premise no present fact can answer cannot fire, so
        it is skipped on the index key instead of being resolved and matched
        against every fact. The rules are still visited in their own order,
        and the available keys are refreshed the moment a rule adds a fact, so
        what is derived — and which rule is credited with deriving it — is
        what trying all of them would give.
        """
        for _ in range(limit):
            before = (len(self.facts), len(self.prevented))
            available: set[tuple[object, str | None]] = set()
            counted = -1
            for key, rule, source in self.keyed_rules():
                if len(self.facts) != counted:
                    counted = len(self.facts)
                    available = {k for fact in self.facts for k in _offered(fact)}
                if key in available:
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
            if all(_event_matches(p, f, binding, self.classes) for p, f in zip(premises, chosen)):
                label = f"derived by {source}"
                derived = []
                for connector, conclusion in conclusions:
                    table = self.prevented if connector == "!>" else self.facts
                    derived.append(_bare(_instantiate(conclusion, binding)))
                    table.setdefault(derived[-1], label)
                # The rule's own action — its last premise, the fact that fired
                # it — heads the chain it licenses: the conclusions follow the
                # cause, not the `when:` state that merely held (spec ch.4 §2).
                self.sequence(chosen[-1:] + tuple(derived),
                              tuple(c for c, _ in conclusions))


# -- report ------------------------------------------------------------------


# A verdict that fails the Grounding Constraint. `misordered` is kept apart
# from `ungrounded` because the two are different complaints and a reader
# needs to tell them apart: the event is not derivable at all, against the
# event is derivable but not at this point in the chain.
REJECTED = frozenset({"ungrounded", "misordered"})


@dataclass(frozen=True)
class Verdict:
    event: Event
    status: str  # "known", "derived", "assumed", "prevented", "ungrounded", "misordered"
    source: str = ""


@dataclass
class Report:
    ungrounded_words: list[tuple[str, int]] = field(default_factory=list)
    verdicts: list[Verdict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.ungrounded_words and all(v.status not in REJECTED for v in self.verdicts)

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
    base = Knowledge(nouns=nouns, classes=memberships(core + context))
    for statement in core:
        base.add_statement(statement, f"core line {statement.line}")
    for statement in context:
        base.add_statement(statement, f"context line {statement.line}")

    for statement in output:
        if statement.prefix in ("RULE", "QUERY"):
            continue
        kb = Knowledge(
            dict(base.facts),
            dict(base.prevented),
            list(base.rules),
            base.nouns,
            classes=base.classes,
            after={event: set(nxt) for event, nxt in base.after.items()},
            _keyed=base.keyed_rules(),
        )
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
        # The verdict index of each event the pipeline puts in sequence, with
        # the facts that license it. The `when:` events are left out: they are
        # joined by no connective and so claim no position (see LIMITS).
        claimed: list[tuple[int, set[Event]]] = []
        for position, (connector, event) in enumerate(zip(connectors, events)):
            bare = _bare(event)
            if bare in assumed:
                report.verdicts.append(Verdict(event, "assumed"))
                licensed_by = {bare}
            else:
                table = kb.prevented if connector == "!>" else kb.facts
                source = kb.lookup(bare, table)
                if source is None:
                    report.verdicts.append(Verdict(event, "ungrounded"))
                    continue
                if connector == "!>":
                    report.verdicts.append(Verdict(event, "prevented", source))
                else:
                    status = "derived" if source.startswith("derived") else "known"
                    report.verdicts.append(Verdict(event, status, source))
                licensed_by = kb.supporters(bare, table)
            if position >= len(cond):
                claimed.append((len(report.verdicts) - 1, licensed_by))

        # Every pair, not only neighbours: the licensed order is partial, so
        # an inversion can straddle an event that is ordered against neither.
        # The event named too early is the one marked; it is the one whose
        # place in the chain the knowledge refuses.
        for step, (index, earlier) in enumerate(claimed):
            for _, later in claimed[step + 1 :]:
                if kb.misordered(earlier, later):
                    verdict = report.verdicts[index]
                    report.verdicts[index] = Verdict(verdict.event, "misordered", verdict.source)
                    break
    return report
