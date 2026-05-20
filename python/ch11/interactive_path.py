# python/ch11/interactive_path.py
"""AHC003 簡略: 推定重みでダイクストラ → フィードバックで辺を更新."""
from __future__ import annotations

import heapq
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_sample(path: Path) -> Tuple[int, List[Tuple[int, int, float]], List[Tuple[int, int]]]:
    lines = path.read_text().splitlines()
    n, m = map(int, lines[0].split())
    edges: List[Tuple[int, int, float]] = []
    for i in range(1, m + 1):
        u, v, w = lines[i].split()
        edges.append((int(u), int(v), float(w)))
    q = int(lines[m + 1])
    queries = []
    for j in range(m + 2, m + 2 + q):
        s, t = map(int, lines[j].split())
        queries.append((s, t))
    return n, edges, queries


def build_adj(n: int, edges: List[Tuple[int, int, float]]) -> List[List[Tuple[int, float]]]:
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj


def dijkstra(adj: List[List[Tuple[int, float]]], start: int, goal: int) -> Tuple[float, List[int]]:
    n = len(adj)
    dist = [math.inf] * n
    prev = [-1] * n
    dist[start] = 0.0
    pq: List[Tuple[float, int]] = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == goal:
            break
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if dist[goal] == math.inf:
        return math.inf, []
    path: List[int] = []
    cur = goal
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return dist[goal], path


def edge_key(u: int, v: int) -> Tuple[int, int]:
    return (u, v) if u < v else (v, u)


def update_estimates(
    est: Dict[Tuple[int, int], float],
    path: List[int],
    predicted: float,
    actual: float,
) -> None:
    if len(path) < 2 or predicted <= 0:
        return
    ratio = actual / predicted
    for i in range(len(path) - 1):
        k = edge_key(path[i], path[i + 1])
        est[k] = max(0.1, est.get(k, 1.0) * ratio)


class Solver:
    def __init__(self, n: int, topo: List[Tuple[int, int]]) -> None:
        self.n = n
        self.est: Dict[Tuple[int, int], float] = {edge_key(u, v): 1.0 for u, v in topo}

    def adj(self) -> List[List[Tuple[int, float]]]:
        adj: List[List[Tuple[int, float]]] = [[] for _ in range(self.n)]
        for (u, v), w in self.est.items():
            adj[u].append((v, w))
            adj[v].append((u, w))
        return adj

    def answer(self, s: int, t: int) -> Tuple[float, List[int]]:
        return dijkstra(self.adj(), s, t)

    def feedback(self, path: List[int], predicted: float, actual: float) -> None:
        update_estimates(self.est, path, predicted, actual)


def run_interactive() -> None:
    lines = sys.stdin.read().splitlines()
    if not lines:
        return
    it = iter(lines)
    n, m = map(int, next(it).split())
    topo = []
    for _ in range(m):
        u, v = map(int, next(it).split())
        topo.append((u, v))
    q = int(next(it))
    solver = Solver(n, topo)
    out_lines: List[str] = []
    for _ in range(q):
        s, t = map(int, next(it).split())
        pred, path = solver.answer(s, t)
        out_lines.append(f"PATH {pred:.4f} {len(path)} " + " ".join(map(str, path)))
        actual_line = next(it)
        parts = actual_line.split()
        actual = float(parts[1])
        k = int(parts[2])
        true_path = list(map(int, parts[3 : 3 + k]))
        solver.feedback(true_path, pred, actual)
    sys.stdout.write("\n".join(out_lines) + "\n")
    sys.stdout.flush()


def run_offline(path: Path) -> None:
    n, edges, queries = load_sample(path)
    true_adj = build_adj(n, edges)
    topo = [(u, v) for u, v, _ in edges]
    solver = Solver(n, topo)
    total_pred = 0.0
    total_true = 0.0
    for qi, (s, t) in enumerate(queries):
        pred, path = solver.answer(s, t)
        true_len, true_path = dijkstra(true_adj, s, t)
        solver.feedback(true_path, pred, true_len)
        total_pred += pred
        total_true += true_len
        print(f"query {qi}: s={s} t={t} pred={pred:.2f} true={true_len:.2f} path={' '.join(map(str, path))}")
    print(f"queries={len(queries)} sum_pred={total_pred:.2f} sum_true={total_true:.2f}")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--offline":
        root = Path(__file__).resolve().parents[2]
        path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "data" / "ch11" / "sample.txt"
        run_offline(path)
        return
    run_interactive()


if __name__ == "__main__":
    main()
