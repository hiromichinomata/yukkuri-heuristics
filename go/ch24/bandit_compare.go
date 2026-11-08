// go/ch24/bandit_compare.go
//
// AHC003 風の玩具で、経路選びの探索戦略を比べる（第24章）。
//
//	go run go/ch24/bandit_compare.go data/ch24/sample.txt
//	go run go/ch24/bandit_compare.go -rounds 5 -epsilon 0.3 data/ch24/sample.txt
//
// 各クエリで、ソルバは自分の推定で経路を選び、選んだ経路の長さ（ノイズ付き）だけを観測する。
// 後悔（regret）= 選んだ経路の真の長さ − 真の最短路長 を、seed を変えた trials 回の平均で比べる。
// 乱数は Go の math/rand なので、数値は Python 版と一致しない（傾向は同じ）。
package main

import (
	"bufio"
	"container/heap"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

const (
	initWeight    = 6.0 // 推定の初期値（真の重みは 1〜6。上限から始める = 悲観的な事前知識）
	learningRate  = 0.5 // 観測と予測のずれをどれだけ反映するか（第12章と同じ）
	noise         = 0.1 // 観測に掛かるノイズ（0.9〜1.1 倍）
	ucbC          = 1.0 // UCB1: 通った回数が少ない辺を、どれだけ短く見せるか
	thompsonSigma = 0.5 // Thompson: 推定のばらつきの大きさ（通るほど小さくなる）
)

var strategies = []string{"greedy", "epsilon_greedy", "ucb1", "thompson"}

type Edge struct{ U, V int }

type Graph struct {
	N     int
	Edges []Edge // 辺の順番を固定する（map の順番に頼らない）
	index map[Edge]int
}

func key(u, v int) Edge {
	if u < v {
		return Edge{u, v}
	}
	return Edge{v, u}
}

func loadSample(path string) (Graph, []float64, [][2]int, error) {
	f, err := os.Open(path)
	if err != nil {
		return Graph{}, nil, nil, err
	}
	defer f.Close()
	var lines []string
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		if strings.TrimSpace(sc.Text()) != "" {
			lines = append(lines, sc.Text())
		}
	}
	head := strings.Fields(lines[0])
	n, _ := strconv.Atoi(head[0])
	m, _ := strconv.Atoi(head[1])
	g := Graph{N: n, index: map[Edge]int{}}
	trueW := make([]float64, 0, m)
	for i := 1; i <= m; i++ {
		p := strings.Fields(lines[i])
		u, _ := strconv.Atoi(p[0])
		v, _ := strconv.Atoi(p[1])
		w, _ := strconv.ParseFloat(p[2], 64)
		g.index[key(u, v)] = len(g.Edges)
		g.Edges = append(g.Edges, key(u, v))
		trueW = append(trueW, w)
	}
	q, _ := strconv.Atoi(strings.TrimSpace(lines[1+m]))
	queries := make([][2]int, q)
	for i := 0; i < q; i++ {
		p := strings.Fields(lines[2+m+i])
		queries[i][0], _ = strconv.Atoi(p[0])
		queries[i][1], _ = strconv.Atoi(p[1])
	}
	return g, trueW, queries, nil
}

type item struct {
	d float64
	v int
}
type pq []item

func (h pq) Len() int            { return len(h) }
func (h pq) Less(i, j int) bool  { return h[i].d < h[j].d }
func (h pq) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *pq) Push(x interface{}) { *h = append(*h, x.(item)) }
func (h *pq) Pop() interface{} {
	old := *h
	x := old[len(old)-1]
	*h = old[:len(old)-1]
	return x
}

// dijkstra は重み w（辺の添字順）で start→goal の最短距離と、通る辺の添字を返す。
func dijkstra(g Graph, w []float64, start, goal int) (float64, []int) {
	type arc struct{ to, e int }
	adj := make([][]arc, g.N)
	for i, e := range g.Edges {
		adj[e.U] = append(adj[e.U], arc{e.V, i})
		adj[e.V] = append(adj[e.V], arc{e.U, i})
	}
	dist := make([]float64, g.N)
	prevEdge := make([]int, g.N)
	prevNode := make([]int, g.N)
	for i := range dist {
		dist[i] = math.Inf(1)
		prevNode[i] = -1
	}
	dist[start] = 0
	h := &pq{{0, start}}
	for h.Len() > 0 {
		it := heap.Pop(h).(item)
		if it.d > dist[it.v] {
			continue
		}
		if it.v == goal {
			break
		}
		for _, a := range adj[it.v] {
			if nd := it.d + w[a.e]; nd < dist[a.to] {
				dist[a.to] = nd
				prevNode[a.to] = it.v
				prevEdge[a.to] = a.e
				heap.Push(h, item{nd, a.to})
			}
		}
	}
	var edges []int
	for cur := goal; prevNode[cur] != -1; cur = prevNode[cur] {
		edges = append(edges, prevEdge[cur])
	}
	return dist[goal], edges
}

