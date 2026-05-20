# python/ch17/territory_greedy.py
"""AHC008 簡略: 2 エージェントが交互に隣接マスを貪欲に占領（第17章）."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional, TextIO, Tuple

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass
class ProblemInput:
    n: int
    grid: List[List[int]]
    starts: List[Tuple[int, int]]


def read_problem(stream: TextIO) -> ProblemInput:
    lines = stream.read().splitlines()
    n = int(lines[0])
    grid = [list(map(int, lines[i + 1].split())) for i in range(n)]
    starts = []
    for i in range(2):
        r, c = map(int, lines[n + 1 + i].split())
        starts.append((r, c))
    return ProblemInput(n=n, grid=grid, starts=starts)


def best_move(
    n: int,
    grid: List[List[int]],
    owner: List[List[int]],
    agent: int,
    pos: Tuple[int, int],
) -> Optional[Tuple[int, int, int]]:
    """(value, r, c) を最大とする未占領隣接マス."""
    r0, c0 = pos
    best: Optional[Tuple[int, int, int]] = None
    for dr, dc in DIRS:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < n and 0 <= c < n):
            continue
        if owner[r][c] != -1:
            continue
        val = grid[r][c]
        if best is None or val > best[0] or (val == best[0] and (r, c) < (best[1], best[2])):
            best = (val, r, c)
    return best


def solve(problem: ProblemInput) -> Tuple[List[int], List[str]]:
    n = problem.n
    owner = [[-1] * n for _ in range(n)]
    scores = [0, 0]
    positions = list(problem.starts)
    moves_log: List[str] = []

    for agent in range(2):
        r, c = positions[agent]
        owner[r][c] = agent
        scores[agent] += problem.grid[r][c]

    turn = 0
    stagnant = 0
    while stagnant < 2:
        agent = turn % 2
        mv = best_move(n, problem.grid, owner, agent, positions[agent])
        if mv is None:
            stagnant += 1
            turn += 1
            continue
        stagnant = 0
        _, r, c = mv
        owner[r][c] = agent
        positions[agent] = (r, c)
        scores[agent] += problem.grid[r][c]
        moves_log.append(f"{agent} {r} {c}")
        turn += 1

    return scores, moves_log


def main() -> None:
    problem = read_problem(sys.stdin)
    scores, moves = solve(problem)
    print(f"territory0={scores[0]} territory1={scores[1]} moves={len(moves)}", file=sys.stderr)
    print(scores[0], scores[1])
    for line in moves:
        print(line)


if __name__ == "__main__":
    main()
