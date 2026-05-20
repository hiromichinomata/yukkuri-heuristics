# python/ch16/ga_placement.py
"""1D 配置（幅つきアイテムを線上に並べる）を GA で最適化（第16章）."""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import List, TextIO, Tuple

POP_SIZE = 40
GENERATIONS = 200
MUTATION_RATE = 0.15
TOURNAMENT_K = 3


@dataclass
class ProblemInput:
    capacity: int
    widths: List[int]


def read_problem(stream: TextIO) -> ProblemInput:
    lines = stream.read().splitlines()
    capacity = int(lines[0])
    n = int(lines[1])
    widths = list(map(int, lines[2].split()))
    if len(widths) != n:
        raise ValueError(f"expected {n} widths, got {len(widths)}")
    return ProblemInput(capacity=capacity, widths=widths)


def evaluate(problem: ProblemInput, order: List[int]) -> Tuple[int, List[Tuple[int, int]]]:
    """順序どおり左から配置し、入った幅の合計と (index, position) を返す."""
    pos = 0
    placed_width = 0
    placement: List[Tuple[int, int]] = []
    for idx in order:
        w = problem.widths[idx]
        if pos + w > problem.capacity:
            continue
        placement.append((idx, pos))
        pos += w
        placed_width += w
    return placed_width, placement


def tournament_select(
    population: List[List[int]], fitness: List[int], rng: random.Random
) -> List[int]:
    best = None
    best_fit = -1
    for _ in range(TOURNAMENT_K):
        i = rng.randrange(len(population))
        if fitness[i] > best_fit:
            best_fit = fitness[i]
            best = population[i]
    assert best is not None
    return list(best)


def order_crossover(p1: List[int], p2: List[int], rng: random.Random) -> List[int]:
    n = len(p1)
    if n <= 2:
        return list(p1)
    a, b = sorted(rng.sample(range(n), 2))
    child = [-1] * n
    child[a : b + 1] = p1[a : b + 1]
    used = set(child[a : b + 1])
    fill = [x for x in p2 if x not in used]
    j = 0
    for i in range(n):
        if child[i] == -1:
            child[i] = fill[j]
            j += 1
    return child


def mutate(order: List[int], rng: random.Random) -> None:
    if rng.random() >= MUTATION_RATE:
        return
    i, j = rng.sample(range(len(order)), 2)
    order[i], order[j] = order[j], order[i]


def ga(problem: ProblemInput, rng: random.Random) -> Tuple[List[int], int, List[Tuple[int, int]]]:
    n = len(problem.widths)
    base = list(range(n))
    population = [rng.sample(base, n) for _ in range(POP_SIZE)]
    best_order = list(population[0])
    best_fit, best_place = evaluate(problem, best_order)

    for gen in range(GENERATIONS):
        fitness = [evaluate(problem, ind)[0] for ind in population]
        for fit, ind in zip(fitness, population):
            if fit > best_fit:
                best_fit = fit
                best_order = list(ind)
                best_place = evaluate(problem, ind)[1]

        next_pop: List[List[int]] = []
        elite = max(range(POP_SIZE), key=lambda i: fitness[i])
        next_pop.append(list(population[elite]))

        while len(next_pop) < POP_SIZE:
            p1 = tournament_select(population, fitness, rng)
            p2 = tournament_select(population, fitness, rng)
            child = order_crossover(p1, p2, rng)
            mutate(child, rng)
            next_pop.append(child)
        population = next_pop

        if gen % 50 == 0:
            print(f"ga gen={gen} best={best_fit}", file=sys.stderr)

    return best_order, best_fit, best_place


def main() -> None:
    rng = random.Random(42)
    problem = read_problem(sys.stdin)
    order, fit, placement = ga(problem, rng)
    print(f"placed_width={fit} capacity={problem.capacity}", file=sys.stderr)
    print(len(placement))
    for idx, pos in placement:
        print(idx, pos, problem.widths[idx])


if __name__ == "__main__":
    main()
