# python/ch12/solver.py
"""AHC003「Shortest Path Queries」形式のソルバ（第12章）.

辺の重みを推定値で持ち、
  1. 推定重みでダイクストラして経路を出す（出したら **必ず flush**）
  2. 返ってきた「ノイズ付きの経路長」と予測の比で、通った辺の推定値を更新する
を 1 クエリずつ繰り返すオンライン解法。

  python python/ch12/local_judge.py --seed 1 -- python python/ch12/solver.py
"""
from __future__ import annotations

import heapq
import sys
from typing import List, Tuple

N = 30
INIT_WEIGHT = 5000.0  # 辺の重みの初期推定（本番の重みは 1000〜9000 程度）
LEARNING_RATE = 0.5  # 予測とのずれをどれだけ反映するか（0〜1）
W_MIN, W_MAX = 1000.0, 9000.0  # 推定値を範囲内にクリップする
MOVES = (("U", -1, 0), ("D", 1, 0), ("L", 0, -1), ("R", 0, 1))

Edge = Tuple[int, int, int]  # (0=横 / 1=縦, i, j)


class Solver:
    def __init__(self) -> None:
        self.h = [[INIT_WEIGHT] * (N - 1) for _ in range(N)]  # (i,j)-(i,j+1)
        self.v = [[INIT_WEIGHT] * N for _ in range(N - 1)]  # (i,j)-(i+1,j)

    def edge(self, i: int, j: int, ni: int, nj: int) -> Edge:
        if i == ni:
            return (0, i, min(j, nj))
        return (1, min(i, ni), j)

    def weight(self, e: Edge) -> float:
        kind, i, j = e
        return self.h[i][j] if kind == 0 else self.v[i][j]

    def shortest_path(self, si: int, sj: int, ti: int, tj: int) -> Tuple[str, List[Edge], float]:
        """推定重みでのダイクストラ。(経路文字列, 通る辺, 予測長) を返す."""
        inf = float("inf")
        dist = [[inf] * N for _ in range(N)]
        prev: List[List[Tuple[int, int, str]]] = [[(-1, -1, "")] * N for _ in range(N)]
        dist[si][sj] = 0.0
        pq = [(0.0, si, sj)]
        while pq:
            d, i, j = heapq.heappop(pq)
            if (i, j) == (ti, tj):
                break
            if d > dist[i][j]:
                continue
            for ch, di, dj in MOVES:
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    nd = d + self.weight(self.edge(i, j, ni, nj))
                    if nd < dist[ni][nj]:
                        dist[ni][nj] = nd
                        prev[ni][nj] = (i, j, ch)
                        heapq.heappush(pq, (nd, ni, nj))
        moves: List[str] = []
        edges: List[Edge] = []
        i, j = ti, tj
        while (i, j) != (si, sj):
            pi, pj, ch = prev[i][j]
            moves.append(ch)
            edges.append(self.edge(pi, pj, i, j))
            i, j = pi, pj
        return "".join(reversed(moves)), edges, dist[ti][tj]

    def update(self, edges: List[Edge], predicted: float, observed: int) -> None:
        """観測長 / 予測長 の比で、通った辺をまとめて伸び縮みさせる."""
        factor = 1.0 + LEARNING_RATE * (observed / predicted - 1.0)
        for kind, i, j in edges:
            table = self.h if kind == 0 else self.v
            table[i][j] = min(W_MAX, max(W_MIN, table[i][j] * factor))


def main() -> None:
    solver = Solver()
    while True:
        line = sys.stdin.readline()
        if not line.strip():
            break  # 入力の終わり
        si, sj, ti, tj = map(int, line.split())
        path, edges, predicted = solver.shortest_path(si, sj, ti, tj)
        print(path, flush=True)  # flush しないとジャッジが返事を待ったまま止まる
        observed = int(sys.stdin.readline())
        solver.update(edges, predicted, observed)


if __name__ == "__main__":
    main()
