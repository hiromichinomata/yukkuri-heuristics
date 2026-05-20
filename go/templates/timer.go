// go/templates/timer.go
package main

import (
	"fmt"
	"time"
)

type Timer struct {
	start time.Time
	limit time.Duration
}

func NewTimer(limitSec float64) *Timer {
	return &Timer{
		start: time.Now(),
		limit: time.Duration(limitSec * float64(time.Second)),
	}
}

func (t *Timer) Elapsed() time.Duration {
	return time.Since(t.start)
}

func (t *Timer) Remaining() time.Duration {
	return t.limit - t.Elapsed()
}

func (t *Timer) Expired() bool {
	return t.Remaining() <= 0
}

func main() {
	timer := NewTimer(0.01)
	for !timer.Expired() {
	}
	fmt.Printf("elapsed: %.3fs\n", timer.Elapsed().Seconds())
}
