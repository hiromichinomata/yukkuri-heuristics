# python/ch12/local_judge.py
"""AHC003「Shortest Path Queries」形式のローカルジャッジ（第12章）.

ソルバを子プロセスとして起動し、本番と同じ手順で 1 クエリずつ会話する。

  1. ジャッジ → ソルバ: "si sj ti tj"（30×30 グリッドの始点・終点）
  2. ソルバ → ジャッジ: U/D/L/R の経路文字列 1 行（出力したら flush）
  3. ジャッジ → ソルバ: 経路長 b にノイズ e∈[0.9, 1.1] を掛けた round(b × e)
  を Q 回（本番は 1000 回）繰り返し、公式と同じ式でスコアを出す:
      score = round(2312311 × Σ_k 0.998^(Q-k) × a_k / b_k)   （a_k は真の最短距離）

辺の重みの生成は **簡略版**（行・列ごとの基準値 ± D の一様乱数）で、公式の生成器とは異なる。

  python python/ch12/local_judge.py --seed 1 -- python python/ch12/solver.py
  python python/ch12/local_judge.py --seed 1 -- go run go/ch12/solver.go
"""
from __future__ import annotations

import argparse
import heapq
import random
import subprocess
import sys
import time
from typing import List, Tuple

N = 30
MOVES = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def generate_weights(rng: random.Random) -> Tuple[List[List[int]], List[List[int]]]:
    """h[i][j]: (i,j)-(i,j+1) の重み、v[i][j]: (i,j)-(i+1,j) の重み（簡略版の生成器）."""
    d = rng.randint(100, 2000)
    h = []
    for _ in range(N):
        base = rng.randint(1000 + d, 9000 - d)
        h.append([base + rng.randint(-d, d) for _ in range(N - 1)])
    v_cols = []
    for _ in range(N):
        base = rng.randint(1000 + d, 9000 - d)
        v_cols.append([base + rng.randint(-d, d) for _ in range(N - 1)])
    v = [[v_cols[j][i] for j in range(N)] for i in range(N - 1)]
    return h, v


def edge_weight(h, v, i: int, j: int, ni: int, nj: int) -> int:
    if i == ni:
        return h[i][min(j, nj)]
    return v[min(i, ni)][j]


def shortest(h, v, si: int, sj: int, ti: int, tj: int) -> int:
    dist = [[float("inf")] * N for _ in range(N)]
    dist[si][sj] = 0
    pq = [(0, si, sj)]
    while pq:
        d, i, j = heapq.heappop(pq)
        if (i, j) == (ti, tj):
            return d
        if d > dist[i][j]:
            continue
        for di, dj in MOVES.values():
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N:
                nd = d + edge_weight(h, v, i, j, ni, nj)
                if nd < dist[ni][nj]:
                    dist[ni][nj] = nd
                    heapq.heappush(pq, (nd, ni, nj))
    raise RuntimeError("unreachable")


def path_length(h, v, si: int, sj: int, ti: int, tj: int, path: str) -> int:
    """経路を検証して長さを返す。本番なら WA になる経路は ValueError."""
    i, j = si, sj
    seen = {(i, j)}
    total = 0
    for ch in path:
        if ch not in MOVES:
            raise ValueError(f"不正な文字 {ch!r}")
        ni, nj = i + MOVES[ch][0], j + MOVES[ch][1]
        if not (0 <= ni < N and 0 <= nj < N):
            raise ValueError("グリッドの外に出た")
        if (ni, nj) in seen:
            raise ValueError("同じ頂点を2回通った")
        seen.add((ni, nj))
        total += edge_weight(h, v, i, j, ni, nj)
        i, j = ni, nj
    if (i, j) != (ti, tj):
        raise ValueError("終点に着いていない")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="AHC003 形式のローカルジャッジ")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--queries", type=int, default=1000, help="クエリ数（本番は 1000）")
    parser.add_argument("solver", nargs=argparse.REMAINDER, help="-- のあとにソルバの起動コマンド")
    args = parser.parse_args()
    cmd = args.solver[1:] if args.solver[:1] == ["--"] else args.solver
    if not cmd:
        parser.error("ソルバのコマンドを -- のあとに書いてください")

    rng = random.Random(args.seed)
    h, v = generate_weights(rng)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    assert proc.stdin is not None and proc.stdout is not None

    q = args.queries
    total = 0.0
    start = time.perf_counter()
    for k in range(1, q + 1):
        while True:  # 本番と同じく、始点と終点のマンハッタン距離は 10 以上
            si, sj, ti, tj = (rng.randrange(N) for _ in range(4))
            if abs(si - ti) + abs(sj - tj) >= 10:
                break
        proc.stdin.write(f"{si} {sj} {ti} {tj}\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            sys.exit(f"query {k}: ソルバが経路を返さずに終了した（flush を忘れていないか）")
        try:
            b = path_length(h, v, si, sj, ti, tj, line.strip())
        except ValueError as exc:
            proc.kill()
            sys.exit(f"query {k}: WA — {exc}")
        a = shortest(h, v, si, sj, ti, tj)
        total += 0.998 ** (q - k) * a / b
        proc.stdin.write(f"{round(b * rng.uniform(0.9, 1.1))}\n")
        proc.stdin.flush()

    proc.stdin.close()
    proc.wait()
    elapsed = time.perf_counter() - start
    score = round(2312311 * total)
    # 1000 クエリ全部で最短経路を出せたときの満点（この値で割ると達成率）
    best = round(2312311 * sum(0.998 ** (q - k) for k in range(1, q + 1)))
    print(f"seed={args.seed} queries={q} score={score} max={best} ratio={score / best:.4f} elapsed={elapsed:.2f}s",
          file=sys.stderr)


if __name__ == "__main__":
    main()
