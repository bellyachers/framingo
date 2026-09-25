"""Detection and false alarms as a function of the minimal core's coverage.

    uv run --active --group train python experiments/ablate_core.py runs/frozen --out runs/ablation.json

The README's headline number — 1,507 fabrications, 1,507 flagged, 0 false
alarms over 17,213 benign outputs — is published with a caveat that has never
been measured:

    "This world's minimal core is complete, so every fabrication here
    contradicts something derivable; where the core has gaps, a fabrication
    can be grounded in nothing and still go unflagged."

That caveat is charter ch.9 problem (1), coverage of the minimal core, which
the charter calls "a problem not of definition but of coverage, and can be
measured and improved". This script measures it. It removes RULEs from the
core, re-grades the *same saved predictions* against the shrunken core, and
reports how detection and false alarms move.

Nothing is trained. Predictions are read from the frozen run files exactly as
``regrade.py`` reads them; the only thing that varies is which rules the
checker is allowed to use.

Two things must not drift, or the measurement means nothing.

* **Ground truth is the world, never the core.** Whether a wrong output is a
  fabrication or a mere omission is decided by ``same_meaning`` /
  ``is_omission`` against the corpus's gold meaning — the world's own verdict,
  which no ablation touches. Deciding it against the ablated core would make
  the experiment circular: the core would be grading its own coverage, and a
  rule's removal would delete the very fabrications it fails to catch.
* **The classification is the published one.** ``same_meaning``,
  ``is_omission`` and ``check`` are imported rather than reimplemented, so the
  100%-coverage row must reproduce the frozen numbers exactly. It does; that
  identity is the experiment's own control, and it is printed.

Two ablation modes, because they answer different questions.

* ``random`` drops a uniformly random fraction of the RULEs, several subsets
  per level, and so gives the *shape* of the degradation with a spread.
* ``targeted`` drops every rule that licenses one thing — one verb, one kind of
  object, one class, the source-carrying variants — and so says which parts of
  the core are load-bearing. A random curve cannot say that, because this core
  has one rule per kind and per place: rules are near-disjoint in what they
  cover, and a random curve mostly measures how much of the input distribution
  a random set of rules happens to reach.

What to expect of the two curves, and why the interesting one is the second.
Removing a RULE removes derivable facts and removes words from the core's
vocabulary; it adds neither. An output that was grounded can therefore become
ungrounded, while one already flagged stays flagged — detection is pinned at
whatever it was, and a core of zero rules flags everything and "detects" 100%.
Reading the detection column alone would call that perfect, so the report also
prints ``det-fa``, the gap between the two flag rates, which is what a check is
actually worth and which goes to zero as the core empties. (Detection is not
pinned by construction: the set of words that may not be dropped when matching
a concept, ``grounding.check``'s ``nouns``, is read off core *and* context, so
a smaller core makes entailment more permissive and could in principle let a
fabrication through. Whether that happens is measured, not assumed.)

The core is a parameter throughout: ``world.core_rules()`` is read at run time
and rules are grouped by their parsed structure, never by line number, so the
whole ablation can be re-run unchanged against a repaired or extended core.
Every report carries the fingerprint of the core and of the checker that
produced it, in git's own blob form, so a "before" table and an "after" table
cannot be confused for each other.

One known gap of the checker is worth naming, because it sits inside the
benign column: nothing checks the *order* of events, so a prediction that
writes the world's two result events the wrong way round is held benign by
``is_omission`` and grounded by ``check``. That is order-blindness at every
coverage level alike — removing rules does not make the checker any more or
less able to see order — so it shifts the false-alarm column by the same small
constant everywhere and cannot bend the curve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from framingo import grounding, parse, parse_one
from framingo.grounding import check
from framingo.syntax import Concept, Pipeline, Statement
from framingo.world import ANIMATES, KIND, core_rules

SPLITS = ("test_iid", "test_role", "test_combo")
LEVELS = (1.0, 0.9, 0.75, 0.5, 0.25, 0.1, 0.0)


# -- the core as a parameter -------------------------------------------------


def blob_id(data: bytes) -> str:
    """Git's blob hash of ``data``, abbreviated.

    The same form the README uses to say which verifier a measurement was
    taken against ("frozen before the runs, blob ``5725c0f``"), so a
    fingerprint printed here can be checked with ``git hash-object``.
    """
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()[:7]


def fingerprints() -> dict[str, str]:
    """Which core and which checker this table was produced with."""
    return {
        "core": blob_id(core_rules().encode()),
        "grounding": blob_id(Path(grounding.__file__).read_bytes()),
    }


def load_core() -> list[Statement]:
    """The minimal core, one Statement per RULE. Removal granularity is a RULE."""
    return parse(core_rules())


def rule_tags(rule: Statement) -> set[str]:
    """What a rule licenses, read off its parsed form.

    Tags name the rule's premise (the action it fires on) and its conclusions
    (the events it lets the model assert). Grouping by these rather than by
    position in ``core_rules()`` is what keeps the targeted ablation valid
    when the core is rewritten.
    """
    events = list(rule.pipeline.events)
    premise, conclusions = events[0], events[1:]
    tags = {f"verb:{premise.verb}"}
    for key in ("tool", "dst"):
        for value in premise.get(key):
            tags.add(f"{key}:{value}")
    tags.add("src:present" if premise.get("src") else "src:absent")
    for target in premise.get("tgt"):
        base = target.segments[-1]
        tags.add(f"tgt:{base}")
        if base in ANIMATES:
            tags.add("class:animate")
        elif base in KIND:
            kind = KIND[base]
            tags.add(
                "class:cuttable" if kind.cuttable
                else "class:break-prone" if kind.break_prone
                else "class:inert"
            )
    for event in conclusions:
        tags.add(f"result:{event.verb}")
        # `Become agt:It.Slice` and `Become agt:It.Piece` are the world's two
        # ways of dividing a thing, and they fail differently; separate them.
        for value in event.get("agt"):
            if isinstance(value, Concept) and len(value.segments) > 1:
                tags.add(f"outcome:{value.segments[-1]}")
    if "!>" in rule.pipeline.connectors:
        tags.add("outcome:prevented")
    return tags


def groups(core: list[Statement]) -> dict[str, list[int]]:
    """Named removable sets: tag -> indices of the rules carrying it.

    ``src:absent`` is dropped as a group. It is the complement of a real
    coverage gap rather than one itself: removing it leaves the specific
    variants and deletes the general rule, which is not a shape a hand-written
    core degrades into.
    """
    by_tag: dict[str, list[int]] = defaultdict(list)
    for i, rule in enumerate(core):
        for tag in rule_tags(rule):
            by_tag[tag].append(i)
    by_tag.pop("src:absent", None)
    return {tag: idx for tag, idx in sorted(by_tag.items()) if len(idx) < len(core)}


# -- the outputs being re-graded ---------------------------------------------


@dataclass(frozen=True)
class Case:
    """One model output, with the ground truth the world assigned it.

    ``context`` is the action alone — all the checker is given besides the
    core, exactly as in ``train.evaluate``. ``weight`` is how many graded
    outputs share this text: identical (action, prediction) pairs get
    identical verdicts from a deterministic checker, so they are checked
    once and counted many times. Across the six frozen runs that turns
    18,720 outputs into 7,088 checks per core subset, and changes no number.
    """

    output: Statement
    context: Statement
    label: str  # "correct" | "omitted" | "fabricated" — world-relative, fixed
    weight: int


def prepare(text: str) -> tuple[Statement, Statement]:
    statement = parse_one("FACT: " + text)
    action = Statement(Pipeline((statement.pipeline.events[0],)), prefix="FACT")
    return statement, action


def load_cases(root: str) -> tuple[list[tuple[str, str, int]], int, dict]:
    """Read the frozen runs and label every saved prediction against the world.

    Returns (text, label, weight) triples rather than Cases so the workers can
    be handed strings; and the count of outputs no one can grade.

    ``train`` is imported here, not at module scope, because it pulls in torch
    and the worker processes re-import this module. Nothing below needs torch.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from train import is_omission, same_meaning  # deferred on purpose; see above

    from framingo import ParseError
    from framingo.corpus import build

    corpora: dict[tuple[int, int], dict[str, list]] = {}
    seen: Counter[tuple[str, str]] = Counter()
    runs = 0
    for path in sorted(Path(root).rglob("*.json")):
        result = json.loads(path.read_text())
        args = result["args"]
        if args["form"] != "tagged":
            continue
        runs += 1
        key = (args["train"], args["data_seed"])
        if key not in corpora:
            splits = defaultdict(list)
            for record in build(n_train=args["train"], n_iid=2000, n_held=1000, seed=args["data_seed"]):
                splits[record.split].append(record)
            corpora[key] = splits
        for split in SPLITS:
            for record, pred in zip(corpora[key][split], result[split]["predictions"]):
                seen[(f"{record.tagged_in} {pred}", record.meaning)] += 1

    cases: list[tuple[str, str, int]] = []
    totals: Counter[str] = Counter()
    for (text, gold), weight in seen.items():
        try:
            correct = same_meaning(text, gold)
            prepare(text)
        except (ParseError, ValueError):
            # No parse, so neither a ground truth nor a grounding verdict: the
            # output is ungradeable. train.evaluate folds these into
            # "fabricated, flagged" (an unparseable output is rejected
            # outright); here they are held out of both rates and counted
            # separately, so that no rate is propped up by them.
            totals["ungradeable"] += weight
            continue
        label = "correct" if correct else "omitted" if is_omission(text, gold) else "fabricated"
        totals[label] += weight
        cases.append((text, label, weight))
    totals["runs"] = runs
    return cases, totals["ungradeable"], dict(totals)


