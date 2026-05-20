# python/ch02/ahc_main.py
import time


class Timer:
    def __init__(self, limit_sec: float):
        self.start = time.perf_counter()
        self.limit = limit_sec

    def expired(self) -> bool:
        return time.perf_counter() - self.start >= self.limit


def solve():
    pass


def main():
    timer = Timer(2.0)
    while not timer.expired():
        solve()
        break


if __name__ == "__main__":
    main()
