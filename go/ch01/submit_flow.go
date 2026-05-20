// go/ch01/submit_flow.go
package main

import "fmt"

type State struct {
	Score int
	Data  []int
}

func bestSoFar(current, best State) State {
	if current.Score > best.Score {
		return current
	}
	return best
}

func main() {
	best := State{Score: -1}
	best = bestSoFar(State{Score: 100, Data: []int{1, 2}}, best)
	best = bestSoFar(State{Score: 250, Data: []int{3, 4}}, best)
	fmt.Println(best)
}
