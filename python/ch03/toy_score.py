# python/ch03/toy_score.py
"""最小例: State / Move / Score のモデリング."""
from dataclasses import dataclass
from typing import List


@dataclass
class ToyState:
    picked: List[bool]


@dataclass
class ToyInput:
    values: List[int]


def apply_move(state: ToyState, index: int, pick: bool) -> ToyState:
    nxt = ToyState(list(state.picked))
    nxt.picked[index] = pick
    return nxt


def score(state: ToyState, inp: ToyInput) -> int:
    total = 0
    for i, picked in enumerate(state.picked):
        if picked:
            total += inp.values[i]
    return total


def main() -> None:
    import sys

    lines = sys.stdin.read().splitlines()
    n = int(lines[0])
    values = list(map(int, lines[1].split()))
    inp = ToyInput(values)
    state = ToyState([False] * n)

    # デモ: 全部 pick する Move を順に適用
    for i in range(n):
        state = apply_move(state, i, True)
        print(f"day {i + 1}: score={score(state, inp)}")


if __name__ == "__main__":
    main()
