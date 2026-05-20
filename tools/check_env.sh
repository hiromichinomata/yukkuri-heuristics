#!/usr/bin/env bash
# tools/check_env.sh — Python / Go 環境の簡易チェック
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== Python =="
python3 --version
python3 python/ch02/env_check.py

echo ""
echo "== Go =="
go version
go run go/ch02/env_check.go

echo ""
echo "OK: environment check passed"
