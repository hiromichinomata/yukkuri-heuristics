"""手元実行用のテスト（標準ライブラリの unittest のみ）.

  python -m unittest discover -s tests -v      # リポジトリのルートで
  ./tools/smoke_test.sh                         # こちらからも呼ばれる

確認すること:
  - 差分更新（第9・16・18章）が全再計算と一致する
  - 乱数を使わないプログラムが、ランダム入力でも Python と Go で同じ出力になる
  - 第27章の簡易 YAML ローダーが PyYAML / JSON と同じ結果を返す
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(rel_path: str):
    """python/chNN/xxx.py を、ファイル名が重なっても衝突しないモジュール名で読み込む."""
    path = ROOT / rel_path
    name = rel_path.replace("/", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod  # dataclass が sys.modules を参照するので先に登録する
    spec.loader.exec_module(mod)
    return mod


def random_intro_hc(rng: random.Random, max_days: int = 40):
    days = rng.randint(2, max_days)
    decay = [rng.randint(0, 100) for _ in range(26)]
    gain = [[rng.randint(0, 20000) for _ in range(26)] for _ in range(days)]
    types = [rng.randint(1, 26) for _ in range(days)]
    return days, decay, gain, types


def intro_hc_text(days, decay, gain) -> str:
    rows = [str(days), " ".join(map(str, decay))] + [" ".join(map(str, g)) for g in gain]
    return "\n".join(rows) + "\n"


class DeltaUpdateTest(unittest.TestCase):
    """差分更新の積み上げ = 全再計算 を、ランダムな入力・操作で確かめる."""

    CASES = 300

    def test_ch09_delta_change(self):
        m = load_module("python/ch09/sa_intro_hc.py")
        rng = random.Random(1)
        for _ in range(self.CASES):
            days, decay, gain, types = random_intro_hc(rng)
            p = m.ProblemInput(days, decay, gain)
            day, new_type = rng.randrange(days), rng.randint(1, 26)
            before = m.raw_score(p, m.ScheduleState(list(types)))
            delta = m.delta_change(p, types, day, new_type)
            after_types = list(types)
            after_types[day] = new_type
            self.assertEqual(before + delta, m.raw_score(p, m.ScheduleState(after_types)))

    def test_ch16_move_delta(self):
        m = load_module("python/ch16/sa_multi_neighborhood.py")
        rng = random.Random(2)
        for i in range(self.CASES):
            days, decay, gain, types = random_intro_hc(rng)
            p = m.ProblemInput(days, decay, gain)
            if i % 2:
                move = ("swap", *rng.sample(range(days), 2))
            else:
                move = ("change", rng.randrange(days), rng.randint(1, 26))
            before = m.raw_score(p, m.ScheduleState(list(types)))
            delta = m.move_delta(p, types, move)
            after_types = list(types)
            m.apply_move(after_types, move)
            self.assertEqual(before + delta, m.raw_score(p, m.ScheduleState(after_types)))

    def test_ch18_delta_change(self):
        m = load_module("python/ch18/multi_start_sa.py")
        rng = random.Random(3)
        for _ in range(self.CASES):
            days, decay, gain, types = random_intro_hc(rng)
            p = m.ProblemInput(days, decay, gain)
            day, new_type = rng.randrange(days), rng.randint(1, 26)
            before = m.raw_score(p, list(types))
            delta = m.delta_change(p, types, day, new_type)
            after_types = list(types)
            after_types[day] = new_type
            self.assertEqual(before + delta, m.raw_score(p, after_types))

    def test_sa_scores_match_full_recompute(self):
        """SA が返す best と、その解を全再計算したスコアが一致する（D=365 でも）."""
        m9 = load_module("python/ch09/sa_intro_hc.py")
        rng = random.Random(4)
        days, decay, gain, _ = random_intro_hc(rng, max_days=365)
        p = m9.ProblemInput(days, decay, gain)
        init = m9.ScheduleState([rng.randint(1, 26) for _ in range(days)])
        with contextlib.redirect_stderr(io.StringIO()):  # SA の進捗ログは捨てる
            best, best_score = m9.sa(p, init, 0.2, random.Random(0))
        self.assertEqual(best_score, m9.score_schedule(p, best))


@unittest.skipIf(shutil.which("go") is None, "go が見つからない")
class PythonGoParityTest(unittest.TestCase):
    """乱数を使わないプログラムを、ランダム入力で Python / Go 両方に流して比べる."""

    CASES = 6

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.bins = {}
        for rel in ("go/ch01/greedy_intro_hc.go", "go/ch10/beam_fill.go", "go/ch15/slide_beam.go"):
            out = cls.tmp / Path(rel).stem
            subprocess.run(["go", "build", "-o", str(out), rel], cwd=ROOT, check=True)
            cls.bins[rel] = out

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_both(self, py_rel: str, go_rel: str, text: str) -> None:
        py = subprocess.run([sys.executable, py_rel], cwd=ROOT, input=text,
                            capture_output=True, text=True, check=True)
        go = subprocess.run([str(self.bins[go_rel])], cwd=ROOT, input=text,
                            capture_output=True, text=True, check=True)
        self.assertEqual(py.stdout, go.stdout, f"{py_rel} と {go_rel} の stdout が違う\n入力:\n{text[:200]}")

    def test_ch01_greedy(self):
        rng = random.Random(10)
        for _ in range(self.CASES):
            days, decay, gain, _ = random_intro_hc(rng, max_days=30)
            self.run_both("python/ch01/greedy_intro_hc.py", "go/ch01/greedy_intro_hc.go",
                          intro_hc_text(days, decay, gain))

    def test_ch10_beam_fill(self):
        rng = random.Random(11)
        for _ in range(self.CASES):
            n = rng.choice([4, 5, 6, 7])
            rows = [" ".join(str(rng.randint(0, 9)) for _ in range(n)) for _ in range(n)]
            self.run_both("python/ch10/beam_fill.py", "go/ch10/beam_fill.go",
                          f"{n}\n" + "\n".join(rows) + "\n")

    def test_ch15_slide_beam(self):
        rng = random.Random(12)
        for _ in range(self.CASES):
            cells = list(range(1, 9)) + [0]
            blank = 8
            for _ in range(60):  # ゴールからランダムに動かすので必ず解ける
                r, c = divmod(blank, 3)
                moves = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                         if 0 <= r + dr < 3 and 0 <= c + dc < 3]
                nr, nc = rng.choice(moves)
                nb = nr * 3 + nc
                cells[blank], cells[nb] = cells[nb], cells[blank]
                blank = nb
            text = "3\n" + "\n".join(" ".join(map(str, cells[i * 3:i * 3 + 3])) for i in range(3)) + "\n"
            self.run_both("python/ch15/slide_beam.py", "go/ch15/slide_beam.go", text)


class YamlLoaderTest(unittest.TestCase):
    def test_ch27_subset_loader_matches_json(self):
        m = load_module("python/ch27/paper_transfer.py")
        text = (ROOT / "data/ch27/paper_notes.yaml").read_text(encoding="utf-8")
        loaded = m.load_yaml_subset(text)
        expected = json.loads((ROOT / "data/ch27/paper_notes.json").read_text(encoding="utf-8"))
        # YAML の "|" ブロックは末尾に改行が付く（JSON 側は付けていない）
        loaded["reader_notes"] = loaded["reader_notes"].rstrip("\n")
        self.assertEqual(loaded, expected)

    def test_ch27_subset_loader_matches_pyyaml(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML なし")
        m = load_module("python/ch27/paper_transfer.py")
        text = (ROOT / "data/ch27/paper_notes.yaml").read_text(encoding="utf-8")
        self.assertEqual(m.load_yaml_subset(text), yaml.safe_load(text))


if __name__ == "__main__":
    unittest.main()
