#!/usr/bin/env bash
# tools/local_test.sh — ソルバ → スコア計算のローカル評価
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INPUT="${1:-data/ch01/sample.txt}"
SOLVER_PY="${2:-python/ch02/sample_solver.py}"
SOLVER_GO="${3:-go/ch02/sample_solver.go}"
SCORER_PY="python/ch01/score_intro_hc.py"

usage() {
  cat <<EOF
usage: ./tools/local_test.sh [input] [python_solver] [go_solver]

Example:
  ./tools/local_test.sh data/ch01/sample.txt
  ./tools/local_test.sh data/ch01/sample.txt python/ch02/sample_solver.py
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

run_python() {
  echo "== Python pipeline =="
  python "$SOLVER_PY" < "$INPUT" > /tmp/yh_out_py.txt
  echo "solver output:"
  cat /tmp/yh_out_py.txt
  echo "daily satisfaction:"
  cat "$INPUT" /tmp/yh_out_py.txt | python "$SCORER_PY" 2>/tmp/yh_err_py.txt
  echo "final score: $(cat /tmp/yh_err_py.txt)"
}

run_go() {
  echo "== Go pipeline =="
  go run "$SOLVER_GO" < "$INPUT" > /tmp/yh_out_go.txt
  echo "solver output:"
  cat /tmp/yh_out_go.txt
  echo "daily satisfaction:"
  cat "$INPUT" /tmp/yh_out_go.txt | go run go/ch01/score_intro_hc.go 2>/tmp/yh_err_go.txt
  echo "final score: $(cat /tmp/yh_err_go.txt)"
}

run_python
echo "---"
run_go
