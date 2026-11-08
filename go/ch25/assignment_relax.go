// go/ch25/assignment_relax.go
// 割当問題: 制約を外す緩和で下界を作り、修復 + 入れ替え山登りで整数解にする（第25章）。
// python/ch25/assignment_relax.py と同じ出力。
package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func readCost(sc *bufio.Scanner) ([][]int, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	n, _ := strconv.Atoi(strings.TrimSpace(lines[0]))
	cost := make([][]int, n)
	for i := 0; i < n; i++ {
		row := strings.Fields(lines[i+1])
		cost[i] = make([]int, n)
		for j, s := range row {
			cost[i][j], _ = strconv.Atoi(s)
		}
	}
	return cost, nil
}

func assignmentCost(cost [][]int, assign []int) int {
	total := 0
	for i, j := range assign {
		total += cost[i][j]
	}
	return total
}

// relaxedLowerBound は「各列に1人」を外した緩和。各行で最安の列を選ぶ（下界）
func relaxedLowerBound(cost [][]int) ([]int, int) {
	n := len(cost)
	choice := make([]int, n)
	for i := range cost {
		for j := 1; j < n; j++ {
			if cost[i][j] < cost[i][choice[i]] {
				choice[i] = j
			}
		}
	}
	return choice, assignmentCost(cost, choice)
}

// repair は後悔（2番目に安いコストとの差）の大きい行から、空いている最安の列を取らせる
func repair(cost [][]int) []int {
	n := len(cost)
	regret := func(i int) int {
		row := append([]int{}, cost[i]...)
		sort.Ints(row)
		if n > 1 {
			return row[1] - row[0]
		}
		return 0
	}
	order := make([]int, n)
	for i := range order {
		order[i] = i
	}
	sort.SliceStable(order, func(a, b int) bool { return regret(order[a]) > regret(order[b]) })
	assign := make([]int, n)
	used := make([]bool, n)
	for _, i := range order {
		best := -1
		for j := 0; j < n; j++ {
			if !used[j] && (best == -1 || cost[i][j] < cost[i][best]) {
				best = j
			}
		}
		assign[i] = best
		used[best] = true
	}
	return assign
}

// swapImprove は 2 行の割当を入れ替えて良くなる限り続ける山登り
func swapImprove(cost [][]int, assign []int) []int {
	assign = append([]int{}, assign...)
	n := len(assign)
	for improved := true; improved; {
		improved = false
		for i := 0; i < n; i++ {
			for k := i + 1; k < n; k++ {
				a, b := assign[i], assign[k]
				if cost[i][b]+cost[k][a] < cost[i][a]+cost[k][b] {
					assign[i], assign[k] = b, a
					improved = true
				}
			}
		}
	}
	return assign
}

// greedyByCost は比較用: コストの安い (i, j) から、行・列が空いていれば詰める
func greedyByCost(cost [][]int) []int {
	n := len(cost)
	type entry struct{ c, i, j int }
	var entries []entry
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			entries = append(entries, entry{cost[i][j], i, j})
		}
	}
	sort.Slice(entries, func(a, b int) bool { // Python の sorted((c, i, j)) と同じ順
		x, y := entries[a], entries[b]
		if x.c != y.c {
			return x.c < y.c
		}
		if x.i != y.i {
			return x.i < y.i
		}
		return x.j < y.j
	})
	assign := make([]int, n)
	for i := range assign {
		assign[i] = -1
	}
	used := make([]bool, n)
	for _, e := range entries {
		if assign[e.i] == -1 && !used[e.j] {
			assign[e.i] = e.j
			used[e.j] = true
		}
	}
	return assign
}

func bruteOptimal(cost [][]int) ([]int, int) {
	n := len(cost)
	perm := make([]int, n)
	for i := range perm {
		perm[i] = i
	}
	best, bestVal := append([]int{}, perm...), assignmentCost(cost, perm)
	var rec func(k int)
	rec = func(k int) { // 辞書順に全順列を試す（最初に見つかった最小を残す = Python の min と同じ）
		if k == n {
			if v := assignmentCost(cost, perm); v < bestVal {
				best, bestVal = append([]int{}, perm...), v
			}
			return
		}
		for i := k; i < n; i++ {
			// perm[k:] を辞書順に保つため、取り出して先頭に回す
			x := perm[i]
			copy(perm[k+1:i+1], perm[k:i])
			perm[k] = x
			rec(k + 1)
			copy(perm[k:i], perm[k+1:i+1])
			perm[i] = x
		}
	}
	rec(0)
	return best, bestVal
}

// pyList は Python の print(list) と同じ表記 [a, b, c] にする
func pyList(a []int) string {
	s := make([]string, len(a))
	for i, v := range a {
		s[i] = strconv.Itoa(v)
	}
	return "[" + strings.Join(s, ", ") + "]"
}

func main() {
	cost, err := readCost(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	relaxed, lb := relaxedLowerBound(cost)
	repaired := repair(cost)
	improved := swapImprove(cost, repaired)
	greedy := greedyByCost(cost)
	optimal, opt := bruteOptimal(cost)
	fmt.Println("lower_bound", lb, "relaxed_assign", pyList(relaxed))
	fmt.Println("repaired_assign", pyList(repaired), "cost", assignmentCost(cost, repaired))
	fmt.Println("improved_assign", pyList(improved), "cost", assignmentCost(cost, improved))
	fmt.Println("greedy_assign", pyList(greedy), "cost", assignmentCost(cost, greedy))
	fmt.Println("optimal_assign", pyList(optimal), "cost", opt)
	fmt.Printf("n=%d optimal is in [%d, %d]\n", len(cost), lb, assignmentCost(cost, improved))
}
