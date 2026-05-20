// go/ch10/pipeline.go
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

const (
	totalSec        = 2.0
	constructRatio  = 0.6
	t0              = 5000.0
	alpha           = 0.995
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type ScheduleState struct {
	Types []int
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

func copyState(s ScheduleState) ScheduleState {
	return ScheduleState{append([]int{}, s.Types...)}
}

func scoreSchedule(problem ProblemInput, state ScheduleState) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= problem.Days; day++ {
		t := state.Types[day-1] - 1
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

func finalSatisfaction(problem ProblemInput, state ScheduleState) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= len(state.Types); day++ {
		t := state.Types[day-1] - 1
		satisfaction += problem.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += problem.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	return satisfaction
}

func greedySchedule(problem ProblemInput) ScheduleState {
	schedule := make([]int, 0, problem.Days)
	for day := 1; day <= problem.Days; day++ {
		bestT, bestSat := 1, int(-1e18)
		for t := 1; t <= 26; t++ {
			trial := append(append([]int{}, schedule...), t)
			sat := finalSatisfaction(problem, ScheduleState{trial})
			if sat > bestSat {
				bestSat = sat
				bestT = t
			}
		}
		schedule = append(schedule, bestT)
	}
	return ScheduleState{schedule}
}

func hillClimb(problem ProblemInput, state ScheduleState, deadline time.Time, rng *rand.Rand) ScheduleState {
	current := copyState(state)
	score := scoreSchedule(problem, current)
	steps := 0
	for time.Now().Before(deadline) {
		day := rng.Intn(problem.Days)
		oldType := current.Types[day]
		improved := false
		for t := 1; t <= 26; t++ {
			if t == oldType {
				continue
			}
			trial := copyState(current)
			trial.Types[day] = t
			trialScore := scoreSchedule(problem, trial)
			if trialScore > score {
				current = trial
				score = trialScore
				improved = true
				break
			}
		}
		steps++
		if steps%5000 == 0 {
			fmt.Fprintf(os.Stderr, "hc step=%d score=%d\n", steps, score)
		}
		_ = improved
	}
	return current
}

func sa(problem ProblemInput, state ScheduleState, deadline time.Time, rng *rand.Rand) ScheduleState {
	current := copyState(state)
	score := scoreSchedule(problem, current)
	best := copyState(current)
	bestScore := score
	temperature := t0
	step := 0

	for time.Now().Before(deadline) {
		day := rng.Intn(problem.Days)
		trial := copyState(current)
		trial.Types[day] = rng.Intn(26) + 1
		trialScore := scoreSchedule(problem, trial)
		delta := float64(trialScore - score)
		if delta >= 0 || rng.Float64() < math.Exp(delta/temperature) {
			current = trial
			score = trialScore
			if score > bestScore {
				best = copyState(current)
				bestScore = score
			}
		}
		temperature *= alpha
		step++
		if step%5000 == 0 {
			fmt.Fprintf(os.Stderr, "sa step=%d score=%d T=%.2f\n", step, score, temperature)
		}
	}
	return best
}

func main() {
	rng := rand.New(rand.NewSource(42))
	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	start := time.Now()
	end := start.Add(time.Duration(totalSec * float64(time.Second)))
	constructEnd := start.Add(time.Duration(totalSec * constructRatio * float64(time.Second)))

	fmt.Fprintln(os.Stderr, "phase=greedy start")
	state := greedySchedule(problem)
	fmt.Fprintf(os.Stderr, "phase=greedy end score=%d\n", scoreSchedule(problem, state))

	fmt.Fprintln(os.Stderr, "phase=hill_climb start")
	state = hillClimb(problem, state, constructEnd, rng)
	fmt.Fprintf(os.Stderr, "phase=hill_climb end score=%d\n", scoreSchedule(problem, state))

	fmt.Fprintln(os.Stderr, "phase=sa start")
	state = sa(problem, state, end, rng)
	final := scoreSchedule(problem, state)
	fmt.Fprintf(os.Stderr, "phase=sa end score=%d\n", final)
	fmt.Fprintf(os.Stderr, "elapsed=%.3fs\n", time.Since(start).Seconds())

	for _, t := range state.Types {
		fmt.Println(t)
	}
}
