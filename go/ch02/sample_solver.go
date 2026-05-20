// go/ch02/sample_solver.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Scan()
	d, _ := strconv.Atoi(sc.Text())
	sc.Scan() // c
	for i := 0; i < d; i++ {
		sc.Scan() // s row
	}
	for i := 0; i < d; i++ {
		fmt.Println(1)
	}
}
