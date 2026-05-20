# python/ch28/benchmark.py
"""同一 Dijkstra ループの Python / Go ベンチマーク（第28章）."""
from __future__ import annotations

import heapq
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

GRID_N = 50
REPEAT = 400
INF = 10**9


def build_grid(n: int) -> List[List[int]]:
    grid = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if (r + c) % 7 == 0:
                grid[r][c] = 1
    grid[0][0] = 0
    grid[n - 1][n - 1] = 0
    return grid


def dijkstra(grid: List[List[int]], sr: int, sc: int, tr: int, tc: int) -> int:
    n = len(grid)
    dist = [[INF] * n for _ in range(n)]
    dist[sr][sc] = 0
    pq: List[Tuple[int, int, int]] = [(0, sr, sc)]
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while pq:
        d, r, c = heapq.heappop(pq)
        if d != dist[r][c]:
            continue
        if r == tr and c == tc:
            return d
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            if grid[nr][nc] == 1:
                continue
            nd = d + 1 + grid[nr][nc]
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(pq, (nd, nr, nc))
    return INF


def run_benchmark() -> Tuple[float, int]:
    grid = build_grid(GRID_N)
    tr, tc = GRID_N - 1, GRID_N - 1
    checksum = 0
    start = time.perf_counter()
    for _ in range(REPEAT):
        for sr in range(0, GRID_N, 5):
            for sc in range(0, GRID_N, 5):
                if grid[sr][sc] == 1:
                    continue
                checksum ^= dijkstra(grid, sr, sc, tr, tc)
    elapsed = time.perf_counter() - start
    return elapsed, checksum


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_go_timing() -> Tuple[float, int]:
    go_file = repo_root() / "go" / "ch28" / "benchmark.go"
    proc = subprocess.run(
        ["go", "run", str(go_file), "--timing-only"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"go benchmark failed: {proc.returncode}")
    elapsed = 0.0
    checksum = 0
    for line in proc.stderr.splitlines():
        if line.startswith("BENCHMARK_SEC="):
            elapsed = float(line.split("=", 1)[1])
        if line.startswith("BENCHMARK_CHECKSUM="):
            checksum = int(line.split("=", 1)[1])
    return elapsed, checksum


def main() -> None:
    py_sec, py_sum = run_benchmark()
    print(f"python: {py_sec:.6f}s  checksum={py_sum}", file=sys.stderr)

    try:
        go_sec, go_sum = run_go_timing()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"go compare skipped: {exc}", file=sys.stderr)
        return

    print(f"go:     {go_sec:.6f}s  checksum={go_sum}", file=sys.stderr)
    if go_sum != py_sum:
        print("warning: checksum mismatch (implementations differ?)", file=sys.stderr)
    if go_sec > 0:
        speedup = py_sec / go_sec
        print(f"speedup (python/go): {speedup:.2f}x", file=sys.stderr)


if __name__ == "__main__":
    main()
