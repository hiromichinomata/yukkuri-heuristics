// go/ch16/ga_placement.go
package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

const (
	popSize       = 40
	generations   = 200
	mutationRate  = 0.15
	tournamentK   = 3
)

type ProblemInput struct {
	Capacity int
	Widths   []int
}

func readProblem(r *bufio.Reader) (ProblemInput, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	capacity, _ := strconv.Atoi(strings.TrimSpace(line))
	line, err = r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	n, _ := strconv.Atoi(strings.TrimSpace(line))
	line, err = r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	widths := parseInts(strings.TrimSpace(line))
	if len(widths) != n {
		return ProblemInput{}, fmt.Errorf("expected %d widths, got %d", n, len(widths))
	}
	return ProblemInput{capacity, widths}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

type placement struct {
	idx, pos, width int
}

func evaluate(problem ProblemInput, order []int) (int, []placement) {
	pos := 0
	placed := 0
	var out []placement
	for _, idx := range order {
		w := problem.Widths[idx]
		if pos+w > problem.Capacity {
			continue
		}
		out = append(out, placement{idx, pos, w})
		pos += w
		placed += w
	}
	return placed, out
}

func tournamentSelect(pop [][]int, fitness []int, rng *rand.Rand) []int {
	bestIdx := -1
	bestFit := -1
	for k := 0; k < tournamentK; k++ {
		i := rng.Intn(len(pop))
		if fitness[i] > bestFit {
			bestFit = fitness[i]
			bestIdx = i
		}
	}
	out := make([]int, len(pop[bestIdx]))
	copy(out, pop[bestIdx])
	return out
}

func orderCrossover(p1, p2 []int, rng *rand.Rand) []int {
	n := len(p1)
	if n <= 2 {
		out := make([]int, n)
		copy(out, p1)
		return out
	}
	a, b := rng.Intn(n), rng.Intn(n)
	if a > b {
		a, b = b, a
	}
	child := make([]int, n)
	for i := range child {
		child[i] = -1
	}
	used := make(map[int]bool)
	for i := a; i <= b; i++ {
		child[i] = p1[i]
		used[p1[i]] = true
	}
	fill := make([]int, 0, n)
	for _, x := range p2 {
		if !used[x] {
			fill = append(fill, x)
		}
	}
	j := 0
	for i := 0; i < n; i++ {
		if child[i] == -1 {
			child[i] = fill[j]
			j++
		}
	}
	return child
}

func mutate(order []int, rng *rand.Rand) {
	if rng.Float64() >= mutationRate {
		return
	}
	i := rng.Intn(len(order))
	j := rng.Intn(len(order))
	order[i], order[j] = order[j], order[i]
}

func ga(problem ProblemInput, rng *rand.Rand) ([]int, int, []placement) {
	n := len(problem.Widths)
	pop := make([][]int, popSize)
	for i := range pop {
		pop[i] = randPerm(n, rng)
	}
	bestOrder := append([]int{}, pop[0]...)
	bestFit, bestPlace := evaluate(problem, bestOrder)

	for gen := 0; gen < generations; gen++ {
		fitness := make([]int, popSize)
		for i, ind := range pop {
			fitness[i], _ = evaluate(problem, ind)
			if fitness[i] > bestFit {
				bestFit = fitness[i]
				bestOrder = append([]int{}, ind...)
				_, bestPlace = evaluate(problem, ind)
			}
		}

		elite := 0
		for i := 1; i < popSize; i++ {
			if fitness[i] > fitness[elite] {
				elite = i
			}
		}
		next := make([][]int, 0, popSize)
		next = append(next, append([]int{}, pop[elite]...))
		for len(next) < popSize {
			p1 := tournamentSelect(pop, fitness, rng)
			p2 := tournamentSelect(pop, fitness, rng)
			child := orderCrossover(p1, p2, rng)
			mutate(child, rng)
			next = append(next, child)
		}
		pop = next

		if gen%50 == 0 {
			fmt.Fprintf(os.Stderr, "ga gen=%d best=%d\n", gen, bestFit)
		}
	}
	return bestOrder, bestFit, bestPlace
}

func randPerm(n int, rng *rand.Rand) []int {
	out := make([]int, n)
	for i := range out {
		out[i] = i
	}
	rng.Shuffle(n, func(i, j int) { out[i], out[j] = out[j], out[i] })
	return out
}

func main() {
	rng := rand.New(rand.NewSource(42))
	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	_, fit, placement := ga(problem, rng)
	fmt.Fprintf(os.Stderr, "placed_width=%d capacity=%d\n", fit, problem.Capacity)
	fmt.Println(len(placement))
	for _, p := range placement {
		fmt.Println(p.idx, p.pos, p.width)
	}
}
