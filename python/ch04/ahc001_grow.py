# python/ch04/ahc001_grow.py
"""AHC001 玩具: 企業点から矩形を素朴に拡大."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, TextIO, Tuple

GRID = 20


@dataclass
class Company:
    x: int
    y: int
    r: int


@dataclass
class Rect:
    a: int
    b: int
    c: int
    d: int

    def area(self) -> int:
        return (self.c - self.a) * (self.d - self.b)

    def copy(self) -> Rect:
        return Rect(self.a, self.b, self.c, self.d)


def read_problem(stream: TextIO) -> List[Company]:
    lines = stream.read().splitlines()
    n = int(lines[0])
    companies: List[Company] = []
    for i in range(1, n + 1):
        x, y, r = map(int, lines[i].split())
        companies.append(Company(x, y, r))
    return companies


def overlaps_positive(r1: Rect, r2: Rect) -> bool:
    ix = min(r1.c, r2.c) - max(r1.a, r2.a)
    iy = min(r1.d, r2.d) - max(r1.b, r2.b)
    return ix > 0 and iy > 0


def can_place(rect: Rect, others: List[Rect]) -> bool:
    if rect.a < 0 or rect.b < 0 or rect.c > GRID or rect.d > GRID:
        return False
    if rect.area() <= 0:
        return False
    return all(not overlaps_positive(rect, o) for o in others)


def grow_rect(company: Company, others: List[Rect]) -> Rect:
    x, y = company.x, company.y
    rect = Rect(x, y, x + 1, y + 1)
    expansions = [
        ("left", -1, 0, 0, 0),
        ("right", 0, 0, 1, 0),
        ("down", 0, -1, 0, 0),
        ("up", 0, 0, 0, 1),
    ]
    while rect.area() < company.r:
        best: Tuple[int, Rect] | None = None
        for _, da, db, dc, dd in expansions:
            nxt = Rect(rect.a + da, rect.b + db, rect.c + dc, rect.d + dd)
            if not can_place(nxt, others):
                continue
            gain = nxt.area() - rect.area()
            if best is None or gain > best[0]:
                best = (gain, nxt)
        if best is None:
            break
        rect = best[1]
    return rect


def solve(companies: List[Company]) -> List[Rect]:
    rects: List[Rect] = []
    for company in companies:
        rect = grow_rect(company, rects)
        rects.append(rect)
    return rects


def main() -> None:
    companies = read_problem(sys.stdin)
    rects = solve(companies)
    for rect in rects:
        print(rect.a, rect.b, rect.c, rect.d)


if __name__ == "__main__":
    main()
