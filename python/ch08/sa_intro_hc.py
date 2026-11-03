# python/ch08/sa_intro_hc.py
"""Intro HC スケジュールを焼きなましで改善（第8章）."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, TextIO, Tuple

T0 = 5000.0  # 開始温度
T1 = 10.0  # 終了温度
TIME_LIMIT_SEC = 1.5
LOG_EVERY = 0.1  # 制限時間の何割ごとに stderr へログを出すか


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
    next_log = LOG_EVERY

    while True:
        elapsed = time.perf_counter() - start
        if elapsed >= time_limit_sec:
            break
        # 時間ベースの指数冷却: T0 → T1 を制限時間いっぱいで下げる
        progress = elapsed / time_limit_sec
        temperature = T0 * (T1 / T0) ** progress

        nxt = random_neighbor(state, rng)
        new_score = score_schedule(problem, nxt)
        delta = new_score - score
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            state = nxt
            score = new_score
            if score > best_score:
                best_score = score
                best_state = ScheduleState(list(state.types))

        step += 1
        if progress >= next_log:  # 経過 10% ごとにログ
            next_log += LOG_EVERY
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
