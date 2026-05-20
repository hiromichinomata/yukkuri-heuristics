// go/ch13/union_find.go
package main

import (
	"fmt"
	"time"
)

type UnionFind struct {
	parent []int
	rank   []int
}

func NewUnionFind(n int) *UnionFind {
	p := make([]int, n)
	for i := range p {
		p[i] = i
	}
	return &UnionFind{parent: p, rank: make([]int, n)}
}

func (uf *UnionFind) Find(x int) int {
	for uf.parent[x] != x {
		uf.parent[x] = uf.parent[uf.parent[x]]
		x = uf.parent[x]
	}
	return x
}

func (uf *UnionFind) Unite(a, b int) bool {
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

func naiveComponents(n int, edges [][2]int) int {
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
	for _, e := range edges {
		ru, rv := find(e[0]), find(e[1])
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

func benchmark() {
	n, m := 5000, 20000
	edges := make([][2]int, m)
	for i := 0; i < m; i++ {
		edges[i] = [2]int{i % n, (i*17 + 3) % n}
	}

	start := time.Now()
	for t := 0; t < 50; t++ {
		naiveComponents(n, edges)
	}
	naiveMs := time.Since(start).Seconds() * 1000 / 50

	start = time.Now()
	for t := 0; t < 50; t++ {
		uf := NewUnionFind(n)
		for _, e := range edges {
			uf.Unite(e[0], e[1])
		}
		uf.Find(0)
	}
	ufMs := time.Since(start).Seconds() * 1000 / 50

	fmt.Printf("n=%d unions=%d\n", n, m)
	fmt.Printf("naive_rebuild_ms=%.2f\n", naiveMs)
	fmt.Printf("union_find_ms=%.2f\n", ufMs)
	fmt.Printf("speedup=%.1fx\n", naiveMs/max(ufMs, 1e-9))
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func main() {
	benchmark()
}
