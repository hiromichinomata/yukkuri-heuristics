// go/ch12/solver.go
// AHC003「Shortest Path Queries」形式のソルバ（第12章）。python/ch12/solver.py と同じ処理。
//
// 辺の重みを推定値で持ち、
//  1. 推定重みでダイクストラして経路を出す（出したら必ず Flush）
//  2. 返ってきた「ノイズ付きの経路長」と予測の比で、通った辺の推定値を更新する
//
// を 1 クエリずつ繰り返す。
//
//	python python/ch12/local_judge.py --seed 1 -- go run go/ch12/solver.go
package main

import (
	"bufio"
	"container/heap"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

const (
	n            = 30
	initWeight   = 5000.0 // 辺の重みの初期推定（本番の重みは 1000〜9000 程度）
	learningRate = 0.5    // 予測とのずれをどれだけ反映するか（0〜1）
	wMin, wMax   = 1000.0, 9000.0
)

var moves = []struct {
	ch     byte
	di, dj int
}{{'U', -1, 0}, {'D', 1, 0}, {'L', 0, -1}, {'R', 0, 1}}

// Edge は (0=横 / 1=縦, i, j)
type Edge struct{ Kind, I, J int }

type Solver struct {
	h [n][n - 1]float64 // (i,j)-(i,j+1)
	v [n - 1][n]float64 // (i,j)-(i+1,j)
}

func newSolver() *Solver {
	s := &Solver{}
	for i := range s.h {
		for j := range s.h[i] {
			s.h[i][j] = initWeight
		}
	}
	for i := range s.v {
		for j := range s.v[i] {
			s.v[i][j] = initWeight
		}
	}
	return s
}

func edgeOf(i, j, ni, nj int) Edge {
	if i == ni {
		return Edge{0, i, min(j, nj)}
	}
	return Edge{1, min(i, ni), j}
}

func (s *Solver) weight(e Edge) *float64 {
	if e.Kind == 0 {
		return &s.h[e.I][e.J]
	}
	return &s.v[e.I][e.J]
}

// item はヒープの要素。Python の heapq と同じく (距離, i, j) の辞書順で取り出す
type item struct {
	d    float64
	i, j int
}
type pq []item

func (q pq) Len() int { return len(q) }
func (q pq) Less(a, b int) bool {
	if q[a].d != q[b].d {
		return q[a].d < q[b].d
	}
	if q[a].i != q[b].i {
		return q[a].i < q[b].i
	}
	return q[a].j < q[b].j
}
func (q pq) Swap(a, b int)       { q[a], q[b] = q[b], q[a] }
func (q *pq) Push(x interface{}) { *q = append(*q, x.(item)) }
func (q *pq) Pop() interface{} {
	old := *q
	x := old[len(old)-1]
	*q = old[:len(old)-1]
	return x
}

// shortestPath は推定重みでのダイクストラ。(経路文字列, 通る辺, 予測長)
func (s *Solver) shortestPath(si, sj, ti, tj int) (string, []Edge, float64) {
	var dist [n][n]float64
	type prevT struct {
		i, j int
		ch   byte
	}
	var prev [n][n]prevT
	for i := range dist {
		for j := range dist[i] {
			dist[i][j] = math.Inf(1)
		}
	}
	dist[si][sj] = 0
	q := &pq{{0, si, sj}}
	for q.Len() > 0 {
		cur := heap.Pop(q).(item)
		if cur.i == ti && cur.j == tj {
			break
		}
		if cur.d > dist[cur.i][cur.j] {
			continue
		}
		for _, m := range moves {
			ni, nj := cur.i+m.di, cur.j+m.dj
			if ni < 0 || ni >= n || nj < 0 || nj >= n {
				continue
			}
			nd := cur.d + *s.weight(edgeOf(cur.i, cur.j, ni, nj))
			if nd < dist[ni][nj] {
				dist[ni][nj] = nd
				prev[ni][nj] = prevT{cur.i, cur.j, m.ch}
				heap.Push(q, item{nd, ni, nj})
			}
		}
	}
	var path []byte
	var edges []Edge
	for i, j := ti, tj; i != si || j != sj; {
		p := prev[i][j]
		path = append(path, p.ch)
		edges = append(edges, edgeOf(p.i, p.j, i, j))
		i, j = p.i, p.j
	}
	for a, b := 0, len(path)-1; a < b; a, b = a+1, b-1 {
		path[a], path[b] = path[b], path[a]
	}
	return string(path), edges, dist[ti][tj]
}

// update は 観測長 / 予測長 の比で、通った辺をまとめて伸び縮みさせる
func (s *Solver) update(edges []Edge, predicted float64, observed int) {
	factor := 1.0 + learningRate*(float64(observed)/predicted-1.0)
	for _, e := range edges {
		w := s.weight(e)
		*w = math.Min(wMax, math.Max(wMin, *w*factor))
	}
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	solver := newSolver()
	for {
		line, err := in.ReadString('\n')
		f := strings.Fields(line)
		if len(f) < 4 {
			if err != nil {
				return // 入力の終わり
			}
			continue
		}
		var q [4]int
		for k := range q {
			q[k], _ = strconv.Atoi(f[k])
		}
		path, edges, predicted := solver.shortestPath(q[0], q[1], q[2], q[3])
		fmt.Fprintln(out, path)
		out.Flush() // Flush しないとジャッジが返事を待ったまま止まる
		line, _ = in.ReadString('\n')
		observed, _ := strconv.Atoi(strings.TrimSpace(line))
		solver.update(edges, predicted, observed)
	}
}
