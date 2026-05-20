// go/ch20/parallel_sa.go
package main

import (
	"bufio"
	"fmt"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	t0           = 5000.0
	alpha        = 0.995
	timeLimitSec = 0.8
	numWorkers   = 4
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type ScheduleState struct {
	Types []int
}

type RunResult struct {
	Types []int
	Score int
	Seed  int
}

func readProblem(r *bufio.Reader) (ProblemInput, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	days, _ := strconv.Atoi(strings.TrimSpace(line))
	line, err = r.ReadString('\n')
	if err != nil {
		return ProblemInput{}, err
	}
	decay := parseInts(strings.TrimSpace(line))
	gain := make([][]int, days)
	for i := 0; i < days; i++ {
		line, err = r.ReadString('\n')
		if err != nil {
			return ProblemInput{}, err
		}
		gain[i] = parseInts(strings.TrimSpace(line))
	}
	return ProblemInput{days, decay, gain}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func scoreSchedule(problem ProblemInput, types []int) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= problem.Days; day++ {
		t := types[day-1] - 1
		satisfaction += problem.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += problem.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	score := 1000000 + satisfaction
	if score < 0 {
		return 0
	}
	return score
}

func randomNeighbor(types []int, rng *rand.Rand) []int {
	nxt := append([]int{}, types...)
	day := rng.Intn(len(nxt))
	nxt[day] = rng.Intn(26) + 1
	return nxt
}

func saRun(problem ProblemInput, seed int64, limit time.Duration) RunResult {
	rng := rand.New(rand.NewSource(seed))
	types := make([]int, problem.Days)
	for i := range types {
		types[i] = rng.Intn(26) + 1
	}
	score := scoreSchedule(problem, types)
	bestTypes := append([]int{}, types...)
	bestScore := score
	temperature := t0
	start := time.Now()
	step := 0

	for time.Since(start) < limit {
		nxt := randomNeighbor(types, rng)
		newScore := scoreSchedule(problem, nxt)
		delta := float64(newScore - score)
		if delta >= 0 || rng.Float64() < math.Exp(delta/temperature) {
			types = nxt
			score = newScore
			if score > bestScore {
				bestScore = score
				bestTypes = append([]int{}, types...)
			}
		}
		temperature *= alpha
		step++
	}

	fmt.Fprintf(os.Stderr, "worker seed=%d best=%d steps=%d\n", seed, bestScore, step)
	return RunResult{bestTypes, bestScore, int(seed)}
}

func parallelSA(problem ProblemInput) RunResult {
	seeds := []int64{42, 43, 44, 45}
	limit := time.Duration(timeLimitSec * float64(time.Second))
	results := make([]RunResult, len(seeds))
	var wg sync.WaitGroup
	wg.Add(len(seeds))
	for i, seed := range seeds {
		i, seed := i, seed
		go func() {
			defer wg.Done()
			results[i] = saRun(problem, seed, limit)
		}()
	}
	wg.Wait()

	best := results[0]
	for _, r := range results[1:] {
		if r.Score > best.Score {
			best = r
		}
	}
	fmt.Fprintf(os.Stderr, "merged best score=%d\n", best.Score)
	return best
}

func main() {
	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	best := parallelSA(problem)
	for _, t := range best.Types {
		fmt.Println(t)
	}
	fmt.Fprintf(os.Stderr, "output days=%d score=%d\n", len(best.Types), best.Score)
}
