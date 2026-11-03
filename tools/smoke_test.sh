#!/usr/bin/env bash
# tools/smoke_test.sh — 全章のサンプルを Python / Go で実行し、壊れていないか確認する
#
#   ./tools/smoke_test.sh          # 全部
#   ./tools/smoke_test.sh ch10     # 名前に ch10 を含むものだけ
#
# 確認すること:
#   1. Go: ファイル単位の go vet（1ディレクトリに main が複数あるので ./... は使えない）
#   2. Python: 構文チェック（py_compile）
#   3. 各プログラムがサンプル入力で終了コード 0 で終わる
#   4. 乱数を使わないプログラムは Python と Go の stdout が一致する
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FILTER="${1:-}"
TIMEOUT_SEC="${TIMEOUT_SEC:-60}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

pass=0
fail=0
failed=()

# macOS には timeout コマンドがないので perl の alarm で代用する
with_timeout() {
  perl -e 'alarm shift; exec @ARGV or die "exec failed: $!\n"' "$TIMEOUT_SEC" "$@"
}

ok() { pass=$((pass + 1)); }
ng() {
  fail=$((fail + 1))
  failed+=("$1")
  echo "FAIL: $1" >&2
  [[ -n "${2:-}" ]] && sed 's/^/    /' "$2" | tail -5 >&2
}

# ---------- 1. go vet ----------
echo "== go vet (file by file) =="
for f in go/*/*.go; do
  [[ -n "$FILTER" && "$f" != *"$FILTER"* ]] && continue
  if go vet "$f" >"$TMP_DIR/vet.log" 2>&1; then ok; else ng "go vet $f" "$TMP_DIR/vet.log"; fi
done
unformatted="$(gofmt -l go/)"
if [[ -n "$unformatted" ]]; then
  echo "$unformatted" >"$TMP_DIR/fmt.log"
  ng "gofmt (run: gofmt -w go/)" "$TMP_DIR/fmt.log"
else
  ok
fi

# ---------- 2. Python 構文 ----------
echo "== python py_compile =="
for f in python/*/*.py; do
  [[ -n "$FILTER" && "$f" != *"$FILTER"* ]] && continue
  if python -c 'import sys, py_compile; py_compile.compile(sys.argv[1], doraise=True, cfile=sys.argv[2])' \
    "$f" "$TMP_DIR/pyc" >"$TMP_DIR/py.log" 2>&1; then ok; else ng "py_compile $f" "$TMP_DIR/py.log"; fi
done

# ---------- 3. 実行 ----------
# run_case <id> <stdin_file> <command...>
#   stdout を $TMP_DIR/<id>.out に保存する（id の "/" は "_" に置換）
run_case() {
  local id="$1" input="$2"
  shift 2
  [[ -n "$FILTER" && "$id" != *"$FILTER"* ]] && return 0
  local key="${id//\//_}"
  if with_timeout "$@" <"$input" >"$TMP_DIR/$key.out" 2>"$TMP_DIR/$key.err"; then
    ok
  else
    ng "$id: $*" "$TMP_DIR/$key.err"
  fi
}

# 章ごとに既定以外の起動方法が必要なもの: "<chNN/name>|<stdin>|<python 引数>|<go 引数>"
special_cases=(
  "templates/io_template|data/sample.txt||"
  "ch02/sample_solver|data/ch02/input_only.txt||"
  "ch12/interactive_path|/dev/null|--offline data/ch12/sample.txt|--offline data/ch12/sample.txt"
  "ch12/query_simulator|/dev/null|data/ch12/sample.txt|"
  "ch21/mock_contest|/dev/null|data/ch23/sample.txt --fast|data/ch23/sample.txt --fast"
  "ch24/bandit_compare|/dev/null|data/ch24/sample.txt|data/ch24/sample.txt"
  "ch08/simple_vis|data/ch08/sample.txt||-input data/ch08/sample.txt"
  "ch29/improvement_log|/dev/null|data/ch29/weekly_log.json|-input data/ch29/weekly_log.json"
)

lookup_special() {
  local name="$1" entry
  for entry in "${special_cases[@]}"; do
    if [[ "${entry%%|*}" == "$name" ]]; then
      echo "$entry"
      return 0
    fi
  done
  return 1
}

echo "== run samples =="
names=()
for f in python/*/*.py go/*/*.go; do
  rel="${f#*/}"
  names+=("${rel%.*}")
done
mapfile_sorted="$(printf '%s\n' "${names[@]}" | sort -u)"

while IFS= read -r name; do
  [[ "$name" == ch04/score_ahc001 ]] && continue # 下で個別に実行（入力+出力が必要）
  ch="${name%%/*}"
  input="data/$ch/sample.txt"
  [[ -f "$input" ]] || input=/dev/null
  py_args=""
  go_args=""
  if entry="$(lookup_special "$name")"; then
    IFS='|' read -r _ input py_args go_args <<<"$entry"
  fi
  # shellcheck disable=SC2086  # 引数は意図的に単語分割する
  [[ -f "python/$name.py" ]] && run_case "py/$name" "$input" python "python/$name.py" $py_args
  # shellcheck disable=SC2086
  [[ -f "go/$name.go" ]] && run_case "go/$name" "$input" go run "go/$name.go" $go_args
done <<<"$mapfile_sorted"

# 第4章のスコア計算は「入力 + ソルバ出力」を食わせる
if [[ -z "$FILTER" || "ch04/score_ahc001" == *"$FILTER"* ]]; then
  if python python/ch04/ahc001_grow.py <data/ch04/sample.txt >"$TMP_DIR/ahc001.out" 2>/dev/null; then
    cat data/ch04/sample.txt "$TMP_DIR/ahc001.out" >"$TMP_DIR/ahc001.in"
    run_case "py/ch04/score_ahc001" "$TMP_DIR/ahc001.in" python python/ch04/score_ahc001.py
    run_case "go/ch04/score_ahc001" "$TMP_DIR/ahc001.in" go run go/ch04/score_ahc001.go
  fi
fi

# ---------- 4. Python / Go の stdout 一致（乱数・時間に依存しないもの） ----------
echo "== python/go output match (deterministic programs) =="
deterministic=(
  ch01/rating_band ch01/score_intro_hc ch01/greedy_intro_hc
  ch03/score_module ch03/toy_score
  ch04/ahc001_grow ch04/score_ahc001 ch05/greedy_delivery ch07/coarsen
  ch10/beam_fill ch15/slide_beam ch17/territory_greedy ch20/mcts_toy
  ch22/review_sheet ch27/paper_transfer
)
for name in "${deterministic[@]}"; do
  [[ -n "$FILTER" && "$name" != *"$FILTER"* ]] && continue
  key="${name//\//_}"
  py_out="$TMP_DIR/py_$key.out"
  go_out="$TMP_DIR/go_$key.out"
  [[ -f "$py_out" && -f "$go_out" ]] || continue
  if cmp -s "$py_out" "$go_out"; then
    ok
  else
    diff "$py_out" "$go_out" >"$TMP_DIR/diff.log"
    ng "stdout differs: $name" "$TMP_DIR/diff.log"
  fi
done

echo ""
echo "passed: $pass  failed: $fail"
if [[ "$fail" -gt 0 ]]; then
  printf '  - %s\n' "${failed[@]}" >&2
  exit 1
fi
