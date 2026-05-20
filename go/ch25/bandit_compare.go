// go/ch25/bandit_compare.go
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

type edge struct {
	u, v int
	w    float64
}

type EdgeStats struct {
	pulls     int
	rewardSum float64
	alpha     float64
	beta      float64
}

type BanditSolver struct {
	n          int
	topo       [][2]int
	strategy   string
	rng        *rand.Rand
	epsilon    float64
	est        map[[2]int]float64
	stats      map[[2]int]*EdgeStats
	totalPulls int
}

func edgeKey(u, v int) [2]int {
	if u < v {
		return [2]int{u, v}
	}
	return [2]int{v, u}
}

func loadSample(path string) (int, []edge, [][2]int, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, nil, nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return 0, nil, nil, err
	}
	p := strings.Fields(lines[0])
	n, _ := strconv.Atoi(p[0])
	m, _ := strconv.Atoi(p[1])
	edges := make([]edge, m)
	topo := make([][2]int, m)
	for i := 0; i < m; i++ {
		q := strings.Fields(lines[1+i])
		u, _ := strconv.Atoi(q[0])
		v, _ := strconv.Atoi(q[1])
		w, _ := strconv.ParseFloat(q[2], 64)
		edges[i] = edge{u, v, w}
		topo[i] = [2]int{u, v}
	}
	q, _ := strconv.Atoi(lines[1+m])
	queries := make([][2]int, q)
	for j := 0; j < q; j++ {
		qp := strings.Fields(lines[2+m+j])
		s, _ := strconv.Atoi(qp[0])
		t, _ := strconv.Atoi(qp[1])
		queries[j] = [2]int{s, t}
	}
	return n, edges, queries, nil
}

func buildAdj(n int, edges []edge) [][]struct {
	to int
	w  float64
} {
	adj := make([][]struct {
		to int
		w  float64
	}, n)
	for _, e := range edges {
		adj[e.u] = append(adj[e.u], struct {
			to int
			w  float64
		}{e.v, e.w})
		adj[e.v] = append(adj[e.v], struct {
			to int
			w  float64
		}{e.u, e.w})
	}
	return adj
}

func dijkstra(adj [][]struct {
	to int
	w  float64
}, start, goal int) (float64, []int) {
	n := len(adj)
	dist := make([]float64, n)
	prev := make([]int, n)
	used := make([]bool, n)
	for i := range dist {
		dist[i] = math.Inf(1)
		prev[i] = -1
	}
	dist[start] = 0
	for iter := 0; iter < n; iter++ {
		u := -1
		best := math.Inf(1)
		for i := 0; i < n; i++ {
			if !used[i] && dist[i] < best {
				best = dist[i]
				u = i
			}
		}
		if u == -1 {
			break
		}
		used[u] = true
		if u == goal {
			break
		}
		for _, e := range adj[u] {
			nd := dist[u] + e.w
			if nd < dist[e.to] {
				dist[e.to] = nd
				prev[e.to] = u
			}
		}
	}
	if dist[goal] == math.Inf(1) {
		return math.Inf(1), nil
	}
	path := []int{}
	cur := goal
	for cur != -1 {
		path = append([]int{cur}, path...)
		cur = prev[cur]
	}
	return dist[goal], path
}

func newBanditSolver(n int, topo [][2]int, strategy string, rng *rand.Rand) *BanditSolver {
	est := make(map[[2]int]float64)
	stats := make(map[[2]int]*EdgeStats)
	for _, e := range topo {
		k := edgeKey(e[0], e[1])
		est[k] = 1.0
		stats[k] = &EdgeStats{alpha: 1, beta: 1}
	}
	return &BanditSolver{
		n: n, topo: topo, strategy: strategy, rng: rng, epsilon: 0.15,
		est: est, stats: stats,
	}
}

func (s *BanditSolver) explorationBonus(key [2]int) float64 {
	st := s.stats[key]
	if st.pulls == 0 {
		return 2.0
	}
	switch s.strategy {
	case "ucb1":
		return 0.5 * math.Sqrt(math.Log(float64(s.totalPulls+1))/float64(st.pulls))
	case "thompson":
		sample := betaSample(s.rng, st.alpha, st.beta)
		mean := st.rewardSum / float64(st.pulls)
		return 0.8 * (sample - mean)
	case "epsilon_greedy":
		if s.rng.Float64() < s.epsilon {
			return 1.5
		}
	}
	return 0
}

