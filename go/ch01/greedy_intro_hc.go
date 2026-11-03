// go/ch01/greedy_intro_hc.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// 各日 26 通り試して、その日終了時満足度が最大のタイプを選ぶ
func greedySchedule(d int, c []int, s [][]int, scoreFn func([]int) []int) []int {
	schedule := make([]int, 0, d)
	for day := 1; day <= d; day++ {
		bestT, bestSat := 1, int(-1e18)
		for t := 1; t <= 26; t++ {
			trial := append(append([]int{}, schedule...), t)
			sat := scoreFn(trial)[len(trial)-1]
			if sat > bestSat {
				bestSat = sat
				bestT = t
			}
		}
		schedule = append(schedule, bestT)
	}
	return schedule
}

// schedule の長さぶんだけ日ごとの満足度を返す
func dailySatisfactions(c []int, s [][]int, schedule []int) []int {
	last := make([]int, 26)
	satisfaction := 0
	result := make([]int, 0, len(schedule))
	for day := 1; day <= len(schedule); day++ {
		t := schedule[day-1] - 1
		satisfaction += s[day-1][t]
		last[t] = day
		for i := 0; i < 26; i++ {
			satisfaction -= c[i] * (day - last[i])
		}
		result = append(result, satisfaction)
	}
	return result
}

func parseInts(line string) []int {
	fields := strings.Fields(line)
	out := make([]int, len(fields))
	for i, f := range fields {
		out[i], _ = strconv.Atoi(f)
	}
	return out
}

// D, c, s を読む（後ろにスケジュール行があっても無視する）
func readProblem(sc *bufio.Scanner) (int, []int, [][]int) {
	sc.Scan()
	d, _ := strconv.Atoi(strings.TrimSpace(sc.Text()))
	sc.Scan()
	c := parseInts(sc.Text())
	s := make([][]int, d)
	for i := 0; i < d; i++ {
		sc.Scan()
		s[i] = parseInts(sc.Text())
	}
	return d, c, s
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	d, c, s := readProblem(sc)
	scoreFn := func(schedule []int) []int { return dailySatisfactions(c, s, schedule) }

	schedule := greedySchedule(d, c, s, scoreFn)
	for _, t := range schedule {
		fmt.Println(t)
	}
	final := 1000000 + scoreFn(schedule)[d-1]
	if final < 0 {
		final = 0
	}
	fmt.Fprintf(os.Stderr, "final score=%d\n", final)
}
