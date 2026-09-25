"""The knowledge layer: what the model asks, and what comes back.

Charter chapter 3 puts knowledge outside the model and has the model fetch it
at inference time. Nothing in the language had to be added for that. A model's
outgoing request is a ``QUERY`` statement — spec ch.2 §6.4 already defines one
as a form with ``?`` where the unknown goes, and calls it a prompt *to* a
model, but the speech act does not change with the asker — and what comes back
is ``RULE`` and ``FACT`` statements, which the language already has. The
checker already skips ``QUERY`` when grounding, because a question asserts
nothing (``grounding.LIMITS``).

**Asking is not a decision.** The model holds no knowledge, so there is nothing
to weigh: every action is looked up, including the ones the model would seem to
know. That is the point of putting the store in this process rather than behind
a network — a lookup that costs nothing needs no rationing, and a lookup that
needs no rationing needs no judgement about what one knows, which is the
judgement models are worst at. The cost that does remain is context, not
latency, so a query must stay narrow: its shape is read off the action, so an
answer is bounded by the action's arity and not by the size of the store.

**An empty answer is a result, not a failure.** Where the store has a gap, the
model gets nothing back and says so, instead of falling through to whatever its
weights happen to hold. That turns a gap in coverage from something invisible
into something logged — the move this project makes everywhere else — and it
is what charter §4.3 needs in order to promote items into the core "from the
profile of search calls": a profile is only a true frequency if everything was
asked.

Matching is not reimplemented here. A rule answers a query when it *fires* on
the query's action, decided by running the checker's own forward chaining, so
the store and the verifier cannot come to disagree about what matches what.
"""

from __future__ import annotations

from dataclasses import dataclass

from .grounding import Knowledge
from .syntax import Event, Pipeline, Placeholder, Statement


def query_for(action: Event) -> Statement:
    """The query an action asks: what follows from this?

    Built from the action alone, which is what keeps query formation a
    structural operation rather than an act of knowing. In natural language,
    turning a situation into a good search is itself a task requiring
    understanding; here the shape of the question is the shape of the action.
    """
    return Statement(
        Pipeline(
            (
                Event(action.verb, action.slots, label="Action"),
                Event(Placeholder(), frozenset(), label="Result"),
            ),
            ("->",),
        ),
        prefix="QUERY",
    )


def asked_about(query: Statement) -> Event | None:
    """The event a query is about: its first event that is not a bare ``?``.

    A query for a result names its action (``Action: Cut … -> Result: ?``); a
    query working back to a cause names its result (``Action: ? -> Result:
    …``), and the store answers both by the same rule — whichever end is
    given is what a statement must match.
    """
    for event in query.pipeline.events:
        if not isinstance(event.verb, Placeholder):
            return event
    return None


@dataclass(frozen=True)
class Answer:
    """What came back, and from where.

    ``sources`` are the store's own labels for the statements returned, so a
    caller can log which part of the store a derivation leaned on — charter
    §4.3's profile of search calls.
    """

    statements: tuple[Statement, ...] = ()
    sources: tuple[str, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.statements

    def __str__(self) -> str:
        return "\n".join(str(s) for s in self.statements) if self.statements else "(nothing)"


class Store:
    """An in-process knowledge layer over a set of statements.

    In this process deliberately: see the module docstring on why the cost of
    asking decides whether asking can be unconditional.
    """

    def __init__(self, statements: list[Statement], source: str = "store") -> None:
        self.statements = list(statements)
        self.labels = [f"{source} line {s.line}" if s.line else f"{source} {i}" for i, s in enumerate(self.statements)]
        self._rules = [
            (s, str(i)) for i, s in enumerate(self.statements) if s.prefix == "RULE"
        ]
        self._facts = [(s, str(i)) for i, s in enumerate(self.statements) if s.prefix != "RULE"]

    def answer(self, query: Statement) -> Answer:
        """Every statement that bears on what the query asks.

        A rule bears on it when it fires on the event asked about, which is
        decided by the checker's own chaining rather than by a second
        implementation of matching. One pass, not to a fixpoint: a rule whose
        conclusion needs another rule is a second question, and the model is
        the one that has to ask it. Chaining silently here would hand back a
        finished derivation and measure nothing about the model's reasoning.

        Each rule is tried **on its own**, which is slower than saturating once
        over all of them and reading off what fired. Saturating once is also
        wrong: two rules that reach the same conclusion are not distinguished
        by the facts they leave behind, so the more general of the pair hides
        the more specific — `Push tgt:Every.Vase` hid `Push
        tgt:Every.Tall.Blue.Vase`, and an answer that omits the rule written
        for the case asked about is an answer that happens to be sufficient
        rather than one that is right. Where a split holds a shape out of
        training, that hidden rule is exactly the knowledge the test means to
        supply for the first time.
        """
        subject = asked_about(query)
        if subject is None:
            return Answer()
        asked = Statement(Pipeline((subject,)), prefix="FACT")
        hits = [
            index
            for rule, index in self._rules
            if _premise_verb(rule) == subject.verb and _fires(rule, index, asked)
        ]
        hits += [index for statement, index in self._facts if _mentions(statement, subject)]
        order = sorted(int(i) for i in hits)
        return Answer(
            tuple(self.statements[i] for i in order),
            tuple(self.labels[i] for i in order),
        )


def _premise_verb(rule: Statement) -> object:
    """The verb of the rule's first premise, which a subject must share.

    A cheap gate before the real test: a rule about ``Cut`` cannot fire on a
    question about ``Push``, and the store holds a rule per kind and modifier
    combination, so most of it can be skipped on the verb alone.
    """
    events = list(rule.condition.events) if rule.condition else list(rule.pipeline.events)
    return events[0].verb if events else None


def _fires(rule: Statement, index: str, asked: Statement) -> bool:
    """Does this one rule conclude anything from the event asked about?"""
    kb = Knowledge(rules=[(rule, index)])
    kb.add_statement(asked, "asked")
    known = len(kb.facts) + len(kb.prevented)
    kb.saturate(limit=1)
    return len(kb.facts) + len(kb.prevented) > known


def _mentions(statement: Statement, subject: Event) -> bool:
    """Does a stored fact speak about the same predicate as the question?

    Deliberately coarse. A fact is returned when it shares the question's
    verb, because narrowing further would need the matching a fact does not
    have a premise to do, and a few extra statements in context cost context
    while a missing one costs an answer.
    """
    return any(
        not isinstance(event.verb, Placeholder)
        and not isinstance(subject.verb, Placeholder)
        and event.verb == subject.verb
        for event in statement.pipeline.events
    )
