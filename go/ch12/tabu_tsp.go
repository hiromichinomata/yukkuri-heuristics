// go/ch12/tabu_tsp.go
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

func edgeDist(pts []Point, a, b int) float64 {
	return math.Hypot(pts[a].X-pts[b].X, pts[a].Y-pts[b].Y)
}

func reverseSegment(tour []int, lo, hi int) {
	for lo < hi {
		tour[lo], tour[hi] = tour[hi], tour[lo]
		lo++
		hi--
	}
}

func tabuSearch(pts []Point, tour []int, tabuTenure, maxIter int) ([]int, float64) {
	n := len(tour)
	best := append([]int(nil), tour...)
	bestLen := tourLength(pts, best)
	cur := append([]int(nil), tour...)
	curLen := bestLen
	tabu := make([][2]int, 0, tabuTenure)
	tabuSet := make(map[[2]int]bool)

	for iter := 0; iter < maxIter; iter++ {
		var bestMove *[3]float64
		for i := 0; i < n; i++ {
			limit := n
			if i == 0 {
				limit = n - 1
			}
			for k := i + 2; k < limit; k++ {
				a, b := cur[i], cur[(i+1)%n]
				c, d := cur[k], cur[(k+1)%n]
				before := edgeDist(pts, a, b) + edgeDist(pts, c, d)
				after := edgeDist(pts, a, c) + edgeDist(pts, b, d)
				if after+1e-9 >= before {
					continue
				}
				move := [2]int{i, k}
				newLen := curLen - before + after
				if tabuSet[move] && newLen >= bestLen {
					continue
				}
				if bestMove == nil || newLen < (*bestMove)[0] {
					bestMove = &[3]float64{newLen, float64(i), float64(k)}
				}
			}
		}
		if bestMove == nil {
			break
		}
		i, k := int((*bestMove)[1]), int((*bestMove)[2])
		reverseSegment(cur, i+1, k)
		curLen = (*bestMove)[0]
		move := [2]int{i, k}
		if len(tabu) == tabuTenure {
			old := tabu[0]
			tabu = tabu[1:]
			delete(tabuSet, old)
		}
		tabu = append(tabu, move)
		tabuSet[move] = true
		if curLen < bestLen {
			bestLen = curLen
			copy(best, cur)
		}
		_ = iter
	}
	return best, bestLen
}

func main() {
	pts, err := readPoints(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rng := rand.New(rand.NewSource(42))
	tour := make([]int, len(pts))
	for i := range tour {
		tour[i] = i
	}
	rng.Shuffle(len(tour), func(i, j int) { tour[i], tour[j] = tour[j], tour[i] })
	before := tourLength(pts, tour)
	tour, after := tabuSearch(pts, tour, 12, 800)
	fmt.Print("tour:")
	for _, i := range tour {
		fmt.Printf(" %d", i)
	}
	fmt.Println()
	fmt.Printf("n=%d before=%.2f after=%.2f tabu_tenure=12\n", len(pts), before, after)
}
