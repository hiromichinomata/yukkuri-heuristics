# python/ch25/assignment_relax.py
"""割当問題: 制約を外す緩和で下界を作り、修復 + 入れ替え山登りで整数解にする（第25章）.

  lower_bound    … 「各列に1人」の制約を外し、各行で最安の列を選んだコスト（真の最適以下＝下界）
  relaxed        … そのときの割当（列が重なるので、そのままでは実行不可能）
  repaired       … 重なりを「後悔（2番目に安いコストとの差）が大きい行」から順に直した整数解
  improved       … repaired から、2行の割当の入れ替えで良くなる限り山登りした解
  greedy         … 比較用: コストの安い (i, j) から順に詰める貪欲
  optimal        … n が小さいので全探索で求めた真の最適

最適値は必ず [lower_bound, improved] の範囲に入る。範囲が狭いほど「もう伸びしろが少ない」と分かる。
"""
from __future__ import annotations

import itertools
import sys
from typing import List, Tuple


def read_cost(stream) -> Tuple[int, List[List[int]]]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    mat = [list(map(int, lines[i + 1].split())) for i in range(n)]
    return n, mat


def assignment_cost(cost: List[List[int]], assign: List[int]) -> int:
    return sum(cost[i][assign[i]] for i in range(len(assign)))


def relaxed_lower_bound(cost: List[List[int]]) -> Tuple[List[int], int]:
    """「各列に1人」を外した緩和。各行で最安の列を選ぶ。どんな実行可能解のコストもこれ以上."""
    n = len(cost)
    choice = [min(range(n), key=lambda j: cost[i][j]) for i in range(n)]
    return choice, assignment_cost(cost, choice)


def repair(cost: List[List[int]]) -> List[int]:
    """後悔の大きい行（最安の列を取れないと損が大きい行）から、空いている最安の列を取らせる."""
    n = len(cost)

    def regret(i: int) -> int:
        row = sorted(cost[i])
        return row[1] - row[0] if n > 1 else 0

    order = sorted(range(n), key=lambda i: -regret(i))  # 同点は行番号の小さい順（sorted は安定）
    assign = [-1] * n
    used = [False] * n
    for i in order:
        j = min((j for j in range(n) if not used[j]), key=lambda j: cost[i][j])
        assign[i] = j
        used[j] = True
    return assign


def swap_improve(cost: List[List[int]], assign: List[int]) -> List[int]:
    """2 行の割当を入れ替えて良くなる限り続ける山登り（第6章の 2-opt と同じ発想）."""
    assign = list(assign)
    n = len(assign)
    improved = True
    while improved:
        improved = False
        for i in range(n):
            for k in range(i + 1, n):
                a, b = assign[i], assign[k]
                delta = (cost[i][b] + cost[k][a]) - (cost[i][a] + cost[k][b])
                if delta < 0:
                    assign[i], assign[k] = b, a
                    improved = True
    return assign


def greedy_by_cost(cost: List[List[int]]) -> List[int]:
    """比較用: コストの安い (i, j) から、行・列が空いていれば詰める."""
    n = len(cost)
    entries = sorted((cost[i][j], i, j) for i in range(n) for j in range(n))
    assign = [-1] * n
    used = [False] * n
    for _, i, j in entries:
        if assign[i] == -1 and not used[j]:
            assign[i] = j
            used[j] = True
    return assign


def brute_optimal(cost: List[List[int]]) -> Tuple[List[int], int]:
    n = len(cost)
    best = min(itertools.permutations(range(n)), key=lambda p: assignment_cost(cost, list(p)))
    return list(best), assignment_cost(cost, list(best))


def main() -> None:
    n, cost = read_cost(sys.stdin)
    relaxed, lb = relaxed_lower_bound(cost)
    repaired = repair(cost)
    improved = swap_improve(cost, repaired)
    greedy = greedy_by_cost(cost)
    optimal, opt = brute_optimal(cost)
    print("lower_bound", lb, "relaxed_assign", relaxed)
    print("repaired_assign", repaired, "cost", assignment_cost(cost, repaired))
    print("improved_assign", improved, "cost", assignment_cost(cost, improved))
    print("greedy_assign", greedy, "cost", assignment_cost(cost, greedy))
    print("optimal_assign", optimal, "cost", opt)
    print(f"n={n} optimal is in [{lb}, {assignment_cost(cost, improved)}]")


if __name__ == "__main__":
    main()
