"""ランダムな入力と、小さすぎる入力でのテスト.

  python -m unittest tests.test_fuzz_parity -v

  - 乱数も時間も使わないプログラムは、ランダムな入力でも Python と Go の stdout が一致する
  - 点が 1 個・1 日しかない、などの小さすぎる入力でも、Python / Go とも落ちない
"""
from __future__ import annotations

import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
CASES_PER_PROGRAM = 15


def intro_hc(rng: random.Random, d: int, with_schedule: bool) -> str:
    s = f"{d}\n" + " ".join(str(rng.randint(0, 100)) for _ in range(26)) + "\n"
    for _ in range(d):
        s += " ".join(str(rng.randint(0, 20000)) for _ in range(26)) + "\n"
    if with_schedule:
        s += "".join(f"{rng.randint(1, 26)}\n" for _ in range(d))
    return s


def ahc001(rng: random.Random) -> str:
    n = rng.randint(1, 12)
    pts = rng.sample([(x, y) for x in range(20) for y in range(20)], n)
    return f"{n}\n" + "".join(f"{x} {y} {rng.randint(1, 60)}\n" for x, y in pts)


def delivery(rng: random.Random) -> str:
    # 座標を小さい整数にして、距離の同点がよく出るようにする
    n = rng.randint(1, 8)
    pts = "".join(f"{rng.randint(0, 5)} {rng.randint(0, 5)}\n" for _ in range(n))
    return f"{rng.randint(0, 5)} {rng.randint(0, 5)}\n{n}\n{pts}"


def square(rng: random.Random, n: int, high: int) -> str:
    return "".join(" ".join(str(rng.randint(0, high)) for _ in range(n)) + "\n" for _ in range(n))


def slide(rng: random.Random) -> str:
    cells = list(range(9))
    rng.shuffle(cells)
    return "3\n" + "".join(" ".join(map(str, cells[i * 3 : i * 3 + 3])) + "\n" for i in range(3))


def territory(rng: random.Random) -> str:
    n = rng.randint(2, 6)
    a, b = rng.sample([(x, y) for x in range(n) for y in range(n)], 2)
    return f"{n}\n{square(rng, n, rng.choice([1, 9]))}{a[0]} {a[1]}\n{b[0]} {b[1]}\n"


GENERATORS: Dict[str, Callable[[random.Random], str]] = {
    "ch01/score_intro_hc": lambda r: intro_hc(r, r.randint(1, 30), True),
    "ch01/greedy_intro_hc": lambda r: intro_hc(r, r.randint(1, 30), False),
    "ch03/score_module": lambda r: intro_hc(r, r.randint(1, 30), True),
    "ch03/toy_score": lambda r: (lambda n: f"{n}\n" + " ".join(str(r.randint(0, 50)) for _ in range(n)) + "\n")(r.randint(1, 10)),
    "ch04/ahc001_grow": ahc001,
    "ch05/greedy_delivery": delivery,
    "ch07/coarsen": lambda r: "16\n" + square(r, 16, r.choice([1, 3, 20])),
    "ch10/beam_fill": lambda r: (lambda n: f"{n}\n" + square(r, n, r.choice([0, 2, 9])))(r.randint(2, 5)),
    "ch15/slide_beam": slide,
    "ch17/territory_greedy": territory,
    "ch25/assignment_relax": lambda r: (lambda n: f"{n}\n" + square(r, n, r.choice([2, 9])))(r.randint(1, 6)),
}

# 小さすぎる入力（落ちなければよい）
EDGE_CASES: List[tuple] = [
    ("ch06/two_opt", "1\n0 0\n"),
    ("ch06/two_opt", "2\n0 0\n1 1\n"),
    ("ch06/two_opt", "3\n0 0\n1 0\n0 1\n"),
    ("ch13/tabu_tsp", "1\n0 0\n"),
    ("ch13/tabu_tsp", "3\n0 0\n1 0\n0 1\n"),
    ("ch19/lns_tsp", "1\n0 0\n"),
    ("ch19/lns_tsp", "3\n0 0\n1 0\n0 1\n"),
    ("ch05/greedy_delivery", "0 0\n0\n"),
    ("ch04/ahc001_grow", "0\n"),
    ("ch10/beam_fill", "1\n5\n"),
    ("ch15/slide_beam", "3\n1 2 3\n4 5 6\n7 8 0\n"),
    ("ch17/territory_greedy", "2\n1 1\n1 1\n0 0\n1 1\n"),
    ("ch25/assignment_relax", "1\n5\n"),
    ("ch26/ga_placement", "10\n1\n5\n"),
    ("ch26/ga_placement", "3\n2\n5 20\n"),
    ("ch16/sa_multi_neighborhood", "1\n" + " ".join(["1"] * 26) + "\n" + " ".join(["5"] * 26) + "\n"),
    ("ch23/hypothesis_compare", "1\n" + " ".join(["1"] * 26) + "\n" + " ".join(["5"] * 26) + "\n"),
]


@unittest.skipUnless(shutil.which("go"), "go が見つからない")
class FuzzParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.bins: Dict[str, str] = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def go_bin(self, name: str) -> str:
        """go run は毎回ビルドして遅いので、1 回だけビルドしたものを使い回す."""
        if name not in self.bins:
            out = str(Path(self.tmp.name) / name.replace("/", "_"))
            subprocess.run(["go", "build", "-o", out, f"go/{name}.go"], cwd=ROOT, check=True)
            self.bins[name] = out
        return self.bins[name]

    def run_both(self, name: str, inp: str):
        py = subprocess.run(["python", f"python/{name}.py"], input=inp, capture_output=True, text=True, cwd=ROOT, timeout=60)
        go = subprocess.run([self.go_bin(name)], input=inp, capture_output=True, text=True, cwd=ROOT, timeout=60)
        return py, go

    def test_random_inputs_match(self):
        for name, gen in GENERATORS.items():
            for seed in range(CASES_PER_PROGRAM):
                inp = gen(random.Random(seed))
                with self.subTest(program=name, seed=seed):
                    py, go = self.run_both(name, inp)
                    self.assertEqual(py.returncode, 0, py.stderr[-500:])
                    self.assertEqual(go.returncode, 0, go.stderr[-500:])
                    self.assertEqual(py.stdout, go.stdout, f"入力:\n{inp[:300]}")

    def test_tiny_inputs_do_not_crash(self):
        for name, inp in EDGE_CASES:
            with self.subTest(program=name, input=inp[:40]):
                py, go = self.run_both(name, inp)
                self.assertEqual(py.returncode, 0, py.stderr[-500:])
                self.assertEqual(go.returncode, 0, go.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
