// go/ch18/sa_multi_neighborhood.go
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
	t0             = 8000.0
	alphaFast      = 0.992
	alphaSlow      = 0.998
	reheatFactor   = 0.6
	stagnantLimit  = 800
	timeLimitSec   = 1.5
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

func neighborChangeDay(state ScheduleState, rng *rand.Rand) ScheduleState {
	nxt := append([]int{}, state.Types...)
	day := rng.Intn(len(nxt))
	nxt[day] = rng.Intn(26) + 1
	return ScheduleState{nxt}
}

func neighborSwapDays(state ScheduleState, rng *rand.Rand) ScheduleState {
	nxt := append([]int{}, state.Types...)
	a := rng.Intn(len(nxt))
	b := rng.Intn(len(nxt))
	nxt[a], nxt[b] = nxt[b], nxt[a]
	return ScheduleState{nxt}
}

func saMulti(problem ProblemInput, initial ScheduleState, limit time.Duration, rng *rand.Rand) (ScheduleState, int) {
	names := []string{"change_day", "swap_days"}
	weights := []float64{1, 1}
	wins := []int{0, 0}

	start := time.Now()
	state := initial
	score := scoreSchedule(problem, state)
	bestState := ScheduleState{append([]int{}, state.Types...)}
	bestScore := score
	temperature := t0
	alpha := alphaFast
	step := 0
	sinceImprove := 0

	for time.Since(start) < limit {
		idx := weightedPick(weights, rng)
		var nxt ScheduleState
		if idx == 0 {
			nxt = neighborChangeDay(state, rng)
		} else {
			nxt = neighborSwapDays(state, rng)
		}
		newScore := scoreSchedule(problem, nxt)
		delta := float64(newScore - score)
		accepted := delta >= 0 || rng.Float64() < math.Exp(delta/temperature)
		if accepted {
			state = nxt
			score = newScore
			wins[idx]++
			if score > bestScore {
				bestScore = score
				bestState = ScheduleState{append([]int{}, state.Types...)}
				sinceImprove = 0
			} else {
				sinceImprove++
			}
		} else {
			sinceImprove++
		}

		if sinceImprove > 200 {
			alpha = alphaSlow
		}
		if sinceImprove >= stagnantLimit {
			if temperature < t0*reheatFactor {
				temperature = t0 * reheatFactor
			}
			sinceImprove = 0
			alpha = alphaFast
			fmt.Fprintf(os.Stderr, "reheat T=%.1f\n", temperature)
		}

		temperature *= alpha
		step++
		if step%500 == 0 {
			fmt.Fprintf(os.Stderr, "sa step=%d score=%d best=%d T=%.1f nh=%s wins=%v\n",
				step, score, bestScore, temperature, names[idx], wins)
			total := wins[0] + wins[1]
			if total == 0 {
				total = 1
			}
			weights[0] = math.Max(0.2, float64(wins[0])/float64(total)*2)
			weights[1] = math.Max(0.2, float64(wins[1])/float64(total)*2)
		}
	}
	return bestState, bestScore
}

func weightedPick(weights []float64, rng *rand.Rand) int {
	sum := 0.0
	for _, w := range weights {
		sum += w
	}
	x := rng.Float64() * sum
	acc := 0.0
	for i, w := range weights {
		acc += w
		if x <= acc {
			return i
		}
	}
	return len(weights) - 1
}

func main() {
	rng := rand.New(rand.NewSource(42))
	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	initial := ScheduleState{make([]int, problem.Days)}
	for i := range initial.Types {
		initial.Types[i] = rng.Intn(26) + 1
	}
	fmt.Fprintf(os.Stderr, "initial score=%d\n", scoreSchedule(problem, initial))

	best, bestScore := saMulti(problem, initial, time.Duration(timeLimitSec*float64(time.Second)), rng)
	fmt.Fprintf(os.Stderr, "best score=%d\n", bestScore)
	for _, t := range best.Types {
		fmt.Println(t)
	}
}
