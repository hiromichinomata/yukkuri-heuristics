# python/ch23/hypothesis_compare.py
"""Intro HC 5 日入力で解法仮説 3 案のスコア比較."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import List, TextIO


@dataclass
class ProblemInput:
    days: int
    decay: List[int]
    gain: List[List[int]]


@dataclass
class ScheduleState:
    types: List[int]

    def copy(self) -> ScheduleState:
        return ScheduleState(list(self.types))


def read_problem(stream: TextIO) -> ProblemInput:
    lines = stream.read().splitlines()
    idx = 0
    days = int(lines[idx])
    idx += 1
    decay = list(map(int, lines[idx].split()))
    idx += 1
    gain = [list(map(int, lines[idx + i].split())) for i in range(days)]
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


def _final_satisfaction(problem: ProblemInput, state: ScheduleState) -> int:
    last = [0] * 26
    satisfaction = 0
    for day in range(1, len(state.types) + 1):
        t = state.types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        decay = sum(problem.decay[i] * (day - last[i]) for i in range(26))
        satisfaction -= decay
    return satisfaction


def strategy_greedy(problem: ProblemInput) -> ScheduleState:
    schedule: List[int] = []
    for day in range(1, problem.days + 1):
        best_t, best_sat = 1, None
        for t in range(1, 27):
            trial = ScheduleState(schedule + [t])
            sat = _final_satisfaction(problem, trial)
            if best_sat is None or sat > best_sat:
                best_sat = sat
                best_t = t
        schedule.append(best_t)
    return ScheduleState(schedule)


def strategy_random_sa(
    problem: ProblemInput,
    rng: random.Random,
    steps: int = 800,
) -> ScheduleState:
    state = ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    score = score_schedule(problem, state)
    best = state.copy()
    best_score = score
    temperature = 5000.0
    alpha = 0.995
    for _ in range(steps):
        day = rng.randrange(problem.days)
        trial = state.copy()
        trial.types[day] = rng.randint(1, 26)
        trial_score = score_schedule(problem, trial)
        delta = trial_score - score
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            state = trial
            score = trial_score
            if score > best_score:
                best = state.copy()
                best_score = score
        temperature *= alpha
    return best


def strategy_pipeline_lite(
    problem: ProblemInput,
    rng: random.Random,
) -> ScheduleState:
    state = strategy_greedy(problem)
    score = score_schedule(problem, state)
    for _ in range(400):
        day = rng.randrange(problem.days)
        old = state.types[day]
        for t in range(1, 27):
            if t == old:
                continue
            trial = state.copy()
            trial.types[day] = t
            trial_score = score_schedule(problem, trial)
            if trial_score > score:
                state = trial
                score = trial_score
                break
    return state


def main() -> None:
    rng = random.Random(42)
    problem = read_problem(sys.stdin)
    t0 = time.perf_counter()

    results = []
    for name, fn in (
        ("greedy", lambda: strategy_greedy(problem)),
        ("random_sa", lambda: strategy_random_sa(problem, rng)),
        ("pipeline_lite", lambda: strategy_pipeline_lite(problem, rng)),
    ):
        start = time.perf_counter()
        state = fn()
        elapsed = time.perf_counter() - start
        score = score_schedule(problem, state)
        results.append((name, score, elapsed, state))
        print(f"strategy={name} score={score} elapsed={elapsed:.3f}s", file=sys.stderr)

    best = max(results, key=lambda x: x[1])
    print(f"best={best[0]} score={best[1]} total_elapsed={time.perf_counter()-t0:.3f}s", file=sys.stderr)
    print(f"# winner schedule ({best[0]})")
    for t in best[3].types:
        print(t)


if __name__ == "__main__":
    main()
