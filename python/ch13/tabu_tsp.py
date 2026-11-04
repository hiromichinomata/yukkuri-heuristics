# python/ch13/tabu_tsp.py
"""TSP タブーサーチ（ch06 データ形式）."""
from __future__ import annotations

import math
import random
import sys
from typing import Dict, List, TextIO, Tuple


def read_points(stream: TextIO) -> List[Tuple[float, float]]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    pts: List[Tuple[float, float]] = []
    for i in range(1, n + 1):
        x, y = map(float, lines[i].split())
        pts.append((x, y))
    return pts


def tour_length(pts: List[Tuple[float, float]], tour: List[int]) -> float:
    total = 0.0
    for i in range(len(tour)):
        a = pts[tour[i]]
        b = pts[tour[(i + 1) % len(tour)]]
        total += math.hypot(a[0] - b[0], a[1] - b[1])
    return total


def edge_dist(pts: List[Tuple[float, float]], a: int, b: int) -> float:
    return math.hypot(pts[a][0] - pts[b][0], pts[a][1] - pts[b][1])


def apply_reverse(tour: List[int], i: int, k: int) -> None:
    tour[i + 1 : k + 1] = reversed(tour[i + 1 : k + 1])


def edge_key(u: int, v: int) -> Tuple[int, int]:
    return (u, v) if u < v else (v, u)


def tabu_search(
    pts: List[Tuple[float, float]],
    tour: List[int],
    tabu_tenure: int = 12,
    max_iter: int = 800,
) -> Tuple[List[int], float]:
    """2-opt 近傍のタブーサーチ.

    毎回「タブーでない手の中で最良の手」を、**悪化する手でも** 採用する（局所最適から抜けるため）。
    タブー = 最近 2-opt で外した辺を tabu_tenure 反復のあいだ付け直さないこと。
    ただしタブーの手でも、過去最良を更新するなら採用する（aspiration）。
    """
    n = len(tour)
    best = tour[:]
    best_len = tour_length(pts, best)
    cur = tour[:]
    cur_len = best_len
    tabu_until: Dict[Tuple[int, int], int] = {}  # 辺 → この反復まで付け直し禁止

    for it in range(max_iter):
        best_move: Tuple[float, int, int] | None = None
        for i in range(n):
            limit = n if i > 0 else n - 1
            for k in range(i + 2, limit):
                a, b = cur[i], cur[(i + 1) % n]
                c, d = cur[k], cur[(k + 1) % n]
                before = edge_dist(pts, a, b) + edge_dist(pts, c, d)
                after = edge_dist(pts, a, c) + edge_dist(pts, b, d)
                new_len = cur_len - before + after  # 差分で新しい長さ（悪化もありうる）
                # 付け足す辺 (a,c), (b,d) のどちらかがタブーなら、この手はタブー
                is_tabu = tabu_until.get(edge_key(a, c), -1) >= it or tabu_until.get(edge_key(b, d), -1) >= it
                if is_tabu and new_len >= best_len - 1e-9:
                    continue  # タブーかつ最良更新にならない → スキップ（aspiration 不成立）
                if best_move is None or new_len < best_move[0]:
                    best_move = (new_len, i, k)
        if best_move is None:
            break  # 全部の手がタブー
        new_len, i, k = best_move
        a, b = cur[i], cur[(i + 1) % n]
        c, d = cur[k], cur[(k + 1) % n]
        apply_reverse(cur, i, k)
        cur_len = new_len
        # 外した辺 (a,b), (c,d) をしばらく付け直さない
        tabu_until[edge_key(a, b)] = it + tabu_tenure
        tabu_until[edge_key(c, d)] = it + tabu_tenure
        if cur_len < best_len - 1e-9:
            best_len = cur_len
            best = cur[:]
    return best, tour_length(pts, best)


def main() -> None:
    pts = read_points(sys.stdin)
    rng = random.Random(42)
    tour = list(range(len(pts)))
    rng.shuffle(tour)
    before = tour_length(pts, tour)
    tour, after = tabu_search(pts, tour)
    print("tour:", " ".join(str(i) for i in tour))
    print(f"n={len(pts)} before={before:.2f} after={after:.2f} tabu_tenure=12")


if __name__ == "__main__":
    main()
