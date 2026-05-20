# python/ch01/compare_schedules.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "data" / "ch01" / "sample.txt"
SCORER = ROOT / "python" / "ch01" / "score_intro_hc.py"


def run_with_schedule(schedule: list[int]) -> tuple[list[int], int]:
    lines = SAMPLE.read_text().splitlines()
    d = int(lines[0])
    body = lines[: 1 + 1 + d]
    text = "\n".join(body + [str(x) for x in schedule]) + "\n"
    proc = subprocess.run(
        [sys.executable, str(SCORER)],
        input=text,
        text=True,
        capture_output=True,
        check=True,
    )
    daily = list(map(int, proc.stdout.split()))
    final = int(proc.stderr.strip())
    return daily, final


if __name__ == "__main__":
    d = 5
    orig = [1, 17, 13, 14, 13]
    all_one = [1] * d
    for name, sched in [("sample", orig), ("all_type1", all_one)]:
        _, final = run_with_schedule(sched)
        print(name, "final_score=", final)
