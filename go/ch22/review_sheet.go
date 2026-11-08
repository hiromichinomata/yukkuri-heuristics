// go/ch22/review_sheet.go
// 過去問復習用 Markdown テンプレートを生成・既存シートに追記（python/ch22/review_sheet.py と同じ動作）
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type Pattern struct {
	ID              string   `json:"id"`
	Name            string   `json:"name"`
	Keywords        []string `json:"keywords"`
	ExampleContests []string `json:"example_contests"`
	TypicalMoves    []string `json:"typical_moves"`
	ReviewQuestions []string `json:"review_questions"`
}

type Catalog struct {
	Version  int       `json:"version"`
	Patterns []Pattern `json:"patterns"`
}

func loadCatalog(path string) ([]Pattern, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var c Catalog
	if err := json.Unmarshal(raw, &c); err != nil {
		return nil, err
	}
	return c.Patterns, nil
}

func patternOptions(catalog []Pattern) string {
	lines := make([]string, 0, len(catalog))
	for _, p := range catalog {
		ex := p.ExampleContests
		if len(ex) > 2 {
			ex = ex[:2]
		}
		lines = append(lines, fmt.Sprintf("- **%s** — %s（例: %s）", p.ID, p.Name, strings.Join(ex, ", ")))
	}
	return strings.Join(lines, "\n")
}

// 復習シートの雛形。”' はコードフェンス（```）に置換される
const sheetTemplate = `# 過去問復習シート — {{CONTEST}} / {{PROBLEM}}

- **日付**: {{TODAY}}
- **パターン**: {{PATTERN_ID}}（{{PATTERN_NAME}}）
- **スコア**: {{SCORE}}

## 1. 自力（タイマー付き）

- [ ] 問題文を 15 分で読み切った
- [ ] 仮説を 3 つ書いた
- [ ] 動く提出（またはローカルスコア）を 1 回出した

メモ:

'''
（ここに仮説・実装方針）
'''

## 2. 解説・editorial

- [ ] 公式解説 / 上位スライドを読んだ
- [ ] 自分との差分を 5 点書いた

| # | 上位の工夫 | 自分の実装 |
|---|-----------|-----------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

## 3. 再実装

- [ ] 解説を見ずに 1 機能だけ再現した
- [ ] スコア差分を計測した（前: ___ → 後: ___）

## 4. パターン照合（第22章カタログ）

{{PATTERN_OPTIONS}}

### この問題向けチェック

{{REVIEW_Q}}

## 5. 次回への 3 点

1.
2.
3.
`

func renderTemplate(contest, problem, patternID string, catalog []Pattern, score *string) string {
	patternName := patternID
	reviewQ := "- （パターン未設定）"
	for _, p := range catalog {
		if p.ID == patternID {
			patternName = p.Name
			qs := make([]string, len(p.ReviewQuestions))
			for i, q := range p.ReviewQuestions {
				qs[i] = "- [ ] " + q
			}
			if len(qs) > 0 {
				reviewQ = strings.Join(qs, "\n")
			}
			break
		}
	}
	scoreLine := "（未記入）"
	if score != nil {
		scoreLine = *score
	}
	today := time.Now().Format("2006-01-02")

	return strings.NewReplacer(
		"{{CONTEST}}", contest,
		"{{PROBLEM}}", problem,
		"{{TODAY}}", today,
		"{{PATTERN_ID}}", patternID,
		"{{PATTERN_NAME}}", patternName,
		"{{SCORE}}", scoreLine,
		"{{PATTERN_OPTIONS}}", patternOptions(catalog),
		"{{REVIEW_Q}}", reviewQ,
		"'''", "```", // Go の生文字列にはバッククォートを書けないので置換する
	).Replace(sheetTemplate)
}

// heading の節を body で置き換える（なければ末尾に追加）
func fillSection(content, heading, body string) string {
	marker := "## " + heading
	idx := strings.Index(content, marker)
	if idx == -1 {
		return content + "\n" + marker + "\n\n" + body + "\n"
	}
	head, rest := content[:idx], content[idx+len(marker):]
	next := strings.Index(rest, "\n## ")
	if next == -1 {
		return head + marker + "\n\n" + body + "\n"
	}
	return head + marker + "\n\n" + body + "\n" + rest[next:]
}

func main() {
	catalogPath := filepath.Join("data", "ch22", "pattern_catalog.json")
	catalog, err := loadCatalog(catalogPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "catalog:", err, "(リポジトリのルートで実行してください)")
		os.Exit(1)
	}

	contest := flag.String("contest", "AHC0XX", "コンテスト名")
	problem := flag.String("problem", "A", "問題記号")
	pattern := flag.String("pattern", "scheduling", "典型パターン ID")
	score := flag.String("score", "", "自分のスコア")
	output := flag.String("o", "", "出力ファイル（省略時は stdout）")
	flag.StringVar(output, "output", "", "出力ファイル（-o と同じ）")
	appendNote := flag.String("append-note", "", "既存シートにメモ追記（-o で指定したファイル）")
	flag.Parse()

	valid := false
	ids := make([]string, len(catalog))
	for i, p := range catalog {
		ids[i] = p.ID
		if p.ID == *pattern {
			valid = true
		}
	}
	if !valid {
		fmt.Fprintf(os.Stderr, "invalid --pattern %q (choose from %s)\n", *pattern, strings.Join(ids, ", "))
		os.Exit(2)
	}

	if *appendNote != "" && *output != "" {
		text := ""
		if raw, err := os.ReadFile(*output); err == nil {
			text = string(raw)
		}
		updated := fillSection(text, "追記メモ", *appendNote)
		if err := os.WriteFile(*output, []byte(updated), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr, "wrote append to %s\n", *output)
		return
	}

	var scorePtr *string
	flag.Visit(func(f *flag.Flag) {
		if f.Name == "score" {
			scorePtr = score
		}
	})
	md := renderTemplate(*contest, *problem, *pattern, catalog, scorePtr)
	if *output != "" {
		if err := os.MkdirAll(filepath.Dir(*output), 0o755); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := os.WriteFile(*output, []byte(md), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr, "wrote %s\n", *output)
		return
	}
	fmt.Println(md)
}
