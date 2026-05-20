// go/ch09/beam_fill.go
package main

import (
	"bufio"
	"container/heap"
	"fmt"
	"os"
	"strconv"
	"strings"
)

const beamWidth = 80

type dir struct {
	dr, dc int
	ch     byte
}

var dirs = []dir{{-1, 0, 'U'}, {1, 0, 'D'}, {0, -1, 'L'}, {0, 1, 'R'}}

type beamNode struct {
	priority int
	depth    int
	r, c     int
	visited  uint64
	score    int
	path     string
	index    int
}

type beamHeap []*beamNode

func (h beamHeap) Len() int           { return len(h) }
func (h beamHeap) Less(i, j int) bool { return h[i].priority < h[j].priority }
func (h beamHeap) Swap(i, j int) {
	h[i], h[j] = h[j], h[i]
	h[i].index = i
	h[j].index = j
}
func (h *beamHeap) Push(x interface{}) {
	n := len(*h)
	node := x.(*beamNode)
	node.index = n
	*h = append(*h, node)
}
func (h *beamHeap) Pop() interface{} {
	old := *h
	n := len(old)
	node := old[n-1]
	old[n-1] = nil
	node.index = -1
	*h = old[:n-1]
	return node
}

func readGrid(sc *bufio.Scanner) (int, [][]int) {
	sc.Scan()
	n, _ := strconv.Atoi(sc.Text())
	grid := make([][]int, n)
	for i := 0; i < n; i++ {
		sc.Scan()
		parts := strings.Fields(sc.Text())
		grid[i] = make([]int, n)
		for j, p := range parts {
			grid[i][j], _ = strconv.Atoi(p)
		}
	}
	return n, grid
}

func cellID(r, c, n int) int {
	return r*n + c
}

func heuristic(grid [][]int, n int, visited uint64, r, c int) int {
	est := 0
	for _, d := range dirs {
		nr, nc := r+d.dr, c+d.dc
		if nr < 0 || nr >= n || nc < 0 || nc >= n {
			continue
		}
		vid := cellID(nr, nc, n)
		if (visited>>vid)&1 == 0 {
			est += grid[nr][nc]
		}
	}
	return est
}

func beamSearch(grid [][]int, n, width int) (int, string) {
	startScore := grid[0][0]
	startVisited := uint64(1)
	beam := []*beamNode{{
		priority: -(startScore + heuristic(grid, n, startVisited, 0, 0)),
		depth:    1,
		visited:  startVisited,
		score:    startScore,
	}}

	bestScore := startScore
	bestPath := ""

	for step := 0; step < n*n-1; step++ {
		var candidates []*beamNode
		for _, node := range beam {
			for _, d := range dirs {
				nr, nc := node.r+d.dr, node.c+d.dc
				if nr < 0 || nr >= n || nc < 0 || nc >= n {
					continue
				}
				vid := cellID(nr, nc, n)
				if (node.visited>>vid)&1 != 0 {
					continue
				}
				newVisited := node.visited | (1 << vid)
				newScore := node.score + grid[nr][nc]
				newPath := node.path + string(d.ch)
				h := heuristic(grid, n, newVisited, nr, nc)
				candidates = append(candidates, &beamNode{
					priority: -(newScore + h),
					depth:    node.depth + 1,
					r:        nr,
					c:        nc,
					visited:  newVisited,
					score:    newScore,
					path:     newPath,
				})
				if newScore > bestScore {
					bestScore = newScore
					bestPath = newPath
				}
			}
		}
		if len(candidates) == 0 {
			break
		}
		h := &beamHeap{}
		heap.Init(h)
		limit := width
		if limit > len(candidates) {
			limit = len(candidates)
		}
		for _, c := range candidates {
			heap.Push(h, c)
			if h.Len() > limit {
				heap.Pop(h)
			}
		}
		beam = make([]*beamNode, h.Len())
		for i := len(beam) - 1; i >= 0; i-- {
			beam[i] = heap.Pop(h).(*beamNode)
		}
		_ = step
	}
	return bestScore, bestPath
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	n, grid := readGrid(sc)
	score, path := beamSearch(grid, n, beamWidth)
	fmt.Println(path)
	fmt.Fprintf(os.Stderr, "tiles=%d score=%d beam_width=%d\n", len(path)+1, score, beamWidth)
}
