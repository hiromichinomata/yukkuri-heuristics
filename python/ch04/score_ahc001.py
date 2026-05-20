# python/ch04/score_ahc001.py
"""AHC001 玩具スコア: 重なり禁止・中心点含有・線形満足度."""
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


def read_all(stream: TextIO) -> Tuple[List[Company], List[Rect]]:
    lines = [ln for ln in stream.read().splitlines() if ln.strip() != ""]
    idx = 0
    n = int(lines[idx])
    idx += 1
    companies: List[Company] = []
    for _ in range(n):
        x, y, r = map(int, lines[idx].split())
        idx += 1
        companies.append(Company(x, y, r))
    rects: List[Rect] = []
    for _ in range(n):
        a, b, c, d = map(int, lines[idx].split())
        idx += 1
        rects.append(Rect(a, b, c, d))
    return companies, rects


def valid_rect(rect: Rect) -> bool:
    return (
        0 <= rect.a < rect.c <= GRID
        and 0 <= rect.b < rect.d <= GRID
        and rect.area() > 0
    )


def contains(rect: Rect, x: int, y: int) -> bool:
    return rect.a <= x + 0.5 < rect.c and rect.b <= y + 0.5 < rect.d


def overlaps_positive(r1: Rect, r2: Rect) -> bool:
    ix = min(r1.c, r2.c) - max(r1.a, r2.a)
    iy = min(r1.d, r2.d) - max(r1.b, r2.b)
    return ix > 0 and iy > 0


def company_score(company: Company, rect: Rect) -> int:
    if not contains(rect, company.x, company.y):
        return 0
    s = rect.area()
    if s <= 0 or company.r <= 0:
        return 0
    return int(company.r * min(s, company.r) / max(s, company.r))


def score_solution(
    companies: List[Company], rects: List[Rect]
) -> Tuple[int, bool, str]:
    n = len(companies)
    if len(rects) != n:
        return 0, False, f"rect count {len(rects)} != {n}"

    for i, rect in enumerate(rects):
        if not valid_rect(rect):
            return 0, False, f"invalid rect {i}: {rect}"

    for i in range(n):
        for j in range(i + 1, n):
            if overlaps_positive(rects[i], rects[j]):
                return 0, False, f"overlap {i} and {j}"

    total = 0
    for company, rect in zip(companies, rects):
        total += company_score(company, rect)
    return total, True, "ok"


def main() -> None:
    companies, rects = read_all(sys.stdin)
    total, ok, msg = score_solution(companies, rects)
    print(total)
    if not ok:
        print(msg, file=sys.stderr)
        sys.exit(1)
    print(f"companies={len(companies)} {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()
