# python/ch11/query_simulator.py
"""AHC003 簡略ローカルジャッジ: クエリを送りフィードバックを返す."""
from __future__ import annotations

import heapq
import math
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SOLVER = ROOT / "python" / "ch11" / "interactive_path.py"


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
    path: List[int] = []
    cur = goal
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return dist[goal], path


def build_judge_input(
    n: int, edges: List[Tuple[int, int, float]], queries: List[Tuple[int, int]]
) -> str:
    lines = [f"{n} {len(edges)}"]
    for u, v, _ in edges:
        lines.append(f"{u} {v}")
    lines.append(str(len(queries)))
    adj = build_adj(n, edges)
    for s, t in queries:
        true_len, true_path = dijkstra(adj, s, t)
        lines.append(f"{s} {t}")
        lines.append(f"FEEDBACK {true_len:.6f} {len(true_path)} " + " ".join(map(str, true_path)))
    return "\n".join(lines) + "\n"


def main() -> None:
    sample = ROOT / "data" / "ch11" / "sample.txt"
    if len(sys.argv) > 1:
        sample = Path(sys.argv[1])
    n, edges, queries = load_sample(sample)
    judge_in = build_judge_input(n, edges, queries)
    proc = subprocess.run(
        [sys.executable, str(SOLVER)],
        input=judge_in,
        text=True,
        capture_output=True,
        check=True,
    )
    print("=== judge input (head) ===")
    print("\n".join(judge_in.splitlines()[:4]), "...")
    print("=== solver output ===")
    print(proc.stdout.strip())
    print(f"=== queries={len(queries)} n={n} edges={len(edges)} ===")


if __name__ == "__main__":
    main()
