// go/ch27/paper_transfer.go
// 論文メモ YAML（または JSON）から AHC 転用アイデアを抽出し、玩具検証を実行（第27章）
// python/ch27/paper_transfer.py と同じ出力。YAML は標準ライブラリにないので簡易ローダーで読む。
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// ---------- YAML サブセットの簡易ローダー ----------
// 対応: インデントによる入れ子の map / list、"- key: value" 形式の list of map、
//       [a, b] のフロー list、"|" のブロック文字列、引用符付き文字列、整数・小数・真偽値。

type yamlParser struct {
	lines []string
	i     int
}

func indentOf(line string) int { return len(line) - len(strings.TrimLeft(line, " ")) }

func skippable(line string) bool {
	t := strings.TrimSpace(line)
	return t == "" || strings.HasPrefix(t, "#")
}

func isListItem(t string) bool { return strings.HasPrefix(t, "- ") || t == "-" }

// "key: value" / "key:" を分ける
func splitKey(text string) (string, string, bool) {
	if strings.HasPrefix(text, `"`) || strings.HasPrefix(text, "'") || strings.HasPrefix(text, "[") {
		return "", "", false
	}
	if strings.HasSuffix(text, ":") {
		return strings.TrimSpace(text[:len(text)-1]), "", true
	}
	if k, v, ok := strings.Cut(text, ": "); ok {
		return strings.TrimSpace(k), strings.TrimSpace(v), true
	}
	return "", "", false
}

func parseScalar(raw string) any {
	val := strings.TrimSpace(raw)
	if len(val) >= 2 && val[0] == '"' && val[len(val)-1] == '"' {
		var s string
		if err := json.Unmarshal([]byte(val), &s); err == nil {
			return s
		}
		return val[1 : len(val)-1]
	}
	if len(val) >= 2 && val[0] == '\'' && val[len(val)-1] == '\'' {
		return strings.ReplaceAll(val[1:len(val)-1], "''", "'")
	}
	if before, _, ok := strings.Cut(val, " #"); ok { // 行末コメント
		val = strings.TrimRight(before, " ")
	}
	if strings.HasPrefix(val, "[") && strings.HasSuffix(val, "]") {
		inner := strings.TrimSpace(val[1 : len(val)-1])
		out := []any{}
		if inner == "" {
			return out
		}
		for _, x := range strings.Split(inner, ",") {
			out = append(out, parseScalar(x))
		}
		return out
	}
	switch val {
	case "", "~", "null":
		return nil
	case "true":
		return true
	case "false":
		return false
	}
	if n, err := strconv.Atoi(val); err == nil {
		return n
	}
	if f, err := strconv.ParseFloat(val, 64); err == nil {
		return f
	}
	return val
}

func (p *yamlParser) skip() {
	for p.i < len(p.lines) && skippable(p.lines[p.i]) {
		p.i++
	}
}

func (p *yamlParser) parse() (any, error) {
	p.skip()
	if p.i >= len(p.lines) {
		return map[string]any{}, nil
	}
	return p.block(indentOf(p.lines[p.i]))
}

func (p *yamlParser) block(indent int) (any, error) {
	if isListItem(strings.TrimSpace(p.lines[p.i])) {
		return p.list(indent)
	}
	return p.mapping(indent)
}

func (p *yamlParser) list(indent int) (any, error) {
	out := []any{}
	for {
		p.skip()
		if p.i >= len(p.lines) {
			return out, nil
		}
		line := p.lines[p.i]
		item := strings.TrimSpace(line)
		if indentOf(line) != indent || !isListItem(item) {
			return out, nil
		}
		rest := strings.TrimSpace(item[1:])
		if rest == "" {
			p.i++
			p.skip()
			v, err := p.block(indentOf(p.lines[p.i]))
			if err != nil {
				return nil, err
			}
			out = append(out, v)
		} else if _, _, ok := splitKey(rest); ok {
			// "- key: value" は、ダッシュの次の位置から始まる map とみなす
			childIndent := indent + (len(item) - len(rest))
			p.lines[p.i] = strings.Repeat(" ", childIndent) + rest
			v, err := p.mapping(childIndent)
			if err != nil {
				return nil, err
			}
			out = append(out, v)
		} else {
			out = append(out, parseScalar(rest))
			p.i++
		}
	}
}

