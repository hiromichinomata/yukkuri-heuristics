// go/templates/rng.go
package main

import (
	"fmt"
	"math/rand"
)

func main() {
	rng := rand.New(rand.NewSource(42))
	items := []int{1, 2, 3, 4, 5}
	fmt.Println("randint:", rng.Intn(10))
	rng.Shuffle(len(items), func(i, j int) {
		items[i], items[j] = items[j], items[i]
	})
	fmt.Println("shuffled:", items)
}
