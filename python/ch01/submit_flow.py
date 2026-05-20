# python/ch01/submit_flow.py
import sys


def pre_submit_checks(output, validator, score_fn, timer):
    assert validator(output), "illegal output"
    score = score_fn(output)
    assert timer.elapsed() < timer.limit, "TLE locally"
    print("score:", score, file=sys.stderr)
    return output
