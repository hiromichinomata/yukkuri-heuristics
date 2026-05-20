// go/ch26/simple_vis.go
package main

import (
	"bufio"
	"flag"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

var cellChars = map[int]string{
	0: ".",
	1: "#",
	2: "S",
	3: "G",
}

type VisInput struct {
	N    int
	Grid [][]int
	Path [][2]int
}

func readVis(path string) (VisInput, error) {
	f, err := os.Open(path)
	if err != nil {
		return VisInput{}, err
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	var lines []string
	for sc.Scan() {
		t := strings.TrimSpace(sc.Text())
		if t != "" {
			lines = append(lines, t)
		}
	}
	if err := sc.Err(); err != nil {
		return VisInput{}, err
	}
	n, _ := strconv.Atoi(lines[0])
	grid := make([][]int, n)
	for i := 0; i < n; i++ {
		grid[i] = parseInts(lines[i+1])
	}
	pathLen, _ := strconv.Atoi(lines[n+1])
	route := make([][2]int, pathLen)
	for i := 0; i < pathLen; i++ {
		p := parseInts(lines[n+2+i])
		route[i] = [2]int{p[0], p[1]}
	}
	return VisInput{n, grid, route}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func overlayPath(grid [][]int, path [][2]int) [][]string {
	n := len(grid)
	view := make([][]string, n)
	for r := 0; r < n; r++ {
		view[r] = make([]string, n)
		for c := 0; c < n; c++ {
			ch, ok := cellChars[grid[r][c]]
			if !ok {
				ch = "?"
			}
			view[r][c] = ch
		}
	}
	for _, p := range path {
		r, c := p[0], p[1]
		if r < 0 || c < 0 || r >= n || c >= n {
			continue
		}
		if grid[r][c] == 2 || grid[r][c] == 3 {
			view[r][c] = cellChars[grid[r][c]]
		} else {
			view[r][c] = "*"
		}
	}
	return view
}

func renderASCII(view [][]string) string {
	var b strings.Builder
	border := "+" + strings.Repeat("-", len(view[0])*2-1) + "+"
	b.WriteString(border + "\n")
	for _, row := range view {
		b.WriteString("| " + strings.Join(row, " ") + " |\n")
	}
	b.WriteString(border)
	return b.String()
}

func cellColor(ch string) string {
	switch ch {
	case ".":
		return "#f8f9fa"
	case "#":
		return "#343a40"
	case "S":
		return "#0d6efd"
	case "G":
		return "#198754"
	case "*":
		return "#ffc107"
	default:
		return "#dee2e6"
	}
}

func renderHTML(view [][]string, title string) string {
	var rows strings.Builder
	for _, row := range view {
		rows.WriteString("<tr>")
		for _, ch := range row {
			bg := cellColor(ch)
			rows.WriteString(fmt.Sprintf(
				`<td style="width:28px;height:28px;text-align:center;background:%s;font-family:monospace;font-weight:bold;">%s</td>`,
				bg, html.EscapeString(ch)))
		}
		rows.WriteString("</tr>")
	}
	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8"><title>%s</title></head>
<body>
<h1>%s</h1>
<p>凡例: . 空き / # 壁 / S 開始 / G ゴール / * 経路</p>
<table cellspacing="2" cellpadding="0">%s</table>
</body>
</html>`, html.EscapeString(title), html.EscapeString(title), rows.String())
}

func main() {
	htmlOut := flag.Bool("html", false, "emit HTML instead of ASCII")
	input := flag.String("input", filepath.Join("data", "ch26", "sample.txt"), "input file")
	flag.Parse()

	vis, err := readVis(*input)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read error: %v\n", err)
		os.Exit(1)
	}
	view := overlayPath(vis.Grid, vis.Path)
	title := fmt.Sprintf("ch26 path vis (%s, n=%d, steps=%d)", *input, vis.N, len(vis.Path))

	if *htmlOut {
		fmt.Println(renderHTML(view, title))
	} else {
		fmt.Println(renderASCII(view))
	}
	fmt.Fprintf(os.Stderr, "legend: . empty  # wall  S start  G goal  * path\n")
	fmt.Fprintf(os.Stderr, "grid=%d path_len=%d\n", vis.N, len(vis.Path))
}
