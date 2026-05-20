# python/ch01/score_intro_hc.py
"""Introduction to Heuristics Contest — 問題B 相当のスコア計算."""
import sys
from typing import List, Tuple


def read_input() -> Tuple[int, List[int], List[List[int]], List[int]]:
    lines = sys.stdin.read().splitlines()
    idx = 0
    d = int(lines[idx])
    idx += 1
    c = list(map(int, lines[idx].split()))
    idx += 1
    s = []
    for _ in range(d):
        s.append(list(map(int, lines[idx].split())))
        idx += 1
    schedule = []
    for _ in range(d):
        schedule.append(int(lines[idx]))
        idx += 1
    return d, c, s, schedule


def daily_satisfactions(
    d: int, c: List[int], s: List[List[int]], schedule: List[int]
) -> List[int]:
    """各日終了時点の満足度 v_d を返す."""
    last = [0] * 26
    satisfaction = 0
    result = []
    for day in range(1, d + 1):
        t = schedule[day - 1] - 1  # 0-indexed type
        satisfaction += s[day - 1][t]
        last[t] = day
        decay = 0
        for i in range(26):
            decay += c[i] * (day - last[i])
        satisfaction -= decay
        result.append(satisfaction)
    return result


def final_score(satisfaction: int) -> int:
    return max(10**6 + satisfaction, 0)


def main() -> None:
    d, c, s, schedule = read_input()
    daily = daily_satisfactions(d, c, s, schedule)
    for v in daily:
        print(v)
    final = daily[-1]
    print(final_score(final), file=sys.stderr)


if __name__ == "__main__":
    main()