type Solver struct {
	g        Graph
	strategy string
	rng      *rand.Rand
	epsilon  float64
	est      []float64
	pulls    []int
	t        int
}

// planningWeight は経路を選ぶときに使う重み。探索したい辺ほど短く見せる。
func (s *Solver) planningWeight(i int) float64 {
	w := s.est[i]
	switch s.strategy {
	case "ucb1":
		// 通った回数が少ない辺ほど短く見せる（楽観）
		return w / (1 + ucbC*math.Sqrt(math.Log(float64(s.t+2))/float64(s.pulls[i]+1)))
	case "thompson":
		// 推定のまわりにばらつかせた値を引く。通った回数が少ない辺ほど大きくばらつく
		return w * math.Exp(s.rng.NormFloat64()*thompsonSigma/math.Sqrt(float64(s.pulls[i]+1)))
	}
	return w
}

func (s *Solver) choosePath(from, to int) []int {
	plan := make([]float64, len(s.est))
	random := s.strategy == "epsilon_greedy" && s.rng.Float64() < s.epsilon
	for i := range plan {
		if random {
			plan[i] = s.rng.Float64() // 確率 ε でランダムな経路
		} else {
			plan[i] = s.planningWeight(i)
		}
	}
	_, edges := dijkstra(s.g, plan, from, to)
	return edges
}

func (s *Solver) update(edges []int, observed float64) {
	predicted := 0.0
	for _, i := range edges {
		predicted += s.est[i]
	}
	factor := 1 + learningRate*(observed/predicted-1)
	for _, i := range edges {
		s.est[i] *= factor
		s.pulls[i]++
	}
	s.t++
}

// run は (後悔の合計, 一度も通らなかった辺の数) を返す。
func run(g Graph, trueW []float64, queries [][2]int, strategy string, seed int64, rounds int, epsilon float64) (float64, int) {
	s := &Solver{g: g, strategy: strategy, rng: rand.New(rand.NewSource(seed)), epsilon: epsilon,
		est: make([]float64, len(g.Edges)), pulls: make([]int, len(g.Edges))}
	for i := range s.est {
		s.est[i] = initWeight
	}
	noiseRng := rand.New(rand.NewSource(seed + 1_000_000)) // 観測ノイズは戦略と別の乱数
	regret := 0.0
	for r := 0; r < rounds; r++ {
		for _, q := range queries {
			edges := s.choosePath(q[0], q[1])
			trueLen := 0.0
			for _, i := range edges {
				trueLen += trueW[i]
			}
			best, _ := dijkstra(g, trueW, q[0], q[1])
			regret += trueLen - best
			s.update(edges, trueLen*(1-noise+2*noise*noiseRng.Float64()))
		}
	}
	untouched := 0
	for _, c := range s.pulls {
		if c == 0 {
			untouched++
		}
	}
	return regret, untouched
}

func main() {
	rounds := flag.Int("rounds", 50, "クエリ列を何周するか")
	trials := flag.Int("trials", 20, "seed を変えて何回平均するか")
	epsilon := flag.Float64("epsilon", 0.15, "ε-greedy でランダムな経路を試す確率")
	flag.Parse()
	path := "data/ch24/sample.txt"
	if flag.NArg() > 0 {
		path = flag.Arg(0)
	}
	g, trueW, queries, err := loadSample(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Fprintf(os.Stderr, "graph n=%d m=%d queries=%d rounds=%d trials=%d\n", g.N, len(g.Edges), len(queries), *rounds, *trials)
	bestName, bestRegret := "", math.Inf(1)
	for _, name := range strategies {
		sumRegret, sumUntouched := 0.0, 0
		for seed := 0; seed < *trials; seed++ {
			r, u := run(g, trueW, queries, name, int64(seed), *rounds, *epsilon)
			sumRegret += r
			sumUntouched += u
		}
		regret := sumRegret / float64(*trials)
		fmt.Fprintf(os.Stderr, "strategy=%s regret=%.2f untouched_edges=%.1f\n", name, regret, float64(sumUntouched)/float64(*trials))
		if regret < bestRegret {
			bestName, bestRegret = name, regret
		}
	}
	fmt.Fprintf(os.Stderr, "best=%s (smallest regret)\n", bestName)
}
