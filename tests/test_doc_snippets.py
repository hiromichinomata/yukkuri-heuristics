"""本文（docs/*.md）のコードと実ファイルのずれを検出するテスト.

  python -m unittest tests.test_doc_snippets -v

対象は、先頭行が `# python/chNN/xxx.py` / `// go/chNN/xxx.go` のようにファイル名で始まる
```python / ```go ブロック。ブロックの各行が、そのファイルのどこかの行と一致するかを調べる。

ファイル名のないブロックは、先頭行のコメントに「改変例」「擬似コード」「骨格」「概念」「イメージ」の
どれかを書く（わざと実物と違うコードだと明示する）。印もファイル名もないブロックはテストが落ちる。

照合しない行:
  - 空行・コメントだけの行・`...` / `…` を含む行（省略の印）
  - 行末のコメント（`# ...` / `// ...`）は本文側・実ファイル側とも外して比べる
  - `def 名前(` / `func 名前(` の行は、同じ名前の定義が実ファイルにあればよい（型注釈の省略は可）
  - Python の変数の型注釈（`best: T | None = None` → `best = None`）は省いてよい
照合しないブロック:
  - 見出し行に上の印を含むもの（わざと実物と違うコード）
  - ファイル名が chNN のような置き換え前提のテンプレート（付録A）
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = re.compile(r"^\s*(?:#|//)\s*((?:python|go)/[\w/.-]+\.(?:py|go))(.*)$")
SKIP_MARKERS = ("改変例", "擬似コード", "骨格", "概念", "イメージ", "解答例")
TRAILING_COMMENT = re.compile(r"\s+(?:#|//)\s.*$")
VAR_ANNOTATION = re.compile(r"^([A-Za-z_]\w*): [^=]+ = ")


def normalize(line: str) -> str:
    line = re.sub(r"\s+", " ", TRAILING_COMMENT.sub("", line).strip())
    return VAR_ANNOTATION.sub(r"\1 = ", line)


DEF = re.compile(r"^\s*(?:def|func|class|type)\s+(?:\([^)]*\)\s*)?(\w+)")


def defined_names(source_lines):
    return {m.group(1) for m in (DEF.match(x) for x in source_lines) if m}


def ignorable(line: str) -> bool:
    t = line.strip()
    return not t or "..." in t or "…" in t or t.startswith(("#", "//"))


def code_blocks():
    """docs の ```python / ```go ブロックを (md ファイル, 本文の開始行番号, 本文の行) で返す."""
    for md in sorted((ROOT / "docs").glob("*.md")):
        lines = md.read_text(encoding="utf-8").split("\n")
        i = 0
        while i < len(lines):
            if not re.match(r"^```(python|go)\s*$", lines[i]):
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            yield md, i + 2, lines[i + 1:j]
            i = j + 1


def snippet_blocks():
    """(md ファイル, 行番号, ソースのパス, 見出しの残り, 本文の行) を順に返す."""
    for md, lineno, body in code_blocks():
        m = HEADER.match(body[0]) if body else None
        if m and "chNN" not in m.group(1):
            yield md, lineno, m.group(1), m.group(2), body[1:]


class DocSnippetTest(unittest.TestCase):
    def test_snippets_match_source(self):
        checked = 0
        for md, lineno, src, rest, body in snippet_blocks():
            if any(marker in rest for marker in SKIP_MARKERS):
                continue
            where = f"{md.relative_to(ROOT)}:{lineno} ({src})"
            with self.subTest(block=where):
                path = ROOT / src
                self.assertTrue(path.exists(), f"{where}: ファイルが存在しない")
                src_lines = path.read_text(encoding="utf-8").split("\n")
                source = {normalize(x) for x in src_lines}
                names = defined_names(src_lines)

                def matches(line: str) -> bool:
                    d = DEF.match(line)
                    return normalize(line) in source or bool(d and d.group(1) in names)

                missing = [b.strip() for b in body if not ignorable(b) and not matches(b)]
                self.assertEqual(missing, [], f"{where}: 実ファイルにない行がある（本文を実物に合わせるか、"
                                              f"わざと違うなら見出しに「改変例」などを付ける）")
                checked += 1
        self.assertGreater(checked, 150, "照合したブロックが少なすぎる（見出しの形式が変わった？）")

    def test_unlabeled_blocks_are_marked(self):
        for md, lineno, body in code_blocks():
            if body and HEADER.match(body[0]):
                continue
            if all(ignorable(b) for b in body):
                continue  # コメントだけのメモ書き
            first = body[0].strip()
            where = f"{md.relative_to(ROOT)}:{lineno}"
            with self.subTest(block=where):
                self.assertTrue(
                    first.startswith(("#", "//")) and any(m in first for m in SKIP_MARKERS),
                    f"{where}: 先頭行にファイル名（実物の抜粋）か「改変例」「擬似コード」などの印を書く: {first!r}",
                )


if __name__ == "__main__":
    unittest.main()
