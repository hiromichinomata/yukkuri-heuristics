// go/ch19/mcts_toy.go
package main

import (
	"bufio"
	"fmt"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

const (
	exploration = 1.41
	iterations  = 300
	maxTurns    = 16
)

type GameInput struct {
	Nodes    int
	Edges    [][2]int
	Start    int
	Terminal int
}

type GameState struct {
	Node   int
	Player int
}

type MCTSNode struct {
	Move     int
	HasMove  bool
	State    GameState
	HasState bool
	Parent   *MCTSNode
	Children map[int]*MCTSNode
	Untried  []int
	Visits   int
	Wins     float64
}

func readGame(r *bufio.Reader) (GameInput, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return GameInput{}, err
	}
	parts := parseInts(strings.TrimSpace(line))
	nodes, m := parts[0], parts[1]
	edges := make([][2]int, m)
	for i := 0; i < m; i++ {
		line, err = r.ReadString('\n')
		if err != nil {
			return GameInput{}, err
		}
		p := parseInts(strings.TrimSpace(line))
		edges[i] = [2]int{p[0], p[1]}
	}
	line, err = r.ReadString('\n')
	if err != nil {
		return GameInput{}, err
	}
	start, _ := strconv.Atoi(strings.TrimSpace(line))
	return GameInput{nodes, edges, start, 3}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func buildAdjacency(game GameInput) [][]int {
	adj := make([][]int, game.Nodes)
	for _, e := range game.Edges {
		adj[e[0]] = append(adj[e[0]], e[1])
		adj[e[1]] = append(adj[e[1]], e[0])
	}
	return adj
}

func terminalWinner(state GameState, game GameInput) (int, bool) {
	if state.Node == game.Terminal {
		return state.Player, true
	}
	return 0, false
}

func applyMove(state GameState, nxt int) GameState {
	return GameState{nxt, 1 - state.Player}
}

func rollout(state GameState, adj [][]int, game GameInput, rng *rand.Rand) int {
	cur := state
	for i := 0; i < game.Nodes*4; i++ {
		if w, ok := terminalWinner(cur, game); ok {
			return w
		}
		moves := adj[cur.Node]
		if len(moves) == 0 {
			return 1 - cur.Player
		}
		cur = applyMove(cur, moves[rng.Intn(len(moves))])
	}
	return 1 - cur.Player
}

func ucb1(parentVisits int, child *MCTSNode) float64 {
	if child.Visits == 0 {
		return math.Inf(1)
	}
	return child.Wins/float64(child.Visits) + exploration*math.Sqrt(math.Log(float64(parentVisits))/float64(child.Visits))
}

func expand(node *MCTSNode, adj [][]int, rng *rand.Rand) *MCTSNode {
	idx := rng.Intn(len(node.Untried))
	move := node.Untried[idx]
	node.Untried = append(node.Untried[:idx], node.Untried[idx+1:]...)
	childState := applyMove(node.State, move)
	child := &MCTSNode{
		Move: move, HasMove: true,
		State: childState, HasState: true,
		Parent: node,
		Children: map[int]*MCTSNode{},
		Untried:  append([]int{}, adj[childState.Node]...),
	}
	node.Children[move] = child
	return child
}

func bestChild(node *MCTSNode) *MCTSNode {
	var best *MCTSNode
	bestScore := -1.0
	for _, c := range node.Children {
		s := ucb1(node.Visits, c)
		if best == nil || s > bestScore {
			best = c
			bestScore = s
		}
	}
	return best
}

func mcts(root *MCTSNode, adj [][]int, game GameInput, rng *rand.Rand) {
	for it := 0; it < iterations; it++ {
		node := root
		path := []*MCTSNode{node}

		for len(node.Untried) == 0 && len(node.Children) > 0 && node.HasState {
			if _, ok := terminalWinner(node.State, game); ok {
				break
			}
			node = bestChild(node)
			path = append(path, node)
		}

		winner := -1
		if node.HasState {
			if w, ok := terminalWinner(node.State, game); ok {
				winner = w
			}
		}

		if winner < 0 && len(node.Untried) > 0 && node.HasState {
			node = expand(node, adj, rng)
			path = append(path, node)
		}

		if winner < 0 && node.HasState {
			winner = rollout(node.State, adj, game, rng)
		} else if winner < 0 {
			winner = 0
		}

		for _, n := range path {
			n.Visits++
			if n.HasState && winner == n.State.Player {
				n.Wins++
			}
		}
	}
}

func selectMove(root *MCTSNode, adj [][]int) int {
	if len(root.Children) == 0 {
		return adj[root.State.Node][0]
	}
	bestMove := -1
	bestVisits := -1
	for m, c := range root.Children {
		if c.Visits > bestVisits {
			bestVisits = c.Visits
			bestMove = m
		}
	}
	return bestMove
}

func playGame(game GameInput, rng *rand.Rand) []int {
	adj := buildAdjacency(game)
	state := GameState{game.Start, 0}
	var log []int

	for turn := 0; turn < maxTurns; turn++ {
		if _, ok := terminalWinner(state, game); ok {
			break
		}
		moves := adj[state.Node]
		if len(moves) == 0 {
			break
		}
		root := &MCTSNode{
			State: state, HasState: true,
			Children: map[int]*MCTSNode{},
			Untried:  append([]int{}, moves...),
		}
		mcts(root, adj, game, rng)
		mv := selectMove(root, adj)
		log = append(log, mv)
		state = applyMove(state, mv)
	}
	return log
}

func main() {
	rng := rand.New(rand.NewSource(42))
	game, err := readGame(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	moves := playGame(game, rng)
	fmt.Fprintf(os.Stderr, "mcts moves=%d path=", len(moves))
	for i, m := range moves {
		if i > 0 {
			fmt.Fprint(os.Stderr, " ")
		}
		fmt.Fprint(os.Stderr, m)
	}
	fmt.Fprintln(os.Stderr)
	for _, m := range moves {
		fmt.Println(m)
	}
}
