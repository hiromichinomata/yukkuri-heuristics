// go/templates/io_template.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func readInts(sc *bufio.Scanner) []int {
	sc.Scan()
	parts := strings.Fields(sc.Text())
	out := make([]int, len(parts))
	for i, p := range parts {
		v, _ := strconv.Atoi(p)
		out[i] = v
	}
	return out
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	n := readInts(sc)[0]
	a := readInts(sc)
	if len(a) != n {
		fmt.Fprintf(os.Stderr, "expected %d integers, got %d\n", n, len(a))
		os.Exit(1)
	}
	sum := 0
	for _, v := range a {
		sum += v
	}
	fmt.Println(sum)
}
