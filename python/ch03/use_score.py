# python/ch03/use_score.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from score_module import read_problem_with_schedule, score_schedule


def main():
    problem, state = read_problem_with_schedule(sys.stdin)
    result = score_schedule(problem, state)
    print("contest_score:", result.contest_score)


if __name__ == "__main__":
    main()