func (p *yamlParser) mapping(indent int) (any, error) {
	out := map[string]any{}
	for {
		p.skip()
		if p.i >= len(p.lines) {
			return out, nil
		}
		line := p.lines[p.i]
		if indentOf(line) != indent || strings.HasPrefix(strings.TrimSpace(line), "- ") {
			return out, nil
		}
		key, val, ok := splitKey(strings.TrimSpace(line))
		if !ok {
			return nil, fmt.Errorf("YAML line %d: expected 'key: value': %q", p.i+1, line)
		}
		p.i++
		switch {
		case val == "|" || val == "|-":
			out[key] = p.blockScalar(indent, val == "|")
		case val == "":
			p.skip()
			if p.i < len(p.lines) && (indentOf(p.lines[p.i]) > indent ||
				(indentOf(p.lines[p.i]) == indent && strings.HasPrefix(strings.TrimSpace(p.lines[p.i]), "- "))) {
				v, err := p.block(indentOf(p.lines[p.i]))
				if err != nil {
					return nil, err
				}
				out[key] = v
			} else {
				out[key] = nil
			}
		default:
			out[key] = parseScalar(val)
		}
	}
}

func (p *yamlParser) blockScalar(parentIndent int, keepNewline bool) string {
	var body []string
	blockIndent := -1
	for p.i < len(p.lines) {
		line := p.lines[p.i]
		if strings.TrimSpace(line) == "" {
			body = append(body, "")
			p.i++
			continue
		}
		ind := indentOf(line)
		if ind <= parentIndent {
			break
		}
		if blockIndent < 0 {
			blockIndent = ind
		}
		body = append(body, line[blockIndent:])
		p.i++
	}
	for len(body) > 0 && body[len(body)-1] == "" {
		body = body[:len(body)-1]
	}
	s := strings.Join(body, "\n")
	if keepNewline && len(body) > 0 {
		s += "\n"
	}
	return s
}

