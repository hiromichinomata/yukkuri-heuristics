"""目次・見出し・章をまたぐ参照のずれを検出するテスト.

  python -m unittest tests.test_doc_structure -v

  - 目次（docs/00-toc.md）の章タイトル・節タイトルと、各章の `#` / `##` 見出しが一致する
  - 「第N章 N.M」のような節の参照が、実在する節を指している
  - 「次章: **タイトル**（第N章）」が、本当に次の章とそのタイトルを指している
  - 「第N章「タイトル」」のタイトルが、その章のタイトルか節タイトルと一致する
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def norm(s: str) -> str:
    """リンク・強調・「ハンズオン:」・末尾の（補足）を外し、空白を詰める."""
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s).replace("**", "").replace("`", "")
    s = re.sub(r"^ハンズオン[:：]\s*", "", s.strip())
    s = re.sub(r"[（(][^）)]*[）)]\s*$", "", s.strip())
    return re.sub(r"\s+", "", s)


def chapters():
    """{章番号: (タイトル, {"N.M": 節タイトル})}."""
    out = {}
    for p in sorted(DOCS.glob("[0-9][0-9].md")):
        text = p.read_text(encoding="utf-8")
        title = re.match(r"# 第\d+章 (.*)", text).group(1)
        secs = {m.group(1): m.group(2) for m in re.finditer(r"^## (\d+\.\d+) (.*)$", text, re.M)}
        out[int(p.stem)] = (title, secs)
    return out


def toc_entries():
    """目次の {章番号: (タイトル, {"N.M": 項目})}."""
    out, cur = {}, None
    for line in (DOCS / "00-toc.md").read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^### 第(\d+)章 (.*)", line)
        if m:
            cur = int(m.group(1))
            out[cur] = (m.group(2), {})
            continue
        m = re.match(r"^- (\d+\.\d+) (.*)", line)
        if m and cur is not None:
            out[cur][1][m.group(1)] = m.group(2)
    return out


def doc_files():
    return sorted(DOCS.glob("*.md")) + [ROOT / "README.md"]


class DocStructureTest(unittest.TestCase):
    def test_toc_matches_headings(self):
        chs, toc = chapters(), toc_entries()
        self.assertEqual(sorted(chs), sorted(toc), "目次にある章と docs/NN.md の章が一致しない")
        for n, (title, secs) in chs.items():
            toc_title, toc_secs = toc[n]
            with self.subTest(chapter=n):
                self.assertEqual(norm(title), norm(toc_title), f"第{n}章のタイトルが目次と違う")
                self.assertEqual(sorted(secs), sorted(toc_secs), f"第{n}章の節番号が目次と違う")
                for k, heading in secs.items():
                    item = toc_secs.get(k, "")
                    # 目次では「**演習**: 内容」と中身まで書き、本文の見出しは「演習」だけ、を許す
                    if norm(heading) == "演習" and item.startswith("**演習**"):
                        continue
                    self.assertEqual(norm(heading), norm(item), f"{k} の見出しが目次と違う")

    def test_section_references_exist(self):
        chs = chapters()
        for p in doc_files():
            for lineno, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
                for m in re.finditer(r"第(\d+)章\s*(?:の\s*)?(\d+)\.(\d+)", line):
                    n, a, b = map(int, m.groups())
                    with self.subTest(at=f"{p.name}:{lineno}"):
                        self.assertEqual(n, a, f"{p.name}:{lineno}: {m.group(0)} は章番号と節番号が食い違う")
                        self.assertIn(f"{a}.{b}", chs.get(n, ("", {}))[1], f"{p.name}:{lineno}: {m.group(0)} という節はない")

    def test_next_chapter_links(self):
        chs = chapters()
        for p in sorted(DOCS.glob("[0-9][0-9].md")):
            cur = int(p.stem)
            for lineno, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
                m = re.search(r"次章[:：](.*)", line)
                if not m:
                    continue
                with self.subTest(at=f"{p.name}:{lineno}"):
                    nums = [int(x) for x in re.findall(r"第(\d+)章", m.group(1))]
                    if nums:
                        self.assertEqual(nums[0], cur + 1, f"{p.name}:{lineno}: 次章の番号が違う")
                    t = re.search(r"\*\*([^*]+)\*\*（第(\d+)章）", m.group(1))
                    if t:
                        title, secs = chs[int(t.group(2))]
                        name = t.group(1)
                        ok = name in title or norm(name) in norm(title) or any(name in s for s in secs.values())
                        self.assertTrue(ok, f"{p.name}:{lineno}: 次章のタイトル「{name}」が第{t.group(2)}章「{title}」と違う")

    def test_quoted_chapter_titles(self):
        chs = chapters()
        for p in doc_files():
            for lineno, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
                for m in re.finditer(r"第(\d+)章\s*[「『]([^」』]+)[」』]", line):
                    n, name = int(m.group(1)), m.group(2)
                    if n not in chs:
                        continue
                    title, secs = chs[n]
                    with self.subTest(at=f"{p.name}:{lineno}"):
                        ok = name in title or title in name or any(name in s for s in secs.values())
                        self.assertTrue(ok, f"{p.name}:{lineno}: 第{n}章「{name}」は第{n}章のタイトル「{title}」と違う")


if __name__ == "__main__":
    unittest.main()
