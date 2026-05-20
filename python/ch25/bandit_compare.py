# python/ch25/bandit_compare.py
"""AHC003 簡略グラフで辺選択バンディット 3 戦略を比較（UCB1 / Thompson / ε-greedy）."""
from __future__ import annotations

import heapq
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


def edge_key(u: int, v: int) -> Tuple[int, int]:
    return (u, v) if u < v else (v, u)


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


@dataclass
class EdgeStats:
    pulls: int = 0
    reward_sum: float = 0.0
    alpha: float = 1.0
    beta: float = 1.0


class BanditSolver:
    def __init__(
        self,
        n: int,
        topo: List[Tuple[int, int]],
        strategy: str,
        rng: random.Random,
        epsilon: float = 0.15,
    ) -> None:
        self.n = n
        self.topo = topo
        self.strategy = strategy
        self.rng = rng
        self.epsilon = epsilon
        self.est: Dict[Tuple[int, int], float] = {edge_key(u, v): 1.0 for u, v in topo}
        self.stats: Dict[Tuple[int, int], EdgeStats] = {
            k: EdgeStats() for k in self.est
        }
        self.total_pulls = 0

    def adj(self) -> List[List[Tuple[int, float]]]:
        adj: List[List[Tuple[int, float]]] = [[] for _ in range(self.n)]
        for (u, v), w in self.est.items():
            bonus = self.exploration_bonus((u, v))
            adj[u].append((v, max(0.01, w - bonus)))
            adj[v].append((u, max(0.01, w - bonus)))
        return adj

    def exploration_bonus(self, key: Tuple[int, int]) -> float:
        st = self.stats[key]
        if st.pulls == 0:
            return 2.0
        if self.strategy == "ucb1":
            return 0.5 * math.sqrt(math.log(self.total_pulls + 1) / st.pulls)
        if self.strategy == "thompson":
            sample = self.rng.betavariate(st.alpha, st.beta)
            mean = st.reward_sum / st.pulls if st.pulls else 0.5
            return 0.8 * (sample - mean)
        if self.strategy == "epsilon_greedy":
            if self.rng.random() < self.epsilon:
                return 1.5
            return 0.0
        return 0.0

    def pick_focus_edge(self, path: List[int]) -> Tuple[int, int]:
        edges_on_path = [edge_key(path[i], path[i + 1]) for i in range(len(path) - 1)]
        if not edges_on_path:
            return next(iter(self.est))
        if self.strategy == "ucb1":
            return max(
                edges_on_path,
                key=lambda k: self.stats[k].reward_sum / max(1, self.stats[k].pulls)
                + math.sqrt(2 * math.log(self.total_pulls + 1) / max(1, self.stats[k].pulls)),
            )
        if self.strategy == "thompson":
            return max(
                edges_on_path,
                key=lambda k: self.rng.betavariate(self.stats[k].alpha, self.stats[k].beta),
            )
        if self.rng.random() < self.epsilon:
            return self.rng.choice(edges_on_path)
        return max(edges_on_path, key=lambda k: self.stats[k].reward_sum / max(1, self.stats[k].pulls))

    def update_estimates(self, path: List[int], predicted: float, actual: float) -> None:
        if len(path) < 2 or predicted <= 0:
            return
        ratio = actual / predicted
        for i in range(len(path) - 1):
            k = edge_key(path[i], path[i + 1])
            self.est[k] = max(0.1, self.est.get(k, 1.0) * ratio)
        focus = self.pick_focus_edge(path)
        err = max(0.0, min(1.0, abs(actual - predicted) / max(actual, 1.0)))
        reward = 1.0 - err
        st = self.stats[focus]
        st.pulls += 1
        st.reward_sum += reward
        st.alpha += reward
        st.beta += 1.0 - reward
        self.total_pulls += 1
        self.est[focus] = max(0.1, self.est[focus] * (0.9 + 0.2 * reward))

    def answer(self, s: int, t: int) -> Tuple[float, List[int]]:
        return dijkstra(self.adj(), s, t)

    def run_offline(
        self,
        true_adj: List[List[Tuple[int, float]]],
        queries: List[Tuple[int, int]],
    ) -> Tuple[float, float]:
        total_pred = 0.0
        total_true = 0.0
        for s, t in queries:
            pred, path = self.answer(s, t)
            true_len, true_path = dijkstra(true_adj, s, t)
            self.update_estimates(true_path, pred, true_len)
            total_pred += pred
            total_true += true_len
        return total_pred, total_true


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "data" / "ch25" / "sample.txt"
    n, edges, queries = load_sample(path)
    true_adj = build_adj(n, edges)
    topo = [(u, v) for u, v, _ in edges]
    rng = random.Random(42)

    print(f"graph n={n} m={len(edges)} queries={len(queries)}", file=sys.stderr)
    results = []
    for name in ("ucb1", "thompson", "epsilon_greedy"):
        solver = BanditSolver(n, topo, name, rng)
        pred, true = solver.run_offline(true_adj, queries)
        gap = pred - true
        results.append((name, pred, true, gap))
        print(
            f"strategy={name} sum_pred={pred:.4f} sum_true={true:.4f} gap={gap:.4f}",
            file=sys.stderr,
        )

    best = min(results, key=lambda x: x[3])
    print(f"best_gap={best[0]} (smallest pred-true gap)", file=sys.stderr)


if __name__ == "__main__":
    main()
