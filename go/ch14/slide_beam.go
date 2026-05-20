// go/ch14/slide_beam.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func readState(sc *bufio.Scanner) (int, []int, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return 0, nil, err
	}
	n, _ := strconv.Atoi(lines[0])
	cells := make([]int, 0, n*n)
	for i := 1; i <= n; i++ {
		for _, s := range strings.Fields(lines[i]) {
			v, _ := strconv.Atoi(s)
			cells = append(cells, v)
		}
	}
	return n, cells, nil
}

func stateKey(cells []int) string {
	parts := make([]string, len(cells))
	for i, v := range cells {
		parts[i] = strconv.Itoa(v)
	}
	return strings.Join(parts, ",")
}

func goalState(n int) []int {
	g := make([]int, n*n)
	for i := 0; i < n*n-1; i++ {
		g[i] = i + 1
	}
	g[n*n-1] = 0
	return g
}

func manhattan(state, goal []int, n int) int {
	pos := make(map[int]int)
	for i, v := range goal {
		pos[v] = i
	}
	h := 0
	for i, v := range state {
		if v == 0 {
			continue
		}
		gi := pos[v]
		r, c := i/n, i%n
		gr, gc := gi/n, gi%n
		dr, dc := r-gr, c-gc
		if dr < 0 {
			dr = -dr
		}
		if dc < 0 {
			dc = -dc
		}
		h += dr + dc
	}
	return h
}

func blankPos(state []int) int {
	for i, v := range state {
		if v == 0 {
			return i
		}
	}
	return -1
}

func neighbors(state []int, n int) [][]int {
	b := blankPos(state)
	r, c := b/n, b%n
	dirs := [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	var out [][]int
	for _, d := range dirs {
		nr, nc := r+d[0], c+d[1]
		if nr < 0 || nr >= n || nc < 0 || nc >= n {
			continue
		}
		nb := nr*n + nc
		nxt := append([]int(nil), state...)
		nxt[b], nxt[nb] = nxt[nb], nxt[b]
		out = append(out, nxt)
	}
	return out
}

type beamNode struct {
	f, depth int
	state    []int
}

func beamSearch(start []int, n, width, maxDepth int) (bool, int, int) {
	goal := goalState(n)
	if stateKey(start) == stateKey(goal) {
		return true, 0, 1
	}
	beam := []beamNode{{manhattan(start, goal, n), 0, start}}
	visited := map[string]bool{stateKey(start): true}
	for depth := 1; depth <= maxDepth; depth++ {
		var candidates []beamNode
		for _, node := range beam {
			for _, nxt := range neighbors(node.state, n) {
				key := stateKey(nxt)
				if visited[key] {
					continue
				}
				visited[key] = true
				if key == stateKey(goal) {
					return true, depth, len(visited)
				}
				f := depth + manhattan(nxt, goal, n)
				candidates = append(candidates, beamNode{f, depth, nxt})
			}
		}
		if len(candidates) == 0 {
			return false, -1, len(visited)
		}
		if len(candidates) > width {
			for i := 0; i < len(candidates)-1; i++ {
				for j := i + 1; j < len(candidates); j++ {
					if candidates[j].f < candidates[i].f {
						candidates[i], candidates[j] = candidates[j], candidates[i]
					}
				}
			}
			candidates = candidates[:width]
		}
		beam = candidates
	}
	return false, -1, len(visited)
}

func main() {
	n, start, err := readState(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	solved, depth, explored := beamSearch(start, n, 100, 40)
	fmt.Printf("n=%d solved=%v depth=%d explored=%d beam_width=100\n", n, solved, depth, explored)
}
