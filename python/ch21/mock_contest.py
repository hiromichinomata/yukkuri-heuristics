# python/ch21/mock_contest.py
"""模擬 AHC: 読解 → 実装 → 改善 → 提出の 4 フェーズ（タイマー・提出ログ）."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, TextIO


@dataclass
class ProblemInput:
    days: int
    decay: List[int]
    gain: List[List[int]]


@dataclass
class ScheduleState:
    types: List[int]


@dataclass
class SubmissionLog:
    phase: str
    elapsed_sec: float
    score: int
    note: str


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


def brief_sa(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = ScheduleState(list(state.types))
    score = 10**6 + _final_satisfaction(problem, current)  # 0 で切らない値で比べる
    best = ScheduleState(list(current.types))
    best_score = score
    t0, t1 = 5000.0, 10.0
    start = time.perf_counter()
    span = max(deadline - start, 1e-9)

    while True:
        now = time.perf_counter()
        if now >= deadline:
            break
        temperature = t0 * (t1 / t0) ** ((now - start) / span)  # 第9章と同じ時間ベース冷却
        day = rng.randrange(problem.days)
        new_type = rng.randint(1, 26)
        delta = delta_change(problem, current.types, day, new_type)  # 差分だけ計算（第9章 9.4）
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            current.types[day] = new_type
            score += delta
            if score > best_score:
                best = ScheduleState(list(current.types))
                best_score = score
    assert score == 10**6 + _final_satisfaction(problem, current), "差分と全再計算が一致しない"
    return best


class MockContest:
    def __init__(
        self,
        problem: ProblemInput,
        phase_min: List[float],
        fast: bool,
        log_json: bool,
    ) -> None:
        self.problem = problem
        self.phase_min = phase_min
        self.fast = fast
        self.log_json = log_json
        self.start = time.perf_counter()
        self.logs: List[SubmissionLog] = []
        self.rng = random.Random(42)
        self.state = ScheduleState([1] * problem.days)
        self.best_score = score_schedule(problem, self.state)

    def elapsed(self) -> float:
        return time.perf_counter() - self.start

    def wait_phase(self, name: str, minutes: float) -> None:
        sec = minutes * 60.0 if not self.fast else minutes
        end = self.elapsed() + sec
        self._emit(name, "start", self.best_score, f"duration={sec:.1f}s")
        while self.elapsed() < end:
            time.sleep(min(0.05, end - self.elapsed()))
        self._emit(name, "end", self.best_score, "phase complete")

    def _emit(self, phase: str, event: str, score: int, note: str) -> None:
        entry = SubmissionLog(
            phase=f"{phase}:{event}",
            elapsed_sec=self.elapsed(),
            score=score,
            note=note,
        )
        self.logs.append(entry)
        line = f"[contest] phase={phase} event={event} t={entry.elapsed_sec:.2f}s score={score} {note}"
        print(line, file=sys.stderr)
        if self.log_json:
            print(json.dumps(asdict(entry), ensure_ascii=False), file=sys.stderr)

    def run(self) -> ScheduleState:
        self.wait_phase("read", self.phase_min[0])
        self.wait_phase("implement", self.phase_min[1])
        self._emit("implement", "work", self.best_score, "greedy build")
        self.state = greedy_schedule(self.problem)
        self.best_score = score_schedule(self.problem, self.state)
        self._emit("implement", "submit", self.best_score, "initial solution")

        # improve フェーズの時間はまるごと SA に使う（待ってから SA、ではない）
        improve_sec = self.phase_min[2] * 60.0 if not self.fast else self.phase_min[2]
        self._emit("improve", "start", self.best_score, f"duration={improve_sec:.1f}s")
        self._emit("improve", "work", self.best_score, "brief SA")
        # brief_sa は time.perf_counter() と比べるので、締め切りも同じ時計で渡す
        improve_end = time.perf_counter() + improve_sec
        self.state = brief_sa(self.problem, self.state, improve_end, self.rng)
        self.best_score = score_schedule(self.problem, self.state)
        self._emit("improve", "submit", self.best_score, "improved solution")
        self._emit("improve", "end", self.best_score, "phase complete")

        self.wait_phase("submit", self.phase_min[3])
        self._emit("submit", "final", self.best_score, "stdout schedule")
        return self.state


def default_input_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    for rel in ("data/ch23/sample.txt", "data/ch09/sample.txt"):
        p = root / rel
        if p.exists():
            return p
    return root / "data/ch23/sample.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description="模擬 AHC 4 フェーズ")
    parser.add_argument(
        "input",
        nargs="?",
        help="Intro HC 形式の入力（省略時は data/ch23/sample.txt）",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="短縮フェーズ（秒単位: 0.3,0.5,0.8,0.2）",
    )
    parser.add_argument("--json-log", action="store_true", help="提出ログを JSON 行でも出力")
    args = parser.parse_args()

    fast = args.fast or __import__("os").environ.get("CONTEST_FAST") == "1"
    if args.input == "-":
        problem = read_problem(sys.stdin)
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            problem = read_problem(f)
    else:
        path = default_input_path()
        with path.open(encoding="utf-8") as f:
            problem = read_problem(f)
        print(f"input={path}", file=sys.stderr)

    phase_min = [0.3, 0.5, 0.8, 0.2] if fast else [30.0, 60.0, 90.0, 30.0]
    contest = MockContest(problem, phase_min, fast=fast, log_json=args.json_log)
    final = contest.run()
    for t in final.types:
        print(t)
    print(
        f"final_score={contest.best_score} elapsed={contest.elapsed():.2f}s submissions={len(contest.logs)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
