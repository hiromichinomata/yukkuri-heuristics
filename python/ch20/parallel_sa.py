# python/ch20/parallel_sa.py
"""多開始 SA（シード並列）で Intro HC を改善（第20章）."""
from __future__ import annotations

import math
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, TextIO, Tuple

T0 = 5000.0
ALPHA = 0.995
TIME_LIMIT_SEC = 0.8
NUM_WORKERS = 4


@dataclass
class ProblemInput:
    days: int
    decay: List[int]
    gain: List[List[int]]


@dataclass
class ScheduleState:
    types: List[int]


def read_problem(stream: TextIO) -> ProblemInput:
    lines = stream.read().splitlines()
    idx = 0
    days = int(lines[idx])
    idx += 1
    decay = list(map(int, lines[idx].split()))
    idx += 1
    gain = [list(map(int, lines[idx].split())) for _ in range(days)]
    return ProblemInput(days=days, decay=decay, gain=gain)


def score_schedule(problem: ProblemInput, state: ScheduleState) -> int:
    last = [0] * 26
    satisfaction = 0
    for day in range(1, problem.days + 1):
        t = state.types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        decay = sum(problem.decay[i] * (day - last[i]) for i in range(26))
        satisfaction -= decay
    return max(10**6 + satisfaction, 0)


def random_neighbor(state: ScheduleState, rng: random.Random) -> ScheduleState:
    nxt = ScheduleState(list(state.types))
    day = rng.randrange(len(nxt.types))
    nxt.types[day] = rng.randint(1, 26)
    return nxt


def sa_run(
    problem: ProblemInput,
    seed: int,
    time_limit_sec: float,
) -> Tuple[List[int], int]:
    rng = random.Random(seed)
    state = ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    score = score_schedule(problem, state)
    best_types = list(state.types)
    best_score = score
    temperature = T0
    start = time.perf_counter()
    step = 0

    while time.perf_counter() - start < time_limit_sec:
        nxt = random_neighbor(state, rng)
        new_score = score_schedule(problem, nxt)
        delta = new_score - score
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            state = nxt
            score = new_score
            if score > best_score:
                best_score = score
                best_types = list(state.types)
        temperature *= ALPHA
        step += 1

    print(f"worker seed={seed} best={best_score} steps={step}", file=sys.stderr)
    return best_types, best_score


def _worker(args: Tuple[ProblemInput, int, float]) -> Tuple[List[int], int]:
    problem, seed, limit = args
    return sa_run(problem, seed, limit)


def parallel_sa(problem: ProblemInput) -> Tuple[List[int], int]:
    seeds = [42, 43, 44, 45]
    results: List[Tuple[List[int], int]] = []

    try:
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as ex:
            futures = [
                ex.submit(_worker, (problem, seed, TIME_LIMIT_SEC)) for seed in seeds
            ]
            for fut in as_completed(futures):
                results.append(fut.result())
    except Exception as exc:
        print(f"parallel fallback ({exc})", file=sys.stderr)
        for seed in seeds:
            results.append(sa_run(problem, seed, TIME_LIMIT_SEC))

    best_types, best_score = max(results, key=lambda x: x[1])
    print(f"merged best score={best_score}", file=sys.stderr)
    return best_types, best_score


def main() -> None:
    problem = read_problem(sys.stdin)
    best_types, best_score = parallel_sa(problem)
    for t in best_types:
        print(t)
    print(f"output days={len(best_types)} score={best_score}", file=sys.stderr)


if __name__ == "__main__":
    main()