func loadNotes(path string) (map[string]any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var data any
	if strings.HasSuffix(path, ".json") {
		err = json.Unmarshal(raw, &data)
	} else {
		p := &yamlParser{lines: strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n")}
		data, err = p.parse()
	}
	if err != nil {
		return nil, err
	}
	m, _ := data.(map[string]any)
	if m == nil {
		m = map[string]any{}
	}
	return m, nil
}

// ---------- 表示ヘルパ（Python の出力に合わせる） ----------

func get(m any, key string, def any) any {
	if mm, ok := m.(map[string]any); ok {
		if v, ok := mm[key]; ok {
			return v
		}
	}
	return def
}

// Python の str() / repr() 風の表示（list は [a, b]、整数値の float は整数で出す）
func pyStr(v any) string {
	switch x := v.(type) {
	case nil:
		return "None"
	case bool:
		if x {
			return "True"
		}
		return "False"
	case float64:
		if x == math.Trunc(x) {
			return strconv.FormatInt(int64(x), 10)
		}
		return strconv.FormatFloat(x, 'g', -1, 64)
	case []any:
		parts := make([]string, len(x))
		for i, e := range x {
			if s, ok := e.(string); ok {
				parts[i] = "'" + s + "'"
			} else {
				parts[i] = pyStr(e)
			}
		}
		return "[" + strings.Join(parts, ", ") + "]"
	default:
		return fmt.Sprint(x)
	}
}

func toFloat(v any) float64 {
	switch x := v.(type) {
	case int:
		return float64(x)
	case float64:
		return x
	}
	return 0
}

// ---------- 玩具検証: 2-opt ----------

type pt struct{ x, y float64 }

func tourLength(pts []pt) float64 {
	n := len(pts)
	if n < 2 {
		return 0
	}
	total := 0.0
	for i := 0; i < n; i++ {
		a, b := pts[i], pts[(i+1)%n]
		total += math.Hypot(b.x-a.x, b.y-a.y)
	}
	return total
}

func twoOptOnce(points []pt) ([]pt, float64) {
	n := len(points)
	best := append([]pt{}, points...)
	bestLen := tourLength(best)
	// 辺 (i, i+1) と (j, j+1) を張り替える。i=0 のとき j=n-1 は辺 (n-1, 0) が隣接するので除く
	for i := 0; i < n-1; i++ {
		end := n
		if i == 0 {
			end = n - 1
		}
		for j := i + 2; j < end; j++ {
			cand := append([]pt{}, best...)
			for l, r := i+1, j; l < r; l, r = l+1, r-1 {
				cand[l], cand[r] = cand[r], cand[l]
			}
			if l := tourLength(cand); l+1e-9 < bestLen {
				best, bestLen = cand, l
			}
		}
	}
	return best, bestLen
}

func formatPoints(pts []pt) string {
	parts := make([]string, len(pts))
	for i, p := range pts {
		parts[i] = "[" + pyStr(p.x) + ", " + pyStr(p.y) + "]"
	}
	return "[" + strings.Join(parts, ", ") + "]"
}

func runToyVerify(spec any) {
	algo := pyStr(get(spec, "algorithm", "two_opt"))
	rawPts, _ := get(spec, "points", []any{}).([]any)
	if algo != "two_opt" {
		fmt.Fprintf(os.Stderr, "toy_verify: unsupported algorithm %s\n", algo)
		return
	}
	if len(rawPts) < 3 {
		fmt.Fprintln(os.Stderr, "toy_verify: need at least 3 points")
		return
	}
	pts := make([]pt, len(rawPts))
	for i, rp := range rawPts {
		xy, _ := rp.([]any)
		if len(xy) >= 2 {
			pts[i] = pt{toFloat(xy[0]), toFloat(xy[1])}
		}
	}
	before := tourLength(pts)
	improved, after := twoOptOnce(pts)
	fmt.Println("=== toy verification (2-opt on sample tour) ===")
	fmt.Printf("points: %s\n", formatPoints(pts))
	fmt.Printf("length before: %.4f\n", before)
	fmt.Printf("length after:  %.4f\n", after)
	fmt.Printf("improved: %s\n", pyStr(after < before-1e-9))
	fmt.Printf("tour after 2-opt: %s\n", formatPoints(improved))
}

func printTransferIdeas(notes map[string]any) {
	paper := get(notes, "paper", map[string]any{})
	fmt.Println("=== paper ===")
	fmt.Printf("title: %s\n", pyStr(get(paper, "title", "?")))
	fmt.Printf("year: %s  venue: %s\n", pyStr(get(paper, "year", "?")), pyStr(get(paper, "venue", "?")))
	fmt.Println()
	fmt.Println("=== key ideas → AHC ===")
	ideas, _ := get(notes, "key_ideas", []any{}).([]any)
	for _, item := range ideas {
		if _, ok := item.(map[string]any); ok {
			fmt.Printf("- %s: %s\n", pyStr(get(item, "name", "?")), pyStr(get(item, "summary", "")))
			fmt.Printf("  AHC: %s\n", pyStr(get(item, "ahc_analogy", "")))
		} else {
			fmt.Printf("- %s\n", pyStr(item))
		}
	}
	fmt.Println()
	fmt.Println("=== transfer candidates ===")
	cands, _ := get(notes, "transfer_candidates", []any{}).([]any)
	for _, c := range cands {
		if _, ok := c.(map[string]any); ok {
			fmt.Printf("- target: %s\n", pyStr(get(c, "target", "?")))
			fmt.Printf("  technique: %s\n", pyStr(get(c, "technique", "?")))
			fmt.Printf("  expected_gain: %s\n", pyStr(get(c, "expected_gain", "?")))
			fmt.Printf("  risk: %s\n", pyStr(get(c, "risk", "?")))
		} else {
			fmt.Printf("- %s\n", pyStr(c))
		}
	}
	if reader, _ := get(notes, "reader_notes", "").(string); reader != "" {
		fmt.Println()
		fmt.Println("=== reader notes (excerpt) ===")
		r := []rune(strings.TrimSpace(reader))
		excerpt := r
		if len(r) > 200 {
			excerpt = r[:200]
		}
		suffix := ""
		if len([]rune(reader)) > 200 {
			suffix = "..."
		}
		fmt.Println(string(excerpt) + suffix)
	}
}

func main() {
	path := filepath.Join("data", "ch27", "paper_notes.yaml")
	if len(os.Args) > 1 {
		path = os.Args[1]
	}
	notes, err := loadNotes(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	printTransferIdeas(notes)
	fmt.Println()
	runToyVerify(get(notes, "toy_verify", map[string]any{}))
}
