"""Command line: ``framingo parse``, ``framingo check`` and ``framingo corpus``."""

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

    g = sub.add_parser("corpus", help="generate the proposition-3 corpus as JSON lines")
    g.add_argument("out")
    g.add_argument("--train", type=int, default=20000)
    g.add_argument("--iid", type=int, default=2000)
    g.add_argument("--held", type=int, default=1000)
    g.add_argument("--seed", type=int, default=0)

    args = ap.parse_args(argv)
    if args.command == "corpus":
        from collections import Counter

        from .corpus import build, write

        records = build(args.train, args.iid, args.held, args.seed)
        write(records, Path(args.out))
        print(dict(Counter(r.split for r in records)))
        return 0
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
