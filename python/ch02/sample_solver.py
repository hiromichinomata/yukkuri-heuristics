# python/ch02/sample_solver.py
"""Intro HC 問題A 形式 — 素朴な解法（毎日タイプ1を開催）."""
import sys


def read_problem():
    lines = sys.stdin.read().splitlines()
    idx = 0
    d = int(lines[idx])
    idx += 1
    idx += 1  # c
    for _ in range(d):
        idx += 1  # s rows
    return d


def main() -> None:
    d = read_problem()
    for _ in range(d):
        print(1)


if __name__ == "__main__":
    main()
