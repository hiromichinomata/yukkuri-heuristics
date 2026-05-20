# python/ch26/simple_vis.py
"""グリッド + 経路を ASCII / HTML で可視化（第26章）."""
from __future__ import annotations

import argparse
import html
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, TextIO, Tuple

CELL_CHARS = {
    0: ".",
    1: "#",
    2: "S",
    3: "G",
}
PATH_CHAR = "*"


@dataclass
class VisInput:
    n: int
    grid: List[List[int]]
    path: List[Tuple[int, int]]


def read_vis(stream: TextIO) -> VisInput:
    lines = [ln.strip() for ln in stream.read().splitlines() if ln.strip()]
    n = int(lines[0])
    grid = [list(map(int, lines[i + 1].split())) for i in range(n)]
    path_len = int(lines[n + 1])
    path = []
    for i in range(path_len):
        r, c = map(int, lines[n + 2 + i].split())
        path.append((r, c))
    return VisInput(n=n, grid=grid, path=path)


def overlay_path(grid: Sequence[Sequence[int]], path: Sequence[Tuple[int, int]]) -> List[List[str]]:
    n = len(grid)
    view = [[CELL_CHARS.get(grid[r][c], "?") for c in range(n)] for r in range(n)]
    for r, c in path:
        if not (0 <= r < n and 0 <= c < n):
            continue
        if grid[r][c] in (2, 3):
            view[r][c] = CELL_CHARS[grid[r][c]]
        else:
            view[r][c] = PATH_CHAR
    return view


def render_ascii(view: Sequence[Sequence[str]]) -> str:
    rows = [" ".join(row) for row in view]
    border = "+" + "-" * (len(view[0]) * 2 - 1) + "+"
    body = "\n".join("| " + row + " |" for row in rows)
    return "\n".join([border, body, border])


def cell_color(ch: str) -> str:
    return {
        ".": "#f8f9fa",
        "#": "#343a40",
        "S": "#0d6efd",
        "G": "#198754",
        "*": "#ffc107",
    }.get(ch, "#dee2e6")


def render_html(view: Sequence[Sequence[str]], title: str) -> str:
    cells = []
    for row in view:
        for ch in row:
            bg = cell_color(ch)
            cells.append(
                f'<td style="width:28px;height:28px;text-align:center;'
                f'background:{bg};font-family:monospace;font-weight:bold;">'
                f"{html.escape(ch)}</td>"
            )
    table = "<tr>" + "</tr><tr>".join(
        "".join(cells[i : i + len(view[0])]) for i in range(0, len(cells), len(view[0]))
    ) + "</tr>"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8"><title>{html.escape(title)}</title></head>
<body>
<h1>{html.escape(title)}</h1>
<p>凡例: . 空き / # 壁 / S 開始 / G ゴール / * 経路</p>
<table cellspacing="2" cellpadding="0">{table}</table>
</body>
</html>
"""


def default_data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "ch26" / "sample.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid path visualizer (ASCII / HTML)")
    parser.add_argument(
        "input",
        nargs="?",
        default=str(default_data_path()),
        help="input file (default: data/ch26/sample.txt)",
    )
    parser.add_argument("--html", action="store_true", help="emit HTML instead of ASCII")
    args = parser.parse_args()

    path = Path(args.input)
    with path.open(encoding="utf-8") as f:
        vis = read_vis(f)
    view = overlay_path(vis.grid, vis.path)
    title = f"ch26 path vis ({path.name}, n={vis.n}, steps={len(vis.path)})"

    if args.html:
        print(render_html(view, title))
    else:
        print(render_ascii(view))

    print(f"legend: . empty  # wall  S start  G goal  * path", file=sys.stderr)
    print(f"grid={vis.n} path_len={len(vis.path)}", file=sys.stderr)


if __name__ == "__main__":
    main()
