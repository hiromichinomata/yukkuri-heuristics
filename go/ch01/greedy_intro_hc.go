// go/ch01/greedy_intro_hc.go
package main

// 各日 26 通り試して、その日終了時満足度が最大のタイプを選ぶ（骨格）
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
