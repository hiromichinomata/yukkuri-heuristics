// go/ch24/lns_tsp.go
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

type Point struct {
	X, Y float64
}

func readPoints(sc *bufio.Scanner) ([]Point, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	n, _ := strconv.Atoi(lines[0])
	pts := make([]Point, n)
	for i := 0; i < n; i++ {
		p := strings.Fields(lines[i+1])
		x, _ := strconv.ParseFloat(p[0], 64)
		y, _ := strconv.ParseFloat(p[1], 64)
		pts[i] = Point{x, y}
	}
	return pts, nil
}

func tourLength(pts []Point, tour []int) float64 {
	total := 0.0
	n := len(tour)
	for i := 0; i < n; i++ {
		a := pts[tour[i]]
		b := pts[tour[(i+1)%n]]
		total += math.Hypot(a.X-b.X, a.Y-b.Y)
	}
	return total
}

func edgeDist(pts []Point, i, j int) float64 {
	return math.Hypot(pts[i].X-pts[j].X, pts[i].Y-pts[j].Y)
}

func nearestNeighbor(pts []Point, start int, nodes []int) []int {
	remaining := make(map[int]bool)
	for _, v := range nodes {
		if v != start {
			remaining[v] = true
		}
	}
	tour := []int{start}
	cur := start
	for len(remaining) > 0 {
		best := -1
		bestD := math.MaxFloat64
		for v := range remaining {
			d := edgeDist(pts, cur, v)
			if d < bestD {
				bestD = d
				best = v
			}
		}
		delete(remaining, best)
		tour = append(tour, best)
		cur = best
	}
	return tour
}

func destroySegment(tour []int, rng *rand.Rand) ([]int, []int) {
	n := len(tour)
	if n <= 3 {
		return append([]int{}, tour...), nil
	}
	segLen := 1 + rng.Intn(max(1, n/3))
	start := rng.Intn(n)
	kept := append([]int{}, tour...)
	removed := make([]int, 0, segLen)
	for k := 0; k < segLen; k++ {
		idx := start % len(kept)
		removed = append(removed, kept[idx])
		kept = append(kept[:idx], kept[idx+1:]...)
		start++
	}
	return kept, removed
}

func repairTour(pts []Point, partial, removed []int) []int {
	if len(partial) == 0 {
		nodes := make([]int, len(pts))
		for i := range nodes {
			nodes[i] = i
		}
		return nearestNeighbor(pts, 0, nodes)
	}
	nodes := append(append([]int{}, partial...), removed...)
	return nearestNeighbor(pts, partial[0], nodes)
}

func lns(pts []Point, rng *rand.Rand, iterations int) ([]int, float64, float64) {
	n := len(pts)
	tour := make([]int, n)
	for i := range tour {
		tour[i] = i
	}
	rng.Shuffle(n, func(i, j int) { tour[i], tour[j] = tour[j], tour[i] })
	initial := tourLength(pts, tour)
	best := append([]int{}, tour...)
	bestLen := initial

	for it := 0; it < iterations; it++ {
		partial, removed := destroySegment(tour, rng)
		candidate := repairTour(pts, partial, removed)
		candLen := tourLength(pts, candidate)
		if candLen+1e-9 < tourLength(pts, tour) {
			tour = candidate
		}
		if candLen+1e-9 < bestLen {
			best = candidate
			bestLen = candLen
		}
		if (it+1)%50 == 0 {
			fmt.Fprintf(os.Stderr, "lns it=%d current=%.2f best=%.2f\n", it+1, tourLength(pts, tour), bestLen)
		}
	}
	return best, initial, bestLen
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func main() {
	pts, err := readPoints(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rng := rand.New(rand.NewSource(42))
	tour, before, after := lns(pts, rng, 200)
	fmt.Print("tour:")
	for _, i := range tour {
		fmt.Printf(" %d", i)
	}
	fmt.Println()
	fmt.Printf("n=%d before=%.2f after=%.2f improved=%.2f\n", len(pts), before, after, before-after)
}
