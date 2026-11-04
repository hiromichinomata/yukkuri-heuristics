"""本文（docs/*.md）に載せた出力例と、実際にコマンドを動かした出力のずれを検出するテスト.

  python -m unittest tests.test_doc_outputs -v

本文の ```bash ブロックにあるコマンドを実行し、その直後（8 行以内）の出力例ブロック（``` か ```text）と比べる。
出力例の各行が、実際の出力（stdout + stderr）のどこかの行と一致すればよい。
`...` / `…` を含む行（省略の印）と `#` で始まる行（「# 出力例」のような見出し）は無視する。

  exact  … 乱数の seed が固定で時間にも依存しないプログラム。行がそのまま一致すること
  shape  … 時間で打ち切るプログラム。数字を伏せて比べる（ログの形式が本文どおりかだけを見る）
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (md ファイル, 本文のコマンド, 比べ方)
CASES = [
    ("01.md", "python python/ch01/score_intro_hc.py < data/ch01/sample.txt", "exact"),
    ("02.md", "python python/ch02/sample_solver.py < data/ch02/input_only.txt", "exact"),
    ("03.md", "python python/ch03/toy_score.py < data/ch03/toy_sample.txt", "exact"),
    ("03.md", "python python/ch03/score_module.py < data/ch03/sample.txt", "exact"),
    ("04.md", "python python/ch04/ahc001_grow.py < data/ch04/sample.txt", "exact"),
    ("05.md", "python python/ch05/greedy_delivery.py < data/ch05/sample.txt", "exact"),
    ("06.md", "python python/ch06/two_opt.py < data/ch06/sample.txt", "exact"),
    ("07.md", "python python/ch07/coarsen.py < data/ch07/sample.txt", "exact"),
    ("08.md", "python python/ch08/simple_vis.py < data/ch08/sample.txt", "exact"),
    ("09.md", "python python/ch09/sa_intro_hc.py < data/ch09/sample.txt", "shape"),
    ("10.md", "python python/ch10/beam_fill.py < data/ch10/sample.txt", "exact"),
    ("11.md", "python python/ch11/pipeline.py < data/ch11/sample.txt", "shape"),
    ("12.md", "python python/ch12/local_judge.py --seed 1 -- python python/ch12/solver.py", "shape"),
    ("13.md", "python python/ch13/tabu_tsp.py < data/ch13/sample.txt", "exact"),
    ("14.md", "python python/ch14/loop_toy.py data/ch14/sample.txt", "shape"),
    ("15.md", "python python/ch15/slide_beam.py < data/ch15/sample.txt", "exact"),
    ("16.md", "python python/ch16/sa_multi_neighborhood.py < data/ch16/sample.txt", "shape"),
    ("18.md", "python python/ch18/multi_start_sa.py < data/ch18/sample.txt", "shape"),
    ("18.md", "python python/ch18/multi_start_sa.py --parallel < data/ch18/sample.txt", "shape"),
    ("19.md", "python python/ch19/lns_tsp.py < data/ch19/sample.txt", "exact"),
    ("23.md", "python python/ch23/hypothesis_compare.py < data/ch23/sample.txt", "shape"),
    ("24.md", "python python/ch24/bandit_compare.py data/ch24/sample.txt", "exact"),
    ("25.md", "python python/ch25/assignment_relax.py < data/ch25/sample.txt", "exact"),
    ("26.md", "python python/ch26/ga_placement.py < data/ch26/sample.txt", "exact"),
    ("27.md", "python python/ch27/paper_transfer.py", "exact"),
]


def code_blocks(lines):
    """(言語, 開始行, 終了行, 本文) を順に返す."""
    i = 0
    while i < len(lines):
        m = re.match(r"^```(\w*)\s*$", lines[i])
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            yield m.group(1), i, j, lines[i + 1:j]
            i = j
        i += 1


def documented_output(md: str, command: str):
    """command を含む bash ブロックの直後にある出力例を返す（なければ None）."""
    lines = (ROOT / "docs" / md).read_text(encoding="utf-8").split("\n")
    blocks = list(code_blocks(lines))
    for k, (lang, _, end, body) in enumerate(blocks):
        if lang == "bash" and any(b.strip() == command for b in body) and k + 1 < len(blocks):
            nlang, nstart, _, nbody = blocks[k + 1]
            if nlang in ("", "text") and nstart - end <= 8:
                return nstart + 2, nbody
    return None


def normalize(line: str, mode: str) -> str:
    line = re.sub(r"\s+", " ", line.strip())
    if mode == "shape":
        line = re.sub(r"\d+(?:\.\d+)?", "N", line)
    return line


class DocOutputTest(unittest.TestCase):
    def test_outputs_match(self):
        for md, command, mode in CASES:
            with self.subTest(doc=md, command=command):
                found = documented_output(md, command)
                self.assertIsNotNone(found, f"docs/{md}: コマンドの直後に出力例が見つからない: {command}")
                lineno, expected = found
                proc = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=120)
                self.assertEqual(proc.returncode, 0, f"{command} が失敗した:\n{proc.stderr}")
                actual = {normalize(x, mode) for x in (proc.stdout + "\n" + proc.stderr).split("\n")}
                missing = [
                    e.strip() for e in expected
                    if e.strip() and not e.strip().startswith("#") and "..." not in e and "…" not in e and normalize(e, mode) not in actual
                ]
                self.assertEqual(missing, [], f"docs/{md}:{lineno}: 出力例に、実際の出力にない行がある（{mode}）")


if __name__ == "__main__":
    unittest.main()
