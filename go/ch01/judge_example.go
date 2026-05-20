// go/ch01/judge_example.go
package main

import "fmt"

func judgeAlgo(output, expected int) string {
	if output == expected {
		return "AC"
	}
	return "WA"
}

func judgeHeuristic(score int, valid bool) any {
	if !valid {
		return "WA"
	}
	return score
}

func main() {
	fmt.Println(judgeAlgo(42, 42))
	fmt.Println(judgeHeuristic(1079325, true))
}
