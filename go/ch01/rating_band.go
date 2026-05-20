// go/ch01/rating_band.go
package main

import "fmt"

func ratingBand(r int) string {
	type band struct {
		limit int
		name  string
	}
	bands := []band{
		{400, "Gray"},
		{800, "Brown"},
		{1200, "Green"},
		{1600, "Cyan"},
		{2000, "Blue"},
		{2400, "Yellow"},
		{2800, "Orange"},
		{1e9, "Red"},
	}
	for _, b := range bands {
		if r < b.limit {
			return b.name
		}
	}
	return "Red"
}

func main() {
	for _, r := range []int{0, 399, 800, 1500, 2100, 3000} {
		fmt.Println(r, ratingBand(r))
	}
}