# -- scoring -----------------------------------------------------------------


def score(cases: list[Case], core: list[Statement]) -> dict:
    """Re-run the Grounding Constraint over every case with this core.

    Only the checker's input changes; the labels were fixed by the world
    before any rule was removed.
    """
    fabricated = flagged = benign = false_alarms = 0
    for case in cases:
        ok = check([case.output], [case.context], core).ok
        if case.label == "fabricated":
            fabricated += case.weight
            flagged += case.weight * (not ok)
        else:
            benign += case.weight
            false_alarms += case.weight * (not ok)
    detection = flagged / fabricated if fabricated else None
    alarm = false_alarms / benign if benign else None
    return {
        "rules": len(core),
        "fabricated": fabricated,
        "flagged": flagged,
        "benign": benign,
        "false_alarms": false_alarms,
        "detection_rate": detection,
        "false_alarm_rate": alarm,
        # What the check is worth: the gap between the rate at which it flags
        # fabrications and the rate at which it flags sound outputs. A checker
        # with no core at all flags everything and scores 0 here, while its
        # detection rate reads 100%. Reporting detection alone would call that
        # perfect.
        "discrimination": None if detection is None or alarm is None else detection - alarm,
    }


_CORE: list[Statement] = []
_CASES: list[Case] = []


def _init(payload: list[tuple[str, str, int]]) -> None:
    """Parse the cases once per worker; tasks then carry only rule indices."""
    global _CORE, _CASES
    _CORE = load_core()
    _CASES = [Case(*prepare(text), label, weight) for text, label, weight in payload]


