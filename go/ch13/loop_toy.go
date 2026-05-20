// go/ch13/loop_toy.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

type loopUF struct {
	parent []int
	rank   []int
}

func newLoopUF(n int) *loopUF {
	p := make([]int, n)
	for i := range p {
		p[i] = i
	}
	return &loopUF{parent: p, rank: make([]int, n)}
}

func (uf *loopUF) Find(x int) int {
	for uf.parent[x] != x {
		uf.parent[x] = uf.parent[uf.parent[x]]
		x = uf.parent[x]
	}
	return x
}

func (uf *loopUF) Unite(a, b int) bool {
	ra, rb := uf.Find(a), uf.Find(b)
	if ra == rb {
		return false
	}
	if uf.rank[ra] < uf.rank[rb] {
		ra, rb = rb, ra
	}
	uf.parent[rb] = ra
	if uf.rank[ra] == uf.rank[rb] {
		uf.rank[ra]++
	}
	return true
}

func readGrid(sc *bufio.Scanner) (int, int, []string, error) {
	sc.Scan()
	p := strings.Fields(sc.Text())
	h, _ := strconv.Atoi(p[0])
	w, _ := strconv.Atoi(p[1])
	grid := make([]string, h)
	for i := 0; i < h; i++ {
		sc.Scan()
		grid[i] = sc.Text()
	}
	return h, w, grid, sc.Err()
}

func cellIndex(r, c, w int) int {
	return r*w + c
}

func gridNeighbors(r, c, h, w int) [][2]int {
	var out [][2]int
	if r > 0 {
		out = append(out, [2]int{r - 1, c})
	}
	if r+1 < h {
		out = append(out, [2]int{r + 1, c})
	}
	if c > 0 {
		out = append(out, [2]int{r, c - 1})
	}
	if c+1 < w {
		out = append(out, [2]int{r, c + 1})
	}
	return out
}

func fullRecompute(h, w int, edges map[[2]int]bool) int {
	n := h * w
	parent := make([]int, n)
	for i := range parent {
		parent[i] = i
	}
	find := func(x int) int {
		for parent[x] != x {
			x = parent[x]
		}
		return x
	}
	for k := range edges {
		ru, rv := find(k[0]), find(k[1])
		if ru != rv {
			parent[rv] = ru
		}
	}
	roots := make(map[int]bool)
	for i := 0; i < n; i++ {
		roots[find(i)] = true
	}
	return len(roots)
}

func greedyLoop(h, w int, grid []string, useUF bool) (int, map[[2]int]bool) {
	edges := make(map[[2]int]bool)
	uf := newLoopUF(h * w)
	placed := 0
	for r := 0; r < h; r++ {
		for c := 0; c < w; c++ {
			if grid[r][c] == '#' {
				continue
			}
			here := cellIndex(r, c, w)
			for _, nb := range gridNeighbors(r, c, h, w) {
				nr, nc := nb[0], nb[1]
				if grid[nr][nc] == '#' {
					continue
				}
				if nr < r || (nr == r && nc < c) {
					continue
				}
				there := cellIndex(nr, nc, w)
				key := [2]int{here, there}
				if here > there {
					key = [2]int{there, here}
				}
				if useUF {
					if uf.Unite(here, there) {
						edges[key] = true
						placed++
					}
				} else {
					trial := make(map[[2]int]bool)
					for k := range edges {
						trial[k] = true
					}
					trial[key] = true
					comps := fullRecompute(h, w, trial)
					if comps <= h*w-len(trial)+1 {
						edges[key] = true
						placed++
					}
				}
			}
		}
	}
	return placed, edges
}

func benchmarkConnectivity(h, w int, grid []string, trials int) {
	start := time.Now()
	for t := 0; t < trials; t++ {
		greedyLoop(h, w, grid, false)
	}
	naiveMs := time.Since(start).Seconds() * 1000

	start = time.Now()
	for t := 0; t < trials; t++ {
		greedyLoop(h, w, grid, true)
	}
	ufMs := time.Since(start).Seconds() * 1000

	fmt.Printf("connectivity_trials=%d\n", trials)
	fmt.Printf("full_recompute_ms=%.2f\n", naiveMs)
	fmt.Printf("union_find_ms=%.2f\n", ufMs)
	fmt.Printf("speedup=%.1fx\n", naiveMs/max(ufMs, 1e-9))
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	h, w, grid, err := readGrid(sc)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	placed, edges := greedyLoop(h, w, grid, true)
	comps := fullRecompute(h, w, edges)
	fmt.Printf("grid=%dx%d edges=%d placed=%d components=%d\n", h, w, len(edges), placed, comps)
	benchmarkConnectivity(h, w, grid, 80)
}
