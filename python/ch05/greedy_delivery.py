# python/ch05/greedy_delivery.py
"""配達問題の最近傍法（貪欲）."""
from __future__ import annotations

import math
import sys
from typing import List, TextIO, Tuple


def read_problem(stream: TextIO) -> Tuple[Tuple[float, float], List[Tuple[float, float]]]:
    lines = stream.read().splitlines()
    dx, dy = map(float, lines[0].split())
    n = int(lines[1])
    orders: List[Tuple[float, float]] = []
    for i in range(2, 2 + n):
        x, y = map(float, lines[i].split())
        orders.append((x, y))
    return (dx, dy), orders


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nearest_neighbor(
    depot: Tuple[float, float], orders: List[Tuple[float, float]]
) -> Tuple[List[int], float]:
    unvisited = set(range(len(orders)))
    route: List[int] = []
    cur = depot
    total = 0.0
    while unvisited:
        nxt = min(unvisited, key=lambda i: dist(cur, orders[i]))
        total += dist(cur, orders[nxt])
        route.append(nxt)
        cur = orders[nxt]
        unvisited.remove(nxt)
    total += dist(cur, depot)
    return route, total


def main() -> None:
    depot, orders = read_problem(sys.stdin)
    route, total = nearest_neighbor(depot, orders)
    print("route:", " ".join(str(i) for i in route))
    print(f"orders={len(orders)} distance={total:.2f}")


if __name__ == "__main__":
    main()
