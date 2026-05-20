# python/ch03/validate.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_module import ScheduleState, read_problem_with_schedule, score_schedule


def validate_schedule(state: ScheduleState, num_types: int = 26) -> bool:
    return all(1 <= t <= num_types for t in state.types)


def score_if_valid(problem, state):
    if not validate_schedule(state):
        raise ValueError("illegal schedule")
    return score_schedule(problem, state)


def main():
    problem, state = read_problem_with_schedule(sys.stdin)
    result = score_if_valid(problem, state)
    print("OK:", result.contest_score)


if __name__ == "__main__":
    main()
