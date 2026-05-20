# python/ch13/fenwick.py
"""Fenwick Tree と区間和の全走査ベンチマーク."""
from __future__ import annotations

import time
from typing import List


class Fenwick:
    def __init__(self, n: int) -> None:
        self.n = n
        self.bit = [0] * (n + 1)

    def add(self, i: int, delta: int) -> None:
        i += 1
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i

    def prefix(self, i: int) -> int:
        i += 1
        s = 0
        while i > 0:
            s += self.bit[i]
            i -= i & -i
        return s

    def range_sum(self, l: int, r: int) -> int:
        if l == 0:
            return self.prefix(r)
        return self.prefix(r) - self.prefix(l - 1)


def naive_range_sum(arr: List[int], l: int, r: int) -> int:
    return sum(arr[l : r + 1])


def benchmark(n: int = 8000, queries: int = 40000) -> None:
    arr = [1] * n
    ops = [(i % n, (i * 7) % n, (i * 13) % n) for i in range(queries)]

    t0 = time.perf_counter()
    total_naive = 0
    for l, r, delta in ops:
        arr[l] += delta % 3
        lo, hi = min(l, r), max(l, r)
        total_naive += naive_range_sum(arr, lo, hi)
    naive_ms = (time.perf_counter() - t0) * 1000

    fw = Fenwick(n)
    for i, v in enumerate(arr):
        fw.add(i, v)
    t0 = time.perf_counter()
    total_fw = 0
    for l, r, delta in ops:
        fw.add(l, delta % 3)
        lo, hi = min(l, r), max(l, r)
        total_fw += fw.range_sum(lo, hi)
    fw_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n} queries={queries}")
    print(f"naive_range_sum_ms={naive_ms:.2f} checksum={total_naive}")
    print(f"fenwick_ms={fw_ms:.2f} checksum={total_fw}")
    print(f"speedup={naive_ms / max(fw_ms, 1e-9):.1f}x")


def main() -> None:
    benchmark()


if __name__ == "__main__":
    main()
