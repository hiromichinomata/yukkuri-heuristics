// go/ch04/ahc001_grow.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

const grid = 20

type Company struct {
	X, Y, R int
}

type Rect struct {
	A, B, C, D int
}

func (r Rect) area() int {
	return (r.C - r.A) * (r.D - r.B)
}

func readProblem(rd *bufio.Scanner) ([]Company, error) {
	var lines []string
	for rd.Scan() {
		lines = append(lines, rd.Text())
	}
	if err := rd.Err(); err != nil {
		return nil, err
	}
	n, _ := strconv.Atoi(lines[0])
	companies := make([]Company, n)
	for i := 0; i < n; i++ {
		p := strings.Fields(lines[i+1])
		x, _ := strconv.Atoi(p[0])
		y, _ := strconv.Atoi(p[1])
		r, _ := strconv.Atoi(p[2])
		companies[i] = Company{x, y, r}
	}
	return companies, nil
}

func overlapsPositive(r1, r2 Rect) bool {
	ix := min(r1.C, r2.C) - max(r1.A, r2.A)
	iy := min(r1.D, r2.D) - max(r1.B, r2.B)
	return ix > 0 && iy > 0
}

func canPlace(rect Rect, others []Rect) bool {
	if rect.A < 0 || rect.B < 0 || rect.C > grid || rect.D > grid {
		return false
	}
	if rect.area() <= 0 {
		return false
	}
	for _, o := range others {
		if overlapsPositive(rect, o) {
			return false
		}
	}
	return true
}

func growRect(c Company, others []Rect) Rect {
	rect := Rect{c.X, c.Y, c.X + 1, c.Y + 1}
	type delta struct{ da, db, dc, dd int }
	expansions := []delta{
		{-1, 0, 0, 0},
		{0, 0, 1, 0},
		{0, -1, 0, 0},
		{0, 0, 0, 1},
	}
	for rect.area() < c.R {
		bestGain := -1
		var best Rect
		found := false
		for _, e := range expansions {
			nxt := Rect{rect.A + e.da, rect.B + e.db, rect.C + e.dc, rect.D + e.dd}
			if !canPlace(nxt, others) {
				continue
			}
			gain := nxt.area() - rect.area()
			if !found || gain > bestGain {
				bestGain = gain
				best = nxt
				found = true
			}
		}
		if !found {
			break
		}
		rect = best
	}
	return rect
}

func solve(companies []Company) []Rect {
	rects := make([]Rect, 0, len(companies))
	for _, c := range companies {
		rects = append(rects, growRect(c, rects))
	}
	return rects
}

func main() {
	companies, err := readProblem(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rects := solve(companies)
	for _, r := range rects {
		fmt.Println(r.A, r.B, r.C, r.D)
	}
}