func betaSample(rng *rand.Rand, alpha, beta float64) float64 {
	// 簡易: 平均 + 小ノイズ（本番は math/rand 以外でも可）
	return alpha/(alpha+beta) + (rng.Float64()-0.5)*0.2
}

func (s *BanditSolver) adj() [][]struct {
	to int
	w  float64
} {
	adj := make([][]struct {
		to int
		w  float64
	}, s.n)
	for k, w := range s.est {
		bonus := s.explorationBonus(k)
		adjW := w - bonus
		if adjW < 0.01 {
			adjW = 0.01
		}
		adj[k[0]] = append(adj[k[0]], struct {
			to int
			w  float64
		}{k[1], adjW})
		adj[k[1]] = append(adj[k[1]], struct {
			to int
			w  float64
		}{k[0], adjW})
	}
	return adj
}

func (s *BanditSolver) pickFocus(path []int) [2]int {
	var edges [][2]int
	for i := 0; i+1 < len(path); i++ {
		edges = append(edges, edgeKey(path[i], path[i+1]))
	}
	if len(edges) == 0 {
		for k := range s.est {
			return k
		}
	}
	bestK := edges[0]
	bestScore := -1.0
	for _, k := range edges {
		st := s.stats[k]
		score := 0.0
		switch s.strategy {
		case "ucb1":
			score = st.rewardSum/float64(max(1, st.pulls)) +
				math.Sqrt(2*math.Log(float64(s.totalPulls+1))/float64(max(1, st.pulls)))
		case "thompson":
			score = betaSample(s.rng, st.alpha, st.beta)
		default:
			score = st.rewardSum / float64(max(1, st.pulls))
			if s.rng.Float64() < s.epsilon {
				return k
			}
		}
		if score > bestScore {
			bestScore = score
			bestK = k
		}
	}
	return bestK
}

func (s *BanditSolver) updateEstimates(path []int, predicted, actual float64) {
	if len(path) < 2 || predicted <= 0 {
		return
	}
	ratio := actual / predicted
	for i := 0; i+1 < len(path); i++ {
		k := edgeKey(path[i], path[i+1])
		s.est[k] = math.Max(0.1, s.est[k]*ratio)
	}
	focus := s.pickFocus(path)
	err := math.Abs(actual-predicted) / math.Max(actual, 1)
	if err < 0 {
		err = 0
	}
	if err > 1 {
		err = 1
	}
	reward := 1.0 - err
	st := s.stats[focus]
	st.pulls++
	st.rewardSum += reward
	st.alpha += reward
	st.beta += 1.0 - reward
	s.totalPulls++
	s.est[focus] = math.Max(0.1, s.est[focus]*(0.9+0.2*reward))
}

func (s *BanditSolver) runOffline(trueAdj [][]struct {
	to int
	w  float64
}, queries [][2]int) (float64, float64) {
	totalPred, totalTrue := 0.0, 0.0
	for _, q := range queries {
		pred, _ := dijkstra(s.adj(), q[0], q[1])
		trueLen, truePath := dijkstra(trueAdj, q[0], q[1])
		s.updateEstimates(truePath, pred, trueLen)
		totalPred += pred
		totalTrue += trueLen
	}
	return totalPred, totalTrue
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func main() {
	path := "data/ch25/sample.txt"
	if len(os.Args) > 1 {
		path = os.Args[1]
	}
	n, edges, queries, err := loadSample(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	trueAdj := buildAdj(n, edges)
	topo := make([][2]int, len(edges))
	for i, e := range edges {
		topo[i] = [2]int{e.u, e.v}
	}
	rng := rand.New(rand.NewSource(42))
	fmt.Fprintf(os.Stderr, "graph n=%d m=%d queries=%d\n", n, len(edges), len(queries))

	bestName := ""
	bestGap := math.MaxFloat64
	for _, name := range []string{"ucb1", "thompson", "epsilon_greedy"} {
		solver := newBanditSolver(n, topo, name, rng)
		pred, true := solver.runOffline(trueAdj, queries)
		gap := pred - true
		fmt.Fprintf(os.Stderr, "strategy=%s sum_pred=%.4f sum_true=%.4f gap=%.4f\n",
			name, pred, true, gap)
		if gap < bestGap {
			bestGap = gap
			bestName = name
		}
	}
	fmt.Fprintf(os.Stderr, "best_gap=%s (smallest pred-true gap)\n", bestName)
}
