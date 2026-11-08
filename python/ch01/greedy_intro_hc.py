# python/ch01/greedy_intro_hc.py
"""Intro HC 問題A 向け貪欲（第5章で本格化）."""


def daily_satisfactions(d, c, s, schedule):
    last = [0] * 26
    satisfaction = 0
    result = []
    for day in range(1, d + 1):
        t = schedule[day - 1] - 1
        satisfaction += s[day - 1][t]
        last[t] = day
        decay = sum(c[i] * (day - last[i]) for i in range(26))
        satisfaction -= decay
        result.append(satisfaction)
    return result


def greedy_schedule(d, c, s):
    schedule = []
    for day in range(1, d + 1):
        best_t, best_sat = 1, None
        for t in range(1, 27):
            trial = schedule + [t]
            sat = daily_satisfactions(day, c, s, trial)[-1]
            if best_sat is None or sat > best_sat:
                best_sat = sat
                best_t = t
        schedule.append(best_t)
    return schedule


def read_problem(stream):
    """D, c, s を読む（後ろにスケジュール行があっても無視する）."""
    lines = stream.read().split("\n")
    d = int(lines[0])
    c = list(map(int, lines[1].split()))
    s = [list(map(int, lines[2 + i].split())) for i in range(d)]
    return d, c, s


def main():
    import sys

    d, c, s = read_problem(sys.stdin)
    schedule = greedy_schedule(d, c, s)
    for t in schedule:
        print(t)
    final = daily_satisfactions(d, c, s, schedule)[-1]
    print(f"final score={max(10**6 + final, 0)}", file=sys.stderr)


if __name__ == "__main__":
    main()
