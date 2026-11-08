# python/ch16/sa_multi_neighborhood.py
"""複数近傍・適応冷却・再ヒート付き SA（Intro HC・第16章）.

土台は第9章と同じ「時間ベースの指数冷却 + 差分更新」。その上に
近傍の重み付き選択、温度の倍率 boost による適応冷却と再ヒートを載せる。
"""
from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import Callable, List, TextIO, Tuple

T0 = 5000.0  # 開始温度（第9章と同じ時間ベース冷却の土台）
T1 = 10.0  # 終了温度
# 適応的冷却: 温度 = 時間ベースの基準温度 × boost。boost は 1 に向かって減衰する
BOOST_DECAY_FAST = 0.999  # 改善が続いているとき（速く 1 に戻す = 速く冷やす）
BOOST_DECAY_SLOW = 0.9999  # 停滞気味のとき（ゆっくり戻す = 熱いまま粘る）
SLOW_AFTER = 2000  # best 更新がこのステップ数ないと「停滞気味」
REHEAT_BOOST = 4.0  # 再ヒート時の倍率
STAGNANT_LIMIT = 20000  # best 更新がこのステップ数ないと再ヒート
WEIGHT_UPDATE_EVERY = 1000
TIME_LIMIT_SEC = 1.5
LOG_EVERY = 0.1


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
    days = int(lines[0])
    decay = list(map(int, lines[1].split()))
    gain = [list(map(int, lines[2 + i].split())) for i in range(days)]
    return ProblemInput(days=days, decay=decay, gain=gain)


def raw_score(problem: ProblemInput, state: ScheduleState) -> int:
    """10^6 + 最終満足度（0 で切らない値）。全再計算 O(26·D)."""
    last = [0] * 26
    satisfaction = 0
    for day in range(1, problem.days + 1):
        t = state.types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        satisfaction -= sum(problem.decay[i] * (day - last[i]) for i in range(26))
    return 10**6 + satisfaction


def score_schedule(problem: ProblemInput, state: ScheduleState) -> int:
    return max(raw_score(problem, state), 0)


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


# --- 近傍: 「操作」を返し、Δ の計算と適用は別関数で行う ---
Move = Tuple[str, int, int]  # ("change", 日, 新タイプ) / ("swap", 日a, 日b)


def neighbor_change_day(state: ScheduleState, rng: random.Random) -> Move:
    return ("change", rng.randrange(len(state.types)), rng.randint(1, 26))


def neighbor_swap_days(state: ScheduleState, rng: random.Random) -> Move:
    if len(state.types) < 2:  # 1 日しかないと入れ替えられないので、1 日の変更で代える
        return neighbor_change_day(state, rng)
    a, b = rng.sample(range(len(state.types)), 2)
    return ("swap", a, b)


def move_delta(problem: ProblemInput, types: List[int], move: Move) -> int:
    kind, x, y = move
    if kind == "change":
        return delta_change(problem, types, x, y)
    # swap は「a を b のタイプに変える」→「b を a のタイプに変える」の 2 回の change
    ta, tb = types[x], types[y]
    if ta == tb:
        return 0
    d1 = delta_change(problem, types, x, tb)
    types[x] = tb
    d2 = delta_change(problem, types, y, ta)
    types[x] = ta
    return d1 + d2


def apply_move(types: List[int], move: Move) -> None:
    kind, x, y = move
    if kind == "change":
        types[x] = y
    else:
        types[x], types[y] = types[y], types[x]


NeighborhoodFn = Callable[[ScheduleState, random.Random], Move]


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
    state = ScheduleState(list(initial.types))
    score = raw_score(problem, state)
    best_state = ScheduleState(list(state.types))
    best_score = score
    boost = 1.0
    step = 0
    since_improve = 0
    reheats = 0
    next_log = LOG_EVERY

    while True:
        elapsed = time.perf_counter() - start
        if elapsed >= time_limit_sec:
            break
        progress = elapsed / time_limit_sec
        temperature = T0 * (T1 / T0) ** progress * boost

        idx = rng.choices(range(len(neighborhoods)), weights=weights, k=1)[0]
        move = neighborhoods[idx][1](state, rng)
        delta = move_delta(problem, state.types, move)
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            apply_move(state.types, move)
            score += delta
            if delta > 0:  # 改善した操作だけ「勝ち」に数える（Δ=0 の入れ替えで水増ししない）
                wins[idx] += 1
        if score > best_score:
            best_score = score
            best_state = ScheduleState(list(state.types))
            since_improve = 0
        else:
            since_improve += 1

        # 適応的冷却: 停滞気味なら boost をゆっくり 1 に戻す（熱いまま粘る）
        decay = BOOST_DECAY_SLOW if since_improve > SLOW_AFTER else BOOST_DECAY_FAST
        boost = max(1.0, boost * decay)
        # 再ヒート: 長く停滞したら温度を一時的に上げて探索をやり直す
        if since_improve >= STAGNANT_LIMIT:
            boost = REHEAT_BOOST
            since_improve = 0
            reheats += 1

        step += 1
        if step % WEIGHT_UPDATE_EVERY == 0:
            total = sum(wins) or 1
            weights = [max(0.2, w / total * 2) for w in wins]
        if progress >= next_log:  # 経過 10% ごとにログ
            next_log += LOG_EVERY
            print(
                f"sa step={step} score={score} best={best_score} T={temperature:.1f} "
                f"boost={boost:.2f} reheats={reheats} wins={wins}",
                file=sys.stderr,
            )

    assert score == raw_score(problem, state), "move_delta と raw_score が一致しない"
    return best_state, max(best_score, 0)


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
