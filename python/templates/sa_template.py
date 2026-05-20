# python/templates/sa_template.py
import math
import random
import sys
import time
from typing import Callable, Optional, Tuple, TypeVar

T = TypeVar("T")

T0 = 100.0
ALPHA = 0.995


def log_score(step: int, score: int) -> None:
    print(step, score, file=sys.stderr)


def sa(
    initial_state: T,
    neighbor_fn: Callable[[T], Optional[T]],
    score_fn: Callable[[T], int],
    time_limit_sec: float = 2.0,
    rng: Optional[random.Random] = None,
) -> Tuple[T, int]:
    """neighbor_fn(state) -> new_state or None
    score_fn(state) -> int (high is better)
    """
    if rng is None:
        rng = random.Random()

    start = time.perf_counter()

    state = initial_state
    best_state = state
    best_score = score = score_fn(state)

    T = T0
    step = 0

    while time.perf_counter() - start < time_limit_sec:
        new_state = neighbor_fn(state)
        if new_state is None:
            continue
        new_score = score_fn(new_state)
        delta = new_score - score

        if delta >= 0 or rng.random() < math.exp(delta / T):
            state = new_state
            score = new_score
            if score > best_score:
                best_score = score
                best_state = state

        T *= ALPHA
        step += 1
        if step % 1000 == 0:
            log_score(step, score)

    return best_state, best_score


def demo() -> None:
    target = 42
    state = 0

    def score_fn(x: int) -> int:
        return -(x - target) ** 2

    def neighbor_fn(x: int) -> Optional[int]:
        dx = random.choice([-1, 1])
        nxt = x + dx
        if 0 <= nxt <= 100:
            return nxt
        return None

    best_state, best_score = sa(state, neighbor_fn, score_fn, time_limit_sec=0.5, rng=random.Random(42))
    print(f"best_state={best_state} best_score={best_score}")


if __name__ == "__main__":
    demo()
