"""Abstract syntax for Framingo (Gisaburo v1).

The tree mirrors the specification's own vocabulary: a Statement carries an
epistemic prefix, an optional ``when:`` condition and a pipeline of events
joined by ``->`` / ``!>``; an Event is a predicate plus an order-free set of
slots; a Concept is a dot chain.

Equality is structural and order-invariant over slots (spec ch.2 §2), so
``Cut agt:John tgt:Bread`` == ``Cut tgt:Bread agt:John``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PREFIXES = frozenset({"RULE", "FACT", "HYPO", "QUERY"})
CLAUSE_LABELS = frozenset({"Action", "Result", "State"})
SLOT_KEYS = frozenset(
    {
        "agt", "tgt", "tool", "src", "dst", "loc",
        "tense", "asp", "mod", "iter", "freq",
        "goal", "reason", "count", "is",
    }
)
DETERMINERS = frozenset({"Every", "Any", "Some", "This", "No"})
SUFFIXES = ("-able", "-prone", "-ed")
CONNECTORS = ("->", "!>")


@dataclass(frozen=True)
class Placeholder:
    """``?`` — an unknown to be filled (spec ch.2 §6.4)."""

    def __str__(self) -> str:
        return "?"


@dataclass(frozen=True)
class Concept:
    """A dot chain such as ``!Every.Break-prone.Glass.Piece<A>``.

    ``segments`` excludes the determiner. ``index`` is the anaphoric index of
    ``<A>`` (spec ch.3 §5.2); ``instance`` is the individual marker written
    ``[1]`` or ``#402`` in the specification's examples.
    """

    segments: tuple[str, ...]
    determiner: str | None = None
    negated: bool = False
    index: str | None = None
    instance: str | None = None

    def __str__(self) -> str:
        head = "!" if self.negated else ""
        parts = ([self.determiner] if self.determiner else []) + list(self.segments)
        tail = f"<{self.index}>" if self.index else ""
        if self.instance is not None:
            tail += f"#{self.instance}"
        return head + ".".join(parts) + tail


@dataclass(frozen=True)
class Event:
    """A predicate with its slots. ``label`` is Action / Result / State or None."""

    verb: Concept | Placeholder
    slots: frozenset[tuple[str, "SlotValue"]] = frozenset()
    label: str | None = None
    condition: "Pipeline | None" = None

    def get(self, key: str) -> "list[SlotValue]":
        return [v for k, v in self.slots if k == key]

    def __str__(self) -> str:
        parts = []
        if self.condition is not None:
            parts.append(f"when:({self.condition})")
        if self.label:
            parts.append(f"{self.label}:")
        parts.append(str(self.verb))
        parts += [f"{k}:{_value_str(v)}" for k, v in sorted(self.slots, key=_slot_order)]
        return " ".join(parts)


@dataclass(frozen=True)
class Pipeline:
    """``e0 c1 e1 c2 e2 ...`` with ``connectors[i]`` joining events i and i+1."""

    events: tuple[Event, ...]
    connectors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.connectors) != len(self.events) - 1:
            raise ValueError("a pipeline needs exactly one connector between events")

    def __str__(self) -> str:
        out = [str(self.events[0])]
        for c, e in zip(self.connectors, self.events[1:]):
            out += [c, str(e)]
        return " ".join(out)


@dataclass(frozen=True)
class Statement:
    pipeline: Pipeline
    prefix: str | None = None
    condition: Pipeline | None = None
    line: int = field(default=0, compare=False)

    def __str__(self) -> str:
        parts = []
        if self.prefix:
            parts.append(f"{self.prefix}:")
        if self.condition is not None:
            parts.append(f"when:({self.condition})")
        parts.append(str(self.pipeline))
        return " ".join(parts)


SlotValue = Concept | Placeholder | Pipeline


def _value_str(v: SlotValue) -> str:
    return f"({v})" if isinstance(v, Pipeline) else str(v)


def _slot_order(item: tuple[str, SlotValue]) -> tuple[str, str]:
    return (item[0], _value_str(item[1]))
