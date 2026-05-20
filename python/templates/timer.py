# python/templates/timer.py
import time


class Timer:
    def __init__(self, limit_sec: float):
        self.start = time.perf_counter()
        self.limit = limit_sec

    def elapsed(self) -> float:
        return time.perf_counter() - self.start

    def remaining(self) -> float:
        return self.limit - self.elapsed()

    def expired(self) -> bool:
        return self.remaining() <= 0


if __name__ == "__main__":
    timer = Timer(1.0)
    while not timer.expired():
        pass
    print(f"elapsed: {timer.elapsed():.3f}s")
