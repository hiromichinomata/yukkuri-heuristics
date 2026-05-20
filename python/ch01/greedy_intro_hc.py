# python/ch01/greedy_intro_hc.py
"""Intro HC 問題A 向け貪欲の骨格（第5章で本実装）."""


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
