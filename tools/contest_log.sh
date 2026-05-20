#!/usr/bin/env bash
# tools/contest_log.sh — 模擬コンテスト実行と提出ログ保存
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAST="${CONTEST_FAST:-1}"
INPUT="${1:-data/ch23/sample.txt}"
LOG_DIR="${LOG_DIR:-/tmp/yukkuri-contest-log}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
PY_LOG="$LOG_DIR/py_${STAMP}.log"
GO_LOG="$LOG_DIR/go_${STAMP}.log"

export CONTEST_FAST="$FAST"

echo "== mock_contest Python (log: $PY_LOG) =="
python python/ch21/mock_contest.py "$INPUT" --fast --json-log 2>"$PY_LOG" | tee "$LOG_DIR/py_${STAMP}.out"

echo "== mock_contest Go (log: $GO_LOG) =="
go run go/ch21/mock_contest.go "$INPUT" --fast --json-log 2>"$GO_LOG" | tee "$LOG_DIR/go_${STAMP}.out"

echo "logs saved under $LOG_DIR"
