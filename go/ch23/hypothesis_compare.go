// go/ch23/hypothesis_compare.go
package main

import (
	"bufio"
	"fmt"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type ScheduleState struct {
	Types []int
}

func readProblem(sc *bufio.Scanner) (ProblemInput, error) {
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return ProblemInput{}, err
	}
	days, _ := strconv.Atoi(lines[0])
	decay := parseInts(lines[1])
	gain := make([][]int, days)
	for i := 0; i < days; i++ {
		gain[i] = parseInts(lines[2+i])
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

func scoreSchedule(p ProblemInput, s ScheduleState) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= p.Days; day++ {
		t := s.Types[day-1] - 1
		satisfaction += p.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += p.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	score := 1000000 + satisfaction
	if score < 0 {
		return 0
	}
	return score
}

func finalSat(p ProblemInput, types []int) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= len(types); day++ {
		t := types[day-1] - 1
		satisfaction += p.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += p.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	return satisfaction
}

func strategyGreedy(p ProblemInput) ScheduleState {
	schedule := make([]int, 0, p.Days)
	for day := 1; day <= p.Days; day++ {
		bestT, bestSat := 1, -1<<30
		for t := 1; t <= 26; t++ {
			trial := append(append([]int{}, schedule...), t)
			sat := finalSat(p, trial)
			if sat > bestSat {
				bestSat = sat
				bestT = t
			}
		}
		schedule = append(schedule, bestT)
	}
	return ScheduleState{schedule}
}

func strategyRandomSA(p ProblemInput, rng *rand.Rand, steps int) ScheduleState {
	types := make([]int, p.Days)
	for i := range types {
		types[i] = 1 + rng.Intn(26)
	}
	state := ScheduleState{types}
	score := scoreSchedule(p, state)
	best := append([]int{}, state.Types...)
	bestScore := score
	temperature := 5000.0
	alpha := 0.995
	for s := 0; s < steps; s++ {
		day := rng.Intn(p.Days)
		trial := append([]int{}, state.Types...)
		trial[day] = 1 + rng.Intn(26)
		trialScore := scoreSchedule(p, ScheduleState{trial})
		delta := trialScore - score
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			state = ScheduleState{trial}
			score = trialScore
			if score > bestScore {
				best = append([]int{}, state.Types...)
				bestScore = score
			}
		}
		temperature *= alpha
	}
	return ScheduleState{best}
}

func strategyPipelineLite(p ProblemInput, rng *rand.Rand) ScheduleState {
	state := strategyGreedy(p)
	score := scoreSchedule(p, state)
	for s := 0; s < 400; s++ {
		day := rng.Intn(p.Days)
		old := state.Types[day]
		for t := 1; t <= 26; t++ {
			if t == old {
				continue
			}
			trial := append([]int{}, state.Types...)
			trial[day] = t
			trialScore := scoreSchedule(p, ScheduleState{trial})
			if trialScore > score {
				state = ScheduleState{trial}
				score = trialScore
				break
			}
		}
	}
	return state
}

func main() {
	problem, err := readProblem(bufio.NewScanner(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rng := rand.New(rand.NewSource(42))
	t0 := time.Now()

	type result struct {
		name    string
		score   int
		elapsed float64
		types   []int
	}
	var results []result
	run := func(name string, fn func() ScheduleState) {
		start := time.Now()
		st := fn()
		elapsed := time.Since(start).Seconds()
		score := scoreSchedule(problem, st)
		results = append(results, result{name, score, elapsed, st.Types})
		fmt.Fprintf(os.Stderr, "strategy=%s score=%d elapsed=%.3fs\n", name, score, elapsed)
	}
	run("greedy", func() ScheduleState { return strategyGreedy(problem) })
	run("random_sa", func() ScheduleState { return strategyRandomSA(problem, rng, 800) })
	run("pipeline_lite", func() ScheduleState { return strategyPipelineLite(problem, rng) })

	best := results[0]
	for _, r := range results[1:] {
		if r.score > best.score {
			best = r
		}
	}
	fmt.Fprintf(os.Stderr, "best=%s score=%d total_elapsed=%.3fs\n",
		best.name, best.score, time.Since(t0).Seconds())
	fmt.Printf("# winner schedule (%s)\n", best.name)
	for _, t := range best.types {
		fmt.Println(t)
	}
}
