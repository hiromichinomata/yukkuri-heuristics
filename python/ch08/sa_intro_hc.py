# python/ch08/sa_intro_hc.py
"""Intro HC スケジュールを焼きなましで改善（第8章）."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, TextIO, Tuple

T0 = 5000.0
ALPHA = 0.995
TIME_LIMIT_SEC = 1.5


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
    gain = []
    for _ in range(days):
        gain.append(list(map(int, lines[idx].split())))
        idx += 1
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
    day = rng.randrange(len(state.types))
    new_type = rng.randint(1, 26)
    nxt = ScheduleState(list(state.types))
    nxt.types[day] = new_type
    return nxt


def sa(
    problem: ProblemInput,
    initial: ScheduleState,
    time_limit_sec: float,
    rng: random.Random,
) -> Tuple[ScheduleState, int]:
    start = time.perf_counter()
    state = initial
    score = score_schedule(problem, state)
    best_state = ScheduleState(list(state.types))
    best_score = score
    temperature = T0
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
                best_state = ScheduleState(list(state.types))

        temperature *= ALPHA
        step += 1
        if step % 500 == 0:
            print(f"sa step={step} score={score} T={temperature:.2f}", file=sys.stderr)

    return best_state, best_score


def main() -> None:
    rng = random.Random(42)
    problem = read_problem(sys.stdin)
    initial = ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    init_score = score_schedule(problem, initial)
    print(f"initial score={init_score}", file=sys.stderr)

    best, best_score = sa(problem, initial, TIME_LIMIT_SEC, rng)
    print(f"best score={best_score}", file=sys.stderr)
    for t in best.types:
        print(t)


if __name__ == "__main__":
    main()
