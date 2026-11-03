#!/usr/bin/env bash
# tools/run.sh — テンプレートまたは章の解法を実行する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
usage:
  ./tools/run.sh template <name>     # io, timer, rng, heap, sa
  ./tools/run.sh io                  # io_template のショートカット
EOF
}

run_template() {
  local name="$1"
  local base

  # 短縮名 → 実ファイル名（python/templates/ と go/templates/ で共通）
  case "$name" in
    io|io_template) base="io_template" ;;
    sa|sa_template) base="sa_template" ;;
    heap|heap_example) base="heap_example" ;;
    timer) base="timer" ;;
    rng) base="rng" ;;
    *)
      echo "unknown template: $name (io, timer, rng, heap, sa)" >&2
      exit 1
      ;;
  esac

  local py="python/templates/${base}.py"
  local go_file="go/templates/${base}.go"

  if [[ ! -f "$py" ]]; then
    echo "missing: $py" >&2
    exit 1
  fi
  if [[ ! -f "$go_file" ]]; then
    echo "missing: $go_file" >&2
    exit 1
  fi

  echo "== Python: $py =="
  if [[ "$base" == "io_template" ]]; then
    python "$py" < data/sample.txt
  else
    python "$py"
  fi

  echo "== Go: $go_file =="
  if [[ "$base" == "io_template" ]]; then
    go run "$go_file" < data/sample.txt
  else
    go run "$go_file"
  fi
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

case "$1" in
  template)
    run_template "${2:-io}"
    ;;
  io)
    run_template io
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    run_template "$1"
    ;;
esac
