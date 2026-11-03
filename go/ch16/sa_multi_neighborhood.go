// go/ch16/sa_multi_neighborhood.go
// 複数近傍・適応冷却・再ヒート付き SA（Intro HC・第16章）
// 土台は第9章と同じ「時間ベースの指数冷却 + 差分更新」。その上に
// 近傍の重み付き選択、温度の倍率 boost による適応冷却と再ヒートを載せる。
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
	t0 = 5000.0 // 開始温度（第9章と同じ時間ベース冷却の土台）
	t1 = 10.0   // 終了温度
	// 適応的冷却: 温度 = 時間ベースの基準温度 × boost。boost は 1 に向かって減衰する
	boostDecayFast    = 0.999  // 改善が続いているとき（速く 1 に戻す = 速く冷やす）
	boostDecaySlow    = 0.9999 // 停滞気味のとき（ゆっくり戻す = 熱いまま粘る）
	slowAfter         = 2000   // best 更新がこのステップ数ないと「停滞気味」
	reheatBoost       = 4.0    // 再ヒート時の倍率
	stagnantLimit     = 20000  // best 更新がこのステップ数ないと再ヒート
	weightUpdateEvery = 1000
	timeLimitSec      = 1.5
	logEvery          = 0.1
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

func scoreSchedule(problem ProblemInput, state ScheduleState) int {
	if s := rawScore(problem, state); s > 0 {
		return s
	}
	return 0
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

// deltaChange は types[day] を newType に変えたときの rawScore の変化量。O(D)（第9章 9.4）
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

// Move は近傍操作。Swap=false なら「X 日目を Y に変える」、true なら「X 日目と Y 日目を入れ替える」
type Move struct {
	Swap bool
	X, Y int
}

func neighborChangeDay(state ScheduleState, rng *rand.Rand) Move {
	return Move{false, rng.Intn(len(state.Types)), rng.Intn(26) + 1}
}

func neighborSwapDays(state ScheduleState, rng *rand.Rand) Move {
	n := len(state.Types)
	a := rng.Intn(n)
	b := rng.Intn(n - 1)
	if b >= a {
		b++
	}
	return Move{true, a, b}
}

func moveDelta(problem ProblemInput, types []int, m Move) int {
	if !m.Swap {
		return deltaChange(problem, types, m.X, m.Y)
	}
	// swap は「a を b のタイプに変える」→「b を a のタイプに変える」の 2 回の change
	ta, tb := types[m.X], types[m.Y]
	if ta == tb {
		return 0
	}
	d1 := deltaChange(problem, types, m.X, tb)
	types[m.X] = tb
	d2 := deltaChange(problem, types, m.Y, ta)
	types[m.X] = ta
	return d1 + d2
}

func applyMove(types []int, m Move) {
	if !m.Swap {
		types[m.X] = m.Y
		return
	}
	types[m.X], types[m.Y] = types[m.Y], types[m.X]
}

func saMulti(problem ProblemInput, initial ScheduleState, limit time.Duration, rng *rand.Rand) (ScheduleState, int) {
	neighborhoods := []func(ScheduleState, *rand.Rand) Move{neighborChangeDay, neighborSwapDays}
	weights := []float64{1, 1}
	wins := []int{0, 0}

	start := time.Now()
	state := ScheduleState{append([]int{}, initial.Types...)}
	score := rawScore(problem, state)
	bestState := ScheduleState{append([]int{}, state.Types...)}
	bestScore := score
	boost := 1.0
	step, sinceImprove, reheats := 0, 0, 0
	nextLog := logEvery

	for {
		elapsed := time.Since(start)
		if elapsed >= limit {
			break
		}
		progress := float64(elapsed) / float64(limit)
		temperature := t0 * math.Pow(t1/t0, progress) * boost

		idx := weightedPick(weights, rng)
		m := neighborhoods[idx](state, rng)
		delta := moveDelta(problem, state.Types, m)
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			applyMove(state.Types, m)
			score += delta
			if delta > 0 { // 改善した操作だけ「勝ち」に数える
				wins[idx]++
			}
		}
		if score > bestScore {
			bestScore = score
			bestState = ScheduleState{append([]int{}, state.Types...)}
			sinceImprove = 0
		} else {
			sinceImprove++
		}

		// 適応的冷却: 停滞気味なら boost をゆっくり 1 に戻す（熱いまま粘る）
		decay := boostDecayFast
		if sinceImprove > slowAfter {
			decay = boostDecaySlow
		}
		boost = math.Max(1.0, boost*decay)
		// 再ヒート: 長く停滞したら温度を一時的に上げて探索をやり直す
		if sinceImprove >= stagnantLimit {
			boost = reheatBoost
			sinceImprove = 0
			reheats++
		}

		step++
		if step%weightUpdateEvery == 0 {
			total := wins[0] + wins[1]
			if total == 0 {
				total = 1
			}
			for i := range weights {
				weights[i] = math.Max(0.2, float64(wins[i])/float64(total)*2)
			}
		}
		if progress >= nextLog { // 経過 10% ごとにログ
			nextLog += logEvery
			fmt.Fprintf(os.Stderr, "sa step=%d score=%d best=%d T=%.1f boost=%.2f reheats=%d wins=%v\n",
				step, score, bestScore, temperature, boost, reheats, wins)
		}
	}
	if score != rawScore(problem, state) {
		panic("moveDelta と rawScore が一致しない")
	}
	if bestScore < 0 {
		bestScore = 0
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
