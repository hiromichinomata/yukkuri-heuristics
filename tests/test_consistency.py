"""手元実行用のテスト（標準ライブラリの unittest のみ）.

  python -m unittest discover -s tests -v      # リポジトリのルートで
  ./tools/smoke_test.sh                         # こちらからも呼ばれる

確認すること:
  - 各章のスコア計算（Intro HC 形式、Python / Go）が、テスト内の基準実装と一致する
    （各章が「1ファイルで提出できる形」を保つために同じ処理を持っているので、写し間違いを検出する）
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
        for rel in ("go/ch01/greedy_intro_hc.go", "go/ch10/beam_fill.go", "go/ch15/slide_beam.go",
                    "go/ch12/solver.go"):
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

    def test_ch12_interactive_judge(self):
        """AHC003 形式のローカルジャッジで、Python / Go のソルバが同じスコアになる."""
        scores = []
        for solver in ([sys.executable, "python/ch12/solver.py"], [str(self.bins["go/ch12/solver.go"])]):
            p = subprocess.run([sys.executable, "python/ch12/local_judge.py", "--seed", "3", "--queries", "200", "--"]
                               + solver, cwd=ROOT, capture_output=True, text=True, timeout=120, check=True)
            scores.append(p.stderr.split("score=")[1].split()[0])
        self.assertEqual(scores[0], scores[1])

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


def reference_score(days, decay, gain, schedule):
    """Intro HC のスコア（テスト用の基準実装。日ごとの満足度の列と最終スコアを返す）."""
    last = [0] * 26
    sat = 0
    daily = []
    for d in range(1, days + 1):
        t = schedule[d - 1] - 1
        sat += gain[d - 1][t]
        last[t] = d
        sat -= sum(decay[i] * (d - last[i]) for i in range(26))
        daily.append(sat)
    return daily, max(10**6 + sat, 0)


def read_intro_hc(path: Path):
    lines = path.read_text().splitlines()
    days = int(lines[0])
    decay = list(map(int, lines[1].split()))
    gain = [list(map(int, lines[2 + i].split())) for i in range(days)]
    return days, decay, gain


@unittest.skipIf(shutil.which("go") is None, "go が見つからない")
class ScorerParityTest(unittest.TestCase):
    """各章のソルバが出した解を基準実装で採点し直し、本人が申告したスコアと一致するか確かめる.

    入力は本番サイズの data/common/intro_hc_d365.txt。入力の読み違い（例: 全日が同じ行を読む）や
    スコア計算の写し間違いがあると、申告スコアと基準スコアがずれる。1 本 2 秒前後かかる。
    """

    INPUT = ROOT / "data/common/intro_hc_d365.txt"
    # (起動コマンド, stderr から申告スコアを拾う正規表現)
    SOLVERS = [
        (["python", "python/ch01/greedy_intro_hc.py"], r"final score=(\d+)"),
        (["go", "go/ch01/greedy_intro_hc.go"], r"final score=(\d+)"),
        (["python", "python/ch09/sa_intro_hc.py"], r"best score=(\d+)"),
        (["go", "go/ch09/sa_intro_hc.go"], r"best score=(\d+)"),
        (["python", "python/ch11/pipeline.py"], r"phase=sa end score=(\d+)"),
        (["go", "go/ch11/pipeline.go"], r"phase=sa end score=(\d+)"),
        (["python", "python/ch16/sa_multi_neighborhood.py"], r"best score=(\d+)"),
        (["go", "go/ch16/sa_multi_neighborhood.go"], r"best score=(\d+)"),
        (["python", "python/ch18/multi_start_sa.py"], r"merged best score=(\d+)"),
        (["go", "go/ch18/multi_start_sa.go"], r"merged best score=(\d+)"),
        (["python", "python/ch21/mock_contest.py", "{input}", "--fast"], r"final_score=(\d+)"),
        (["go", "go/ch21/mock_contest.go", "{input}", "--fast"], r"final_score=(\d+)"),
        (["python", "python/ch23/hypothesis_compare.py"], r"best=\w+ score=(\d+)"),
        (["go", "go/ch23/hypothesis_compare.go"], r"best=\w+ score=(\d+)"),
    ]
    # 入力 + 日程 を読んで、stdout に日ごとの満足度、stderr に最終スコアを出すプログラム
    SCORERS = [
        ["python", "python/ch01/score_intro_hc.py"],
        ["go", "go/ch01/score_intro_hc.go"],
        ["python", "python/ch03/score_module.py"],
        ["go", "go/ch03/score_module.go"],
    ]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.problem = read_intro_hc(cls.INPUT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def command(self, cmd):
        """go のソースはビルドして実行（go run より速い）。"{input}" は入力ファイルに置き換える."""
        cmd = [str(self.INPUT) if c == "{input}" else c for c in cmd]
        if cmd[0] == "go":
            out = self.tmp / Path(cmd[1]).parent.name / Path(cmd[1]).stem
            if not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["go", "build", "-o", str(out), cmd[1]], cwd=ROOT, check=True)
            return [str(out)] + cmd[2:]
        return [sys.executable] + cmd[1:]

    def test_solver_reported_scores(self):
        import re
        days, decay, gain = self.problem
        text = self.INPUT.read_text()
        for cmd, pattern in self.SOLVERS:
            with self.subTest(cmd=" ".join(cmd)):
                p = subprocess.run(self.command(cmd), cwd=ROOT, input=text,
                                   capture_output=True, text=True, timeout=60, check=True)
                schedule = [int(x) for x in p.stdout.split()]
                self.assertEqual(len(schedule), days, "出力の行数が D と違う")
                self.assertTrue(all(1 <= t <= 26 for t in schedule), "タイプが 1〜26 の範囲外")
                found = re.findall(pattern, p.stderr)
                self.assertTrue(found, f"申告スコアが stderr に見つからない: {pattern}")
                _, expected = reference_score(days, decay, gain, schedule)
                self.assertEqual(int(found[-1]), expected, "申告スコアが基準実装の採点と違う")

    def test_scorers(self):
        days, decay, gain = self.problem
        rng = random.Random(5)
        schedule = [rng.randint(1, 26) for _ in range(days)]
        daily, final = reference_score(days, decay, gain, schedule)
        text = self.INPUT.read_text() + "\n".join(map(str, schedule)) + "\n"
        for cmd in self.SCORERS:
            with self.subTest(cmd=" ".join(cmd)):
                p = subprocess.run(self.command(cmd), cwd=ROOT, input=text,
                                   capture_output=True, text=True, timeout=60, check=True)
                self.assertEqual([int(x) for x in p.stdout.split()], daily, "日ごとの満足度が違う")
                self.assertEqual(int(p.stderr.split()[-1]), final, "最終スコアが違う")


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
