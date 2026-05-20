// go/ch07/coarsen.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

const (
	nGrid  = 16
	blockN = 4
)

func readGrid(sc *bufio.Scanner) ([][]int, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	header, _ := strconv.Atoi(lines[0])
	if header != nGrid {
		return nil, fmt.Errorf("expected %d rows, got header %d", nGrid, header)
	}
	grid := make([][]int, nGrid)
	for i := 0; i < nGrid; i++ {
		p := strings.Fields(lines[i+1])
		row := make([]int, nGrid)
		for j := 0; j < nGrid; j++ {
			row[j], _ = strconv.Atoi(p[j])
		}
		grid[i] = row
	}
	return grid, nil
}

func blockAvg(grid [][]int, bi, bj int) int {
	sum := 0
	for i := bi * blockN; i < (bi+1)*blockN; i++ {
		for j := bj * blockN; j < (bj+1)*blockN; j++ {
			sum += grid[i][j]
		}
	}
	return sum / (blockN * blockN)
}

func coarseMatrix(grid [][]int) [][]int {
	out := make([][]int, blockN)
	for bi := 0; bi < blockN; bi++ {
		out[bi] = make([]int, blockN)
		for bj := 0; bj < blockN; bj++ {
			out[bi][bj] = blockAvg(grid, bi, bj)
		}
	}
	return out
}

type pos struct{ i, j int }

func greedyPerBlock(grid [][]int) []pos {
	picks := make([]pos, 0, blockN*blockN)
	for bi := 0; bi < blockN; bi++ {
		for bj := 0; bj < blockN; bj++ {
			bestVal := -1
			best := pos{bi * blockN, bj * blockN}
			for i := bi * blockN; i < (bi+1)*blockN; i++ {
				for j := bj * blockN; j < (bj+1)*blockN; j++ {
					if grid[i][j] > bestVal {
						bestVal = grid[i][j]
						best = pos{i, j}
					}
				}
			}
			picks = append(picks, best)
		}
	}
	return picks
}

func pickSum(grid [][]int, picks []pos) int {
	s := 0
	for _, p := range picks {
		s += grid[p.i][p.j]
	}
	return s
}

func refine(grid [][]int, picks []pos) []pos {
	refined := append([]pos{}, picks...)
	improved := true
	for improved {
		improved = false
		for idx, p := range refined {
			bi, bj := p.i/blockN, p.j/blockN
			bestVal := grid[p.i][p.j]
			best := p
			for di := -1; di <= 1; di++ {
				for dj := -1; dj <= 1; dj++ {
					ni, nj := p.i+di, p.j+dj
					if ni < 0 || ni >= nGrid || nj < 0 || nj >= nGrid {
						continue
					}
					if ni/blockN != bi || nj/blockN != bj {
						continue
					}
					if grid[ni][nj] > bestVal {
						bestVal = grid[ni][nj]
						best = pos{ni, nj}
					}
				}
			}
			if best != p {
				refined[idx] = best
				improved = true
			}
		}
	}
	return refined
}

func main() {
	grid, err := readGrid(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	coarse := coarseMatrix(grid)
	greedy := greedyPerBlock(grid)
	refined := refine(grid, greedy)
	fmt.Println("coarse 4x4 (block averages):")
	for _, row := range coarse {
		for j, v := range row {
			if j > 0 {
				fmt.Print(" ")
			}
			fmt.Print(v)
		}
		fmt.Println()
	}
	fmt.Printf("greedy_sum=%d\n", pickSum(grid, greedy))
	fmt.Printf("refined_sum=%d\n", pickSum(grid, refined))
	fmt.Println("refined picks (row col):")
	for _, p := range refined {
		fmt.Println(p.i, p.j)
	}
}
