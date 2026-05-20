# python/ch10/pipeline.py
"""貪欲 → 山登り → 焼きなましの多段パイプライン（第10章）."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import List, TextIO

TOTAL_SEC = 2.0
CONSTRUCT_RATIO = 0.6

T0 = 5000.0
ALPHA = 0.995


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


def greedy_schedule(problem: ProblemInput) -> ScheduleState:
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


def hill_climb(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = state.copy()
    score = score_schedule(problem, current)
    steps = 0
    while time.perf_counter() < deadline:
        day = rng.randrange(problem.days)
        old_type = current.types[day]
        improved = False
        for t in range(1, 27):
            if t == old_type:
                continue
            trial = current.copy()
            trial.types[day] = t
            trial_score = score_schedule(problem, trial)
            if trial_score > score:
                current = trial
                score = trial_score
                improved = True
                break
        steps += 1
        if steps % 200 == 0:
            print(f"hc step={steps} score={score}", file=sys.stderr)
        if not improved and steps % 50 == 0:
            continue
    return current


def sa(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = state.copy()
    score = score_schedule(problem, current)
    best = current.copy()
    best_score = score
    temperature = T0
    step = 0

    while time.perf_counter() < deadline:
        day = rng.randrange(problem.days)
        trial = current.copy()
        trial.types[day] = rng.randint(1, 26)
        trial_score = score_schedule(problem, trial)
        delta = trial_score - score
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            current = trial
            score = trial_score
            if score > best_score:
                best = current.copy()
                best_score = score
        temperature *= ALPHA
        step += 1
        if step % 500 == 0:
            print(f"sa step={step} score={score} T={temperature:.2f}", file=sys.stderr)

    return best


def main() -> None:
    rng = random.Random(42)
    problem = read_problem(sys.stdin)
    t0 = time.perf_counter()
    end = t0 + TOTAL_SEC
    construct_end = t0 + TOTAL_SEC * CONSTRUCT_RATIO

    print("phase=greedy start", file=sys.stderr)
    state = greedy_schedule(problem)
    print(f"phase=greedy end score={score_schedule(problem, state)}", file=sys.stderr)

    print("phase=hill_climb start", file=sys.stderr)
    state = hill_climb(problem, state, construct_end, rng)
    print(f"phase=hill_climb end score={score_schedule(problem, state)}", file=sys.stderr)

    print("phase=sa start", file=sys.stderr)
    state = sa(problem, state, end, rng)
    final = score_schedule(problem, state)
    print(f"phase=sa end score={final}", file=sys.stderr)
    print(f"elapsed={time.perf_counter()-t0:.3f}s", file=sys.stderr)

    for t in state.types:
        print(t)


if __name__ == "__main__":
    main()
