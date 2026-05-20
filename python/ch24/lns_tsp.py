# python/ch24/lns_tsp.py
"""TSP LNS: ランダム区間破壊 + 貪欲最近傍で再構築."""
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


def dist(pts: List[Tuple[float, float]], i: int, j: int) -> float:
    return math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])


def nearest_neighbor_tour(pts: List[Tuple[float, float]], start: int, nodes: List[int]) -> List[int]:
    remaining = set(nodes)
    remaining.discard(start)
    tour = [start]
    cur = start
    while remaining:
        nxt = min(remaining, key=lambda j: dist(pts, cur, j))
        remaining.remove(nxt)
        tour.append(nxt)
        cur = nxt
    return tour


def destroy_segment(tour: List[int], rng: random.Random) -> Tuple[List[int], List[int]]:
    n = len(tour)
    if n <= 3:
        return list(tour), []
    seg_len = rng.randint(1, max(1, n // 3))
    start = rng.randint(0, n - 1)
    removed = []
    kept = list(tour)
    for _ in range(seg_len):
        idx = start % len(kept)
        removed.append(kept.pop(idx))
        start += 1
    return kept, removed


def repair_tour(
    pts: List[Tuple[float, float]],
    partial: List[int],
    removed: List[int],
) -> List[int]:
    if not partial:
        return nearest_neighbor_tour(pts, 0, list(range(len(pts))))
    nodes = partial + removed
    start = partial[0]
    rebuilt = nearest_neighbor_tour(pts, start, nodes)
    return rebuilt


def lns(
    pts: List[Tuple[float, float]],
    rng: random.Random,
    iterations: int = 200,
) -> Tuple[List[int], float, float]:
    n = len(pts)
    tour = list(range(n))
    rng.shuffle(tour)
    initial = tour_length(pts, tour)
    best = list(tour)
    best_len = initial

    for it in range(iterations):
        partial, removed = destroy_segment(tour, rng)
        candidate = repair_tour(pts, partial, removed)
        cand_len = tour_length(pts, candidate)
        if cand_len + 1e-9 < tour_length(pts, tour):
            tour = candidate
        if cand_len + 1e-9 < best_len:
            best = candidate
            best_len = cand_len
        if (it + 1) % 50 == 0:
            print(f"lns it={it+1} current={tour_length(pts, tour):.2f} best={best_len:.2f}", file=sys.stderr)
    return best, initial, best_len


def main() -> None:
    pts = read_points(sys.stdin)
    rng = random.Random(42)
    tour, before, after = lns(pts, rng)
    print("tour:", " ".join(str(i) for i in tour))
    print(f"n={len(pts)} before={before:.2f} after={after:.2f} improved={before-after:.2f}")


if __name__ == "__main__":
    main()
