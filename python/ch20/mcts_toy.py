# python/ch20/mcts_toy.py
"""4 ノードグラフ上のターン制ゲームに MCTS（UCB1）を適用（第20章）.

  python python/ch20/mcts_toy.py < data/ch20/sample.txt                 # 1手 ITERATIONS 回（再現性のため既定）
  python python/ch20/mcts_toy.py --time-per-move 0.05 < data/ch20/sample.txt  # 本番と同じく時間で回す
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TextIO, Tuple

EXPLORATION = 1.41
ITERATIONS = 300
MAX_TURNS = 16


@dataclass
class GameInput:
    nodes: int
    edges: List[Tuple[int, int]]
    start: int
    terminal: int = 3


@dataclass
class GameState:
    node: int
    player: int


@dataclass
class MCTSNode:
    move: Optional[int] = None
    state: Optional[GameState] = None
    parent: Optional[MCTSNode] = None
    children: Dict[int, MCTSNode] = field(default_factory=dict)
    untried: List[int] = field(default_factory=list)
    visits: int = 0
    wins: float = 0.0


def read_game(stream: TextIO) -> GameInput:
    lines = stream.read().splitlines()
    parts = list(map(int, lines[0].split()))
    nodes, m = parts[0], parts[1]
    edges = []
    for i in range(1, 1 + m):
        u, v = map(int, lines[i].split())
        edges.append((u, v))
    start = int(lines[1 + m])
    return GameInput(nodes=nodes, edges=edges, start=start)


def build_adjacency(game: GameInput) -> List[List[int]]:
    adj: List[List[int]] = [[] for _ in range(game.nodes)]
    for u, v in game.edges:
        adj[u].append(v)
        adj[v].append(u)
    for i in range(game.nodes):
        adj[i].sort()
    return adj


def terminal_winner(state: GameState, game: GameInput) -> Optional[int]:
    if state.node == game.terminal:
        # state.player は「次に指す人」。終点に入ったのはその相手なので、相手の勝ち
        return 1 - state.player
    return None


def apply_move(state: GameState, nxt_node: int) -> GameState:
    return GameState(node=nxt_node, player=1 - state.player)


def rollout(state: GameState, adj: List[List[int]], game: GameInput, rng: random.Random) -> int:
    cur = state
    for _ in range(game.nodes * 4):
        winner = terminal_winner(cur, game)
        if winner is not None:
            return winner
        moves = adj[cur.node]
        if not moves:
            return 1 - cur.player
        cur = apply_move(cur, rng.choice(moves))
    return 1 - cur.player


def ucb1(parent_visits: int, child: MCTSNode) -> float:
    if child.visits == 0:
        return float("inf")
    return child.wins / child.visits + EXPLORATION * math.sqrt(
        math.log(parent_visits) / child.visits
    )


def expand(node: MCTSNode, adj: List[List[int]], rng: random.Random) -> MCTSNode:
    assert node.state is not None
    move = node.untried.pop(rng.randrange(len(node.untried)))
    child_state = apply_move(node.state, move)
    child = MCTSNode(move=move, state=child_state, parent=node, untried=list(adj[child_state.node]))
    node.children[move] = child
    return child


def best_child(node: MCTSNode) -> MCTSNode:
    return max(node.children.values(), key=lambda c: ucb1(node.visits, c))


def mcts(
    root: MCTSNode,
    adj: List[List[int]],
    game: GameInput,
    rng: random.Random,
    deadline: Optional[float] = None,
) -> int:
    """deadline が None なら ITERATIONS 回、指定されていればその時刻まで回す。回した回数を返す."""
    done = 0
    while done < ITERATIONS if deadline is None else time.perf_counter() < deadline:
        done += 1
        node = root
        path: List[MCTSNode] = [node]

        while not node.untried and node.children and node.state is not None:
            winner = terminal_winner(node.state, game)
            if winner is not None:
                break
            node = best_child(node)
            path.append(node)

        winner = None
        if node.state is not None:
            winner = terminal_winner(node.state, game)

        if winner is None and node.untried and node.state is not None:
            node = expand(node, adj, rng)
            path.append(node)

        if node.state is not None and winner is None:
            winner = rollout(node.state, adj, game, rng)
        elif winner is None:
            winner = 0

        for n in path:
            n.visits += 1
            # ノード n の勝率は「n へ進む手を指した人」（= n で次に指す人の相手）から見たもの。
            # 親は子の勝率で手を選ぶので、こう数えると「自分の勝率が高い手」を選べる
            if n.state is not None and winner == 1 - n.state.player:
                n.wins += 1.0
    return done


def select_move(root: MCTSNode, adj: List[List[int]]) -> int:
    if not root.children:
        return adj[root.state.node][0]  # type: ignore[union-attr]
    return max(root.children, key=lambda m: root.children[m].visits)


def play_game(game: GameInput, rng: random.Random, time_per_move: Optional[float] = None) -> Tuple[List[int], int]:
    adj = build_adjacency(game)
    state = GameState(node=game.start, player=0)
    log: List[int] = []
    total_iters = 0

    for _ in range(MAX_TURNS):
        winner = terminal_winner(state, game)
        if winner is not None:
            break
        moves = adj[state.node]
        if not moves:
            break

        root = MCTSNode(state=state, untried=list(moves))
        deadline = None if time_per_move is None else time.perf_counter() + time_per_move
        total_iters += mcts(root, adj, game, rng, deadline)
        mv = select_move(root, adj)
        log.append(mv)
        state = apply_move(state, mv)

    return log, total_iters


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--time-per-move", type=float, default=None, help="1手あたりの秒数（省略時は ITERATIONS 回）")
    args = parser.parse_args()
    rng = random.Random(42)
    game = read_game(sys.stdin)
    moves, total_iters = play_game(game, rng, args.time_per_move)
    print(f"mcts moves={len(moves)} path={' '.join(map(str, moves))}", file=sys.stderr)
    print(f"mcts iterations={total_iters}", file=sys.stderr)
    for m in moves:
        print(m)


if __name__ == "__main__":
    main()
