// go/ch06/two_opt.go
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

func twoOpt(pts []Point, tour []int) []int {
	n := len(tour)
	improved := true
	for improved {
		improved = false
		for i := 0; i < n; i++ {
			limit := n
			if i == 0 {
				limit = n - 1
			}
			for k := i + 2; k < limit; k++ {
				a, b := tour[i], tour[(i+1)%n]
				c, d := tour[k], tour[(k+1)%n]
				before := edgeDist(pts, a, b) + edgeDist(pts, c, d)
				after := edgeDist(pts, a, c) + edgeDist(pts, b, d)
				if after+1e-9 < before {
					reverseSegment(tour, i+1, k)
					improved = true
				}
			}
		}
	}
	return tour
}

func reverseSegment(tour []int, lo, hi int) {
	for lo < hi {
		tour[lo], tour[hi] = tour[hi], tour[lo]
		lo++
		hi--
	}
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
	tour = twoOpt(pts, tour)
	after := tourLength(pts, tour)
	fmt.Print("tour:")
	for _, i := range tour {
		fmt.Printf(" %d", i)
	}
	fmt.Println()
	fmt.Printf("n=%d before=%.2f after=%.2f\n", len(pts), before, after)
}
