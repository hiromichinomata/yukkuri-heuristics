# 付録D 推奨過去問リスト（レーティング帯別）

**霊夢**: 練習問題、どれから手をつければいいの？

**魔理沙**: **今の色の帯** から始めて、解けたら1つ上の帯に進む。全部解く必要はないぜ。

---

## 一覧表

| 色 | レーティング | 推奨コンテスト・問題 | 本書の章 | 身につけること |
|----|-------------|---------------------|---------|---------------|
| 灰色 | 1–399 | [Intro HC](https://atcoder.jp/contests/intro-heuristics), [AHC001](https://atcoder.jp/contests/ahc001) | 第1–4章 | スコア計算、合法解、シミュレーション |
| 茶色 | 400–799 | [AHC005](https://atcoder.jp/contests/ahc005), [AHC006](https://atcoder.jp/contests/ahc006) | 第5–7章 | 貪欲、2-opt、粗視化 |
| 緑色 | 800–1199 | [AHC002](https://atcoder.jp/contests/ahc002), AHC011, AHC015 | 第8–10章 | SA、ビーム、パイプライン |
| 水色 | 1200–1599 | [AHC003](https://atcoder.jp/contests/ahc003), AHC009, AHC010 | 第11–14章 | インタラクティブ、タブー、データ構造 |
| 青色 | 1600–1999 | [AHC008](https://atcoder.jp/contests/ahc008), AHC014, AHC016 | 第15–18章 | LP、GA、マルチエージェント、高度SA |
| 黄色 | 2000–2399 | AHC020 以降（解説充実） | 第19–22章 | MCTS、並列、戦略、復習 |
| 橙色 | 2400–2799 | 直近2年の AHC 全問 | 第23–26章 | 問題固有、LNS、バンディット、vis |
| 赤色 | 2800– | 最新 AHC + 他サイト | 第27–30章 | 研究、高速化、チーム、解説執筆 |

---

## 灰色帯（1–399）

| 優先 | 問題 | 理由 |
|------|------|------|
| 1 | [Intro HC 問題B](https://atcoder.jp/contests/intro-heuristics/tasks/intro_heuristics_b) | スコア計算のみ。本書第1・3章 |
| 2 | [Intro HC 問題A](https://atcoder.jp/contests/intro-heuristics/tasks/intro_heuristics_a) | 貪欲の入門。公式ガイド付き |
| 3 | [AHC001](https://atcoder.jp/contests/ahc001/tasks/ahc001_a) | 配置の元祖。第4章玩具版の本番 |

```bash
# 本書ローカル（Intro HC 形式）
python python/ch03/score_module.py < data/ch03/sample.txt
python python/ch04/ahc001_grow.py < data/ch04/sample.txt
```

---

## 茶色帯（400–799）

| 優先 | 問題 | パターン | 本書 |
|------|------|---------|------|
| 1 | AHC005 Patrolling | path | 第6章 2-opt |
| 2 | AHC006 Food Delivery | path + 貪欲 | 第5章 |
| 3 | AHC001 再挑戦 | placement | 第4章 + 第5章 |

---

## 緑色帯（800–1199）

| 優先 | 問題 | 技法 |
|------|------|------|
| 1 | Intro HC 問題C | SA |
| 2 | AHC002 Walking on Tiles | ビームサーチ |
| 3 | AHC011 Sliding Tree Puzzle | 初期解 + SA（第10章） |

```bash
python python/ch08/sa_intro_hc.py < data/ch08/sample.txt
python python/ch09/beam_fill.py < data/ch09/sample.txt
python python/ch10/pipeline.py < data/ch10/sample.txt
```

---

## 水色帯（1200–1599）

| 優先 | 問題 | 技法 |
|------|------|------|
| 1 | AHC003 Shortest Path Queries | インタラクティブ + ダイクストラ |
| 2 | AHC010 Loop Lines | データ構造 + 合法手生成 |
| 3 | AHC009 | シミュレーション + 構造 |

```bash
python python/ch11/interactive_path.py --offline data/ch11/sample.txt
python python/ch13/loop_toy.py < data/ch13/sample.txt
```

---

## 青色帯（1600–1999）

| 優先 | 問題 | 技法 |
|------|------|------|
| 1 | AHC008 Territory | マルチエージェント |
| 2 | AHC014 / AHC016 | 配置・構造 |
| 3 | 割当・配置系 | LP 緩和（第15章） |

---

## 黄色帯（2000–2399）

| 優先 | 活動 |
|------|------|
| 1 | AHC020 以降を **解説付き** で復習（第22章） |
| 2 | 模擬コンテスト（第21章 `mock_contest.py --fast`） |
| 3 | 並列 multi-start SA（第20章） |

---

## 橙色・赤色帯（2400–）

| 帯 | 活動 |
|----|------|
| 橙 | 直近 AHC を **仮説3案比較**（第23章）、LNS・vis 必須 |
| 赤 | 他サイト参加、論文転用（第27章）、チーム戦（第29章） |

### 他サイト（参考）

| サイト | URL | 特徴 |
|--------|-----|------|
| CodinGame | https://www.codingame.com/ | マラソン・ボット戦 |
| Topcoder Marathon | https://www.topcoder.com/ | 長期ヒューリスティック |

---

## 進め方の型

```text
1. 付録C でパターンを当てる
2. 今の色の行から1問選ぶ
3. 本書の該当章 + ローカルテスターで実装
4. 解説を読み、第22章の復習シートで差分5点
5. 次の色の帯へ（無理なら同帯の別問題）
```

**霊夢**: Rated で失敗してもレートは下がらないから、怖くないのね。

**魔理沙**: その通り。**出て、直して、また出る** が最短ルートだ。Intro HC は何度でも Unrated で練習できるぜ。
