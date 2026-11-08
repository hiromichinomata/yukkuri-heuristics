# python/ch09/sa_intro_hc.py
"""Intro HC スケジュールを焼きなましで改善（第9章）."""
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


def raw_score(problem: ProblemInput, state: ScheduleState) -> int:
    """10^6 + 最終満足度（0 で切らない値）。全再計算 O(26·D)."""
    last = [0] * 26
    satisfaction = 0
    for day in range(1, problem.days + 1):
        t = state.types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        decay = sum(problem.decay[i] * (day - last[i]) for i in range(26))
        satisfaction -= decay
    return 10**6 + satisfaction


def score_schedule(problem: ProblemInput, state: ScheduleState) -> int:
    """提出スコア max(10^6 + 最終満足度, 0)."""
    return max(raw_score(problem, state), 0)


def type_penalty(problem: ProblemInput, types: List[int], t: int) -> int:
    """タイプ t（1〜26）の減衰ペナルティの合計。O(D).

    t を開催した日を a_1 < … < a_k、a_0 = 0、a_{k+1} = D + 1 とすると、
    間隔 L = a_{j+1} - a_j の区間で c_t * (0 + 1 + … + (L-1)) = c_t * L(L-1)/2 だけ減る。
    """
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
    """types[day] を new_type に変えたときの raw_score の変化量。O(D).

    影響を受けるのは「元のタイプ」と「新しいタイプ」のペナルティだけなので、
    26 タイプ全部を数え直す必要はない。
    """
    old_type = types[day]
    if old_type == new_type:
        return 0
    before = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = new_type
    after = type_penalty(problem, types, old_type) + type_penalty(problem, types, new_type)
    types[day] = old_type  # 元に戻す（採用するかは呼び出し側が決める）
    gain = problem.gain[day][new_type - 1] - problem.gain[day][old_type - 1]
    return gain - (after - before)


def random_move(state: ScheduleState, rng: random.Random) -> Tuple[int, int]:
    """近傍: ある1日のタイプを別の値に変える。(日の添字, 新タイプ) を返す."""
    day = rng.randrange(len(state.types))
    new_type = rng.randint(1, 26)
    return day, new_type


def sa(
    problem: ProblemInput,
    initial: ScheduleState,
    time_limit_sec: float,
    rng: random.Random,
) -> Tuple[ScheduleState, int]:
    start = time.perf_counter()
    state = ScheduleState(list(initial.types))  # 現在解はこのリストを直接書き換える
    score = raw_score(problem, state)
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

        day, new_type = random_move(state, rng)
        delta = delta_change(problem, state.types, day, new_type)  # 全再計算せず差分だけ
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            state.types[day] = new_type
            score += delta
            if score > best_score:
                best_score = score
                best_state = ScheduleState(list(state.types))

        step += 1
        if progress >= next_log:  # 経過 10% ごとにログ
            next_log += LOG_EVERY
            print(f"sa step={step} score={score} T={temperature:.2f}", file=sys.stderr)

    # 差分の積み上げが全再計算と一致するか確認（デバッグ用。ずれたらバグ）
    assert score == raw_score(problem, state), "delta_change と raw_score が一致しない"
    return best_state, max(best_score, 0)


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
