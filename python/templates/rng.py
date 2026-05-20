# python/templates/rng.py
import random


def new_rng(seed: int) -> random.Random:
    return random.Random(seed)


def randint(rng: random.Random, n: int) -> int:
    return rng.randint(0, n - 1)


def shuffle(rng: random.Random, items: list) -> None:
    rng.shuffle(items)


if __name__ == "__main__":
    rng = new_rng(42)
    items = [1, 2, 3, 4, 5]
    print("randint:", randint(rng, 10))
    shuffle(rng, items)
    print("shuffled:", items)
