// go/ch28/benchmark.go
package main

import (
	"container/heap"
	"flag"
	"fmt"
	"os"
	"time"
)

const (
	gridN  = 50
	repeat = 400
	inf    = 1_000_000_000
)

type cell struct {
	d, r, c int
}

type pq []cell

func (h pq) Len() int            { return len(h) }
func (h pq) Less(i, j int) bool   { return h[i].d < h[j].d }
func (h pq) Swap(i, j int)        { h[i], h[j] = h[j], h[i] }
func (h *pq) Push(x interface{}) { *h = append(*h, x.(cell)) }
func (h *pq) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

func buildGrid(n int) [][]int {
	grid := make([][]int, n)
	for r := 0; r < n; r++ {
		grid[r] = make([]int, n)
		for c := 0; c < n; c++ {
			if (r+c)%7 == 0 {
				grid[r][c] = 1
			}
		}
	}
	grid[0][0] = 0
	grid[n-1][n-1] = 0
	return grid
}

func dijkstra(grid [][]int, sr, sc, tr, tc int) int {
	n := len(grid)
	dist := make([][]int, n)
	for i := range dist {
		dist[i] = make([]int, n)
		for j := range dist[i] {
			dist[i][j] = inf
		}
	}
	dist[sr][sc] = 0
	h := &pq{{0, sr, sc}}
	heap.Init(h)
	dirs := [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	for h.Len() > 0 {
		cur := heap.Pop(h).(cell)
		d, r, c := cur.d, cur.r, cur.c
		if d != dist[r][c] {
			continue
		}
		if r == tr && c == tc {
			return d
		}
		for _, dc := range dirs {
			nr, nc := r+dc[0], c+dc[1]
			if nr < 0 || nc < 0 || nr >= n || nc >= n {
				continue
			}
			if grid[nr][nc] == 1 {
				continue
			}
			nd := d + 1 + grid[nr][nc]
			if nd < dist[nr][nc] {
				dist[nr][nc] = nd
				heap.Push(h, cell{nd, nr, nc})
			}
		}
	}
	return inf
}

func runBenchmark() (float64, int) {
	grid := buildGrid(gridN)
	tr, tc := gridN-1, gridN-1
	checksum := 0
	start := time.Now()
	for rep := 0; rep < repeat; rep++ {
		for sr := 0; sr < gridN; sr += 5 {
			for sc := 0; sc < gridN; sc += 5 {
				if grid[sr][sc] == 1 {
					continue
				}
				checksum ^= dijkstra(grid, sr, sc, tr, tc)
			}
		}
	}
	elapsed := time.Since(start).Seconds()
	return elapsed, checksum
}

func main() {
	timingOnly := flag.Bool("timing-only", false, "print BENCHMARK_SEC/CHECKSUM to stderr and exit")
	flag.Parse()

	elapsed, checksum := runBenchmark()
	fmt.Fprintf(os.Stderr, "BENCHMARK_SEC=%.6f\n", elapsed)
	fmt.Fprintf(os.Stderr, "BENCHMARK_CHECKSUM=%d\n", checksum)
	if !*timingOnly {
		fmt.Fprintf(os.Stderr, "go: %.6fs checksum=%d\n", elapsed, checksum)
		fmt.Fprintf(os.Stderr, "hint: run python/ch28/benchmark.py for python/go speedup\n")
	}
}
