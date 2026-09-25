"""Hand-written lexer and recursive-descent parser for Framingo.

The grammar followed is the chapter 4 EBNF of ``docs/language-spec.md``,
widened where the specification's own examples go beyond it. Every widening
is listed in ``SPEC_DEVIATIONS`` so that the gap between the grammar and the
examples stays visible instead of being silently absorbed.

Newlines are whitespace. A statement ends where its pipeline cannot continue,
that is, at the first event not followed by ``->``, ``!>`` or ``&>``; this is what lets
one code block hold several statements and one statement span blank lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .syntax import (
    CLAUSE_LABELS,
    DETERMINERS,
    PREFIXES,
    SLOT_KEYS,
    Concept,
    Event,
    Pipeline,
    Placeholder,
    Statement,
)

SPEC_DEVIATIONS = {
    "instance-marker": "`Bread[1]` and `Bread#402` appear in examples; the EBNF defines only `<Index>`.",
    "negation-prefix": "`!Lock-ed.Door` appears in ch.3 §3.3; the EBNF has no `!` on concepts.",
    "dotted-verb": "`Heavy.Hit` and `No.Change` are used as verbs; the EBNF's `Verb` is a bare identifier.",
    "bare-state": "`State tgt:...` without a colon appears in examples; the EBNF writes `State:`.",
    "predicate-header": "`Cut: agt:John ...` (ch.2 §1.2) is not in the chapter 4 EBNF.",
    "event-condition": "ch.2 puts `when:` on each Event, ch.4 once per block; both are accepted.",
    "determiner-clash": "`No.Change` (ch.4 §6.1) is a verb, but `No.` is also a determiner (ch.3 §4.1); it parses as determiner `No` + `Change`.",
    "condition-pipeline": "ch.4 allows only a StateExpression inside `when:( )`; ch.2 allows an EventSequence.",
}


class ParseError(ValueError):
    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"{line}:{column}: {message}")
        self.line = line
        self.column = column


@dataclass(frozen=True)
class Token:
    kind: str  # LABEL, WORD, ARROW, LPAREN, RPAREN, QMARK, EOF
    text: str
    line: int
    column: int


# A leading apostrophe marks a word the model does not hold: a name, or any
# term outside the instinct vocabulary (spec ch.2). The mark is morphological
# on purpose — Lojban separates its root words from its borrowings and names by
# shape, and shape is what lets a parser sort them without judgement. Because
# the parser can tell, resolving such a word is not something a model has to
# remember to do; it is done before the model sees anything.
_SEG = r"'?[A-Za-z0-9_]+(?:-[A-Za-z]+)*"
_TOKEN_RE = re.compile(
    rf"""
    (?P<COMMENT>//[^\n]*)
  | (?P<SPACE>[ \t\r\n]+)
  | (?P<ARROW>->|!>|&>)
  | (?P<LABEL>[A-Za-z_][A-Za-z0-9_]*:)
  | (?P<WORD>!?{_SEG}(?:\.{_SEG})*(?:<[A-Za-z0-9]+>)?(?:\[[0-9]+\]|\#[0-9]+)?)
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<QMARK>\?)
    """,
    re.VERBOSE,
)


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    pos, line, line_start = 0, 1, 0
    while pos < len(source):
        m = _TOKEN_RE.match(source, pos)
        if m is None:
            raise ParseError(f"unexpected character {source[pos]!r}", line, pos - line_start + 1)
        kind, text = m.lastgroup, m.group()
        if kind not in ("SPACE", "COMMENT"):
            tokens.append(Token(kind, text, line, pos - line_start + 1))
        newlines = text.count("\n")
        if newlines:
            line += newlines
            line_start = pos + text.rindex("\n") + 1
        pos = m.end()
    tokens.append(Token("EOF", "", line, pos - line_start + 1))
    return tokens


_CONCEPT_RE = re.compile(
    rf"^(?P<neg>!)?(?P<chain>{_SEG}(?:\.{_SEG})*)(?:<(?P<index>[A-Za-z0-9]+)>)?"
    r"(?:\[(?P<bracket>[0-9]+)\]|#(?P<hash>[0-9]+))?$"
)


def parse_concept(text: str) -> Concept:
    m = _CONCEPT_RE.match(text)
    if m is None:
        raise ValueError(f"not a concept: {text!r}")
    segments = m.group("chain").split(".")
    determiner = None
    if len(segments) > 1 and segments[0] in DETERMINERS:
        determiner, segments = segments[0], segments[1:]
    return Concept(
        segments=tuple(segments),
        determiner=determiner,
        negated=bool(m.group("neg")),
        index=m.group("index"),
        instance=m.group("bracket") or m.group("hash"),
    )


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # -- token helpers -----------------------------------------------------

    def peek(self, offset: int = 0) -> Token:
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def next(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, kind: str, text: str | None = None) -> Token:
        tok = self.next()
        if tok.kind != kind or (text is not None and tok.text != text):
            want = text or kind
            raise ParseError(f"expected {want}, found {tok.text or tok.kind!r}", tok.line, tok.column)
        return tok

    def at_label(self, names: frozenset[str] | set[str]) -> bool:
        tok = self.peek()
        return tok.kind == "LABEL" and tok.text[:-1] in names

    # -- grammar ------------------------------------------------------------

    def statements(self) -> list[Statement]:
        out = []
        while self.peek().kind != "EOF":
            out.append(self.statement())
        return out

    def statement(self) -> Statement:
        first = self.peek()
        prefix = None
        if self.at_label(PREFIXES):
            prefix = self.next().text[:-1]
        condition = self.condition() if self.at_label({"when"}) else None
        return Statement(self.pipeline(), prefix=prefix, condition=condition, line=first.line)

    def condition(self) -> Pipeline:
        self.expect("LABEL", "when:")
        self.expect("LPAREN")
        inner = self.pipeline()
        self.expect("RPAREN")
        return inner

    def pipeline(self) -> Pipeline:
        events = [self.event()]
        connectors = []
        while self.peek().kind == "ARROW":
            connectors.append(self.next().text)
            events.append(self.event())
        return Pipeline(tuple(events), tuple(connectors))

    def event(self) -> Event:
        condition = self.condition() if self.at_label({"when"}) else None
        tok = self.peek()
        label = None
        if self.at_label(CLAUSE_LABELS):
            label = self.next().text[:-1]
            verb = self.verb()
        elif tok.kind == "LABEL" and tok.text[:-1] not in SLOT_KEYS | PREFIXES | {"when"}:
            # predicate-header form: `Cut: agt:John ...`
            self.next()
            verb = parse_concept(tok.text[:-1])
        else:
            verb = self.verb()
        return Event(verb=verb, slots=frozenset(self.slots()), label=label, condition=condition)

    def verb(self) -> Concept | Placeholder:
        tok = self.next()
        if tok.kind == "QMARK":
            return Placeholder()
        if tok.kind == "WORD":
            return parse_concept(tok.text)
        raise ParseError(f"expected a predicate, found {tok.text or tok.kind!r}", tok.line, tok.column)

    def slots(self) -> list[tuple[str, object]]:
        out = []
        while self.at_label(SLOT_KEYS):
            key = self.next().text[:-1]
            out.append((key, self.slot_value()))
        return out

    def slot_value(self) -> object:
        tok = self.peek()
        if tok.kind == "QMARK":
            self.next()
            return Placeholder()
        if tok.kind == "LPAREN":
            self.next()
            inner = self.pipeline()
            self.expect("RPAREN")
            return inner
        if tok.kind == "WORD":
            self.next()
            return parse_concept(tok.text)
        raise ParseError(f"expected a slot value, found {tok.text or tok.kind!r}", tok.line, tok.column)


def parse(source: str) -> list[Statement]:
    """Parse zero or more statements."""
    return _Parser(tokenize(source)).statements()


def parse_one(source: str) -> Statement:
    statements = parse(source)
    if len(statements) != 1:
        raise ValueError(f"expected one statement, got {len(statements)}")
    return statements[0]
