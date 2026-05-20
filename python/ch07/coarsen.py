# python/ch07/coarsen.py
"""16x16 グリッドを 4x4 ブロックに分割し、貪欲 + 局所 refine."""
from __future__ import annotations

import sys
from typing import List, TextIO, Tuple

N = 16
BLOCK = 4


def read_grid(stream: TextIO) -> List[List[int]]:
    lines = stream.read().splitlines()
    if int(lines[0]) != N:
        raise ValueError(f"expected {N} rows, got header {lines[0]}")
    grid: List[List[int]] = []
    for i in range(1, N + 1):
        row = list(map(int, lines[i].split()))
        if len(row) != N:
            raise ValueError(f"row {i} has {len(row)} cols")
        grid.append(row)
    return grid


def block_avg(grid: List[List[int]], bi: int, bj: int) -> int:
    s = 0
    for i in range(bi * BLOCK, (bi + 1) * BLOCK):
        for j in range(bj * BLOCK, (bj + 1) * BLOCK):
            s += grid[i][j]
    return s // (BLOCK * BLOCK)


def coarse_matrix(grid: List[List[int]]) -> List[List[int]]:
    return [
        [block_avg(grid, bi, bj) for bj in range(BLOCK)]
        for bi in range(BLOCK)
    ]


def greedy_per_block(grid: List[List[int]]) -> List[Tuple[int, int]]:
    picks: List[Tuple[int, int]] = []
    for bi in range(BLOCK):
        for bj in range(BLOCK):
            best_val = -1
            best_pos = (bi * BLOCK, bj * BLOCK)
            for i in range(bi * BLOCK, (bi + 1) * BLOCK):
                for j in range(bj * BLOCK, (bj + 1) * BLOCK):
                    if grid[i][j] > best_val:
                        best_val = grid[i][j]
                        best_pos = (i, j)
            picks.append(best_pos)
    return picks


def pick_sum(grid: List[List[int]], picks: List[Tuple[int, int]]) -> int:
    return sum(grid[i][j] for i, j in picks)


def refine(
    grid: List[List[int]], picks: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    refined = list(picks)
    improved = True
    while improved:
        improved = False
        for idx, (i, j) in enumerate(refined):
            bi, bj = i // BLOCK, j // BLOCK
            best = (grid[i][j], (i, j))
            for di in range(-1, 2):
                for dj in range(-1, 2):
                    ni, nj = i + di, j + dj
                    if not (0 <= ni < N and 0 <= nj < N):
                        continue
                    if ni // BLOCK != bi or nj // BLOCK != bj:
                        continue
                    if grid[ni][nj] > best[0]:
                        best = (grid[ni][nj], (ni, nj))
            if best[1] != (i, j):
                refined[idx] = best[1]
                improved = True
    return refined


def main() -> None:
    grid = read_grid(sys.stdin)
    coarse = coarse_matrix(grid)
    greedy = greedy_per_block(grid)
    refined = refine(grid, greedy)
    print("coarse 4x4 (block averages):")
    for row in coarse:
        print(" ".join(str(v) for v in row))
    print(f"greedy_sum={pick_sum(grid, greedy)}")
    print(f"refined_sum={pick_sum(grid, refined)}")
    print("refined picks (row col):")
    for i, j in refined:
        print(i, j)


if __name__ == "__main__":
    main()
