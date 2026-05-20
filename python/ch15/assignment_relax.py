# python/ch15/assignment_relax.py
"""割当問題: 分数緩和 + 丸め、n=4 で全探索と比較."""
from __future__ import annotations

import itertools
import sys
from typing import List, Tuple


def read_cost(stream) -> Tuple[int, List[List[int]]]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    mat = [list(map(int, lines[i + 1].split())) for i in range(n)]
    return n, mat


def fractional_relaxation(cost: List[List[int]]) -> Tuple[List[List[float]], float]:
    n = len(cost)
    entries = [(cost[i][j], i, j) for i in range(n) for j in range(n)]
    entries.sort()
    row_rem = [1.0] * n
    col_rem = [1.0] * n
    x = [[0.0] * n for _ in range(n)]
    total = 0.0
    for c, i, j in entries:
        val = min(row_rem[i], col_rem[j])
        if val <= 0:
            continue
        x[i][j] = val
        row_rem[i] -= val
        col_rem[j] -= val
        total += c * val
    return x, total


def round_assignment(cost: List[List[int]], frac: List[List[float]]) -> Tuple[List[int], int]:
    n = len(cost)
    items = [(frac[i][j], cost[i][j], i, j) for i in range(n) for j in range(n)]
    items.sort(reverse=True)
    assign = [-1] * n
    used_col = [False] * n
    total = 0
    for _, c, i, j in items:
        if assign[i] != -1 or used_col[j]:
            continue
        assign[i] = j
        used_col[j] = True
        total += c
    return assign, total


def brute_optimal(cost: List[List[int]]) -> Tuple[List[int], int]:
    n = len(cost)
    best_perm = None
    best_val = None
    for perm in itertools.permutations(range(n)):
        val = sum(cost[i][perm[i]] for i in range(n))
        if best_val is None or val < best_val:
            best_val = val
            best_perm = list(perm)
    assert best_perm is not None and best_val is not None
    return best_perm, best_val


def main() -> None:
    n, cost = read_cost(sys.stdin)
    frac, frac_cost = fractional_relaxation(cost)
    assign, rounded_cost = round_assignment(cost, frac)
    optimal, opt_cost = brute_optimal(cost)
    gap = rounded_cost - opt_cost
    print("fractional_cost", f"{frac_cost:.2f}")
    print("rounded_assign", assign, "cost", rounded_cost)
    print("optimal_assign", optimal, "cost", opt_cost)
    print(f"n={n} gap={gap} ratio={rounded_cost / max(opt_cost, 1):.3f}")


if __name__ == "__main__":
    main()
