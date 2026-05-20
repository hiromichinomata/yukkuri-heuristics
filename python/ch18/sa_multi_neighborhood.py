# python/ch18/sa_multi_neighborhood.py
"""複数近傍・適応冷却・再ヒート付き SA（Intro HC・第18章）."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, TextIO, Tuple

T0 = 8000.0
ALPHA_FAST = 0.992
ALPHA_SLOW = 0.998
REHEAT_FACTOR = 0.6
STAGNANT_LIMIT = 800
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
    gain = [list(map(int, lines[idx].split())) for _ in range(days)]
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


NeighborhoodFn = Callable[[ScheduleState, random.Random], ScheduleState]


def neighbor_change_day(state: ScheduleState, rng: random.Random) -> ScheduleState:
    nxt = ScheduleState(list(state.types))
    day = rng.randrange(len(nxt.types))
    nxt.types[day] = rng.randint(1, 26)
    return nxt


def neighbor_swap_days(state: ScheduleState, rng: random.Random) -> ScheduleState:
    nxt = ScheduleState(list(state.types))
    a, b = rng.sample(range(len(nxt.types)), 2)
    nxt.types[a], nxt.types[b] = nxt.types[b], nxt.types[a]
    return nxt


def sa_multi(
    problem: ProblemInput,
    initial: ScheduleState,
    time_limit_sec: float,
    rng: random.Random,
) -> Tuple[ScheduleState, int]:
    neighborhoods: List[Tuple[str, NeighborhoodFn]] = [
        ("change_day", neighbor_change_day),
        ("swap_days", neighbor_swap_days),
    ]
    weights = [1.0, 1.0]
    wins = [0, 0]

    start = time.perf_counter()
    state = initial
    score = score_schedule(problem, state)
    best_state = ScheduleState(list(state.types))
    best_score = score
    temperature = T0
    alpha = ALPHA_FAST
    step = 0
    since_improve = 0

    while time.perf_counter() - start < time_limit_sec:
        idx = rng.choices(range(len(neighborhoods)), weights=weights, k=1)[0]
        name, neigh_fn = neighborhoods[idx]
        nxt = neigh_fn(state, rng)
        new_score = score_schedule(problem, nxt)
        delta = new_score - score
        accepted = delta >= 0 or rng.random() < math.exp(delta / temperature)
        if accepted:
            state = nxt
            score = new_score
            wins[idx] += 1
            if score > best_score:
                best_score = score
                best_state = ScheduleState(list(state.types))
                since_improve = 0
            else:
                since_improve += 1
        else:
            since_improve += 1

        if since_improve > 200:
            alpha = ALPHA_SLOW
        if since_improve >= STAGNANT_LIMIT:
            temperature = max(temperature, T0 * REHEAT_FACTOR)
            since_improve = 0
            alpha = ALPHA_FAST
            print(f"reheat T={temperature:.1f}", file=sys.stderr)

        temperature *= alpha
        step += 1
        if step % 500 == 0:
            print(
                f"sa step={step} score={score} best={best_score} T={temperature:.1f} "
                f"nh={name} wins={wins}",
                file=sys.stderr,
            )
            total = sum(wins) or 1
            weights = [max(0.2, w / total * 2) for w in wins]

    return best_state, best_score


def main() -> None:
    rng = random.Random(42)
    problem = read_problem(sys.stdin)
    initial = ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    print(f"initial score={score_schedule(problem, initial)}", file=sys.stderr)

    best, best_score = sa_multi(problem, initial, TIME_LIMIT_SEC, rng)
    print(f"best score={best_score}", file=sys.stderr)
    for t in best.types:
        print(t)


if __name__ == "__main__":
    main()
