// go/ch13/tabu_tsp.go
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

func edgeKey(u, v int) [2]int {
	if u < v {
		return [2]int{u, v}
	}
	return [2]int{v, u}
}

// tabuSearch は 2-opt 近傍のタブーサーチ（python/ch13/tabu_tsp.py と同じ）。
// 毎回「タブーでない手の中で最良の手」を、悪化する手でも採用する。
// タブー = 最近外した辺を tabuTenure 反復のあいだ付け直さないこと。過去最良を更新するならタブーでも採用（aspiration）。
func tabuSearch(pts []Point, tour []int, tabuTenure, maxIter int) ([]int, float64) {
	n := len(tour)
	best := append([]int(nil), tour...)
	bestLen := tourLength(pts, best)
	cur := append([]int(nil), tour...)
	curLen := bestLen
	tabuUntil := map[[2]int]int{} // 辺 → この反復まで付け直し禁止
	isTabu := func(e [2]int, it int) bool {
		until, ok := tabuUntil[e]
		return ok && until >= it
	}

	for it := 0; it < maxIter; it++ {
		found := false
		var bestNew float64
		bi, bk := -1, -1
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
				newLen := curLen - before + after // 悪化もありうる
				tabu := isTabu(edgeKey(a, c), it) || isTabu(edgeKey(b, d), it)
				if tabu && newLen >= bestLen-1e-9 {
					continue // タブーかつ最良更新にならない
				}
				if !found || newLen < bestNew {
					found, bestNew, bi, bk = true, newLen, i, k
				}
			}
		}
		if !found {
			break // 全部の手がタブー
		}
		a, b := cur[bi], cur[(bi+1)%n]
		c, d := cur[bk], cur[(bk+1)%n]
		reverseSegment(cur, bi+1, bk)
		curLen = bestNew
		tabuUntil[edgeKey(a, b)] = it + tabuTenure // 外した辺をしばらく付け直さない
		tabuUntil[edgeKey(c, d)] = it + tabuTenure
		if curLen < bestLen-1e-9 {
			bestLen = curLen
			copy(best, cur)
		}
	}
	return best, tourLength(pts, best)
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
