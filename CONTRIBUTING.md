# 執筆・メンテナンス用メモ

本文やコードを直す人向けの情報です。学習者は [README.md](README.md) と [docs/00-toc.md](docs/00-toc.md) から読み始めてください。

## 直したあとの確認

```bash
# 全章のサンプルを Python / Go で一括実行（go vet・構文チェック・Python/Go の出力一致・単体テストも含む）
./tools/smoke_test.sh

# 単体テストだけ
python -m unittest discover -s tests -v
```

| テスト | 確かめること |
|--------|-------------|
| `tests/test_consistency.py` | 差分更新と全再計算の一致、ランダム入力での Python / Go 一致、YAML ローダー |
| `tests/test_doc_snippets.py` | 本文のコードと実ファイルのずれ |
| `tests/test_doc_outputs.py` | 本文の出力例と、実際にコマンドを動かした出力のずれ |
| `tests/test_doc_structure.py` | 目次と見出しの一致、「第N章 N.M」「次章」などの章をまたぐ参照 |

GitHub Actions は使っていないので、push 前に手元で `./tools/smoke_test.sh` を通してください。

## 本文のコードブロックの決まり

`python` / `go` のコードブロックは、先頭行で次のどちらかにします（`tests/test_doc_snippets.py` が確かめる）。

| 先頭行 | 中身 |
|--------|------|
| `# python/chNN/xxx.py` / `// go/chNN/xxx.go`（後ろに ` — 説明` を付けてもよい） | 実物の抜粋。書いた行はそのままファイルにあること。途中は `...` で省略してよい |
| `# 改変例` `# 擬似コード` `# 骨格` `# 概念` `# イメージ` のどれかを含むコメント | わざと実物と違うコード |

照合では、空白の違い・行末コメント・`def` / `func` の型注釈・Python の変数の型注釈は無視します。

## 出力例の決まり

- コマンド（```` ```bash ````）の直後 8 行以内に出力例（```` ``` ```` か ```` ```text ````）を置くと、`tests/test_doc_outputs.py` の対象にできる。対象にするには、テストの `CASES` にコマンドを足す。
- 乱数の seed が固定で時間に依存しないものは `exact`、時間で打ち切るものは `shape`（数字を伏せて形式だけ比べる）。
- 時間で打ち切るプログラムの出力例の直後には「時間・step 数・途中のスコアはマシン速度で変わる」と注記する。

## 章を書くときのチェックリスト

```
[ ] 全小節を目次（docs/00-toc.md）に沿って書いた（節タイトルは目次と一致させる）
[ ] 各技法節に Python と Go のコードがある
[ ] ハンズオンに bash コマンドがある
[ ] 霊夢の質問が1節に1回以上
[ ] 章末まとめが blockquote
[ ] コードブロックの先頭行にファイル名か「改変例」などの印がある
[ ] 「ゆっくり＝霊夢・魔理沙」である（速度の意味ではない）
```

台本の型は [付録A](docs/appendix-a.md) にあります。Cursor を使う場合は、章執筆スキル `.cursor/skills/write-chapter/` も使えます。

## 変更履歴

章番号の変更などは [CHANGELOG.md](CHANGELOG.md) に書いています。
