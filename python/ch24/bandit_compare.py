# python/ch24/bandit_compare.py
"""AHC003 風の玩具で、経路選びの探索戦略を比べる（第24章）.

  python python/ch24/bandit_compare.py data/ch24/sample.txt
  python python/ch24/bandit_compare.py data/ch24/sample.txt --rounds 5 --epsilon 0.3

各クエリで、ソルバは **自分の推定** で経路を選び、**選んだ経路の長さ（ノイズ付き）だけ** を観測する。
どの辺が長かったかは分からないので、第12章と同じく、ずれを経路上の辺にまとめて配る。

  後悔（regret）= 選んだ経路の真の長さ − 真の最短路長

をクエリ全体で足し、seed を変えた TRIALS 回の平均で比べる（小さいほど良い）。
"""
from __future__ import annotations

import argparse
import heapq
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

Edge = Tuple[int, int]

STRATEGIES = ("greedy", "epsilon_greedy", "ucb1", "thompson")
INIT_WEIGHT = 6.0  # 推定の初期値（真の重みは 1〜6。上限から始める = 悲観的な事前知識）
LEARNING_RATE = 0.5  # 観測と予測のずれをどれだけ反映するか（第12章と同じ）
NOISE = 0.1  # 観測に掛かるノイズ（0.9〜1.1 倍、AHC003 と同じ）
ROUNDS = 50  # クエリ列を何周するか
TRIALS = 20  # seed を変えて何回走らせ、平均を取るか
EPSILON = 0.15  # ε-greedy: この確率でランダムな経路を試す
UCB_C = 1.0  # UCB1: 通った回数が少ない辺を、どれだけ短く見せるか
THOMPSON_SIGMA = 0.5  # Thompson: 推定のばらつきの大きさ（通るほど小さくなる）


def edge_key(u: int, v: int) -> Edge:
    return (u, v) if u < v else (v, u)


def load_sample(path: Path) -> Tuple[int, Dict[Edge, float], List[Tuple[int, int]]]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    n, m = map(int, lines[0].split())
    weights: Dict[Edge, float] = {}
    for i in range(1, 1 + m):
        u, v, w = lines[i].split()
        weights[edge_key(int(u), int(v))] = float(w)
    q = int(lines[1 + m])
    queries = [tuple(map(int, lines[2 + m + i].split())) for i in range(q)]
    return n, weights, queries  # type: ignore[return-value]


def dijkstra(n: int, weights: Dict[Edge, float], start: int, goal: int) -> Tuple[float, List[int]]:
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for (u, v), w in weights.items():
        adj[u].append((v, w))
        adj[v].append((u, w))
    dist = [math.inf] * n
    prev = [-1] * n
    dist[start] = 0.0
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == goal:
            break
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    path = []
    cur = goal
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    return dist[goal], path[::-1]


def path_edges(path: List[int]) -> List[Edge]:
    return [edge_key(path[i], path[i + 1]) for i in range(len(path) - 1)]


class Solver:
    def __init__(self, n: int, edges: List[Edge], strategy: str, rng: random.Random, epsilon: float) -> None:
        self.n = n
        self.strategy = strategy
        self.rng = rng
        self.epsilon = epsilon
        self.est: Dict[Edge, float] = {k: INIT_WEIGHT for k in edges}
        self.pulls: Dict[Edge, int] = {k: 0 for k in edges}
        self.t = 0  # これまでのクエリ数

    def planning_weight(self, key: Edge) -> float:
        """経路を選ぶときに使う重み。探索したい辺ほど短く見せる."""
        w = self.est[key]
        if self.strategy == "ucb1":
            # 通った回数が少ない辺ほど短く見せる（楽観）。クエリが進むと log でゆっくり効きが弱まる
            return w / (1.0 + UCB_C * math.sqrt(math.log(self.t + 2) / (self.pulls[key] + 1)))
        if self.strategy == "thompson":
            # 推定のまわりにばらつかせた値を引く。通った回数が少ない辺ほど大きくばらつく
            return w * math.exp(self.rng.gauss(0.0, THOMPSON_SIGMA / math.sqrt(self.pulls[key] + 1)))
        return w

    def choose_path(self, s: int, t: int) -> List[int]:
        if self.strategy == "epsilon_greedy" and self.rng.random() < self.epsilon:
            plan = {k: self.rng.random() for k in self.est}  # 確率 ε でランダムな経路
        else:
            plan = {k: self.planning_weight(k) for k in self.est}
        return dijkstra(self.n, plan, s, t)[1]

    def update(self, path: List[int], observed: float) -> None:
        keys = path_edges(path)
        predicted = sum(self.est[k] for k in keys)
        factor = 1.0 + LEARNING_RATE * (observed / predicted - 1.0)
        for k in keys:
            self.est[k] *= factor
            self.pulls[k] += 1
        self.t += 1


def run(
    n: int,
    true_w: Dict[Edge, float],
    queries: List[Tuple[int, int]],
    strategy: str,
    seed: int,
    rounds: int,
    epsilon: float,
) -> Tuple[float, int]:
    """(後悔の合計, 一度も通らなかった辺の数) を返す."""
    solver = Solver(n, list(true_w), strategy, random.Random(seed), epsilon)
    noise = random.Random(seed + 1_000_000)  # 観測ノイズは戦略と別の乱数（全戦略で同じ列になる）
    regret = 0.0
    for _ in range(rounds):
        for s, t in queries:
            path = solver.choose_path(s, t)
            true_len = sum(true_w[k] for k in path_edges(path))
            regret += true_len - dijkstra(n, true_w, s, t)[0]
            solver.update(path, true_len * noise.uniform(1 - NOISE, 1 + NOISE))
    untouched = sum(1 for c in solver.pulls.values() if c == 0)
    return regret, untouched


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="探索戦略の比較（第24章）")
    parser.add_argument("input", nargs="?", default=str(root / "data" / "ch24" / "sample.txt"))
    parser.add_argument("--rounds", type=int, default=ROUNDS, help="クエリ列を何周するか")
    parser.add_argument("--trials", type=int, default=TRIALS, help="seed を変えて何回平均するか")
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    args = parser.parse_args()

    n, true_w, queries = load_sample(Path(args.input))
    print(
        f"graph n={n} m={len(true_w)} queries={len(queries)} rounds={args.rounds} trials={args.trials}",
        file=sys.stderr,
    )
    results = []
    for name in STRATEGIES:
        runs = [run(n, true_w, queries, name, seed, args.rounds, args.epsilon) for seed in range(args.trials)]
        regret = sum(r[0] for r in runs) / len(runs)
        untouched = sum(r[1] for r in runs) / len(runs)
        results.append((regret, name))
        print(f"strategy={name} regret={regret:.2f} untouched_edges={untouched:.1f}", file=sys.stderr)
    best = min(results)
    print(f"best={best[1]} (smallest regret)", file=sys.stderr)


if __name__ == "__main__":
    main()
