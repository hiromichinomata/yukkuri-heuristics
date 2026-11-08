# python/ch27/paper_transfer.py
"""論文メモ YAML（または JSON）から AHC 転用アイデアを抽出し、玩具検証を実行（第27章）."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def default_notes_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "ch27" / "paper_notes.yaml"


def load_notes(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    elif yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = load_yaml_subset(text)
    return data if isinstance(data, dict) else {}


# --- PyYAML がなくても paper_notes.yaml 程度の YAML を読む簡易ローダー ---
# 対応: インデントによる入れ子の map / list、"- key: value" 形式の list of map、
#       [a, b] のフロー list、"|" のブロック文字列、引用符付き文字列、整数・小数・真偽値。
# アンカーや複数行のフロー記法などは非対応（必要なら pip install pyyaml）。


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_skippable(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _parse_scalar(raw: str) -> Any:
    val = raw.strip()
    if val.startswith('"') and val.endswith('"') and len(val) >= 2:
        return json.loads(val)
    if val.startswith("'") and val.endswith("'") and len(val) >= 2:
        return val[1:-1].replace("''", "'")
    if " #" in val:  # 行末コメント
        val = val.split(" #", 1)[0].rstrip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [_parse_scalar(x) for x in inner.split(",")] if inner else []
    if val in ("", "~", "null"):
        return None
    if val in ("true", "false"):
        return val == "true"
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        return val


class _YamlSubsetParser:
    def __init__(self, text: str) -> None:
        self.lines = text.splitlines()
        self.i = 0

    def _skip(self) -> None:
        while self.i < len(self.lines) and _is_skippable(self.lines[self.i]):
            self.i += 1

    def parse(self) -> Any:
        self._skip()
        if self.i >= len(self.lines):
            return {}
        return self._block(_indent_of(self.lines[self.i]))

    def _block(self, indent: int) -> Any:
        if self.lines[self.i].strip().startswith("- ") or self.lines[self.i].strip() == "-":
            return self._list(indent)
        return self._map(indent)

    def _list(self, indent: int) -> List[Any]:
        out: List[Any] = []
        while True:
            self._skip()
            if self.i >= len(self.lines):
                return out
            line = self.lines[self.i]
            item = line.strip()
            if _indent_of(line) != indent or not (item.startswith("- ") or item == "-"):
                return out
            rest = item[1:].strip()
            if rest == "":
                self.i += 1
                self._skip()
                out.append(self._block(_indent_of(self.lines[self.i])))
            elif _split_key(rest) is not None:
                # "- key: value" は、ダッシュの次の位置から始まる map とみなす
                child_indent = indent + (len(item) - len(rest))
                self.lines[self.i] = " " * child_indent + rest
                out.append(self._map(child_indent))
            else:
                out.append(_parse_scalar(rest))
                self.i += 1

    def _map(self, indent: int) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        while True:
            self._skip()
            if self.i >= len(self.lines):
                return out
            line = self.lines[self.i]
            if _indent_of(line) != indent or line.strip().startswith("- "):
                return out
            kv = _split_key(line.strip())
            if kv is None:
                raise ValueError(f"YAML line {self.i + 1}: expected 'key: value': {line!r}")
            key, val = kv
            self.i += 1
            if val in ("|", "|-"):
                out[key] = self._block_scalar(indent, keep_newline=(val == "|"))
            elif val == "":
                self._skip()
                if self.i < len(self.lines) and _indent_of(self.lines[self.i]) > indent:
                    out[key] = self._block(_indent_of(self.lines[self.i]))
                elif self.i < len(self.lines) and _indent_of(self.lines[self.i]) == indent and self.lines[self.i].strip().startswith("- "):
                    out[key] = self._list(indent)  # インデントなしの list
                else:
                    out[key] = None
            else:
                out[key] = _parse_scalar(val)

    def _block_scalar(self, parent_indent: int, keep_newline: bool) -> str:
        body: List[str] = []
        block_indent = None
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.strip() == "":
                body.append("")
                self.i += 1
                continue
            ind = _indent_of(line)
            if ind <= parent_indent:
                break
            if block_indent is None:
                block_indent = ind
            body.append(line[block_indent:])
            self.i += 1
        while body and body[-1] == "":
            body.pop()
        return "\n".join(body) + ("\n" if keep_newline and body else "")


def _split_key(text: str) -> Any:
    """'key: value' / 'key:' を (key, value) に分ける。そうでなければ None."""
    if text.startswith(('"', "'", "[")):
        return None
    if text.endswith(":"):
        return text[:-1].strip(), ""
    if ": " in text:
        key, val = text.split(": ", 1)
        return key.strip(), val.strip()
    return None


def load_yaml_subset(text: str) -> Any:
    return _YamlSubsetParser(text).parse()


def tour_length(points: Sequence[Sequence[int]]) -> float:
    n = len(points)
    if n < 2:
        return 0.0
    total = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def two_opt_once(points: List[List[int]]) -> Tuple[List[List[int]], float]:
    n = len(points)
    best = [list(p) for p in points]
    best_len = tour_length(best)
    # 辺 (i, i+1) と (j, j+1) を張り替える。i=0 のとき j=n-1 は辺 (n-1, 0) が隣接するので除く
    for i in range(n - 1):
        for j in range(i + 2, n if i > 0 else n - 1):
            new = best[: i + 1] + best[i + 1 : j + 1][::-1] + best[j + 1 :]
            new_len = tour_length(new)
            if new_len + 1e-9 < best_len:
                best = new
                best_len = new_len
    return best, best_len


def run_toy_verify(spec: Dict[str, Any]) -> None:
    algo = spec.get("algorithm", "two_opt")
    points = spec.get("points", [])
    if algo != "two_opt":
        print(f"toy_verify: unsupported algorithm {algo}", file=sys.stderr)
        return
    if len(points) < 3:
        print("toy_verify: need at least 3 points", file=sys.stderr)
        return
    before = tour_length(points)
    improved, after = two_opt_once([list(p) for p in points])
    print("=== toy verification (2-opt on sample tour) ===")
    print(f"points: {points}")
    print(f"length before: {before:.4f}")
    print(f"length after:  {after:.4f}")
    print(f"improved: {after < before - 1e-9}")
    print(f"tour after 2-opt: {improved}")


def print_transfer_ideas(notes: Dict[str, Any]) -> None:
    paper = notes.get("paper", {})
    print("=== paper ===")
    print(f"title: {paper.get('title', '?')}")
    print(f"year: {paper.get('year', '?')}  venue: {paper.get('venue', '?')}")
    print()
    print("=== key ideas → AHC ===")
    for item in notes.get("key_ideas", []):
        if isinstance(item, dict):
            print(f"- {item.get('name', '?')}: {item.get('summary', '')}")
            print(f"  AHC: {item.get('ahc_analogy', '')}")
        else:
            print(f"- {item}")
    print()
    print("=== transfer candidates ===")
    for cand in notes.get("transfer_candidates", []):
        if isinstance(cand, dict):
            print(f"- target: {cand.get('target', '?')}")
            print(f"  technique: {cand.get('technique', '?')}")
            print(f"  expected_gain: {cand.get('expected_gain', '?')}")
            print(f"  risk: {cand.get('risk', '?')}")
        else:
            print(f"- {cand}")
    reader = notes.get("reader_notes", "")
    if reader:
        print()
        print("=== reader notes (excerpt) ===")
        print(reader.strip()[:200] + ("..." if len(str(reader)) > 200 else ""))


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_notes_path()
    if yaml is None and path.suffix in (".yaml", ".yml"):
        print("note: PyYAML なしのため簡易ローダーで読みます（pip install pyyaml 推奨）", file=sys.stderr)
    notes = load_notes(path)
    print_transfer_ideas(notes)
    print()
    run_toy_verify(notes.get("toy_verify", {}))


if __name__ == "__main__":
    main()
