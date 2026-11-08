# python/ch18/multi_start_sa.py
"""シードを変えた multi-start SA で Intro HC を改善（第18章）.

既定は **提出用**: 制限時間をシードの数で区切り、逐次に SA を回して最良解を採る。
`--parallel` を付けると **ローカル実験用**: 各シードを別プロセスで同時に回す
（壁時計は短くなるが、ジャッジで同じ効果が出る保証はない）。

  python python/ch18/multi_start_sa.py < data/ch18/sample.txt             # 提出用（逐次）
  python python/ch18/multi_start_sa.py --parallel < data/ch18/sample.txt  # ローカル実験用
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, TextIO, Tuple

T0 = 5000.0  # 開始温度
T1 = 10.0  # 終了温度
TOTAL_TIME_SEC = 1.6  # 提出用: 全シード合計の探索時間（本番 2 秒なら余裕を残す）
SEEDS = [42, 43, 44, 45]


@dataclass
class ProblemInput:
    days: int
    decay: List[int]
    gain: List[List[int]]


def read_problem(stream: TextIO) -> ProblemInput:
    lines = stream.read().splitlines()
    days = int(lines[0])
    decay = list(map(int, lines[1].split()))
    gain = [list(map(int, lines[2 + i].split())) for i in range(days)]
    return ProblemInput(days=days, decay=decay, gain=gain)


def raw_score(problem: ProblemInput, types: List[int]) -> int:
    """10^6 + 最終満足度（0 で切らない値）。全再計算 O(26·D)."""
    last = [0] * 26
    satisfaction = 0
    for day in range(1, problem.days + 1):
        t = types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        satisfaction -= sum(problem.decay[i] * (day - last[i]) for i in range(26))
    return 10**6 + satisfaction


def type_penalty(problem: ProblemInput, types: List[int], t: int) -> int:
    """タイプ t の減衰ペナルティ合計 c_t * Σ L(L-1)/2。O(D)（第9章 9.4）."""
    total = 0
    prev = 0
    for day, x in enumerate(types, start=1):
        if x == t:
            gap = day - prev
            total += gap * (gap - 1) // 2
            prev = day
    gap = problem.days + 1 - prev
    total += gap * (gap - 1) // 2
    return problem.decay[t - 1] * total


def delta_change(problem: ProblemInput, types: List[int], day: int, new_type: int) -> int:
    """types[day] を new_type に変えたときの raw_score の変化量。O(D)（第9章 9.4）."""
    old_type = types[day]
    if old_type == new_type:
        return 0
    before = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = new_type
    after = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = old_type
    gain = problem.gain[day][new_type - 1] - problem.gain[day][old_type - 1]
    return gain - (after - before)


def sa_run(problem: ProblemInput, seed: int, time_limit_sec: float) -> Tuple[List[int], int, int]:
    """1 シード分の SA（第9章と同じ時間ベース冷却 + 差分更新）。(best, score, steps)."""
    rng = random.Random(seed)
    types = [rng.randint(1, 26) for _ in range(problem.days)]
    score = raw_score(problem, types)
    best_types = list(types)
    best_score = score
    start = time.perf_counter()
    step = 0

    while True:
        elapsed = time.perf_counter() - start
        if elapsed >= time_limit_sec:
            break
        temperature = T0 * (T1 / T0) ** (elapsed / time_limit_sec)
        day = rng.randrange(problem.days)
        new_type = rng.randint(1, 26)
        delta = delta_change(problem, types, day, new_type)
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            types[day] = new_type
            score += delta
            if score > best_score:
                best_score = score
                best_types = list(types)
        step += 1

    assert score == raw_score(problem, types), "delta_change と raw_score が一致しない"
    print(f"seed={seed} best={max(best_score, 0)} steps={step}", file=sys.stderr)
    return best_types, max(best_score, 0), step


def multi_start_sequential(problem: ProblemInput, seeds: List[int], total_sec: float) -> Tuple[List[int], int]:
    """提出用: total_sec をシード数で等分し、1 本ずつ順番に回す。"""
    per_seed = total_sec / len(seeds)
    results = [sa_run(problem, seed, per_seed) for seed in seeds]
    best_types, best_score, _ = max(results, key=lambda r: r[1])
    return best_types, best_score


def _worker(args: Tuple[ProblemInput, int, float]) -> Tuple[List[int], int, int]:
    problem, seed, limit = args
    return sa_run(problem, seed, limit)


def multi_start_parallel(problem: ProblemInput, seeds: List[int], per_seed_sec: float) -> Tuple[List[int], int]:
    """ローカル実験用: 各シードを別プロセスで同時に回す。"""
    with ProcessPoolExecutor(max_workers=len(seeds)) as ex:
        results = list(ex.map(_worker, [(problem, seed, per_seed_sec) for seed in seeds]))
    best_types, best_score, _ = max(results, key=lambda r: r[1])
    return best_types, best_score


def main() -> None:
    parser = argparse.ArgumentParser(description="multi-start SA（第18章）")
    parser.add_argument("--parallel", action="store_true", help="ローカル実験用に各シードを並列実行する")
    parser.add_argument("--seeds", type=int, default=len(SEEDS), help="シード数（42 から連番）")
    parser.add_argument("--time", type=float, default=TOTAL_TIME_SEC, help="全シード合計の探索時間（秒）")
    args = parser.parse_args()

    problem = read_problem(sys.stdin)
    seeds = list(range(42, 42 + args.seeds))
    wall_start = time.perf_counter()
    if args.parallel:
        # 1 シードあたりの時間は逐次版と同じにそろえ、壁時計だけ短くする
        best_types, best_score = multi_start_parallel(problem, seeds, args.time / len(seeds))
        mode = "parallel"
    else:
        best_types, best_score = multi_start_sequential(problem, seeds, args.time)
        mode = "sequential"
    wall = time.perf_counter() - wall_start

    for t in best_types:
        print(t)
    print(f"mode={mode} seeds={len(seeds)} merged best score={best_score} wall={wall:.2f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
