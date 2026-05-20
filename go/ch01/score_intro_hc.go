// go/ch01/score_intro_hc.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func readInput(sc *bufio.Scanner) (d int, c []int, s [][]int, schedule []int) {
	sc.Scan()
	d, _ = strconv.Atoi(sc.Text())

	sc.Scan()
	for _, v := range strings.Fields(sc.Text()) {
		x, _ := strconv.Atoi(v)
		c = append(c, x)
	}

	s = make([][]int, d)
	for i := 0; i < d; i++ {
		sc.Scan()
		row := strings.Fields(sc.Text())
		s[i] = make([]int, 26)
		for j, v := range row {
			s[i][j], _ = strconv.Atoi(v)
		}
	}

	schedule = make([]int, d)
	for i := 0; i < d; i++ {
		sc.Scan()
		schedule[i], _ = strconv.Atoi(sc.Text())
	}
	return
}

func dailySatisfactions(d int, c []int, s [][]int, schedule []int) []int {
	last := make([]int, 26)
	satisfaction := 0
	result := make([]int, 0, d)

	for day := 1; day <= d; day++ {
		t := schedule[day-1] - 1
		satisfaction += s[day-1][t]
		last[t] = day

		decay := 0
		for i := 0; i < 26; i++ {
			decay += c[i] * (day - last[i])
		}
		satisfaction -= decay
		result = append(result, satisfaction)
	}
	return result
}

func finalScore(satisfaction int) int {
	score := 1000000 + satisfaction
	if score < 0 {
		return 0
	}
	return score
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	d, c, s, schedule := readInput(sc)

	daily := dailySatisfactions(d, c, s, schedule)
	for _, v := range daily {
		fmt.Println(v)
	}
	fmt.Fprintf(os.Stderr, "%d\n", finalScore(daily[len(daily)-1]))
}
