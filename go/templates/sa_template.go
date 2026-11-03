// go/templates/sa_template.go
package main

import (
	"fmt"
	"math"
	"math/rand"
	"os"
	"time"
)

const (
	T0 = 100.0 // 開始温度
	T1 = 0.1   // 終了温度
)

func logScore(step, score int) {
	fmt.Fprintf(os.Stderr, "%d %d\n", step, score)
}

func sa(
	initial int,
	neighbor func(x int, rng *rand.Rand) (int, bool),
	score func(x int) int,
	limit time.Duration,
	rng *rand.Rand,
) (bestState, bestScore int) {
	start := time.Now()
	state := initial
	bestState = state
	bestScore = score(state)
	curScore := bestScore

	step := 0
	nextLog := 0.1

	for {
		elapsed := time.Since(start)
		if elapsed >= limit {
			break
		}
		// 時間ベースの指数冷却: 経過割合 progress に応じて T0 → T1
		progress := float64(elapsed) / float64(limit)
		T := T0 * math.Pow(T1/T0, progress)

		newState, ok := neighbor(state, rng)
		if !ok {
			continue
		}
		newScore := score(newState)
		delta := float64(newScore - curScore)

		if delta >= 0 || rng.Float64() < math.Exp(delta/T) {
			state = newState
			curScore = newScore
			if curScore > bestScore {
				bestScore = curScore
				bestState = state
			}
		}

		step++
		if progress >= nextLog { // 経過 10% ごとにログ
			nextLog += 0.1
			logScore(step, curScore)
		}
	}

	return bestState, bestScore
}

func main() {
	const target = 42
	rng := rand.New(rand.NewSource(42))

	score := func(x int) int {
		d := x - target
		return -(d * d)
	}

	neighbor := func(x int, rng *rand.Rand) (int, bool) {
		dx := 1
		if rng.Intn(2) == 0 {
			dx = -1
		}
		nxt := x + dx
		if nxt < 0 || nxt > 100 {
			return 0, false
		}
		return nxt, true
	}

	bestState, bestScore := sa(0, neighbor, score, 500*time.Millisecond, rng)
	fmt.Printf("best_state=%d best_score=%d\n", bestState, bestScore)
}
