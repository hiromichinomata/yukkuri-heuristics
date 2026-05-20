# python/ch09/beam_fill.py
"""6x6 盤面をビームサーチで埋める（AHC002 簡略版・第9章）."""
from __future__ import annotations

import heapq
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

DIRS = ((-1, 0, "U"), (1, 0, "D"), (0, -1, "L"), (0, 1, "R"))
BEAM_WIDTH = 80


@dataclass(order=True)
class BeamNode:
    neg_score: int
    depth: int
    r: int = field(compare=False)
    c: int = field(compare=False)
    visited: int = field(compare=False)
    score: int = field(compare=False)
    path: str = field(compare=False)


def read_grid(stream) -> Tuple[int, List[List[int]]]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    grid = []
    for i in range(1, n + 1):
        grid.append(list(map(int, lines[i].split())))
    return n, grid


def cell_id(r: int, c: int, n: int) -> int:
    return r * n + c


def heuristic(grid: List[List[int]], n: int, visited: int, r: int, c: int) -> int:
    """未訪問隣接マスの最大値の和（簡易見積もり）."""
    est = 0
    for dr, dc, _ in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n:
            vid = cell_id(nr, nc, n)
            if (visited >> vid) & 1 == 0:
                est += grid[nr][nc]
    return est


def beam_search(grid: List[List[int]], n: int, beam_width: int) -> Tuple[int, str]:
    start_r, start_c = 0, 0
    start_vid = cell_id(start_r, start_c, n)
    start_score = grid[start_r][start_c]
    start_visited = 1 << start_vid

    beam = [
        BeamNode(
            neg_score=-(start_score + heuristic(grid, n, start_visited, start_r, start_c)),
            depth=1,
            r=start_r,
            c=start_c,
            visited=start_visited,
            score=start_score,
            path="",
        )
    ]

    best_score = start_score
    best_path = ""

    for _ in range(n * n - 1):
        candidates: List[BeamNode] = []
        for node in beam:
            for dr, dc, ch in DIRS:
                nr, nc = node.r + dr, node.c + dc
                if not (0 <= nr < n and 0 <= nc < n):
                    continue
                vid = cell_id(nr, nc, n)
                if (node.visited >> vid) & 1:
                    continue
                new_visited = node.visited | (1 << vid)
                new_score = node.score + grid[nr][nc]
                new_path = node.path + ch
                h = heuristic(grid, n, new_visited, nr, nc)
                candidates.append(
                    BeamNode(
                        neg_score=-(new_score + h),
                        depth=node.depth + 1,
                        r=nr,
                        c=nc,
                        visited=new_visited,
                        score=new_score,
                        path=new_path,
                    )
                )
                if new_score > best_score:
                    best_score = new_score
                    best_path = new_path

        if not candidates:
            break
        beam = heapq.nsmallest(beam_width, candidates)

    return best_score, best_path


def main() -> None:
    n, grid = read_grid(sys.stdin)
    score, path = beam_search(grid, n, BEAM_WIDTH)
    print(path)
    print(f"tiles={len(path)+1} score={score} beam_width={BEAM_WIDTH}", file=sys.stderr)


if __name__ == "__main__":
    main()
