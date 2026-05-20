# Chapter writing reference (yukkuri-heuristics)

## Chapter index

| File | Chapter | Title | Rating band |
|------|---------|-------|-------------|
| `docs/00.md` | 0 | 本書の使い方 | — |
| `docs/01.md` | 1 | ヒューリスティック競技プログラミング概論 | — |
| `docs/02.md` | 2 | 開発環境とコンテスト参加の準備 | Gray |
| `docs/03.md` | 3 | 問題文の読み方と設計の第一歩 | Gray |
| `docs/04.md` | 4 | シミュレーションと素朴な解法 | Gray |
| `docs/05.md` | 5 | 貪欲法 | Brown |
| `docs/06.md` | 6 | 山登り法 | Brown |
| `docs/07.md` | 7 | 問題の粗視化と分割 | Brown |
| `docs/08.md` | 8 | 焼きなまし法 | Green |
| `docs/09.md` | 9 | ビームサーチ | Green |
| `docs/10.md` | 10 | 多段パイプライン | Green |
| `docs/11.md` | 11 | インタラクティブ問題 | Cyan |
| `docs/12.md` | 12 | タブーサーチと反復局所探索 | Cyan |
| `docs/13.md` | 13 | データ構造で速くする | Cyan |
| `docs/14.md` | 14 | パズル・構造問題 | Cyan |
| `docs/15.md` | 15 | 整数計画と緩和 | Blue |
| `docs/16.md` | 16 | 遺伝的アルゴリズム | Blue |
| `docs/17.md` | 17 | マルチエージェント問題 | Blue |
| `docs/18.md` | 18 | 高度な焼きなまし | Blue |
| `docs/19.md` | 19 | MCTS | Yellow |
| `docs/20.md` | 20 | 並列探索と多開始 | Yellow |
| `docs/21.md` | 21 | コンテスト戦略 | Yellow |
| `docs/22.md` | 22 | 過去問の徹底復習 | Yellow |
| `docs/23.md` | 23 | 問題固有解法の設計 | Orange |
| `docs/24.md` | 24 | 大近傍探索 (LNS) | Orange |
| `docs/25.md` | 25 | 高度なインタラクティブ | Orange |
| `docs/26.md` | 26 | ビジュアライザ駆動開発 | Orange |
| `docs/27.md` | 27 | 最新研究と AHC 解法 | Red |
| `docs/28.md` | 28 | 超高速実装 | Red |
| `docs/29.md` | 29 | チーム戦・マラソン | Red |
| `docs/30.md` | 30 | コンテスト後の成長 | Red |

Source of truth for subsection bullets: `docs/toc.md`.

## Section markdown template

```markdown
# 第N章 章タイトル

---

## N.1 節タイトル

**霊夢**: （読者の疑問）

**魔理沙**: （概念の説明）

**霊夢**: （確認・突っ込み）

**魔理沙**: （コードへ）

```python
# python/chNN/example.py
...
```

```go
// go/chNN/example.go
...
```

**霊夢**: （理解の言い直し）

**魔理沙**: （補足）

---

## N.M ハンズオン: 問題名

**霊夢**: 実際に動かすの？

**魔理沙**: こう実行するぜ。

```bash
python python/chNN/solution.py < data/chNN/sample.txt
go run go/chNN/solution.go < data/chNN/sample.txt
```

---

## 演習

1. （パラメータを1つ変えて観察）
2. （近傍操作を追加）
3. （任意: AHC 過去問への応用）

---

## 章末まとめ

**霊夢**: まとめると？

**魔理沙**: こうだぜ。

> **第N章まとめ**
>
> - ポイント1
> - ポイント2
> - 次章: 第N+1章「…」
```

## Shared templates

| Template | Python | Go |
|----------|--------|-----|
| I/O | `python/templates/io_template.py` | `go/templates/io_template.go` |
| Timer | `python/templates/timer.py` | `go/templates/timer.go` |
| RNG | `python/templates/rng.py` | `go/templates/rng.go` |
| Heap | `python/templates/heap_example.py` | `go/templates/heap_example.go` |
| SA | `python/templates/sa_template.py` | `go/templates/sa_template.go` |

Import or copy patterns from templates; extend in `python/chNN/` rather than duplicating boilerplate in markdown only.

## Recommended AHC problems by band

Use in hands-on / 演習 when toc specifies or when a concrete example is needed:

| Band | Problems |
|------|----------|
| Gray | Intro HC, AHC001 |
| Brown | AHC005, AHC006 |
| Green | AHC002, AHC011, AHC015 |
| Cyan | AHC003, AHC009, AHC010 |
| Blue | AHC008, AHC014, AHC016 |

Do not paste full problem statements; link to AtCoder and describe inputs/outputs needed for local samples.

## Code style

**Python**

- Standard library preferred; type hints welcome
- `if __name__ == "__main__":` for runnable scripts
- stderr for debug logs (`log_score`, timer progress)

**Go**

- Each file runnable via `go run go/chNN/file.go` (single-file `main` packages OK)
- `bufio` for fast I/O in contests
- Match Python algorithm structure (same function boundaries where practical)

## Quality checklist

- [ ] All toc.md subsections for chapter N are covered
- [ ] At least 10 code blocks in technique chapters (more is better)
- [ ] Both `python/chNN/` and `go/chNN/` exist when chapter introduces runnable solution
- [ ] Commands in doc match actual paths
- [ ] 霊夢 / 魔理沙 labels on every dialogue line
- [ ] 章末まとめ present
- [ ] No 「ゆっくり」= slow learning wording
- [ ] Code runs without error on sample data

## External links (reuse in chapters)

- [AHC レーティングのしくみ](https://info.atcoder.jp/overview/contest/rating)
- [Introduction to Heuristics Contest](https://atcoder.jp/contests/intro-heuristics)
- [Heuristic Contest 概要](https://info.atcoder.jp/overview/contest/heuristic)
