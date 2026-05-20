# python/ch22/review_sheet.py
"""過去問復習用 Markdown テンプレートを生成・既存シートに追記."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_catalog(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("patterns", [])


def pattern_options(catalog: List[Dict[str, Any]]) -> str:
    lines = []
    for p in catalog:
        lines.append(f"- **{p['id']}** — {p['name']}（例: {', '.join(p['example_contests'][:2])}）")
    return "\n".join(lines)


def render_template(
    contest: str,
    problem: str,
    pattern_id: str,
    catalog: List[Dict[str, Any]],
    score: Optional[str],
) -> str:
    pattern = next((p for p in catalog if p["id"] == pattern_id), None)
    pattern_name = pattern["name"] if pattern else pattern_id
    review_q = ""
    if pattern:
        review_q = "\n".join(f"- [ ] {q}" for q in pattern["review_questions"])

    score_line = score if score is not None else "（未記入）"
    today = date.today().isoformat()

    return f"""# 過去問復習シート — {contest} / {problem}

- **日付**: {today}
- **パターン**: {pattern_id}（{pattern_name}）
- **スコア**: {score_line}

## 1. 自力（タイマー付き）

- [ ] 問題文を 15 分で読み切った
- [ ] 仮説を 3 つ書いた
- [ ] 動く提出（またはローカルスコア）を 1 回出した

メモ:

```
（ここに仮説・実装方針）
```

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

{pattern_options(catalog)}

### この問題向けチェック

{review_q if review_q else "- （パターン未設定）"}

## 5. 次回への 3 点

1.
2.
3.
"""


def fill_section(content: str, heading: str, body: str) -> str:
    marker = f"## {heading}"
    if marker not in content:
        return content + f"\n{marker}\n\n{body}\n"
    parts = content.split(marker, 1)
    rest = parts[1]
    next_idx = rest.find("\n## ")
    if next_idx == -1:
        return parts[0] + marker + "\n\n" + body + "\n"
    return parts[0] + marker + "\n\n" + body + "\n" + rest[next_idx:]


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    catalog_path = root / "data" / "ch22" / "pattern_catalog.json"
    catalog = load_catalog(catalog_path)

    parser = argparse.ArgumentParser(description="復習シート Markdown 生成")
    parser.add_argument("--contest", default="AHC0XX", help="コンテスト名")
    parser.add_argument("--problem", default="A", help="問題記号")
    parser.add_argument(
        "--pattern",
        default="scheduling",
        choices=[p["id"] for p in catalog],
        help="典型パターン ID",
    )
    parser.add_argument("--score", default=None, help="自分のスコア")
    parser.add_argument("-o", "--output", help="出力ファイル（省略時は stdout）")
    parser.add_argument(
        "--append-note",
        metavar="TEXT",
        help="既存シートにメモ追記（-o で指定したファイル）",
    )
    args = parser.parse_args()

    if args.append_note and args.output:
        path = Path(args.output)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        updated = fill_section(text, "追記メモ", args.append_note)
        path.write_text(updated, encoding="utf-8")
        print(f"wrote append to {path}", file=__import__("sys").stderr)
        return

    md = render_template(args.contest, args.problem, args.pattern, catalog, args.score)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}", file=__import__("sys").stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
