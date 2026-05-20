# python/ch14/slide_beam.py
"""3x3 スライドパズルをビームサーチで解く."""
from __future__ import annotations

import heapq
import sys
from typing import List, Tuple


def read_state(stream) -> Tuple[int, Tuple[int, ...]]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    cells: List[int] = []
    for i in range(1, n + 1):
        cells.extend(map(int, lines[i].split()))
    return n, tuple(cells)


def goal_state(n: int) -> Tuple[int, ...]:
    return tuple(list(range(1, n * n)) + [0])


def manhattan(state: Tuple[int, ...], n: int, goal: Tuple[int, ...]) -> int:
    h = 0
    for i, v in enumerate(state):
        if v == 0:
            continue
        gi = goal.index(v)
        r, c = divmod(i, n)
        gr, gc = divmod(gi, n)
        h += abs(r - gr) + abs(c - gc)
    return h


def blank_pos(state: Tuple[int, ...]) -> int:
    return state.index(0)


def neighbors(state: Tuple[int, ...], n: int) -> List[Tuple[int, ...]]:
    b = blank_pos(state)
    r, c = divmod(b, n)
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n:
            nb = nr * n + nc
            lst = list(state)
            lst[b], lst[nb] = lst[nb], lst[b]
            out.append(tuple(lst))
    return out


def beam_search(start: Tuple[int, ...], n: int, width: int = 100, max_depth: int = 40) -> Tuple[bool, int, int]:
    goal = goal_state(n)
    if start == goal:
        return True, 0, 1
    beam = [(manhattan(start, n, goal), 0, start)]
    visited = {start}
    for depth in range(1, max_depth + 1):
        candidates = []
        for _, _, state in beam:
            for nxt in neighbors(state, n):
                if nxt in visited:
                    continue
                visited.add(nxt)
                if nxt == goal:
                    return True, depth, len(visited)
                f = depth + manhattan(nxt, n, goal)
                candidates.append((f, depth, nxt))
        if not candidates:
            return False, -1, len(visited)
        beam = heapq.nsmallest(width, candidates)
    return False, -1, len(visited)


def main() -> None:
    n, start = read_state(sys.stdin)
    solved, depth, explored = beam_search(start, n)
    print(f"n={n} solved={solved} depth={depth} explored={explored} beam_width=100")


if __name__ == "__main__":
    main()
