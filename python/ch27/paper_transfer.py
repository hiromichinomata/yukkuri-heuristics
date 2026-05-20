# python/ch27/paper_transfer.py
"""論文メモ YAML から AHC 転用アイデアを抽出し、玩具検証を実行（第27章）."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple  # noqa: F401 used in minimal loader

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def default_notes_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "ch27" / "paper_notes.yaml"


def load_notes(path: Path) -> Dict[str, Any]:
    if yaml is not None and path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    json_path = path.with_suffix(".json")
    if json_path.is_file():
        with json_path.open(encoding="utf-8") as f:
            return json.load(f)
    return _load_notes_minimal(path.read_text(encoding="utf-8"))


def _load_notes_minimal(text: str) -> Dict[str, Any]:
    """PyYAML なしでも data/ch27/paper_notes.yaml を読む."""
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]

    def container() -> Any:
        return stack[-1][1]

    def pop_to(indent: int) -> None:
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        pop_to(indent)

        if line.startswith("- "):
            rest = line[2:].strip()
            parent = container()
            if not isinstance(parent, list):
                continue
            if rest.startswith("[") and rest.endswith("]"):
                a, b = rest[1:-1].split(",")
                parent.append([int(a.strip()), int(b.strip())])
            elif ":" in rest:
                k, v = rest.split(":", 1)
                parent.append({k.strip(): v.strip().strip('"')})
            else:
                parent.append(rest.strip('"'))
            continue

        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        parent = container()

        if val == "":
            child: Any = []
            if isinstance(parent, dict):
                parent[key] = child
            stack.append((indent, child))
            continue
        if val == "|":
            block: List[str] = []
            if isinstance(parent, dict):
                parent[key] = "\n".join(block)
            stack.append((indent, block))
            continue

        if isinstance(stack[-1][1], list) and not line.startswith("- "):
            # multiline block content
            stack[-1][1].append(raw.strip())
            continue

        cleaned = val.strip('"')
        if isinstance(parent, dict):
            parent[key] = cleaned
        elif isinstance(parent, list) and parent and isinstance(parent[-1], dict):
            parent[-1][key] = cleaned

    # リスト項目の続きキー (summary など) をマージ
    notes = root
    for section in ("key_ideas", "transfer_candidates"):
        items = notes.get(section, [])
        if items and all(isinstance(x, dict) for x in items):
            continue
    return notes


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
    improved = False
    for i in range(n):
        for k in range(i + 2, n + (0 if i == 0 else 1)):
            j = k % n
            if j == i or (j + 1) % n == i:
                continue
            new = best[: i + 1] + best[i + 1 : j + 1][::-1] + best[j + 1 :]
            new_len = tour_length(new)
            if new_len + 1e-9 < best_len:
                best = new
                best_len = new_len
                improved = True
    return best, best_len if improved else best_len


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
        print(
            "note: loaded data/ch27/paper_notes.json "
            "(pip install pyyaml to parse .yaml directly)",
            file=sys.stderr,
        )
    notes = load_notes(path)
    print_transfer_ideas(notes)
    print()
    run_toy_verify(notes.get("toy_verify", {}))


if __name__ == "__main__":
    main()
