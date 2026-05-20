// go/ch04/score_ahc001.go
package main

import (
	"bufio"
	"fmt"
	"io"
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

func readAll(rd io.Reader) ([]Company, []Rect, error) {
	sc := bufio.NewScanner(rd)
	var lines []string
	for sc.Scan() {
		if strings.TrimSpace(sc.Text()) != "" {
			lines = append(lines, sc.Text())
		}
	}
	if err := sc.Err(); err != nil {
		return nil, nil, err
	}
	idx := 0
	n, _ := strconv.Atoi(lines[idx])
	idx++
	companies := make([]Company, n)
	for i := 0; i < n; i++ {
		p := strings.Fields(lines[idx])
		idx++
		x, _ := strconv.Atoi(p[0])
		y, _ := strconv.Atoi(p[1])
		r, _ := strconv.Atoi(p[2])
		companies[i] = Company{x, y, r}
	}
	rects := make([]Rect, n)
	for i := 0; i < n; i++ {
		p := strings.Fields(lines[idx])
		idx++
		a, _ := strconv.Atoi(p[0])
		b, _ := strconv.Atoi(p[1])
		c, _ := strconv.Atoi(p[2])
		d, _ := strconv.Atoi(p[3])
		rects[i] = Rect{a, b, c, d}
	}
	return companies, rects, nil
}

func validRect(r Rect) bool {
	return r.A >= 0 && r.B >= 0 && r.C <= grid && r.D <= grid &&
		r.A < r.C && r.B < r.D && r.area() > 0
}

func contains(rect Rect, x, y int) bool {
	return rect.A <= x && float64(x)+0.5 < float64(rect.C) &&
		rect.B <= y && float64(y)+0.5 < float64(rect.D)
}

func overlapsPositive(r1, r2 Rect) bool {
	ix := min(r1.C, r2.C) - max(r1.A, r2.A)
	iy := min(r1.D, r2.D) - max(r1.B, r2.B)
	return ix > 0 && iy > 0
}

func companyScore(c Company, rect Rect) int {
	if !contains(rect, c.X, c.Y) {
		return 0
	}
	s := rect.area()
	if s <= 0 || c.R <= 0 {
		return 0
	}
	return int(int64(c.R) * int64(min(s, c.R)) / int64(max(s, c.R)))
}

func scoreSolution(companies []Company, rects []Rect) (int, bool, string) {
	n := len(companies)
	if len(rects) != n {
		return 0, false, fmt.Sprintf("rect count %d != %d", len(rects), n)
	}
	for i, rect := range rects {
		if !validRect(rect) {
			return 0, false, fmt.Sprintf("invalid rect %d", i)
		}
	}
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			if overlapsPositive(rects[i], rects[j]) {
				return 0, false, fmt.Sprintf("overlap %d and %d", i, j)
			}
		}
	}
	total := 0
	for i := range companies {
		total += companyScore(companies[i], rects[i])
	}
	return total, true, "ok"
}

func main() {
	companies, rects, err := readAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	total, ok, msg := scoreSolution(companies, rects)
	fmt.Println(total)
	if !ok {
		fmt.Fprintln(os.Stderr, msg)
		os.Exit(1)
	}
	fmt.Fprintf(os.Stderr, "companies=%d %s\n", len(companies), msg)
}
