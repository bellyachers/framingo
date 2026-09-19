"""Re-grade saved predictions with the current checker, without retraining.

    uv run --group train python experiments/regrade.py runs/sweep

Recomputes every metric from the predictions stored in each result file, so
a fix to the checker can be measured against the same model outputs.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from train import evaluate

from framingo.corpus import build


def main(root: str) -> None:
    corpora: dict[tuple[int, int], dict[str, list]] = {}
    table = defaultdict(lambda: defaultdict(int))
    for path in sorted(Path(root).rglob("*.json")):
        result = json.loads(path.read_text())
        args = result["args"]
        if args["form"] != "tagged":
            continue
        key = (args["train"], args["data_seed"])
        if key not in corpora:
            splits = defaultdict(list)
            for r in build(n_train=args["train"], n_iid=2000, n_held=1000, seed=args["data_seed"]):
                splits[r.split].append(r)
            corpora[key] = splits
        for split in ("test_iid", "test_role", "test_combo"):
            m = evaluate(corpora[key][split], result[split]["predictions"], "tagged")
            t = table[(args["train"], split)]
            benign = round(m["accuracy"] * m["n"]) + m["omitted"]
            t["fabricated"] += m["fabricated"]
            t["flagged"] += round((m["detection_rate"] or 0) * m["fabricated"])
            t["omitted"] += m["omitted"]
            t["benign"] += benign
            t["false_alarms"] += round((m["false_alarm_rate"] or 0) * benign)
    print(f"{'train':>6} {'split':11} {'fabricated':>10} {'detected':>9} {'omitted':>8} {'false alarms':>13}")
    for (n, split), t in sorted(table.items()):
        rate = f"{t['flagged'] / t['fabricated']:.0%}" if t["fabricated"] else "-"
        print(f"{n:>6} {split:11} {t['fabricated']:>10} {t['flagged']:>5} {rate:>4} {t['omitted']:>7} "
              f"{t['false_alarms']:>6}/{t['benign']}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(sys.argv[1] if len(sys.argv) > 1 else "runs")
