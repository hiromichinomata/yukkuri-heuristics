// go/ch15/assignment_relax.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func readCost(sc *bufio.Scanner) (int, [][]int, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return 0, nil, err
	}
	n, _ := strconv.Atoi(lines[0])
	cost := make([][]int, n)
	for i := 0; i < n; i++ {
		row := strings.Fields(lines[i+1])
		cost[i] = make([]int, n)
		for j, s := range row {
			cost[i][j], _ = strconv.Atoi(s)
		}
	}
	return n, cost, nil
}

type fracEntry struct {
	c, i, j int
}

func fractionalRelaxation(cost [][]int) ([][]float64, float64) {
	n := len(cost)
	var entries []fracEntry
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			entries = append(entries, fracEntry{cost[i][j], i, j})
		}
	}
	sort.Slice(entries, func(a, b int) bool { return entries[a].c < entries[b].c })
	rowRem := make([]float64, n)
	colRem := make([]float64, n)
	for i := range rowRem {
		rowRem[i], colRem[i] = 1, 1
	}
	x := make([][]float64, n)
	for i := range x {
		x[i] = make([]float64, n)
	}
	total := 0.0
	for _, e := range entries {
		val := rowRem[e.i]
		if colRem[e.j] < val {
			val = colRem[e.j]
		}
		if val <= 0 {
			continue
		}
		x[e.i][e.j] = val
		rowRem[e.i] -= val
		colRem[e.j] -= val
		total += float64(e.c) * val
	}
	return x, total
}

type roundItem struct {
	frac float64
	c    int
	i, j int
}

func roundAssignment(cost [][]int, frac [][]float64) ([]int, int) {
	n := len(cost)
	var items []roundItem
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			items = append(items, roundItem{frac[i][j], cost[i][j], i, j})
		}
	}
	sort.Slice(items, func(a, b int) bool { return items[a].frac > items[b].frac })
	assign := make([]int, n)
	for i := range assign {
		assign[i] = -1
	}
	usedCol := make([]bool, n)
	total := 0
	for _, it := range items {
		if assign[it.i] != -1 || usedCol[it.j] {
			continue
		}
		assign[it.i] = it.j
		usedCol[it.j] = true
		total += it.c
	}
	return assign, total
}

func permCost(cost [][]int, perm []int) int {
	s := 0
	for i, j := range perm {
		s += cost[i][j]
	}
	return s
}

func bruteOptimal(cost [][]int) ([]int, int) {
	n := len(cost)
	perm := make([]int, n)
	for i := range perm {
		perm[i] = i
	}
	best := append([]int(nil), perm...)
	bestVal := permCost(cost, perm)
	var dfs func(int)
	dfs = func(pos int) {
		if pos == n {
			v := permCost(cost, perm)
			if v < bestVal {
				bestVal = v
				copy(best, perm)
			}
			return
		}
		for j := pos; j < n; j++ {
			perm[pos], perm[j] = perm[j], perm[pos]
			dfs(pos + 1)
			perm[pos], perm[j] = perm[j], perm[pos]
		}
	}
	dfs(0)
	return best, bestVal
}

func main() {
	_, cost, err := readCost(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	n := len(cost)
	frac, fracCost := fractionalRelaxation(cost)
	assign, rounded := roundAssignment(cost, frac)
	opt, optCost := bruteOptimal(cost)
	gap := rounded - optCost
	fmt.Printf("fractional_cost %.2f\n", fracCost)
	fmt.Printf("rounded_assign %v cost %d\n", assign, rounded)
	fmt.Printf("optimal_assign %v cost %d\n", opt, optCost)
	fmt.Printf("n=%d gap=%d ratio=%.3f\n", n, gap, float64(rounded)/float64(max(optCost, 1)))
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
