# 付録B Python / Go テンプレート集

**霊夢**: 毎回ゼロから書くの、しんどいの。

**魔理沙**: `python/templates/` と `go/templates/` に共通部品がある。ここは **コピー元の索引** だぜ。

---

## B.1 入出力テンプレート

| ファイル | 用途 |
|---------|------|
| `python/templates/io_template.py` | stdin から整数列 |
| `go/templates/io_template.go` | `bufio` + `strconv` |

```bash
python python/templates/io_template.py < data/sample.txt
go run go/templates/io_template.go < data/sample.txt
```

```python
# python/templates/io_template.py（抜粋）
import sys

def read_ints():
    return list(map(int, sys.stdin.readline().split()))

def main():
    n, = read_ints()
    a = read_ints()
    print(sum(a))
```

```go
// go/templates/io_template.go（抜粋）
func readInts(sc *bufio.Scanner) []int {
    sc.Scan()
    parts := strings.Fields(sc.Text())
    // ...
}
```

| やりたいこと | Python | Go |
|-------------|--------|-----|
| 1行1整数 | `int(input())` | `strconv.Atoi` |
| 複数整数 | `map(int, input().split())` | `strings.Fields` + loop |
| 高速出力 | `sys.stdout.write` | `bufio.NewWriter` |

---

## B.2 スコア計算テンプレート

| ファイル | 用途 |
|---------|------|
| `python/ch03/score_module.py` | Intro HC（State 分離版） |
| `python/ch01/score_intro_hc.py` | Intro HC（1ファイル版） |
| `python/ch04/score_ahc001.py` | AHC001 玩具版 |

**3層構造**（第3章）:

```text
read_*()     → ProblemInput, State
score_*()    → ScoreResult
main()       → stdin/stdout
```

```python
# スコア計算の骨格
def score(state) -> int:
    ...

def main():
    problem = read_problem(sys.stdin)
    state = read_solution(...)
    print(score(state))
```

```go
// Go も同様に read → score → main
func scoreSchedule(problem ProblemInput, state ScheduleState) ScoreResult
```

---

## B.3 焼きなまし法テンプレート

| ファイル | 用途 |
|---------|------|
| `python/templates/sa_template.py` | SA 骨格（T0=100, ALPHA=0.995） |
| `go/templates/sa_template.go` | 同上 |
| `python/ch08/sa_intro_hc.py` | Intro HC 向け本番例 |
| `python/ch18/sa_multi_neighborhood.py` | 複数近傍 + 再ヒート |

```python
# python/templates/sa_template.py — 定数
T0 = 100.0
ALPHA = 0.995

# 受理
if delta >= 0 or rng.random() < math.exp(delta / T):
    state = new_state
    score = new_score
T *= ALPHA
```

```go
// go/templates/sa_template.go
const (
    T0    = 100.0
    Alpha = 0.995
)
```

| パラメータ | 触り方 |
|-----------|--------|
| T0 | 大きいほど悪化受理が増える |
| ALPHA | 1に近いほど冷却が遅い |
| 近傍 | 問題ごとに差し替え |

---

## B.4 ビームサーチテンプレート

公式 `templates/` にはビーム用ファイルがない。**第9章** を参照。

| ファイル | 用途 |
|---------|------|
| `python/ch09/beam_fill.py` | グリッド埋め（簡略 AHC002） |
| `go/ch09/beam_fill.go` | 同上 |
| `python/ch14/slide_beam.py` | スライドパズル + ヒューリスティック |

```python
# ビームサーチの骨格
candidates = [initial_state]
for step in range(max_steps):
    next_candidates = []
    for state in candidates:
        for move in neighbors(state):
            next_candidates.append(apply(state, move))
    next_candidates.sort(key=score, reverse=True)
    candidates = next_candidates[:beam_width]
```

```go
// 優先度付きキュー + ビーム幅で枝刈り
// go/ch09/beam_fill.go を参照
```

---

## B.5 タイマーと提出管理

| ファイル | 用途 |
|---------|------|
| `python/templates/timer.py` | `Timer` クラス |
| `go/templates/timer.go` | `NewTimer`, `Expired()` |
| `python/ch02/ahc_main.py` | main + Timer 統合例 |
| `python/ch10/pipeline.py` | フェーズ別時間配分 |

```python
# python/templates/timer.py
class Timer:
    def __init__(self, limit_sec: float): ...
    def expired(self) -> bool: ...
```

```python
# 最良解の保持（提出用）
best_state, best_score = state, score
while not timer.expired():
    ...
    if new_score > best_score:
        best_state, best_score = new_state, new_score
# 終了後は best_state を出力
```

```go
// go/templates/timer.go
func (t *Timer) Expired() bool {
    return t.Remaining() <= 0
}
```

| 本番の注意 | 内容 |
|-----------|------|
| 提出間隔 | 同一問題は **5分** |
| TLE | 最良解を **必ず** 出力 |
| stderr | スコアログは stderr へ |

---

## テンプレート早見（章 → ファイル）

| やりたいこと | まず見るファイル |
|-------------|-----------------|
| 入出力 | `templates/io_template.*` |
| スコアだけ | `ch03/score_module.py` |
| 貪欲 | `ch05/greedy_delivery.py` |
| 2-opt | `ch06/two_opt.py` |
| SA | `templates/sa_template.py` → `ch08/` |
| ビーム | `ch09/beam_fill.py` |
| パイプライン | `ch10/pipeline.py` |
| 並列 SA | `ch20/parallel_sa.py` |

**霊夢**: コピー元が一覧にあると探しやすいのだ。

**魔理沙**: 新問題では **テンプレをコピーして chNN に置く**。`tools/run.sh` と `tools/local_test.sh` で動作確認するのを忘れるな。
