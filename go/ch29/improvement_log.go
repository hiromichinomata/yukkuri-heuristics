// go/ch29/improvement_log.go
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
)

type DayEntry struct {
	Day     int    `json:"day"`
	Date    string `json:"date"`
	Owner   string `json:"owner"`
	Score   int    `json:"score"`
	Notes   string `json:"notes"`
	Commits int    `json:"commits"`
}

type WeeklyLog struct {
	Contest string     `json:"contest"`
	Problem string     `json:"problem"`
	Team    string     `json:"team"`
	Unit    string     `json:"unit"`
	Days    []DayEntry `json:"days"`
}

func loadLog(path string) (WeeklyLog, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return WeeklyLog{}, err
	}
	var log WeeklyLog
	if err := json.Unmarshal(data, &log); err != nil {
		return WeeklyLog{}, err
	}
	return log, nil
}

func summarize(log WeeklyLog) {
	if len(log.Days) == 0 {
		fmt.Fprintln(os.Stderr, "no days in log")
		return
	}
	scores := make([]int, len(log.Days))
	for i, d := range log.Days {
		scores[i] = d.Score
	}
	best := scores[0]
	bestDay := log.Days[0].Day
	for i, s := range scores {
		if s > best {
			best = s
			bestDay = log.Days[i].Day
		}
	}
	first, last := scores[0], scores[len(scores)-1]
	delta := last - first
	pct := 0.0
	if first != 0 {
		pct = 100.0 * float64(delta) / float64(first)
	}

	fmt.Printf("contest: %s\n", log.Contest)
	fmt.Printf("problem: %s  team: %s\n", log.Problem, log.Team)
	fmt.Printf("days: %d  unit: %s\n\n", len(log.Days), log.Unit)
	fmt.Println("day  date        owner    score     delta    note")

	prev := -1
	for _, d := range log.Days {
		deltaS := ""
		if prev >= 0 {
			deltaS = fmt.Sprintf("%+d", d.Score-prev)
		}
		note := d.Notes
		if len(note) > 28 {
			note = note[:28]
		}
		fmt.Printf("%3d  %-10s  %-8s  %9d  %7s  %s\n",
			d.Day, d.Date, d.Owner, d.Score, deltaS, note)
		prev = d.Score
	}
	fmt.Println()
	fmt.Printf("start → end: %d → %d  (Δ %+d, %+.2f%%)\n", first, last, delta, pct)
	fmt.Printf("best: %d on day %d\n", best, bestDay)

	regressions := 0
	for i := 1; i < len(scores); i++ {
		if scores[i] < scores[i-1] {
			regressions++
		}
	}
	fmt.Printf("regression days: %d\n", regressions)
	commits := 0
	for _, d := range log.Days {
		commits += d.Commits
	}
	fmt.Fprintf(os.Stderr, "total commits: %d\n", commits)
}

func main() {
	input := flag.String("input", filepath.Join("data", "ch29", "weekly_log.json"), "weekly log JSON")
	flag.Parse()

	log, err := loadLog(*input)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read error: %v\n", err)
		os.Exit(1)
	}
	summarize(log)
}
