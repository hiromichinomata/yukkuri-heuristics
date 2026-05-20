# python/ch02/run_local.py
"""ローカル評価パイプライン（ソルバ → スコア計算）."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(input_path: Path, solver: Path, scorer: Path) -> None:
    inp = input_path.read_text()
    sol = subprocess.run(
        [sys.executable, str(solver)],
        input=inp,
        text=True,
        capture_output=True,
        check=True,
    )
    combined = inp + sol.stdout
    score = subprocess.run(
        [sys.executable, str(scorer)],
        input=combined,
        text=True,
        capture_output=True,
        check=True,
    )
    print("=== solver output (head) ===")
    print("\n".join(sol.stdout.splitlines()[:5]), "...")
    print("=== daily satisfaction ===")
    print(score.stdout.strip())
    print("=== final score (stderr) ===")
    print(score.stderr.strip())


if __name__ == "__main__":
    inp = ROOT / "data" / "ch01" / "sample.txt"
    solver = ROOT / "python" / "ch02" / "sample_solver.py"
    scorer = ROOT / "python" / "ch01" / "score_intro_hc.py"
    run(inp, solver, scorer)
