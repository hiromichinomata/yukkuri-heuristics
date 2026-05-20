# python/ch03/score_module.py
"""Intro HC 形式のスコア計算モジュール（第3章）."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, TextIO, Tuple


# --- 3.3 State ---


@dataclass
class ProblemInput:
    days: int
    decay: List[int]
    gain: List[List[int]]


@dataclass
class ScheduleState:
    types: List[int]  # 1-indexed contest types

    def copy(self) -> ScheduleState:
        return ScheduleState(list(self.types))


@dataclass
class ScoreResult:
    daily: List[int]
    final_satisfaction: int
    contest_score: int


# --- 3.1 read ---


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


def read_problem_with_schedule(stream: TextIO) -> Tuple[ProblemInput, ScheduleState]:
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
    types = [int(lines[idx + i]) for i in range(days)]
    return ProblemInput(days, decay, gain), ScheduleState(types)


# --- 3.4 score ---


def apply_move(state: ScheduleState, day: int, contest_type: int) -> ScheduleState:
    """day: 0-indexed, contest_type: 1-indexed."""
    nxt = state.copy()
    nxt.types[day] = contest_type
    return nxt


def score_schedule(problem: ProblemInput, state: ScheduleState) -> ScoreResult:
    last = [0] * 26
    satisfaction = 0
    daily: List[int] = []

    for day in range(1, problem.days + 1):
        t = state.types[day - 1] - 1
        satisfaction += problem.gain[day - 1][t]
        last[t] = day
        decay = sum(problem.decay[i] * (day - last[i]) for i in range(26))
        satisfaction -= decay
        daily.append(satisfaction)

    final = daily[-1] if daily else 0
    return ScoreResult(
        daily=daily,
        final_satisfaction=final,
        contest_score=max(10**6 + final, 0),
    )


def main() -> None:
    problem, state = read_problem_with_schedule(sys.stdin)
    result = score_schedule(problem, state)
    for v in result.daily:
        print(v)
    print(result.contest_score, file=sys.stderr)


if __name__ == "__main__":
    main()
