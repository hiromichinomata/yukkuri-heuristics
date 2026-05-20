# python/ch13/union_find.py
"""Union-Find と素朴 union のベンチマーク."""
from __future__ import annotations

import time
from typing import List


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unite(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def naive_components(n: int, edges: List[tuple[int, int]]) -> int:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[rv] = ru
    roots = {find(i) for i in range(n)}
    return len(roots)


def benchmark(n: int = 5000, m: int = 20000) -> None:
    edges = [(i % n, (i * 17 + 3) % n) for i in range(m)]

    t0 = time.perf_counter()
    for _ in range(50):
        naive_components(n, edges)
    naive_ms = (time.perf_counter() - t0) * 1000 / 50

    t0 = time.perf_counter()
    for _ in range(50):
        uf = UnionFind(n)
        for u, v in edges:
            uf.unite(u, v)
        _ = uf.find(0)
    uf_ms = (time.perf_counter() - t0) * 1000 / 50

    print(f"n={n} unions={m}")
    print(f"naive_rebuild_ms={naive_ms:.2f}")
    print(f"union_find_ms={uf_ms:.2f}")
    print(f"speedup={naive_ms / max(uf_ms, 1e-9):.1f}x")


def main() -> None:
    benchmark()


if __name__ == "__main__":
    main()
