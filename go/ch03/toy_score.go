// go/ch03/toy_score.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

type ToyState struct {
	Picked []bool
}

type ToyInput struct {
	Values []int
}

func applyMove(state ToyState, index int, pick bool) ToyState {
	nxt := append([]bool{}, state.Picked...)
	nxt[index] = pick
	return ToyState{nxt}
}

func score(state ToyState, inp ToyInput) int {
	total := 0
	for i, picked := range state.Picked {
		if picked {
			total += inp.Values[i]
		}
	}
	return total
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Scan()
	n, _ := strconv.Atoi(sc.Text())
	sc.Scan()
	vals := parseInts(sc.Text())
	inp := ToyInput{vals}
	state := ToyState{Picked: make([]bool, n)}

	for i := 0; i < n; i++ {
		state = applyMove(state, i, true)
		fmt.Printf("day %d: score=%d\n", i+1, score(state, inp))
	}
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}