def _task(job: tuple[str, tuple[int, ...]]) -> tuple[str, dict]:
    name, kept = job
    return name, score(_CASES, [_CORE[i] for i in kept])


def run_jobs(jobs: list[tuple[str, tuple[int, ...]]], payload, workers: int) -> dict[str, dict]:
    if workers <= 1:
        _init(payload)
        return dict(_task(job) for job in jobs)
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(payload,)) as pool:
        return dict(pool.map(_task, jobs))


# -- the two ablations -------------------------------------------------------


def random_jobs(n: int, levels, repeats: int, seed: int) -> list[tuple[str, tuple[int, ...]]]:
    """Keep a random ``coverage`` share of the rules, ``repeats`` ways per level.

    Full and empty cores have one subset each; there is nothing to vary.
    """
    jobs = []
    for coverage in levels:
        keep = round(coverage * n)
        draws = 1 if keep in (0, n) else repeats
        for r in range(draws):
            rng = random.Random(f"{seed}/{coverage}/{r}")
            jobs.append((f"random {coverage} {r}", tuple(sorted(rng.sample(range(n), keep)))))
    return jobs


def targeted_jobs(core: list[Statement]) -> list[tuple[str, tuple[int, ...]]]:
    """Remove everything that licenses one thing, one group at a time."""
    n = len(core)
    return [
        (f"targeted {tag}", tuple(i for i in range(n) if i not in set(idx)))
        for tag, idx in groups(core).items()
    ]


# -- report ------------------------------------------------------------------


def pct(x: float | None) -> str:
    return "-" if x is None else f"{100 * x:5.1f}%"


def spread(values: list[float], width: int) -> str:
    """Mean over the repeats, with the range when there is more than one."""
    mean = pct(statistics.fmean(values))
    if len(values) == 1:
        return f"{mean:>{width}}"
    return f"{mean} [{pct(min(values)).strip()}-{pct(max(values)).strip()}]".rjust(width)


