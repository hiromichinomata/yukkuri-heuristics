# python/ch11/pipeline.py
"""貪欲 → 山登り → 焼きなましの多段パイプライン（第11章）."""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import List, TextIO

TOTAL_SEC = 2.0
CONSTRUCT_RATIO = 0.6

T0 = 5000.0  # SA 段の開始温度
T1 = 10.0  # SA 段の終了温度（第9章と同じ時間ベース冷却）


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
    """各日、その日終了時の満足度が最大になるタイプを選ぶ。

    満足度と各タイプの最終開催日 last を持ち回すので 1 日あたり O(26²)、全体 O(26²·D)。
    （毎回スケジュール全体を計算し直すと O(26²·D²) になり、D=365 では Python で数秒かかる）
    """
    last = [0] * 26
    satisfaction = 0
    schedule: List[int] = []
    for day in range(1, problem.days + 1):
        decay_all = sum(problem.decay[i] * (day - last[i]) for i in range(26))
        best_t, best_sat = 1, None
        for t in range(1, 27):
            # タイプ t を開くと、t の減衰だけ 0 になる
            sat = satisfaction + problem.gain[day - 1][t - 1] - (decay_all - problem.decay[t - 1] * (day - last[t - 1]))
            if best_sat is None or sat > best_sat:
                best_sat = sat
                best_t = t
        schedule.append(best_t)
        satisfaction = best_sat
        last[best_t - 1] = day
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
    """types[day] を new_type に変えたときの (10^6 + 満足度) の変化量。O(D)（第9章 9.4）."""
    old_type = types[day]
    if old_type == new_type:
        return 0
    before = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = new_type
    after = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = old_type
    gain = problem.gain[day][new_type - 1] - problem.gain[day][old_type - 1]
    return gain - (after - before)


def hill_climb(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = state.copy()
    score = 10**6 + _final_satisfaction(problem, current)  # 0 で切らない値で比べる
    steps = 0
    while time.perf_counter() < deadline:
        day = rng.randrange(problem.days)
        old_type = current.types[day]
        for t in range(1, 27):
            if t == old_type:
                continue
            delta = delta_change(problem, current.types, day, t)  # 全再計算せず差分だけ（第9章 9.4）
            if delta > 0:
                current.types[day] = t
                score += delta
                break
        steps += 1
        if steps % 200 == 0:
            print(f"hc step={steps} score={max(score, 0)}", file=sys.stderr)
    assert score == 10**6 + _final_satisfaction(problem, current), "差分と全再計算が一致しない"
    return current


def sa(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = state.copy()
    score = 10**6 + _final_satisfaction(problem, current)  # 0 で切らない値で比べる
    best = current.copy()
    best_score = score
    temperature = T0
    step = 0
    start = time.perf_counter()
    span = max(deadline - start, 1e-9)
    next_log = 0.1

    while True:
        now = time.perf_counter()
        if now >= deadline:
            break
        # SA 段に割り当てられた時間の中で T0 → T1 へ下げる
        progress = (now - start) / span
        temperature = T0 * (T1 / T0) ** progress
        day = rng.randrange(problem.days)
        new_type = rng.randint(1, 26)
        delta = delta_change(problem, current.types, day, new_type)  # 全再計算せず差分だけ（第9章 9.4）
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            current.types[day] = new_type
            score += delta
            if score > best_score:
                best = current.copy()
                best_score = score
        step += 1
        if progress >= next_log:  # SA 段の 10% ごとにログ
            next_log += 0.1
            print(f"sa step={step} score={max(score, 0)} T={temperature:.2f}", file=sys.stderr)

    assert score == 10**6 + _final_satisfaction(problem, current), "差分と全再計算が一致しない"
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
