# python/ch29/improvement_log.py
"""週次改善ログ JSON を読み、スコア推移を要約（第29章）."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def default_log_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "ch29" / "weekly_log.json"


def load_log(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def summarize(log: Dict[str, Any]) -> None:
    days: List[Dict[str, Any]] = log.get("days", [])
    if not days:
        print("no days in log", file=sys.stderr)
        return

    scores = [int(d["score"]) for d in days]
    best = max(scores)
    best_day = days[scores.index(best)]["day"]
    first, last = scores[0], scores[-1]
    delta = last - first
    pct = (100.0 * delta / first) if first else 0.0

    print(f"contest: {log.get('contest', '?')}")
    print(f"problem: {log.get('problem', '?')}  team: {log.get('team', '?')}")
    print(f"days: {len(days)}  unit: {log.get('unit', 'score')}")
    print()
    print("day  date        owner    score     delta    note")
    prev = None
    for d in days:
        sc = int(d["score"])
        delta_s = "" if prev is None else f"{sc - prev:+d}"
        note = str(d.get("notes", ""))[:28]
        print(
            f"{d.get('day', '?'):>3}  {d.get('date', '?'):10}  "
            f"{d.get('owner', '?'):8}  {sc:>9}  {delta_s:>7}  {note}"
        )
        prev = sc
    print()
    print(f"start → end: {first} → {last}  (Δ {delta:+d}, {pct:+.2f}%)")
    print(f"best: {best} on day {best_day}")
    regressions = sum(
        1 for i in range(1, len(scores)) if scores[i] < scores[i - 1]
    )
    print(f"regression days: {regressions}")
    total_commits = sum(int(d.get("commits", 0)) for d in days)
    print(f"total commits: {total_commits}", file=sys.stderr)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_log_path()
    log = load_log(path)
    summarize(log)


if __name__ == "__main__":
    main()
