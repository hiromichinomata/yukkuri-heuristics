"""本文（docs/*.md）のコードと実ファイルのずれを検出するテスト.

  python -m unittest tests.test_doc_snippets -v

対象は、先頭行が `# python/chNN/xxx.py` / `// go/chNN/xxx.go` のようにファイル名で始まる
```python / ```go ブロック。ブロックの各行が、そのファイルのどこかの行と一致するかを調べる。

照合しない行:
  - 空行・コメントだけの行・`...` / `…` を含む行（省略の印）
  - 行末のコメント（`# ...` / `// ...`）は本文側・実ファイル側とも外して比べる
  - `def 名前(` / `func 名前(` の行は、同じ名前の定義が実ファイルにあればよい（型注釈の省略は可）
照合しないブロック:
  - 見出し行に「改変例」「擬似コード」「概念」「イメージ」を含むもの（わざと実物と違うコード）
  - ファイル名が chNN のような置き換え前提のテンプレート（付録A）
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = re.compile(r"^\s*(?:#|//)\s*((?:python|go)/[\w/.-]+\.(?:py|go))(.*)$")
SKIP_MARKERS = ("改変例", "擬似コード", "概念", "イメージ")
TRAILING_COMMENT = re.compile(r"\s+(?:#|//)\s.*$")


def normalize(line: str) -> str:
    return re.sub(r"\s+", " ", TRAILING_COMMENT.sub("", line).strip())


DEF = re.compile(r"^\s*(?:def|func|class|type)\s+(?:\([^)]*\)\s*)?(\w+)")


def defined_names(source_lines):
    return {m.group(1) for m in (DEF.match(x) for x in source_lines) if m}


def ignorable(line: str) -> bool:
    t = line.strip()
    return not t or "..." in t or "…" in t or t.startswith(("#", "//"))


def snippet_blocks():
    """(md ファイル, 行番号, ソースのパス, 見出しの残り, 本文の行) を順に返す."""
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
            body = lines[i + 1:j]
            m = HEADER.match(body[0]) if body else None
            if m and "chNN" not in m.group(1):
                yield md, i + 2, m.group(1), m.group(2), body[1:]
            i = j + 1


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
        self.assertGreater(checked, 50, "照合したブロックが少なすぎる（見出しの形式が変わった？）")


if __name__ == "__main__":
    unittest.main()