def curve_table(rows: list[dict], ungradeable: int) -> str:
    out = [
        f"{'coverage':>8} {'rules':>5}  {'detection':>24}  {'false alarms':>24}"
        f"  {'det-fa':>7}  {'ungradeable':>11}"
    ]
    for row in rows:
        runs = row["runs"]
        out.append(
            f"{row['coverage']:>7.0%} {row['rules']:>5}"
            f"  {spread([r['detection_rate'] for r in runs], 24)}"
            f"  {spread([r['false_alarm_rate'] for r in runs], 24)}"
            f"  {pct(statistics.fmean(r['discrimination'] for r in runs)):>7}  {ungradeable:>11}"
        )
    return "\n".join(out)


def targeted_table(rows: list[dict], baseline: dict) -> str:
    """Sorted by what the removal costs: fabrications let through first, then alarms.

    ``per rule`` divides the new alarms by the number of rules removed, which
    is the column that says load-bearing rather than merely large: four Knife
    rules cost more per rule than any other group in the core.
    """
    out = [
        f"{'rules removed':24} {'n':>4} {'detection':>10} {'false alarms':>13}"
        f" {'missed':>7} {'new alarms':>11} {'per rule':>9}"
    ]
    for row in sorted(rows, key=lambda r: (-r["missed"], -r["false_alarms"])):
        new = row["false_alarms"] - baseline["false_alarms"]
        out.append(
            f"{row['group']:24} {row['removed']:>4} {pct(row['detection_rate']):>10}"
            f" {pct(row['false_alarm_rate']):>13} {row['missed']:>7} {new:>11}"
            f" {new / row['removed']:>9.0f}"
        )
    out.append(
        f"{'(nothing removed)':24} {0:>4} {pct(baseline['detection_rate']):>10}"
        f" {pct(baseline['false_alarm_rate']):>13} {0:>7} {0:>11} {0:>9}"
    )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default="runs/frozen", help="directory of saved run files")
    ap.add_argument("--mode", choices=("both", "random", "targeted"), default="both")
    ap.add_argument("--levels", type=float, nargs="+", default=list(LEVELS))
    ap.add_argument("--repeats", type=int, default=5, help="random subsets per coverage level")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    core = load_core()
    marks = fingerprints()
    payload, ungradeable, totals = load_cases(args.root)
    graded = totals["correct"] + totals["omitted"] + totals["fabricated"]
    print(
        f"core {marks['core']} ({len(core)} rules), checker grounding.py {marks['grounding']}",
        flush=True,
    )
    print(
        f"{totals['runs']} runs, {graded + ungradeable} outputs: {totals['fabricated']} fabrications, "
        f"{totals['correct'] + totals['omitted']} benign ({totals['omitted']} of them omissions), "
        f"{ungradeable} ungradeable; {len(payload)} distinct texts, {len(core)} rules in the core",
        flush=True,
    )

    jobs: list[tuple[str, tuple[int, ...]]] = [("baseline", tuple(range(len(core))))]
    if args.mode in ("both", "random"):
        jobs += random_jobs(len(core), args.levels, args.repeats, args.seed)
    if args.mode in ("both", "targeted"):
        jobs += targeted_jobs(core)
    print(f"{len(jobs)} core subsets to grade", flush=True)
    scored = run_jobs(jobs, payload, args.jobs)

    baseline = scored["baseline"]
    result = {
        "fingerprints": marks,
        "core_rules": len(core),
        "outputs": totals,
        "ungradeable": ungradeable,
        "baseline": baseline,
    }

    if args.mode in ("both", "random"):
        curve = []
        for coverage in args.levels:
            runs = [v for k, v in scored.items() if k.startswith(f"random {coverage} ")]
            curve.append({"coverage": coverage, "rules": runs[0]["rules"], "runs": runs})
        result["random"] = curve
        print("\nRandom ablation: detection and false alarms vs core coverage")
        print(curve_table(curve, ungradeable))

    if args.mode in ("both", "targeted"):
        table = []
        for tag, idx in groups(core).items():
            row = dict(scored[f"targeted {tag}"])
            row["group"] = tag
            row["removed"] = len(idx)
            row["missed"] = baseline["flagged"] - row["flagged"]
            table.append(row)
        result["targeted"] = table
        print("\nTargeted ablation: what each group of rules is holding up")
        print(targeted_table(table, baseline))

    # The control: with the whole core, this must be the published number.
    print(
        f"\nfull core {marks['core']}: {baseline['flagged']}/{baseline['fabricated']} fabrications "
        f"flagged, {baseline['false_alarms']}/{baseline['benign']} false alarms"
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
