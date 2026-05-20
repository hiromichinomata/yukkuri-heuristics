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


def brief_sa(
    problem: ProblemInput,
    state: ScheduleState,
    deadline: float,
    rng: random.Random,
) -> ScheduleState:
    current = ScheduleState(list(state.types))
    score = score_schedule(problem, current)
    best = ScheduleState(list(current.types))
    best_score = score
    temperature = 5000.0
    alpha = 0.995

    while time.perf_counter() < deadline:
        day = rng.randrange(problem.days)
        trial = ScheduleState(list(current.types))
        trial.types[day] = rng.randint(1, 26)
        trial_score = score_schedule(problem, trial)
        delta = trial_score - score
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            current = trial
            score = trial_score
            if score > best_score:
                best = ScheduleState(list(current.types))
                best_score = score
        temperature *= alpha
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

        self.wait_phase("improve", self.phase_min[2])
        improve_end = self.elapsed() + (
            self.phase_min[2] * 60.0 if not self.fast else self.phase_min[2]
        )
        self._emit("improve", "work", self.best_score, "brief SA")
        self.state = brief_sa(self.problem, self.state, improve_end, self.rng)
        self.best_score = score_schedule(self.problem, self.state)
        self._emit("improve", "submit", self.best_score, "improved solution")

        self.wait_phase("submit", self.phase_min[3])
        self._emit("submit", "final", self.best_score, "stdout schedule")
        return self.state


def default_input_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    for rel in ("data/ch23/sample.txt", "data/ch08/sample.txt"):
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
