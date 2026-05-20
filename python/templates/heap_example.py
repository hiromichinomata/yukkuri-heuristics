# python/templates/heap_example.py
import heapq


def main():
    pq = []
    heapq.heappush(pq, (10, "a"))
    heapq.heappush(pq, (5, "b"))
    best = heapq.heappop(pq)
    print(best)


if __name__ == "__main__":
    main()
