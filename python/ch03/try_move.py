# python/ch03/try_move.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_module import apply_move, read_problem_with_schedule, score_schedule


def main():
    problem, state = read_problem_with_schedule(sys.stdin)
    base = score_schedule(problem, state)
    moved = apply_move(state, day=0, contest_type=2)
    after = score_schedule(problem, moved)
    print("before:", base.contest_score)
    print("after:", after.contest_score)


if __name__ == "__main__":
    main()
