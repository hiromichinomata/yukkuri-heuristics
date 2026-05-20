// go/ch05/greedy_delivery.go
package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

type Point struct {
	X, Y float64
}

func readProblem(sc *bufio.Scanner) (Point, []Point, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return Point{}, nil, err
	}
	p0 := strings.Fields(lines[0])
	dx, _ := strconv.ParseFloat(p0[0], 64)
	dy, _ := strconv.ParseFloat(p0[1], 64)
	n, _ := strconv.Atoi(lines[1])
	orders := make([]Point, n)
	for i := 0; i < n; i++ {
		p := strings.Fields(lines[i+2])
		x, _ := strconv.ParseFloat(p[0], 64)
		y, _ := strconv.ParseFloat(p[1], 64)
		orders[i] = Point{x, y}
	}
	return Point{dx, dy}, orders, nil
}

func dist(a, b Point) float64 {
	return math.Hypot(a.X-b.X, a.Y-b.Y)
}

func nearestNeighbor(depot Point, orders []Point) ([]int, float64) {
	unvisited := make(map[int]bool)
	for i := range orders {
		unvisited[i] = true
	}
	route := []int{}
	cur := depot
	total := 0.0
	for len(unvisited) > 0 {
		best := -1
		bestD := math.MaxFloat64
		for i := range unvisited {
			d := dist(cur, orders[i])
			if d < bestD {
				bestD = d
				best = i
			}
		}
		total += bestD
		route = append(route, best)
		cur = orders[best]
		delete(unvisited, best)
	}
	total += dist(cur, depot)
	return route, total
}

func main() {
	depot, orders, err := readProblem(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	route, total := nearestNeighbor(depot, orders)
	fmt.Print("route:")
	for _, i := range route {
		fmt.Printf(" %d", i)
	}
	fmt.Println()
	fmt.Printf("orders=%d distance=%.2f\n", len(orders), total)
}
