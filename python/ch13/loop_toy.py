# python/ch13/loop_toy.py
"""AHC010 簡略: ループ用辺を貪欲配置し UF で連結性を維持."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List, Set, Tuple

from union_find import UnionFind


def read_grid(stream) -> Tuple[int, int, List[str]]:
    lines = stream.read().splitlines()
    h, w = map(int, lines[0].split())
    grid = [lines[i + 1] for i in range(h)]
    return h, w, grid


def cell_index(r: int, c: int, w: int) -> int:
    return r * w + c


def neighbors(r: int, c: int, h: int, w: int) -> List[Tuple[int, int]]:
    out = []
    if r > 0:
        out.append((r - 1, c))
    if r + 1 < h:
        out.append((r + 1, c))
    if c > 0:
        out.append((r, c - 1))
    if c + 1 < w:
        out.append((r, c + 1))
    return out


def full_recompute_components(h: int, w: int, edges: Set[Tuple[int, int]]) -> int:
    n = h * w
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[rv] = ru
    return len({find(i) for i in range(n)})


def greedy_loop_edges(h: int, w: int, grid: List[str], use_uf: bool) -> Tuple[int, Set[Tuple[int, int]]]:
    edges: Set[Tuple[int, int]] = set()
    uf = UnionFind(h * w) if use_uf else None
    placed = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == "#":
                continue
            here = cell_index(r, c, w)
            for nr, nc in neighbors(r, c, h, w):
                if grid[nr][nc] == "#":
                    continue
                if (nr, nc) < (r, c):
                    continue
                there = cell_index(nr, nc, w)
                key = (min(here, there), max(here, there))
                if use_uf:
                    if uf.unite(here, there):
                        edges.add(key)
                        placed += 1
                else:
                    trial = set(edges)
                    trial.add(key)
                    comps = full_recompute_components(h, w, trial)
                    if comps <= h * w - len(trial) + 1:
                        edges.add(key)
                        placed += 1
    return placed, edges


def benchmark_connectivity(h: int, w: int, grid: List[str], trials: int = 200) -> None:
    t0 = time.perf_counter()
    for _ in range(trials):
        greedy_loop_edges(h, w, grid, use_uf=False)
    naive_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(trials):
        greedy_loop_edges(h, w, grid, use_uf=True)
    uf_ms = (time.perf_counter() - t0) * 1000

    print(f"connectivity_trials={trials}")
    print(f"full_recompute_ms={naive_ms:.2f}")
    print(f"union_find_ms={uf_ms:.2f}")
    print(f"speedup={naive_ms / max(uf_ms, 1e-9):.1f}x")


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        text = path.read_text()
    else:
        text = sys.stdin.read()
    from io import StringIO

    h, w, grid = read_grid(StringIO(text))
    placed, edges = greedy_loop_edges(h, w, grid, use_uf=True)
    comps = full_recompute_components(h, w, edges)
    print(f"grid={h}x{w} edges={len(edges)} placed={placed} components={comps}")
    benchmark_connectivity(h, w, grid, trials=80)


if __name__ == "__main__":
    main()
