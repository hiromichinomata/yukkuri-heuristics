// go/ch11/interactive_path.go
package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

type edge struct {
	u, v int
	w    float64
}

func edgeKey(u, v int) (int, int) {
	if u < v {
		return u, v
	}
	return v, u
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
	for cur := goal; cur != -1; cur = prev[cur] {
		path = append([]int{cur}, path...)
	}
	return dist[goal], path
}

type solver struct {
	n   int
	est map[[2]int]float64
}

func newSolver(n int, topo [][2]int) *solver {
	est := make(map[[2]int]float64)
	for _, e := range topo {
		est[[2]int{e[0], e[1]}] = 1.0
	}
	return &solver{n: n, est: est}
}

func (s *solver) adj() [][]struct {
	to int
	w  float64
} {
	adj := make([][]struct {
		to int
		w  float64
	}, s.n)
	for k, w := range s.est {
		u, v := k[0], k[1]
		adj[u] = append(adj[u], struct {
			to int
			w  float64
		}{v, w})
		adj[v] = append(adj[v], struct {
			to int
			w  float64
		}{u, w})
	}
	return adj
}

func updateEst(est map[[2]int]float64, path []int, predicted, actual float64) {
	if len(path) < 2 || predicted <= 0 {
		return
	}
	ratio := actual / predicted
	for i := 0; i < len(path)-1; i++ {
		u, v := edgeKey(path[i], path[i+1])
		k := [2]int{u, v}
		w := est[k]
		if w < 0.1 {
			w = 1.0
		}
		est[k] = math.Max(0.1, w*ratio)
	}
}

func loadSample(path string) (int, []edge, [][2]int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, nil, nil, err
	}
	lines := strings.Split(strings.TrimSpace(string(data)), "\n")
	n, m, _ := parse2(lines[0])
	edges := make([]edge, m)
	for i := 0; i < m; i++ {
		p := strings.Fields(lines[i+1])
		u, _ := strconv.Atoi(p[0])
		v, _ := strconv.Atoi(p[1])
		w, _ := strconv.ParseFloat(p[2], 64)
		edges[i] = edge{u, v, w}
	}
	q, _ := strconv.Atoi(lines[m+1])
	queries := make([][2]int, q)
	for j := 0; j < q; j++ {
		p := strings.Fields(lines[m+2+j])
		s, _ := strconv.Atoi(p[0])
		t, _ := strconv.Atoi(p[1])
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

func parse2(s string) (int, int, error) {
	p := strings.Fields(s)
	a, _ := strconv.Atoi(p[0])
	b, _ := strconv.Atoi(p[1])
	return a, b, nil
}

func runOffline(path string) error {
	n, edges, queries, err := loadSample(path)
	if err != nil {
		return err
	}
	trueAdj := buildAdj(n, edges)
	topo := make([][2]int, len(edges))
	for i, e := range edges {
		topo[i] = [2]int{e.u, e.v}
	}
	s := newSolver(n, topo)
	var sumPred, sumTrue float64
	for qi, q := range queries {
		pred, path := dijkstra(s.adj(), q[0], q[1])
		trueLen, truePath := dijkstra(trueAdj, q[0], q[1])
		updateEst(s.est, truePath, pred, trueLen)
		sumPred += pred
		sumTrue += trueLen
		fmt.Printf("query %d: s=%d t=%d pred=%.2f true=%.2f path=", qi, q[0], q[1], pred, trueLen)
		for _, v := range path {
			fmt.Printf("%d ", v)
		}
		fmt.Println()
	}
	fmt.Printf("queries=%d sum_pred=%.2f sum_true=%.2f\n", len(queries), sumPred, sumTrue)
	return nil
}

func runInteractive(sc *bufio.Scanner) error {
	sc.Scan()
	n, m, _ := parse2(sc.Text())
	topo := make([][2]int, m)
	for i := 0; i < m; i++ {
		sc.Scan()
		p := strings.Fields(sc.Text())
		u, _ := strconv.Atoi(p[0])
		v, _ := strconv.Atoi(p[1])
		topo[i] = [2]int{u, v}
	}
	sc.Scan()
	q, _ := strconv.Atoi(sc.Text())
	s := newSolver(n, topo)
	for qi := 0; qi < q; qi++ {
		sc.Scan()
		p := strings.Fields(sc.Text())
		sv, _ := strconv.Atoi(p[0])
		tv, _ := strconv.Atoi(p[1])
		pred, path := dijkstra(s.adj(), sv, tv)
		fmt.Printf("PATH %.4f %d", pred, len(path))
		for _, v := range path {
			fmt.Printf(" %d", v)
		}
		fmt.Println()
		sc.Scan()
		parts := strings.Fields(sc.Text())
		actual, _ := strconv.ParseFloat(parts[1], 64)
		k, _ := strconv.Atoi(parts[2])
		truePath := make([]int, k)
		for i := 0; i < k; i++ {
			truePath[i], _ = strconv.Atoi(parts[3+i])
		}
		updateEst(s.est, truePath, pred, actual)
		_ = qi
	}
	return nil
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--offline" {
		path := "data/ch11/sample.txt"
		if len(os.Args) > 2 {
			path = os.Args[2]
		}
		if err := runOffline(path); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}
	if err := runInteractive(bufio.NewScanner(os.Stdin)); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
