// go/ch21/mock_contest.go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"
)

type ProblemInput struct {
	Days  int
	Decay []int
	Gain  [][]int
}

type ScheduleState struct {
	Types []int
}

type SubmissionLog struct {
	Phase      string  `json:"phase"`
	ElapsedSec float64 `json:"elapsed_sec"`
	Score      int     `json:"score"`
	Note       string  `json:"note"`
}

func readProblem(path string) (ProblemInput, error) {
	var f *os.File
	var err error
	if path == "" {
		f = os.Stdin
	} else {
		f, err = os.Open(path)
		if err != nil {
			return ProblemInput{}, err
		}
		defer f.Close()
	}
	sc := bufio.NewScanner(f)
	var lines []string
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return ProblemInput{}, err
	}
	days, _ := strconv.Atoi(lines[0])
	decay := parseInts(lines[1])
	gain := make([][]int, days)
	for i := 0; i < days; i++ {
		gain[i] = parseInts(lines[2+i])
	}
	return ProblemInput{days, decay, gain}, nil
}

func parseInts(line string) []int {
	parts := strings.Fields(line)
	out := make([]int, len(parts))
	for i, p := range parts {
		out[i], _ = strconv.Atoi(p)
	}
	return out
}

func scoreSchedule(p ProblemInput, s ScheduleState) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= p.Days; day++ {
		t := s.Types[day-1] - 1
		satisfaction += p.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += p.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	score := 1000000 + satisfaction
	if score < 0 {
		return 0
	}
	return score
}

func finalSat(p ProblemInput, types []int) int {
	last := make([]int, 26)
	satisfaction := 0
	for day := 1; day <= len(types); day++ {
		t := types[day-1] - 1
		satisfaction += p.Gain[day-1][t]
		last[t] = day
		decay := 0
		for i := 0; i < 26; i++ {
			decay += p.Decay[i] * (day - last[i])
		}
		satisfaction -= decay
	}
	return satisfaction
}

func greedySchedule(p ProblemInput) ScheduleState {
	schedule := make([]int, 0, p.Days)
	for day := 1; day <= p.Days; day++ {
		bestT, bestSat := 1, -1<<30
		for t := 1; t <= 26; t++ {
			trial := append(append([]int{}, schedule...), t)
			sat := finalSat(p, trial)
			if sat > bestSat {
				bestSat = sat
				bestT = t
			}
		}
		schedule = append(schedule, bestT)
	}
	return ScheduleState{schedule}
}

func briefSA(p ProblemInput, state ScheduleState, deadline time.Time, rng *rand.Rand) ScheduleState {
	current := append([]int{}, state.Types...)
	score := scoreSchedule(p, ScheduleState{current})
	best := append([]int{}, current...)
	bestScore := score
	temperature := 5000.0
	alpha := 0.995

	for time.Now().Before(deadline) {
		day := rng.Intn(p.Days)
		trial := append([]int{}, current...)
		trial[day] = 1 + rng.Intn(26)
		trialScore := scoreSchedule(p, ScheduleState{trial})
		delta := trialScore - score
		if delta >= 0 || rng.Float64() < math.Exp(float64(delta)/temperature) {
			current = trial
			score = trialScore
			if score > bestScore {
				best = append([]int{}, current...)
				bestScore = score
			}
		}
		temperature *= alpha
	}
	return ScheduleState{best}
}

type MockContest struct {
	problem   ProblemInput
	phaseMin  []float64
	fast      bool
	jsonLog   bool
	start     time.Time
	logs      []SubmissionLog
	rng       *rand.Rand
	state     ScheduleState
	bestScore int
}

func (c *MockContest) elapsed() float64 {
	return time.Since(c.start).Seconds()
}

func (c *MockContest) emit(phase, event string, score int, note string) {
	entry := SubmissionLog{
		Phase:      phase + ":" + event,
		ElapsedSec: c.elapsed(),
		Score:      score,
		Note:       note,
	}
	c.logs = append(c.logs, entry)
	fmt.Fprintf(os.Stderr, "[contest] phase=%s event=%s t=%.2fs score=%d %s\n",
		phase, event, entry.ElapsedSec, score, note)
	if c.jsonLog {
		b, _ := json.Marshal(entry)
		fmt.Fprintln(os.Stderr, string(b))
	}
}

func (c *MockContest) waitPhase(name string, minutes float64) {
	sec := minutes * 60.0
	if c.fast {
		sec = minutes
	}
	end := c.elapsed() + sec
	c.emit(name, "start", c.bestScore, fmt.Sprintf("duration=%.1fs", sec))
	for c.elapsed() < end {
		time.Sleep(50 * time.Millisecond)
	}
	c.emit(name, "end", c.bestScore, "phase complete")
}

func (c *MockContest) run() ScheduleState {
	c.waitPhase("read", c.phaseMin[0])
	c.waitPhase("implement", c.phaseMin[1])
	c.emit("implement", "work", c.bestScore, "greedy build")
	c.state = greedySchedule(c.problem)
	c.bestScore = scoreSchedule(c.problem, c.state)
	c.emit("implement", "submit", c.bestScore, "initial solution")

	c.waitPhase("improve", c.phaseMin[2])
	improveDur := c.phaseMin[2] * 60.0
	if c.fast {
		improveDur = c.phaseMin[2]
	}
	deadline := time.Now().Add(time.Duration(improveDur * float64(time.Second)))
	c.emit("improve", "work", c.bestScore, "brief SA")
	c.state = briefSA(c.problem, c.state, deadline, c.rng)
	c.bestScore = scoreSchedule(c.problem, c.state)
	c.emit("improve", "submit", c.bestScore, "improved solution")

	c.waitPhase("submit", c.phaseMin[3])
	c.emit("submit", "final", c.bestScore, "stdout schedule")
	return c.state
}

func defaultInput() string {
	for _, rel := range []string{"data/ch23/sample.txt", "data/ch08/sample.txt"} {
		if _, err := os.Stat(rel); err == nil {
			return rel
		}
	}
	return "data/ch23/sample.txt"
}

func main() {
	fast := false
	jsonLog := false
	inputPath := ""
	for _, arg := range os.Args[1:] {
		switch arg {
		case "--fast":
			fast = true
		case "--json-log":
			jsonLog = true
		default:
			if !strings.HasPrefix(arg, "-") {
				inputPath = arg
			}
		}
	}
	if os.Getenv("CONTEST_FAST") == "1" {
		fast = true
	}
	if inputPath == "" {
		inputPath = defaultInput()
		fmt.Fprintf(os.Stderr, "input=%s\n", inputPath)
	}

	problem, err := readProblem(inputPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	phaseMin := []float64{30, 60, 90, 30}
	if fast {
		phaseMin = []float64{0.3, 0.5, 0.8, 0.2}
	}
	types := make([]int, problem.Days)
	for i := range types {
		types[i] = 1
	}
	contest := &MockContest{
		problem:   problem,
		phaseMin:  phaseMin,
		fast:      fast,
		jsonLog:   jsonLog,
		start:     time.Now(),
		rng:       rand.New(rand.NewSource(42)),
		state:     ScheduleState{types},
		bestScore: scoreSchedule(problem, ScheduleState{types}),
	}
	final := contest.run()
	for _, t := range final.Types {
		fmt.Println(t)
	}
	fmt.Fprintf(os.Stderr, "final_score=%d elapsed=%.2fs submissions=%d\n",
		contest.bestScore, contest.elapsed(), len(contest.logs))
}
