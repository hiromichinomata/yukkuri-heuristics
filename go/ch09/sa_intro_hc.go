// go/ch09/sa_intro_hc.go
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
	t0           = 5000.0 // 開始温度
	t1           = 10.0   // 終了温度
	timeLimitSec = 1.5
	logEvery     = 0.1 // 制限時間の何割ごとに stderr へログを出すか
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

// rawScore は 10^6 + 最終満足度（0 で切らない値）。全再計算 O(26·D)
func rawScore(problem ProblemInput, state ScheduleState) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= problem.Days; day++ {
		t := state.Types[day-1] - 1
		satisfaction += problem.Gain[day-1][t]
		last[t] = day
		for i := 0; i < 26; i++ {
			satisfaction -= problem.Decay[i] * (day - last[i])
		}
	}
	return 1000000 + satisfaction
}

// scoreSchedule は提出スコア max(10^6 + 最終満足度, 0)
func scoreSchedule(problem ProblemInput, state ScheduleState) int {
	if s := rawScore(problem, state); s > 0 {
		return s
	}
	return 0
}

// typePenalty はタイプ t（1〜26）の減衰ペナルティの合計。O(D)
// 開催日の間隔 L ごとに c_t * L(L-1)/2 だけ減る（最初は 0 日目、最後は D+1 日目を端とみなす）
func typePenalty(problem ProblemInput, types []int, t int) int {
	total, prev := 0, 0
	for i, x := range types {
		if x == t {
			day := i + 1
			gap := day - prev
			total += gap * (gap - 1) / 2
			prev = day
		}
	}
	gap := problem.Days + 1 - prev
	total += gap * (gap - 1) / 2
	return problem.Decay[t-1] * total
}

// deltaChange は types[day] を newType に変えたときの rawScore の変化量。O(D)
// 影響を受けるのは元のタイプと新しいタイプのペナルティだけ
func deltaChange(problem ProblemInput, types []int, day, newType int) int {
	oldType := types[day]
	if oldType == newType {
		return 0
	}
	before := typePenalty(problem, types, oldType) + typePenalty(problem, types, newType)
	types[day] = newType
	after := typePenalty(problem, types, oldType) + typePenalty(problem, types, newType)
	types[day] = oldType // 元に戻す（採用するかは呼び出し側が決める）
	gain := problem.Gain[day][newType-1] - problem.Gain[day][oldType-1]
	return gain - (after - before)
}

// randomMove は近傍「ある1日のタイプを別の値に変える」を (日の添字, 新タイプ) で返す
func randomMove(state ScheduleState, rng *rand.Rand) (int, int) {
	day := rng.Intn(len(state.Types))
	return day, rng.Intn(26) + 1
}

func sa(problem ProblemInput, initial ScheduleState, limit time.Duration, rng *rand.Rand) (ScheduleState, int) {
	start := time.Now()
	state := ScheduleState{append([]int{}, initial.Types...)} // 現在解はこのスライスを直接書き換える
	score := rawScore(problem, state)
	bestState := ScheduleState{append([]int{}, state.Types...)}
	bestScore := score
	temperature := t0
	step := 0
	nextLog := logEvery

	for {
		elapsed := time.Since(start)
		if elapsed >= limit {
			break
		}
		// 時間ベースの指数冷却: t0 → t1 を制限時間いっぱいで下げる
		progress := float64(elapsed) / float64(limit)
		temperature = t0 * math.Pow(t1/t0, progress)

		day, newType := randomMove(state, rng)
		delta := deltaChange(problem, state.Types, day, newType) // 全再計算せず差分だけ
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			state.Types[day] = newType
			score += delta
			if score > bestScore {
				bestScore = score
				bestState = ScheduleState{append([]int{}, state.Types...)}
			}
		}
		step++
		if progress >= nextLog { // 経過 10% ごとにログ
			nextLog += logEvery
			fmt.Fprintf(os.Stderr, "sa step=%d score=%d T=%.2f\n", step, score, temperature)
		}
	}
	// 差分の積み上げが全再計算と一致するか確認（デバッグ用。ずれたらバグ）
	if score != rawScore(problem, state) {
		panic("deltaChange と rawScore が一致しない")
	}
	if bestScore < 0 {
		bestScore = 0
	}
	return bestState, bestScore
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

	best, bestScore := sa(problem, initial, time.Duration(timeLimitSec*float64(time.Second)), rng)
	fmt.Fprintf(os.Stderr, "best score=%d\n", bestScore)
	for _, t := range best.Types {
		fmt.Println(t)
	}
}
