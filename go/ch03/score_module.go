// go/ch03/score_module.go
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type ScheduleState struct {
	Types []int
}

type ScoreResult struct {
	Daily              []int
	FinalSatisfaction  int
	ContestScore       int
}

func readProblemWithSchedule(r io.Reader) (ProblemInput, ScheduleState, error) {
	sc := bufio.NewScanner(r)
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return ProblemInput{}, ScheduleState{}, err
	}

	idx := 0
	d, _ := strconv.Atoi(lines[idx])
	idx++
	decay := parseInts(lines[idx])
	idx++
	gain := make([][]int, d)
	for i := 0; i < d; i++ {
		gain[i] = parseInts(lines[idx])
		idx++
	}
	types := make([]int, d)
	for i := 0; i < d; i++ {
		types[i], _ = strconv.Atoi(lines[idx])
		idx++
	}
	return ProblemInput{d, decay, gain}, ScheduleState{types}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func applyMove(state ScheduleState, day, contestType int) ScheduleState {
	nxt := append([]int{}, state.Types...)
	nxt[day] = contestType
	return ScheduleState{nxt}
}

func scoreSchedule(problem ProblemInput, state ScheduleState) ScoreResult {
	last := make([]int, 26)
	satisfaction := 0
	daily := make([]int, 0, problem.Days)

	for day := 1; day <= problem.Days; day++ {
		t := state.Types[day-1] - 1
		satisfaction += problem.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += problem.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
		daily = append(daily, satisfaction)
	}

	final := 0
	if len(daily) > 0 {
		final = daily[len(daily)-1]
	}
	contestScore := 1000000 + final
	if contestScore < 0 {
		contestScore = 0
	}
	return ScoreResult{daily, final, contestScore}
}

func main() {
	problem, state, err := readProblemWithSchedule(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	result := scoreSchedule(problem, state)
	for _, v := range result.Daily {
		fmt.Println(v)
	}
	fmt.Fprintln(os.Stderr, result.ContestScore)
}
