// go/ch11/pipeline.go
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
	totalSec       = 1.8 // 本番の制限時間 2 秒から、起動と出力の分を残す
	constructRatio = 0.6
	t0             = 5000.0
	t1             = 10.0 // SA 段の終了温度（第9章と同じ時間ベース冷却）
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

// typePenalty はタイプ t の減衰ペナルティ合計 c_t * Σ L(L-1)/2。O(D)（第9章 9.4）
func typePenalty(problem ProblemInput, types []int, t int) int {
	total, prev := 0, 0
	for i, x := range types {
		if x == t {
			gap := i + 1 - prev
			total += gap * (gap - 1) / 2
			prev = i + 1
		}
	}
	gap := problem.Days + 1 - prev
	total += gap * (gap - 1) / 2
	return problem.Decay[t-1] * total
}

// deltaChange は types[day] を newType に変えたときの (10^6 + 満足度) の変化量。O(D)（第9章 9.4）
func deltaChange(problem ProblemInput, types []int, day, newType int) int {
	oldType := types[day]
	if oldType == newType {
		return 0
	}
	before := typePenalty(problem, types, oldType) + typePenalty(problem, types, newType)
	types[day] = newType
	after := typePenalty(problem, types, oldType) + typePenalty(problem, types, newType)
	types[day] = oldType
	gain := problem.Gain[day][newType-1] - problem.Gain[day][oldType-1]
	return gain - (after - before)
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
	score := 1000000 + finalSatisfaction(problem, current) // 0 で切らない値で比べる
	steps := 0
	for time.Now().Before(deadline) {
		day := rng.Intn(problem.Days)
		oldType := current.Types[day]
		for t := 1; t <= 26; t++ {
			if t == oldType {
				continue
			}
			if delta := deltaChange(problem, current.Types, day, t); delta > 0 { // 差分だけ（第9章 9.4）
				current.Types[day] = t
				score += delta
				break
			}
		}
		steps++
		if steps%5000 == 0 {
			fmt.Fprintf(os.Stderr, "hc step=%d score=%d\n", steps, max(score, 0))
		}
	}
	if score != 1000000+finalSatisfaction(problem, current) {
		panic("差分と全再計算が一致しない")
	}
	return current
}

func sa(problem ProblemInput, state ScheduleState, deadline time.Time, rng *rand.Rand) ScheduleState {
	current := copyState(state)
	score := 1000000 + finalSatisfaction(problem, current) // 0 で切らない値で比べる
	best := copyState(current)
	bestScore := score
	temperature := t0
	step := 0
	start := time.Now()
	span := deadline.Sub(start)
	nextLog := 0.1

	for {
		now := time.Now()
		if !now.Before(deadline) {
			break
		}
		// SA 段に割り当てられた時間の中で t0 → t1 へ下げる
		progress := float64(now.Sub(start)) / float64(span)
		temperature = t0 * math.Pow(t1/t0, progress)
		day := rng.Intn(problem.Days)
		newType := rng.Intn(26) + 1
		delta := deltaChange(problem, current.Types, day, newType) // 差分だけ（第9章 9.4）
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			current.Types[day] = newType
			score += delta
			if score > bestScore {
				best = copyState(current)
				bestScore = score
			}
		}
		step++
		if progress >= nextLog { // SA 段の 10% ごとにログ
			nextLog += 0.1
			fmt.Fprintf(os.Stderr, "sa step=%d score=%d T=%.2f\n", step, max(score, 0), temperature)
		}
	}
	if score != 1000000+finalSatisfaction(problem, current) {
		panic("差分と全再計算が一致しない")
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
