#!/usr/bin/env python
"""Intro HC 問題A の解法を、複数の入力でまとめて採点する（付録G）.

  python tools/eval_intro_hc.py -- python python/ch09/sa_intro_hc.py
  python tools/eval_intro_hc.py --seeds 10 -- go run go/ch09/sa_intro_hc.go

seed 1〜N の入力（D=365）を tools/gen_intro_hc.py と同じ方法で作り、解法の stdout を
第1章の score_intro_hc.py と同じ式で採点する。実行時間が --tl 秒を超えたら TLE と表示する。
go run はビルドの時間も含んでしまうので、時間を正しく見たいときは go build したものを渡す。
"""
from __future__ import annotations

import argparse
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python" / "ch01"))
from score_intro_hc import daily_satisfactions, final_score  # noqa: E402


def make_input(seed: int, days: int = 365):
    """tools/gen_intro_hc.py と同じ乱数の使い方で入力を作る."""
    rng = random.Random(seed)
    c = [rng.randint(0, 100) for _ in range(26)]
    s = [[rng.randint(0, 20000) for _ in range(26)] for _ in range(days)]
    text = f"{days}\n" + " ".join(map(str, c)) + "\n" + "".join(" ".join(map(str, row)) + "\n" for row in s)
    return text, days, c, s


def score_output(stdout: str, days: int, c, s) -> int:
    """出力が不正（行数が違う、1〜26 以外）なら 0 点（本番の WA の代わり）."""
    try:
        schedule = [int(x) for x in stdout.split()]
    except ValueError:
        return 0
    if len(schedule) != days or not all(1 <= t <= 26 for t in schedule):
        return 0
    return final_score(daily_satisfactions(days, c, s, schedule)[-1])


def main() -> None:
    parser = argparse.ArgumentParser(description="Intro HC 問題A の解法をまとめて採点")
    parser.add_argument("--seeds", type=int, default=5, help="seed 1〜N の入力で採点する")
    parser.add_argument("--tl", type=float, default=2.0, help="制限時間（秒）")
    parser.add_argument("solver", nargs=argparse.REMAINDER, help="-- のあとに解法の起動コマンド")
    args = parser.parse_args()
    cmd = args.solver[1:] if args.solver[:1] == ["--"] else args.solver
    if not cmd:
        parser.error("解法のコマンドを -- のあとに書いてください")

    total, worst = 0, 0.0
    for seed in range(1, args.seeds + 1):
        text, days, c, s = make_input(seed)
        start = time.perf_counter()
        proc = subprocess.run(cmd, input=text, capture_output=True, text=True, cwd=ROOT)
        elapsed = time.perf_counter() - start
        worst = max(worst, elapsed)
        score = score_output(proc.stdout, days, c, s) if proc.returncode == 0 else 0
        status = "RE" if proc.returncode != 0 else ("TLE" if elapsed > args.tl else "ok")
        total += score
        print(f"seed={seed} score={score} time={elapsed:.2f}s {status}")
    print(f"average={total // args.seeds} max_time={worst:.2f}s")


if __name__ == "__main__":
    main()
