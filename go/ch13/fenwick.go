// go/ch13/fenwick.go
package main

import (
	"fmt"
	"time"
)

type Fenwick struct {
	n   int
	bit []int
}

func NewFenwick(n int) *Fenwick {
	return &Fenwick{n: n, bit: make([]int, n+1)}
}

func (f *Fenwick) Add(i, delta int) {
	i++
	for i <= f.n {
		f.bit[i] += delta
		i += i & -i
	}
}

func (f *Fenwick) Prefix(i int) int {
	i++
	s := 0
	for i > 0 {
		s += f.bit[i]
		i -= i & -i
	}
	return s
}

func (f *Fenwick) RangeSum(l, r int) int {
	if l == 0 {
		return f.Prefix(r)
	}
	return f.Prefix(r) - f.Prefix(l-1)
}

func naiveRangeSum(arr []int, l, r int) int {
	s := 0
	for i := l; i <= r; i++ {
		s += arr[i]
	}
	return s
}

func benchmark() {
	n, queries := 8000, 40000
	arr := make([]int, n)
	for i := range arr {
		arr[i] = 1
	}
	ops := make([][3]int, queries)
	for i := 0; i < queries; i++ {
		ops[i] = [3]int{i % n, (i * 7) % n, (i * 13) % n}
	}

	start := time.Now()
	totalNaive := 0
	for _, op := range ops {
		arr[op[0]] += op[2] % 3
		lo, hi := op[0], op[1]
		if lo > hi {
			lo, hi = hi, lo
		}
		totalNaive += naiveRangeSum(arr, lo, hi)
	}
	naiveMs := time.Since(start).Seconds() * 1000

	fw := NewFenwick(n)
	for i, v := range arr {
		fw.Add(i, v)
	}
	start = time.Now()
	totalFw := 0
	for _, op := range ops {
		fw.Add(op[0], op[2]%3)
		lo, hi := op[0], op[1]
		if lo > hi {
			lo, hi = hi, lo
		}
		totalFw += fw.RangeSum(lo, hi)
	}
	fwMs := time.Since(start).Seconds() * 1000

	fmt.Printf("n=%d queries=%d\n", n, queries)
	fmt.Printf("naive_range_sum_ms=%.2f checksum=%d\n", naiveMs, totalNaive)
	fmt.Printf("fenwick_ms=%.2f checksum=%d\n", fwMs, totalFw)
	fmt.Printf("speedup=%.1fx\n", naiveMs/max(fwMs, 1e-9))
}

func main() {
	benchmark()
}
