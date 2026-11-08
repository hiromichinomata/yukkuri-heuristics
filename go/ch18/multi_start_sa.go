// go/ch18/multi_start_sa.go
// シードを変えた multi-start SA で Intro HC を改善（第18章）
//
// 既定は提出用: 制限時間をシードの数で区切り、逐次に SA を回して最良解を採る。
// -parallel を付けるとローカル実験用: 各シードを goroutine で同時に回す
// （壁時計は短くなるが、ジャッジで同じ効果が出る保証はない）。
//
//	go run go/ch18/multi_start_sa.go < data/ch18/sample.txt            # 提出用（逐次）
//	go run go/ch18/multi_start_sa.go -parallel < data/ch18/sample.txt  # ローカル実験用
package main

import (
	"bufio"
	"flag"
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
	t0           = 5000.0 // 開始温度
	t1           = 10.0   // 終了温度
	totalTimeSec = 1.6    // 提出用: 全シード合計の探索時間（本番 2 秒なら余裕を残す）
	defaultSeeds = 4
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type RunResult struct {
	Types []int
	Score int
	Seed  int64
	Steps int
}

func parseInts(line string) []int {
	fields := strings.Fields(line)
	out := make([]int, len(fields))
	for i, f := range fields {
		out[i], _ = strconv.Atoi(f)
	}
	return out
}

func readProblem(r *bufio.Reader) (ProblemInput, error) {
	readLine := func() (string, error) {
		line, err := r.ReadString('\n')
		if err != nil && line == "" {
			return "", err
		}
		return strings.TrimSpace(line), nil
	}
	line, err := readLine()
	if err != nil {
		return ProblemInput{}, err
	}
	days, _ := strconv.Atoi(line)
	if line, err = readLine(); err != nil {
		return ProblemInput{}, err
	}
	decay := parseInts(line)
	gain := make([][]int, days)
	for i := range gain {
		if line, err = readLine(); err != nil {
			return ProblemInput{}, err
		}
		gain[i] = parseInts(line)
	}
	return ProblemInput{days, decay, gain}, nil
}

// rawScore は 10^6 + 最終満足度（0 で切らない値）。全再計算 O(26·D)
func rawScore(problem ProblemInput, types []int) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= problem.Days; day++ {
		t := types[day-1] - 1
		satisfaction += problem.Gain[day-1][t]
		last[t] = day
		for i := 0; i < 26; i++ {
			satisfaction -= problem.Decay[i] * (day - last[i])
		}
	}
	return 1000000 + satisfaction
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

// saRun は 1 シード分の SA（第9章と同じ時間ベース冷却 + 差分更新）
func saRun(problem ProblemInput, seed int64, limit time.Duration) RunResult {
	rng := rand.New(rand.NewSource(seed))
	types := make([]int, problem.Days)
	for i := range types {
		types[i] = rng.Intn(26) + 1
	}
	score := rawScore(problem, types)
	bestTypes := append([]int{}, types...)
	bestScore := score
	start := time.Now()
	step := 0

	for {
		elapsed := time.Since(start)
		if elapsed >= limit {
			break
		}
		temperature := t0 * math.Pow(t1/t0, float64(elapsed)/float64(limit))
		day := rng.Intn(problem.Days)
		newType := rng.Intn(26) + 1
		delta := deltaChange(problem, types, day, newType)
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			types[day] = newType
			score += delta
			if score > bestScore {
				bestScore = score
				bestTypes = append(bestTypes[:0], types...)
			}
		}
		step++
	}
	if score != rawScore(problem, types) {
		panic("deltaChange と rawScore が一致しない")
	}
	if bestScore < 0 {
		bestScore = 0
	}
	fmt.Fprintf(os.Stderr, "seed=%d best=%d steps=%d\n", seed, bestScore, step)
	return RunResult{bestTypes, bestScore, seed, step}
}

func pickBest(results []RunResult) RunResult {
	best := results[0]
	for _, r := range results[1:] {
		if r.Score > best.Score {
			best = r
		}
	}
	return best
}

// multiStartSequential は提出用: total をシード数で等分し、1 本ずつ順番に回す
func multiStartSequential(problem ProblemInput, seeds []int64, total time.Duration) RunResult {
	perSeed := total / time.Duration(len(seeds))
	results := make([]RunResult, 0, len(seeds))
	for _, seed := range seeds {
		results = append(results, saRun(problem, seed, perSeed))
	}
	return pickBest(results)
}

// multiStartParallel はローカル実験用: 各シードを goroutine で同時に回す
func multiStartParallel(problem ProblemInput, seeds []int64, perSeed time.Duration) RunResult {
	results := make([]RunResult, len(seeds))
	var wg sync.WaitGroup
	for i, seed := range seeds {
		wg.Add(1)
		go func(i int, seed int64) {
			defer wg.Done()
			results[i] = saRun(problem, seed, perSeed)
		}(i, seed)
	}
	wg.Wait()
	return pickBest(results)
}

func main() {
	parallel := flag.Bool("parallel", false, "ローカル実験用に各シードを並列実行する")
	numSeeds := flag.Int("seeds", defaultSeeds, "シード数（42 から連番）")
	totalSec := flag.Float64("time", totalTimeSec, "全シード合計の探索時間（秒）")
	flag.Parse()

	problem, err := readProblem(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	seeds := make([]int64, *numSeeds)
	for i := range seeds {
		seeds[i] = int64(42 + i)
	}
	total := time.Duration(*totalSec * float64(time.Second))

	wallStart := time.Now()
	var best RunResult
	mode := "sequential"
	if *parallel {
		// 1 シードあたりの時間は逐次版と同じにそろえ、壁時計だけ短くする
		best = multiStartParallel(problem, seeds, total/time.Duration(len(seeds)))
		mode = "parallel"
	} else {
		best = multiStartSequential(problem, seeds, total)
	}
	wall := time.Since(wallStart).Seconds()

	for _, t := range best.Types {
		fmt.Println(t)
	}
	fmt.Fprintf(os.Stderr, "mode=%s seeds=%d merged best score=%d wall=%.2fs\n", mode, len(seeds), best.Score, wall)
}
