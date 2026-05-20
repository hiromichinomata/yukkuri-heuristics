// go/ch17/territory_greedy.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var dirs = [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}

type ProblemInput struct {
	N      int
	Grid   [][]int
	Starts [2][2]int
}

func readProblem(r *bufio.Reader) (ProblemInput, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	n, _ := strconv.Atoi(strings.TrimSpace(line))
	grid := make([][]int, n)
	for i := 0; i < n; i++ {
		line, err = r.ReadString('\n')
		if err != nil {
			return ProblemInput{}, err
		}
		grid[i] = parseInts(strings.TrimSpace(line))
	}
	var starts [2][2]int
	for i := 0; i < 2; i++ {
		line, err = r.ReadString('\n')
		if err != nil {
			return ProblemInput{}, err
		}
		p := parseInts(strings.TrimSpace(line))
		starts[i] = [2]int{p[0], p[1]}
	}
	return ProblemInput{n, grid, starts}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func bestMove(n int, grid [][]int, owner [][]int, pos [2]int) (bool, int, int) {
	bestVal := -1
	bestR, bestC := -1, -1
	for _, d := range dirs {
		r, c := pos[0]+d[0], pos[1]+d[1]
		if r < 0 || c < 0 || r >= n || c >= n {
			continue
		}
		if owner[r][c] != -1 {
			continue
		}
		val := grid[r][c]
		if bestVal < 0 || val > bestVal || (val == bestVal && (r < bestR || (r == bestR && c < bestC))) {
			bestVal = val
			bestR, bestC = r, c
		}
	}
	return bestVal >= 0, bestR, bestC
}

func solve(problem ProblemInput) ([]int, []string) {
	n := problem.N
	owner := make([][]int, n)
	for i := range owner {
		owner[i] = make([]int, n)
		for j := range owner[i] {
			owner[i][j] = -1
		}
	}
	scores := []int{0, 0}
	pos := problem.Starts
	for agent := 0; agent < 2; agent++ {
		r, c := pos[agent][0], pos[agent][1]
		owner[r][c] = agent
		scores[agent] += problem.Grid[r][c]
	}

	var moves []string
	turn := 0
	stagnant := 0
	for stagnant < 2 {
		agent := turn % 2
		ok, r, c := bestMove(n, problem.Grid, owner, pos[agent])
		if !ok {
			stagnant++
			turn++
			continue
		}
		stagnant = 0
		owner[r][c] = agent
		pos[agent] = [2]int{r, c}
		scores[agent] += problem.Grid[r][c]
		moves = append(moves, fmt.Sprintf("%d %d %d", agent, r, c))
		turn++
	}
	return scores, moves
}

func main() {
	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	scores, moves := solve(problem)
	fmt.Fprintf(os.Stderr, "territory0=%d territory1=%d moves=%d\n", scores[0], scores[1], len(moves))
	fmt.Println(scores[0], scores[1])
	for _, line := range moves {
		fmt.Println(line)
	}
}
