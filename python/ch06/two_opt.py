# python/ch06/two_opt.py
"""TSP 玩具: ランダム初期巡回 + 2-opt."""
from __future__ import annotations

import math
import random
import sys
from typing import List, TextIO, Tuple


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


def two_opt(pts: List[Tuple[float, float]], tour: List[int]) -> List[int]:
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(n):
            for k in range(i + 2, n if i > 0 else n - 1):
                a, b = tour[i], tour[(i + 1) % n]
                c, d = tour[k], tour[(k + 1) % n]
                before = (
                    math.hypot(pts[a][0] - pts[b][0], pts[a][1] - pts[b][1])
                    + math.hypot(pts[c][0] - pts[d][0], pts[c][1] - pts[d][1])
                )
                after = (
                    math.hypot(pts[a][0] - pts[c][0], pts[a][1] - pts[c][1])
                    + math.hypot(pts[b][0] - pts[d][0], pts[b][1] - pts[d][1])
                )
                if after + 1e-9 < before:
                    tour[i + 1 : k + 1] = reversed(tour[i + 1 : k + 1])
                    improved = True
    return tour


def main() -> None:
    pts = read_points(sys.stdin)
    rng = random.Random(42)
    tour = list(range(len(pts)))
    rng.shuffle(tour)
    before = tour_length(pts, tour)
    tour = two_opt(pts, tour)
    after = tour_length(pts, tour)
    print("tour:", " ".join(str(i) for i in tour))
    print(f"n={len(pts)} before={before:.2f} after={after:.2f}")


if __name__ == "__main__":
    main()
