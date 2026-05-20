#!/usr/bin/env bash
# Validate a chapter file for basic yukkuri-heuristics conventions.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

chapter="${1:?usage: validate-chapter.sh <chapter_number>}"
chapter="$(printf '%02d' "$chapter")"
doc="docs/${chapter}.md"

if [[ ! -f "$doc" ]]; then
  echo "FAIL: missing $doc" >&2
  exit 1
fi

errors=0
warn=0

check() {
  local desc="$1"
  local pattern="$2"
  if ! grep -qE "$pattern" "$doc"; then
    echo "FAIL: $desc" >&2
    errors=$((errors + 1))
  fi
}

warn_if() {
  local desc="$1"
  local pattern="$2"
  if ! grep -qE "$pattern" "$doc"; then
    echo "WARN: $desc" >&2
    warn=$((warn + 1))
  fi
}

check "no Reimu dialogue" '\*\*霊夢\*\*:'
check "no Marisa dialogue" '\*\*魔理沙\*\*:'
check "no python code block" '```python'
check "no go code block" '```go'
warn_if "no chapter summary (章末まとめ)" '章末まとめ'

code_blocks="$(grep -c '^```' "$doc" || true)"
if [[ "$code_blocks" -lt 6 ]]; then
  echo "WARN: only $code_blocks code fence lines (recommend more for technique chapters)" >&2
  warn=$((warn + 1))
fi

# Extract referenced python/go paths from markdown
while IFS= read -r path; do
  if [[ ! -f "$path" ]]; then
    echo "WARN: referenced file missing: $path" >&2
    warn=$((warn + 1))
  fi
done < <(grep -oE '(python|go)/[a-zA-Z0-9_./-]+\.(py|go)' "$doc" | sort -u)

if [[ "$errors" -gt 0 ]]; then
  echo "Validation failed with $errors error(s), $warn warning(s)." >&2
  exit 1
fi

echo "OK: $doc ($code_blocks code fence lines, $warn warning(s))"
