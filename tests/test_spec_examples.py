"""Every Framingo sample in docs/language-spec.md must parse.

The specification is the test corpus: when an example stops parsing, either
the parser or the example is wrong, and the failure says which block.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from framingo import parse

SPEC = Path(__file__).resolve().parents[1] / "docs" / "language-spec.md"

# Blocks that describe syntax rather than being Framingo: the EBNF, and
# schemata written with [Placeholder] brackets.
_SCHEMA = re.compile(r"::=|\[[A-Z][A-Za-z_0-9]*(?:\.\.\.)?\]|\[PREFIX\]")


def _blocks() -> list[tuple[int, str]]:
    text = SPEC.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^[ \t]*```[a-z]*\n(.*?)^[ \t]*```", text, re.S | re.M):
        body = m.group(1)
        if not _SCHEMA.search(body):
            out.append((text.count("\n", 0, m.start()) + 1, body))
    return out


BLOCKS = _blocks()


def test_corpus_is_not_empty():
    assert len(BLOCKS) >= 35


@pytest.mark.parametrize("line,body", BLOCKS, ids=[f"spec:{line}" for line, _ in BLOCKS])
def test_example_parses(line, body):
    statements = parse(body)
    assert statements, f"block at line {line} produced no statements"
