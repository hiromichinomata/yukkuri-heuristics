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
  local py="python/templates/${name}_template.py"
  local go_file="go/templates/${name}_template.go"

  case "$name" in
    io|timer|rng|heap|sa)
      py="python/templates/${name}_template.py"
      go_file="go/templates/${name}_template.go"
      ;;
    io_template|timer_template|rng_template|heap_example|sa_template)
      py="python/templates/${name}.py"
      go_file="go/templates/${name}.go"
      if [[ "$name" == "heap_example" ]]; then
        py="python/templates/heap_example.py"
        go_file="go/templates/heap_example.go"
      fi
      ;;
    *)
      echo "unknown template: $name" >&2
      exit 1
      ;;
  esac

  # heap はファイル名が *_example
  if [[ "$name" == "heap" ]]; then
    py="python/templates/heap_example.py"
    go_file="go/templates/heap_example.go"
  fi

  if [[ ! -f "$py" ]]; then
    echo "missing: $py" >&2
    exit 1
  fi
  if [[ ! -f "$go_file" ]]; then
    echo "missing: $go_file" >&2
    exit 1
  fi

  echo "== Python: $py =="
  if [[ "$name" == "io" || "$name" == "io_template" ]]; then
    python "$py" < data/sample.txt
  else
    python "$py"
  fi

  echo "== Go: $go_file =="
  if [[ "$name" == "io" || "$name" == "io_template" ]]; then
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
