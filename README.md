# ゆっくり霊夢・魔理沙が教えるヒューリスティック競技プログラミング

**ゆっくり霊夢** と **ゆっくり魔理沙** の掛け合いで、[AtCoder Heuristic Contest（AHC）](https://info.atcoder.jp/overview/contest/heuristic) を学ぶ教材です。  
Python / Go の両方で、レーティング帯（灰〜赤）に応じた解法を段階的に身につけます。

## はじめに

| 項目 | 内容 |
|------|------|
| 目次 | [docs/00-toc.md](docs/00-toc.md) |
| 第0章（使い方） | [docs/00.md](docs/00.md) |
| 付録 | [docs/appendix-a.md](docs/appendix-a.md) 〜 [appendix-f.md](docs/appendix-f.md) |

## 必要環境

| 言語 | 推奨バージョン |
|------|---------------|
| Python | 3.10 以上（CPython。本番提出は PyPy3 も可） |
| Go | 1.22 以上 |

```bash
git clone https://github.com/hiromichinomata/yukkuri-heuristics.git
cd yukkuri-heuristics

# 環境確認
./tools/check_env.sh
```

### Python（任意: venv）

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

## クイックスタート

```bash
# 入出力テンプレート
python python/templates/io_template.py < data/sample.txt
go run go/templates/io_template.go < data/sample.txt

# Intro HC 形式のスコア計算（第1・3章）
python python/ch01/score_intro_hc.py < data/ch01/sample.txt

# ローカル評価パイプライン（第2章）
./tools/local_test.sh data/ch02/input_only.txt
```

## リポジトリ構成

```text
yukkuri-heuristics/
├── README.md
├── docs/
│   ├── 00-toc.md          # 目次（ls で先頭に来るよう命名）
│   ├── 00.md … 30.md      # 各章本文
│   └── appendix-*.md      # 付録 A〜F
├── python/
│   ├── templates/         # 共通テンプレート（I/O, SA, タイマー等）
│   └── chNN/              # 章ごとのサンプルコード
├── go/
│   ├── templates/
│   └── chNN/
├── data/chNN/             # サンプル入力
├── tools/
│   ├── check_env.sh       # 環境チェック
│   ├── local_test.sh      # ソルバ → スコア計算
│   └── run.sh             # テンプレート実行
└── .cursor/skills/        # 章執筆用 Cursor スキル（任意）
```

## 章の読み方

1. [docs/00-toc.md](docs/00-toc.md) で全体像と自分のレーティング帯を確認
2. 該当する `docs/NN.md` を読む（掛け合い → ハンズオン → コード → 演習）
3. `python/chNN/` と `go/chNN/` を実行して手を動かす
4. [付録D](docs/appendix-d.md) の過去問リストで AtCoder 本番問題に挑戦

## 参考リンク

- [AHC レーティングのしくみ](https://info.atcoder.jp/overview/contest/rating)
- [Introduction to Heuristics Contest](https://atcoder.jp/contests/intro-heuristics)（入門者向け）
- 詳細なリンク集: [docs/appendix-f.md](docs/appendix-f.md)
