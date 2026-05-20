# 付録F 参考文献・リンク

**霊夢**: もっと深く学ぶとき、どこを見ればいいの？

**魔理沙**: 公式ドキュメントと、コミュニティの定番記事だ。URL は **そのまま開ける** 形で載せたぜ。

---

## F.1 AtCoder 公式

| タイトル | URL | 内容 |
|---------|-----|------|
| レーティングのしくみ | https://info.atcoder.jp/overview/contest/rating | Algorithm / Heuristic の違い、色、参加回数 |
| Heuristic Contest 概要 | https://info.atcoder.jp/overview/contest/heuristic | AHC の形式・Rated の考え方 |
| AHC Rating System（計算式） | https://img.atcoder.jp/file/AHC_rating_v2_en.pdf | 2025年以降の時間減衰・重み付け |
| AtCoder コンテスト一覧 | https://atcoder.jp/contests/ | 開催予定・過去問 |
| AtCoder Problems | https://kenkoooo.com/atcoder/ | 過去問フィルタ・進捗管理 |

---

## F.2 入門コンテスト・問題

| タイトル | URL | 本書での位置 |
|---------|-----|-------------|
| Introduction to Heuristics Contest | https://atcoder.jp/contests/intro-heuristics | 第1・3・8章 |
| Intro HC 問題A（スケジューリング） | https://atcoder.jp/contests/intro-heuristics/tasks/intro_heuristics_a | 第1・5章 |
| Intro HC 問題B（Scoring） | https://atcoder.jp/contests/intro-heuristics/tasks/intro_heuristics_b | 第1・3章 |
| Intro HC 問題C | https://atcoder.jp/contests/intro-heuristics/tasks/intro_heuristics_c | 第8章 |
| Intro HC tools | https://img.atcoder.jp/intro-heuristics/tools.zip | 第2章 |
| AHC001 AtCoder Ad | https://atcoder.jp/contests/ahc001/tasks/ahc001_a | 第4章 |
| AHC002 Walking on Tiles | https://atcoder.jp/contests/ahc002/tasks/ahc002_a | 第9章 |
| AHC003 Shortest Path Queries | https://atcoder.jp/contests/ahc003/tasks/ahc003_a | 第11章 |
| AHC005 Patrolling | https://atcoder.jp/contests/ahc005/tasks/ahc005_a | 第6章 |
| AHC008 Territory | https://atcoder.jp/contests/ahc008/tasks/ahc008_a | 第17章 |

---

## F.3 解説・記事（日本語）

| タイトル | URL | 内容 |
|---------|-----|------|
| AHC典型解法シリーズ（焼きなまし） | https://qiita.com/thun-c/items/ecd438fde4d237b1f7bc | SA の実装の型 |
| AHC001 初心者向け解説（TERRY） | https://www.terry-u16.net/entry/ahc001-for-beginners | 配置・ビジュアライザ |
| AHC006 初心者向け | https://www.terry-u16.net/entry/ahc006-for-beginners | 強い貪欲 |
| ヒューリスティック競プロのヒント | https://qiita.com/tanaka-a/items/ab1c1f539a826606dc65 | 粗視化・分割の考え方 |
| AHC レート変動（公式ブログ） | https://atcoder.jp/posts/1381 | 2025年レーティング変更 |

---

## F.4 英語・その他

| タイトル | URL | 内容 |
|---------|-----|------|
| Simulated Annealing（概要） | https://en.wikipedia.org/wiki/Simulated_annealing | 理論背景 |
| Beam search | https://en.wikipedia.org/wiki/Beam_search | 探索の基礎 |
| CodinGame | https://www.codingame.com/ | マラソン形式の練習 |
| Topcoder Marathon | https://www.topcoder.com/ | 長期ヒューリスティック |

---

## F.5 本リポジトリ内の参照

| パス | 内容 |
|------|------|
| `docs/toc.md` | 全体目次 |
| `docs/00.md` | 本書の使い方 |
| `docs/appendix-a.md` 〜 `appendix-f.md` | 本付録群 |
| `python/templates/` | 共通テンプレート |
| `data/ch22/pattern_catalog.json` | 問題パターン JSON |
| `tools/local_test.sh` | ローカル評価 |
| `tools/check_env.sh` | 環境確認 |
| `.cursor/skills/write-chapter/` | 章執筆スキル |

---

## F.6 学習の順番（推奨）

```text
1. 本書 第0–3章 + Intro HC 問題B
2. 付録D の灰色帯問題
3. 第4–10章 + 該当 AHC 過去問
4. 付録C でパターン判定 → 水色〜青の章
5. 第21–22章（戦略・復習）
6. 付録F の外部記事で深掘り
```

---

## F.7 コミュニティ

| 媒体 | 用途 |
|------|------|
| X (Twitter) | コンテスト直後の解法共有・雰囲気 |
| 競プロ界隈の Discord | 質問・マラソン仲間 |
| 個人ブログ（はてな/Qiita） | 詳細な振り返り |
| AtCoder 掲示板・コメント | 公式・非公式の補足 |

**霊夢**: リンクが1か所にまとまってると助かるのだ。

**魔理沙**: URL は変更されることがある。**開けないときは AtCoder トップからコンテスト名で検索** しろ。本書のコードはローカルで動くから、Web がなくても第0–10章は進められるぜ。

---

## 更新メモ

| 日付 | 内容 |
|------|------|
| 2025 | AHC レーティング v2（時間減衰）— 第1章・付録F 参照 |
| 本書執筆時 | Intro HC / AHC001–020 を章・付録D にマッピング |

> **注**: 最新 AHC の問題 URL は `https://atcoder.jp/contests/ahcNNN` 形式。NNN はコンテスト番号。
