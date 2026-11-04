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
    print_gains(days, scores)


def print_gains(days: List[Dict[str, Any]], scores: List[int]) -> None:
    """一番伸びた日と、担当者ごとの伸び・コミット数（その日の伸びは、その日の owner の成果とみなす）."""
    if len(scores) < 2:
        return
    gains = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
    i = max(range(len(gains)), key=lambda k: gains[k])
    top = days[i + 1]
    print(f"biggest gain: day {top.get('day', '?')} ({gains[i]:+d}) {top.get('notes', '')}")

    owners: Dict[str, List[int]] = {}  # owner → [日数, 伸びの合計, コミット数]
    for d, g in zip(days[1:], gains):
        row = owners.setdefault(str(d.get("owner", "?")), [0, 0, 0])
        row[0] += 1
        row[1] += g
        row[2] += int(d.get("commits", 0))
    print()
    print("owner     days     gain  commits  gain/commit")
    for owner, (n, gain, commits) in sorted(owners.items()):
        per = f"{gain / commits:.0f}" if commits else "-"
        print(f"{owner:8}  {n:>4}  {gain:>+7d}  {commits:>7}  {per:>11}")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_log_path()
    log = load_log(path)
    summarize(log)


if __name__ == "__main__":
    main()
