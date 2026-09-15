"""Command line: ``framingo parse FILE...`` and ``framingo check``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .grounding import check
from .parser import ParseError, parse


def _load(path: str):
    try:
        return parse(Path(path).read_text(encoding="utf-8"))
    except ParseError as exc:
        raise SystemExit(f"{path}:{exc}") from None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="framingo")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="parse files and print each statement in canonical form")
    p.add_argument("files", nargs="+")

    c = sub.add_parser("check", help="check an output against the Grounding Constraint")
    c.add_argument("output")
    c.add_argument("--context", action="append", default=[], help="knowledge placed in context")
    c.add_argument("--core", action="append", default=[], help="minimal core axioms")

    args = ap.parse_args(argv)
    if args.command == "parse":
        for path in args.files:
            for statement in _load(path):
                print(statement)
        return 0

    context = [s for path in args.context for s in _load(path)]
    core = [s for path in args.core for s in _load(path)]
    report = check(_load(args.output), context, core)
    print(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
