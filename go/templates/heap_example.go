// go/templates/heap_example.go
package main

import (
	"container/heap"
	"fmt"
)

type Item struct {
	Score int
	ID    string
}

type PriorityQueue []Item

func (pq PriorityQueue) Len() int { return len(pq) }

func (pq PriorityQueue) Less(i, j int) bool { return pq[i].Score < pq[j].Score }

func (pq PriorityQueue) Swap(i, j int) { pq[i], pq[j] = pq[j], pq[i] }

func (pq *PriorityQueue) Push(x any) {
	*pq = append(*pq, x.(Item))
}

func (pq *PriorityQueue) Pop() any {
	old := *pq
	n := len(old)
	item := old[n-1]
	*pq = old[:n-1]
	return item
}

func main() {
	pq := &PriorityQueue{}
	heap.Init(pq)
	heap.Push(pq, Item{Score: 10, ID: "a"})
	heap.Push(pq, Item{Score: 5, ID: "b"})
	best := heap.Pop(pq).(Item)
	fmt.Println(best)
}
