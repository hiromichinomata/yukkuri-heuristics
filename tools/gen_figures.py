#!/usr/bin/env python
"""本文の図（docs/images/*.svg）を、各章のコードを実際に動かして作る.

  python tools/gen_figures.py              # docs/images/ に書き出す
  python tools/gen_figures.py --out DIR    # 別の場所に書き出す（テストで使う）

外部ライブラリは使わない。乱数の seed も手数も固定しているので、何度動かしても同じ SVG になる。
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import math
import random
import sys
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]

# 色（白地で見やすく、色の区別がつきにくい人にも分かりやすい組み合わせ）
BLUE, ORANGE, GREEN, PURPLE, RED = "#2563eb", "#ea580c", "#16a34a", "#7c3aed", "#dc2626"
GRAY, LIGHT, INK = "#9ca3af", "#e5e7eb", "#111827"
FONT = "Hiragino Sans, Noto Sans CJK JP, Meiryo, sans-serif"


def load(rel: str, name: str):
    """python/chNN/xxx.py をモジュールとして読む（同じ名前のファイルがあってもぶつからないように）."""
    path = ROOT / "python" / rel
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass が sys.modules を参照するので先に登録する
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    sys.path.pop(0)
    return mod


class Svg:
    def __init__(self, width: int, height: int) -> None:
        self.w, self.h = width, height
        self.items: List[str] = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>']
        self.title = ""  # 最初に書いた文字（各図の見出し）。<title> に入れて、読み上げや単体表示で使う

    def add(self, s: str) -> None:
        self.items.append(s)

    def line(self, x1, y1, x2, y2, color=INK, width=1.5, dash: str = "", opacity: float = 1.0) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' stroke-opacity="{opacity}"' if opacity < 1 else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{d}{o}/>')

    def polyline(self, pts: Sequence[Tuple[float, float]], color=INK, width=1.5, closed=False) -> None:
        tag = "polygon" if closed else "polyline"
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<{tag} points="{p}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')

    def rect(self, x, y, w, h, fill="none", stroke=INK, width=1.0, opacity: float = 1.0) -> None:
        o = f' fill-opacity="{opacity}"' if opacity < 1 else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{o} stroke="{stroke}" stroke-width="{width}"/>')

    def circle(self, x, y, r, fill=INK, stroke="none", width=1.0) -> None:
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x, y, s, size=13, color=INK, anchor="start", weight="normal") -> None:
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if not self.title:
            self.title = s
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>'
        )

    def arrow(self, x1, y1, x2, y2, color=INK, width=1.5) -> None:
        self.line(x1, y1, x2, y2, color, width)
        ang = math.atan2(y2 - y1, x2 - x1)
        for da in (2.6, -2.6):
            self.line(x2, y2, x2 + 8 * math.cos(ang + da), y2 + 8 * math.sin(ang + da), color, width)

    def render(self) -> str:
        body = "\n".join(self.items)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img">\n<title>{self.title}</title>\n{body}\n</svg>\n'
        )


def legend(svg: Svg, x: float, y: float, entries: Sequence[Tuple[str, str]]) -> None:
    for i, (color, label) in enumerate(entries):
        yy = y + i * 18
        svg.line(x, yy - 4, x + 18, yy - 4, color, 3)
        svg.text(x + 24, yy, label, 12)


def chart(
    svg: Svg,
    box: Tuple[float, float, float, float],
    series: Sequence[Tuple[str, Sequence[Tuple[float, float]]]],
    xlabel: str,
    ylabel: str,
    ymin: float | None = None,
    ymax: float | None = None,
    yfmt: Callable[[float], str] = lambda v: f"{v:g}",
    xticks: Sequence[float] | None = None,
) -> Callable[[float, float], Tuple[float, float]]:
    """折れ線グラフを描き、データ座標 → 画面座標の変換を返す."""
    x0, y0, w, h = box
    xs = [p[0] for _, s in series for p in s]
    ys = [p[1] for _, s in series for p in s]
    lo = min(ys) if ymin is None else ymin
    hi = max(ys) if ymax is None else ymax
    xlo, xhi = min(xs), max(xs)

    def tr(x: float, y: float) -> Tuple[float, float]:
        return x0 + (x - xlo) / (xhi - xlo or 1) * w, y0 + h - (y - lo) / (hi - lo or 1) * h

    for k in range(5):
        v = lo + (hi - lo) * k / 4
        _, yy = tr(xlo, v)
        svg.line(x0, yy, x0 + w, yy, LIGHT, 1)
        svg.text(x0 - 6, yy + 4, yfmt(v), 11, GRAY, "end")
    for v in xticks if xticks is not None else [xlo + (xhi - xlo) * k / 4 for k in range(5)]:
        xx, _ = tr(v, lo)
        svg.text(xx, y0 + h + 16, f"{v:.0f}" if xhi - xlo >= 8 else f"{v:g}", 11, GRAY, "middle")
    svg.line(x0, y0 + h, x0 + w, y0 + h, INK, 1)
    svg.line(x0, y0, x0, y0 + h, INK, 1)
    svg.text(x0 + w / 2, y0 + h + 34, xlabel, 12, INK, "middle")
    svg.text(x0, y0 - 10, ylabel, 12, INK, "start")
    for color, s in series:
        svg.polyline([tr(x, y) for x, y in s], color, 2)
    return tr


def draw_tour(svg: Svg, box, pts, tour, color=BLUE, highlight: Sequence[int] = ()) -> None:
    x0, y0, w, h = box
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)

    def tr(p):
        return x0 + (p[0] - lo_x) / (hi_x - lo_x or 1) * w, y0 + h - (p[1] - lo_y) / (hi_y - lo_y or 1) * h

    if tour:
        svg.polyline([tr(pts[i]) for i in tour], color, 1.8, closed=True)
    hl = set(highlight)
    for i, p in enumerate(pts):
        x, y = tr(p)
        if i in hl:
            svg.circle(x, y, 5, "#ffffff", RED, 2)
        else:
            svg.circle(x, y, 3, INK)


# ---------------------------------------------------------------- 各図


def box(svg: Svg, x: float, y: float, w: float, h: float, lines: Sequence[str], color: str = INK, fill: str = "#ffffff", size: int = 12) -> None:
    """角丸の箱に、中央ぞろえで 1〜数行の文字を書く（概念図用）."""
    svg.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="{fill}" stroke="{color}" stroke-width="1.5"/>')
    top = y + h / 2 - (len(lines) - 1) * (size + 4) / 2 + size * 0.38
    for k, s in enumerate(lines):
        svg.text(x + w / 2, top + k * (size + 4), s, size, color if k == 0 else INK, "middle", "bold" if k == 0 else "normal")


def read_intro_hc(rel: str) -> Tuple[int, List[int], List[List[int]], List[int]]:
    """Intro HC 形式（D, c, s と、あれば後ろの日程）を読む."""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    d = int(lines[0])
    c = list(map(int, lines[1].split()))
    s = [list(map(int, lines[2 + i].split())) for i in range(d)]
    rest = [int(x) for x in lines[2 + d : 2 + 2 * d] if x.strip()]
    return d, c, s, rest


def fig_ch01_daily() -> str:
    g = load("ch01/greedy_intro_hc.py", "fig_greedy01")
    d, c, s, schedule = read_intro_hc("data/ch01/sample.txt")
    daily = g.daily_satisfactions(d, c, s, schedule)
    gains, decays = [], []
    last = [0] * 26
    for day in range(1, d + 1):
        t = schedule[day - 1] - 1
        last[t] = day
        gains.append(s[day - 1][t])
        decays.append(sum(c[i] * (day - last[i]) for i in range(26)))
    assert all(daily[k] == sum(gains[: k + 1]) - sum(decays[: k + 1]) for k in range(d))
    svg = Svg(660, 350)
    svg.text(20, 24, "第1章: 1 日ごとの満足度の増減（data/ch01/sample.txt の日程）", 13, INK, "start", "bold")
    x0, y0, w, h = 80, 60, 380, 220
    hi = max(max(gains), max(daily)) * 1.1
    lo = -max(decays) * 1.6

    def ty(v: float) -> float:
        return y0 + h - (v - lo) / (hi - lo) * h

    for k in range(6):
        v = lo + (hi - lo) * k / 5
        svg.line(x0, ty(v), x0 + w, ty(v), LIGHT, 1)
        svg.text(x0 - 6, ty(v) + 4, f"{v / 1000:.0f}", 11, GRAY, "end")
    svg.line(x0, ty(0), x0 + w, ty(0), INK, 1)
    svg.line(x0, y0, x0, y0 + h, INK, 1)
    svg.text(x0, y0 - 10, "満足度（千）", 12)
    step = w / d
    pts = []
    for k in range(d):
        cx = x0 + (k + 0.5) * step
        svg.rect(cx - 22, ty(gains[k]), 20, ty(0) - ty(gains[k]), GREEN, "none", 0, 0.8)
        svg.rect(cx + 2, ty(0), 20, ty(-decays[k]) - ty(0), ORANGE, "none", 0, 0.8)
        svg.text(cx, y0 + h + 16, f"{k + 1} 日目", 11, GRAY, "middle")
        svg.text(cx, y0 + h + 30, f"タイプ {schedule[k]}", 11, GRAY, "middle")
        pts.append((cx, ty(daily[k])))
    svg.polyline(pts, BLUE, 2.5)
    for x, y in pts:
        svg.circle(x, y, 4, BLUE)
    lx = 490
    svg.rect(lx, 76, 14, 14, GREEN, "none", 0, 0.8)
    svg.text(lx + 22, 88, "その日の開催で増える s", 12)
    svg.rect(lx, 100, 14, 14, ORANGE, "none", 0, 0.8)
    svg.text(lx + 22, 112, "開いていない種類の減衰", 12)
    legend(svg, lx, 140, [(BLUE, "満足度（累計）")])
    svg.text(lx, 178, f"最終の満足度 {daily[-1]}", 12, BLUE, "start", "bold")
    svg.text(lx, 196, f"スコア 10⁶ + {daily[-1]}", 12, BLUE)
    svg.text(lx, 214, f"= {10**6 + daily[-1]}", 12, BLUE)
    svg.text(20, 340, "減衰は、長く開いていない種類ほど毎日大きくなる。増える分だけでなく、減る分も見て日程を選ぶ", 11, GRAY)
    return svg.render()


def fig_ch02_pipeline() -> str:
    svg = Svg(700, 250)
    svg.text(20, 24, "第2章: ローカル評価の流れ（python/ch02/run_local.py が自動でつなぐ部分は青）", 13, INK, "start", "bold")
    y, h = 70, 56
    box(svg, 20, y, 110, h, ["gen", "入力を作る"], GRAY)
    box(svg, 170, y, 110, h, ["input.txt", "問題の入力"], INK)
    box(svg, 320, y, 110, h, ["solver", "自分のプログラム"], BLUE, "#eff6ff")
    box(svg, 470, y, 110, h, ["output.txt", "解"], INK)
    box(svg, 470, 170, 110, h, ["score", "スコアを計算"], BLUE, "#eff6ff")
    box(svg, 620 - 30, 170, 100, h, ["vis", "目で見る（任意）"], GRAY)
    svg.arrow(130, y + h / 2, 168, y + h / 2)
    svg.arrow(280, y + h / 2, 318, y + h / 2, BLUE, 2)
    svg.arrow(430, y + h / 2, 468, y + h / 2, BLUE, 2)
    svg.arrow(525, y + h, 525, 168, BLUE, 2)
    svg.add(f'<path d="M 225 {y + h} L 225 198 L 466 198" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    svg.arrow(450, 198, 468, 198, BLUE, 2)
    svg.text(240, 192, "入力も一緒に渡す", 11, GRAY)
    svg.arrow(580, y + h / 2 + 10, 630, 168, GRAY, 1.5)
    svg.text(20, 242, "solver は標準入力から読んで標準出力に書く。score は「入力 + 出力」を読んでスコアを stderr に出す", 11, GRAY)
    return svg.render()


def fig_ch03_state_move() -> str:
    sm = load("ch03/score_module.py", "fig_score03")
    problem, state = sm.read_problem_with_schedule(open(ROOT / "data/ch03/sample.txt", encoding="utf-8"))
    moved = sm.apply_move(state, day=0, contest_type=2)  # try_move.py と同じ 1 手
    before, after = sm.score_schedule(problem, state), sm.score_schedule(problem, moved)
    svg = Svg(700, 330)
    svg.text(20, 24, "第3章: State・Move・Score（data/ch03/sample.txt、try_move.py の 1 手）", 13, INK, "start", "bold")
    cw = 40

    def row(x: float, y: float, types: List[int], title: str, col: str, hl: int = -1) -> None:
        svg.text(x, y - 8, title, 12, col, "start", "bold")
        for k, t in enumerate(types):
            fill = "#fff7ed" if k == hl else "#ffffff"
            svg.rect(x + k * cw, y, cw, 32, fill, ORANGE if k == hl else INK, 2 if k == hl else 1)
            svg.text(x + (k + 0.5) * cw, y + 21, str(t), 13, INK, "middle")
            svg.text(x + (k + 0.5) * cw, y + 46, f"{k + 1}日", 10, GRAY, "middle")

    row(30, 70, state.types, "State: 各日のコンテストの種類", BLUE)
    svg.arrow(130, 130, 130, 168, ORANGE, 2)
    svg.text(142, 154, "Move: 1 日目を種類 2 に変える", 12, ORANGE, "start", "bold")
    row(30, 196, moved.types, "次の State", BLUE, 0)
    svg.text(30, 270, f"Score: {before.contest_score} → {after.contest_score}（{after.contest_score - before.contest_score:+d}）", 13, INK, "start", "bold")
    svg.text(30, 290, "悪くなる 1 手。山登りなら採用しない", 12, GRAY)
    tr = chart(svg, (330, 70, 330, 190), [(GRAY, [(k + 1, v / 1000) for k, v in enumerate(before.daily)]), (ORANGE, [(k + 1, v / 1000) for k, v in enumerate(after.daily)])],
               "日", "その日の終わりの満足度（千）", None, None, lambda v: f"{v:.0f}")
    legend(svg, 470, 230, [(GRAY, "元の日程"), (ORANGE, "1 日目を変えた日程")])
    svg.text(20, 320, "Move は State の一部だけを変える。Score は日程全体から計算し直す（第9章で差分だけ計算する方法を学ぶ）", 11, GRAY)
    return svg.render()


def fig_ch08_vis() -> str:
    v = load("ch08/simple_vis.py", "fig_vis")
    inp = v.read_vis(open(ROOT / "data/ch08/sample.txt", encoding="utf-8"))
    view = v.overlay_path(inp.grid, inp.path)
    svg = Svg(660, 330)
    svg.text(20, 24, "第8章: simple_vis.py の ASCII 出力と、同じ内容を色で描いたもの（data/ch08/sample.txt）", 13, INK, "start", "bold")
    ascii_lines = v.render_ascii(view).splitlines()
    for k, line in enumerate(ascii_lines):
        svg.add(f'<text x="30" y="{70 + k * 20}" font-family="Menlo, Consolas, monospace" font-size="15" fill="{INK}" xml:space="preserve">{line}</text>')
    cell, ox, oy = 30, 340, 50
    colors = {".": "#ffffff", "#": "#374151", "S": GREEN, "G": RED, "*": "#bfdbfe"}
    for r, row in enumerate(view):
        for c, ch in enumerate(row):
            svg.rect(ox + c * cell, oy + r * cell, cell, cell, colors.get(ch, "#ffffff"), LIGHT, 1)
            if ch in "SG":
                svg.text(ox + (c + 0.5) * cell, oy + (r + 0.5) * cell + 5, ch, 13, "#ffffff", "middle", "bold")
    svg.polyline([(ox + (c + 0.5) * cell, oy + (r + 0.5) * cell) for r, c in inp.path], BLUE, 2.5)
    svg.text(20, 320, "* と青い線 = 経路、# = 壁。この例の経路はゴール G に届いていない——数字だけ見ていると気づきにくい", 11, GRAY)
    return svg.render()


def fig_ch11_pipeline() -> str:
    p = load("ch11/pipeline.py", "fig_pipeline")
    problem = p.read_problem(open(ROOT / "data/common/intro_hc_d365.txt", encoding="utf-8"))
    rng = random.Random(42)
    state = p.greedy_schedule(problem)
    types = list(state.types)
    score = 10**6 + p._final_satisfaction(problem, state)
    greedy_score = score
    hc_steps, sa_steps = 1200, 12000  # 時間の代わりに手数で区切る（図を毎回同じにするため）
    hc_pts, sa_cur, sa_best = [(0, score / 1e6)], [], []
    for step in range(1, hc_steps + 1):  # hill_climb と同じ手順
        day = rng.randrange(problem.days)
        old = types[day]
        for t in range(1, 27):
            if t != old:
                delta = p.delta_change(problem, types, day, t)
                if delta > 0:
                    types[day] = t
                    score += delta
                    break
        if step % 20 == 0:
            hc_pts.append((step, score / 1e6))
    hc_score = best = score
    for i in range(sa_steps):  # sa と同じ手順
        temp = p.T0 * (p.T1 / p.T0) ** (i / sa_steps)
        day, new_type = rng.randrange(problem.days), rng.randint(1, 26)
        delta = p.delta_change(problem, types, day, new_type)
        if delta >= 0 or rng.random() < math.exp(delta / temp):
            types[day] = new_type
            score += delta
            best = max(best, score)
        if (i + 1) % 100 == 0:
            sa_cur.append((hc_steps + i + 1, score / 1e6))
            sa_best.append((hc_steps + i + 1, best / 1e6))
    assert score == 10**6 + p._final_satisfaction(problem, p.ScheduleState(types))
    svg = Svg(720, 340)
    svg.text(20, 24, f"第11章: 貪欲 → 山登り（{hc_steps} 手）→ 焼きなまし（{sa_steps} 手）（D=365）", 13, INK, "start", "bold")
    all_v = [v for _, v in hc_pts + sa_cur]
    tr = chart(svg, (80, 60, 440, 210), [(ORANGE, hc_pts), (GRAY, sa_cur), (GREEN, sa_best)], "手数", "スコア（百万、0 で切る前）",
               min(all_v), max(all_v), lambda v: f"{v:.2f}")
    x1, _ = tr(hc_steps, 0)
    svg.line(x1, 60, x1, 270, INK, 1, "4 3")
    legend(svg, 540, 80, [(ORANGE, "山登り"), (GRAY, "焼きなまし（今の解）"), (GREEN, "焼きなまし（最良）")])
    svg.text(540, 150, f"貪欲: {greedy_score}", 12)
    svg.text(540, 168, f"山登り後: {hc_score}", 12, ORANGE)
    svg.text(540, 186, f"焼きなまし後: {best}", 12, GREEN)
    svg.text(20, 330, "山登りはすぐ頭打ちになる。焼きなましは序盤いったん悪くなってから、山登りの先まで伸びる", 11, GRAY)
    return svg.render()


def fig_ch14_uf() -> str:
    lt = load("ch14/loop_toy.py", "fig_loop")
    h, w, grid = lt.read_grid(open(ROOT / "data/ch14/sample.txt", encoding="utf-8"))
    _, edges = lt.greedy_loop_edges(h, w, grid, use_uf=True)
    rejected = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == "#":
                continue
            for nr, nc in lt.neighbors(r, c, h, w):
                if grid[nr][nc] != "#" and (nr, nc) > (r, c):
                    key = (lt.cell_index(r, c, w), lt.cell_index(nr, nc, w))
                    if key not in edges:
                        rejected.add(key)
    svg = Svg(640, 330)
    svg.text(20, 24, "第14章: Union-Find で「同じ組どうしを結ぶ辺」を弾く（data/ch14/sample.txt）", 13, INK, "start", "bold")
    cell, ox, oy = 52, 40, 50

    def center(i: int) -> Tuple[float, float]:
        r, c = divmod(i, w)
        return ox + (c + 0.5) * cell, oy + (r + 0.5) * cell

    for r in range(h):
        for c in range(w):
            if grid[r][c] == "#":
                svg.rect(ox + c * cell + 6, oy + r * cell + 6, cell - 12, cell - 12, "#374151", "none", 0)
    for u, vv in sorted(rejected):
        (x1, y1), (x2, y2) = center(u), center(vv)
        svg.line(x1, y1, x2, y2, RED, 1.5, "4 3")
    for u, vv in sorted(edges):
        (x1, y1), (x2, y2) = center(u), center(vv)
        svg.line(x1, y1, x2, y2, BLUE, 3)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != "#":
                x, y = center(lt.cell_index(r, c, w))
                svg.circle(x, y, 5, INK)
    lx = ox + w * cell + 30
    legend(svg, lx, 80, [(BLUE, f"採用した辺 {len(edges)} 本")])
    svg.line(lx, 104, lx + 18, 104, RED, 1.5, "4 3")
    svg.text(lx + 24, 108, f"弾いた辺 {len(rejected)} 本", 12)
    svg.text(lx, 140, "左上から順に辺を見て、", 12)
    svg.text(lx, 158, "find(u) == find(v) なら", 12)
    svg.text(lx, 176, "閉路ができるので弾く", 12)
    svg.text(lx, 206, "判定は 1 本あたり", 12)
    svg.text(lx, 224, "ほぼ O(1)", 12, BLUE, "start", "bold")
    svg.text(lx, 242, "（全体を数え直すと O(V+E)）", 12, GRAY)
    svg.text(20, 320, f"空きマス {sum(row.count('.') for row in grid)} 個を、閉路を作らずに 1 つにつなぐと、辺はちょうど「マスの数 − 1」本になる", 11, GRAY)
    return svg.render()


def fig_ch15_puzzle() -> str:
    sb = load("ch15/slide_beam.py", "fig_slide")
    n, start = sb.read_state(open(ROOT / "data/ch15/sample.txt", encoding="utf-8"))
    goal = sb.goal_state(n)
    solved, depth, _ = sb.beam_search(start, n)
    assert solved
    # 盤面の並びを手で追うため、manhattan が 1 ずつ減る手を選んで goal まで進める（このサンプルはそれで最短）
    seq = [start]
    while seq[-1] != goal:
        seq.append(min(sb.neighbors(seq[-1], n), key=lambda s: sb.manhattan(s, n, goal)))
    assert len(seq) - 1 == depth
    svg = Svg(660, 280)
    svg.text(20, 24, f"第15章: 3×3 スライドパズル（data/ch15/sample.txt、{depth} 手）と、評価に使うマンハッタン距離", 13, INK, "start", "bold")
    cell = 46
    for k, st in enumerate(seq):
        ox, oy = 40 + k * 220, 70
        hval = sb.manhattan(st, n, goal)
        svg.text(ox, oy - 12, "スタート" if k == 0 else ("ゴール" if st == goal else f"{k} 手目"), 12, INK, "start", "bold")
        for i, val in enumerate(st):
            r, c = divmod(i, n)
            off = val != 0 and goal.index(val) != i
            svg.rect(ox + c * cell, oy + r * cell, cell, cell, "#fff7ed" if off else ("#f3f4f6" if val == 0 else "#ffffff"), ORANGE if off else INK, 2 if off else 1)
            if val:
                svg.text(ox + (c + 0.5) * cell, oy + (r + 0.5) * cell + 6, str(val), 16, INK, "middle", "bold")
        svg.text(ox, oy + n * cell + 22, f"マンハッタン距離 h = {hval}", 12, ORANGE if hval else GREEN, "start", "bold")
        if k + 1 < len(seq):
            svg.arrow(ox + n * cell + 14, oy + n * cell / 2, ox + n * cell + 60, oy + n * cell / 2, INK, 2)
    svg.text(20, 250, "オレンジ = 正しい位置にないタイル。h はそれぞれのタイルが正しい位置まで縦横に何マス離れているかの合計", 11, GRAY)
    svg.text(20, 268, "1 手で動くタイルは 1 枚なので、h は 1 手で高々 1 しか減らない。だから h は「あと何手かかるか」の下界になる", 11, GRAY)
    return svg.render()


def fig_ch17_territory() -> str:
    t = load("ch17/territory_greedy.py", "fig_territory")
    problem = t.read_problem(open(ROOT / "data/ch17/sample.txt", encoding="utf-8"))
    scores, moves = t.solve(problem)
    n = problem.n
    owner = [[-1] * n for _ in range(n)]
    paths: List[List[Tuple[int, int]]] = [[problem.starts[0]], [problem.starts[1]]]
    for a in range(2):
        r, c = problem.starts[a]
        owner[r][c] = a
    for line in moves:
        a, r, c = map(int, line.split())
        owner[r][c] = a
        paths[a].append((r, c))
    svg = Svg(640, 370)
    svg.text(20, 24, f"第17章: 2 人が交互に、隣の空きマスで一番大きい値を取る（data/ch17/sample.txt）", 13, INK, "start", "bold")
    cell, ox, oy = 46, 40, 50
    cols = [BLUE, ORANGE]
    fills = ["#dbeafe", "#ffedd5"]
    for r in range(n):
        for c in range(n):
            o = owner[r][c]
            svg.rect(ox + c * cell, oy + r * cell, cell, cell, fills[o] if o >= 0 else "#ffffff", LIGHT, 1)
            svg.text(ox + c * cell + 6, oy + r * cell + 15, str(problem.grid[r][c]), 11, GRAY)
    for a in range(2):
        pts = [(ox + (c + 0.5) * cell, oy + (r + 0.5) * cell) for r, c in paths[a]]
        svg.polyline(pts, cols[a], 2.5)
        for k, (x, y) in enumerate(pts):
            svg.circle(x, y, 9 if k == 0 else 7, cols[a] if k == 0 else "#ffffff", cols[a], 1.5)
            svg.text(x, y + 4, "S" if k == 0 else str(k), 9, "#ffffff" if k == 0 else cols[a], "middle", "bold")
    lx = ox + n * cell + 30
    for a in range(2):
        svg.text(lx, 80 + a * 50, f"エージェント {a}: {scores[a]} 点", 13, cols[a], "start", "bold")
        svg.text(lx, 98 + a * 50, f"{len(paths[a])} マス", 12)
    svg.text(lx, 200, "左上の小さい数字 = マスの値", 12, GRAY)
    svg.text(lx, 218, "丸の数字 = 何手目に取ったか", 12, GRAY)
    svg.text(20, 360, "どちらも目の前の値だけで動くので、相手の通り道をふさいだり、ふさがれたりしても気にしない", 11, GRAY)
    return svg.render()


def fig_ch21_timeline() -> str:
    import re

    src = (ROOT / "python/ch21/mock_contest.py").read_text(encoding="utf-8")
    phase_min = [float(x) for x in re.search(r"phase_min = \[[^\]]*\] if fast else \[([^\]]*)\]", src).group(1).split(",")]
    names = [("読解", "スコア式・仮説", GRAY), ("実装", "貪欲で 1 本目を提出", BLUE), ("改善", "焼きなましで伸ばす", GREEN), ("提出", "最終確認・提出", ORANGE)]
    total = sum(phase_min)
    assert total == 240, "本文は「4 時間」と書いている"
    svg = Svg(700, 230)
    svg.text(20, 24, f"第21章: 模擬 AHC（{total / 60:g} 時間）の 4 フェーズ（python/ch21/mock_contest.py の既定）", 13, INK, "start", "bold")
    x0, w, y = 30, 640, 70
    x = x0
    for (name, desc, col), mins in zip(names, phase_min):
        ww = w * mins / total
        svg.rect(x, y, ww, 50, col, "#ffffff", 2, 0.25)
        svg.text(x + ww / 2, y + 22, f"{name} {mins:.0f} 分", 13, INK, "middle", "bold")
        svg.text(x + ww / 2, y + 40, desc, 11, INK, "middle")
        x += ww
    for k in range(int(total // 30) + 1):
        xx = x0 + w * k * 30 / total
        svg.line(xx, y + 50, xx, y + 56, INK, 1)
        svg.text(xx, y + 70, f"{k * 30}", 11, GRAY, "middle")
    svg.text(x0 + w, y + 86, "分", 11, GRAY, "end")
    for at, label in [(phase_min[0] + phase_min[1], "1 本目の提出"), (sum(phase_min[:3]), "改善版の提出")]:
        xx = x0 + w * at / total
        svg.line(xx, y - 14, xx, y + 50, RED, 2)
        svg.circle(xx, y - 14, 4, RED)
        svg.text(xx, y - 22, label, 11, RED, "middle", "bold")
    svg.text(20, 200, "実装フェーズの終わりには、どんなに弱くても提出できる解を 1 本出しておく。改善はその上に積む", 11, GRAY)
    svg.text(20, 218, "最後の 30 分は提出の確認用の予備。--fast を付けると、各フェーズを 1 秒未満に縮めて数秒で流れを試せる", 11, GRAY)
    return svg.render()


def fig_ch22_catalog() -> str:
    import json

    cat = json.loads((ROOT / "data/ch22/pattern_catalog.json").read_text(encoding="utf-8"))["patterns"]
    svg = Svg(680, 380)
    svg.text(20, 24, "第22章: 復習の 4 段と、照らし合わせる 5 つの典型パターン（data/ch22/pattern_catalog.json）", 13, INK, "start", "bold")
    steps = [("1. 自力", "タイマー付き"), ("2. 解説", "上位の工夫"), ("3. 再実装", "見ずに 1 機能"), ("4. 差分分析", "差を 5 点書く")]
    cx, cy, rad = 145, 200, 80
    for k, (a, b) in enumerate(steps):
        ang = -math.pi / 2 + k * math.pi / 2
        x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
        box(svg, x - 52, y - 24, 104, 48, [a, b], BLUE, "#eff6ff")
        ang2 = ang + math.pi / 4
        svg.arrow(cx + (rad - 20) * math.cos(ang2 - 0.3), cy + (rad - 20) * math.sin(ang2 - 0.3),
                  cx + (rad - 20) * math.cos(ang2 + 0.3), cy + (rad - 20) * math.sin(ang2 + 0.3), GRAY, 1.5)
    svg.text(cx, cy + 5, "1 問", 13, INK, "middle", "bold")
    svg.arrow(280, 200, 306, 200, INK, 2)
    svg.text(293, 190, "照合", 11, GRAY, "middle")
    cols = [BLUE, ORANGE, GREEN, PURPLE, RED]
    for k, p in enumerate(cat):
        y = 50 + k * 64
        col = cols[k % len(cols)]
        svg.rect(310, y, 300, 56, "#ffffff", col, 1.5)
        svg.text(322, y + 24, p["name"], 13, col, "start", "bold")
        svg.text(322, y + 44, f"--pattern {p['id']}", 11, GRAY)
    svg.text(20, 372, "4 段を回して出てきた工夫を、どのパターンに当たるかで整理する。代表コンテストと典型操作は本文の表を見る", 11, GRAY)
    return svg.render()


def fig_ch23_hypotheses() -> str:
    hc = load("ch23/hypothesis_compare.py", "fig_hypo")
    names = ["greedy", "random_sa", "pipeline_lite"]
    results = {}
    for label, rel in [("D=5", "data/ch23/sample.txt"), ("D=365", "data/common/intro_hc_d365.txt")]:
        problem = hc.read_problem(open(ROOT / rel, encoding="utf-8"))
        rng = random.Random(42)  # main と同じ順に乱数を使う
        states = [hc.strategy_greedy(problem), hc.strategy_random_sa(problem, rng), hc.strategy_pipeline_lite(problem, rng)]
        results[label] = [hc.score_schedule(problem, s) for s in states]
    svg = Svg(700, 320)
    svg.text(20, 24, "第23章: 解法仮説 3 案のスコア（hypothesis_compare.py。入力の大きさで勝者が変わる）", 13, INK, "start", "bold")
    cols = [GRAY, ORANGE, GREEN]
    for p, (label, vals) in enumerate(results.items()):
        x0, y0, w, h = 60 + p * 330, 70, 260, 180
        hi = max(vals) * 1.15
        svg.text(x0, y0 - 14, f"{label}（data/{'ch23/sample.txt' if label == 'D=5' else 'common/intro_hc_d365.txt'}）", 12, INK, "start", "bold")
        svg.line(x0, y0 + h, x0 + w, y0 + h, INK, 1)
        best = max(vals)
        for k, (name, v) in enumerate(zip(names, vals)):
            bx = x0 + 15 + k * 85
            bh = v / hi * h
            svg.rect(bx, y0 + h - bh, 60, bh, cols[k], "none", 0, 0.85)
            svg.text(bx + 30, y0 + h - bh - 6, f"{v:,}", 11, INK, "middle", "bold" if v == best else "normal")
            svg.text(bx + 30, y0 + h + 16, name, 11, INK, "middle")
            if v == best:
                svg.text(bx + 30, y0 + h + 32, "勝ち", 11, RED, "middle", "bold")
    svg.text(20, 296, "D=5 は 3 案ともほぼ同じで、ランダム初期解の焼きなまし（800 手）がわずかに勝つ。D=365 ではその 800 手が足りずに 0 点、", 11, GRAY)
    svg.text(20, 312, "貪欲 + 山登りの pipeline_lite が大きく勝つ。小さい入力で当たりを付けても、最後は本番サイズで確かめる", 11, GRAY)
    return svg.render()


def fig_ch26_ga() -> str:
    g = load("ch26/ga_placement.py", "fig_ga")
    problem = g.read_problem(open(ROOT / "data/ch26/hard.txt", encoding="utf-8"))
    rng = random.Random(42)
    n = len(problem.widths)
    population = [rng.sample(list(range(n)), n) for _ in range(g.POP_SIZE)]
    best_fit, _ = g.evaluate(problem, list(population[0]))
    best_pts, avg_pts = [], []
    best_order = list(population[0])
    for gen in range(g.GENERATIONS):  # ga() と同じ手順で、世代ごとの best と平均を記録する
        fitness = [g.evaluate(problem, ind)[0] for ind in population]
        for fit, ind in zip(fitness, population):
            if fit > best_fit:
                best_fit, best_order = fit, list(ind)
        best_pts.append((gen, best_fit))
        avg_pts.append((gen, sum(fitness) / len(fitness)))
        nxt = [list(population[max(range(g.POP_SIZE), key=lambda i: fitness[i])])]
        while len(nxt) < g.POP_SIZE:
            child = g.order_crossover(g.tournament_select(population, fitness, rng), g.tournament_select(population, fitness, rng), rng)
            g.mutate(child, rng)
            nxt.append(child)
        population = nxt
    with contextlib.redirect_stderr(io.StringIO()):
        assert g.ga(problem, random.Random(42))[1] == best_fit, "図の再現が ga() とずれた"
    greedy_order = sorted(range(n), key=lambda i: -problem.widths[i])
    greedy_fit, greedy_place = g.evaluate(problem, greedy_order)
    _, best_place = g.evaluate(problem, best_order)
    svg = Svg(720, 380)
    svg.text(20, 24, f"第26章: GA の世代ごとのスコア（data/ch26/hard.txt、容量 {problem.capacity}）", 13, INK, "start", "bold")
    chart(svg, (80, 60, 380, 170), [(GRAY, avg_pts), (BLUE, best_pts)], "世代", "入った幅の合計", None, problem.capacity, lambda v: f"{v:.0f}")
    legend(svg, 490, 80, [(BLUE, "これまでの最良"), (GRAY, "その世代の平均")])
    svg.text(490, 140, f"最良: {best_fit}", 12, BLUE, "start", "bold")
    svg.text(490, 158, f"幅の大きい順の貪欲: {greedy_fit}", 12)
    x0, wbar = 80, 600
    for k, (label, place, col) in enumerate([("貪欲", greedy_place, GRAY), ("GA", best_place, BLUE)]):
        y = 292 + k * 34
        svg.text(x0 - 10, y + 16, label, 12, INK, "end", "bold")
        svg.rect(x0, y, wbar, 22, "#ffffff", INK, 1)
        for idx, pos in place:
            svg.rect(x0 + pos / problem.capacity * wbar, y, problem.widths[idx] / problem.capacity * wbar, 22, col, "#ffffff", 1.5, 0.6)
            svg.text(x0 + (pos + problem.widths[idx] / 2) / problem.capacity * wbar, y + 15, str(problem.widths[idx]), 10, INK, "middle")
    svg.text(x0, 284, "左から詰めた結果（四角の数字 = 部品の幅、右の空き = 入りきらなかった分）", 11, GRAY)
    return svg.render()


def fig_ch27_transfer() -> str:
    pt = load("ch27/paper_transfer.py", "fig_paper")
    notes = pt.load_notes(ROOT / "data/ch27/paper_notes.yaml")
    pts = notes["toy_verify"]["points"]
    improved, after = pt.two_opt_once([list(p) for p in pts])
    svg = Svg(720, 340)
    svg.text(20, 24, "第27章: 論文から AHC へ — 読む順と、転用する前の玩具での検証", 13, INK, "start", "bold")
    steps = [("Abstract", "何を解くか"), ("Figure", "何と比べたか"), ("Algorithm", "手順そのもの"), ("限界", "効かない条件"), ("転用メモ", "自分の言葉で")]
    for k, (a, b) in enumerate(steps):
        x = 20 + k * 138
        box(svg, x, 60, 112, 50, [a, b], BLUE if k < 4 else ORANGE, "#eff6ff" if k < 4 else "#fff7ed")
        if k < len(steps) - 1:
            svg.arrow(x + 114, 85, x + 136, 85, GRAY, 1.5)
    svg.arrow(642, 112, 560, 150, ORANGE, 1.5)
    svg.text(20, 150, "玩具検証（paper_notes.yaml の toy_verify）", 12, INK, "start", "bold")
    for k, (title, tour, col) in enumerate([(f"前: {pt.tour_length(pts):.2f}", pts, GRAY), (f"2-opt 後: {after:.2f}", improved, GREEN)]):
        x0, y0 = 60 + k * 230, 175
        scale = 50
        xy = [(x0 + p[0] * scale, y0 + p[1] * scale) for p in tour]
        svg.polyline(xy, col, 2.5, closed=True)
        for x, y in xy:
            svg.circle(x, y, 5, INK)
        svg.text(x0 + 75, y0 + 2 * scale + 24, title, 12, col, "middle", "bold")
    svg.arrow(240, 225, 280, 225, INK, 2)
    svg.text(520, 190, "全部を実装する前に、", 12)
    svg.text(520, 208, "核になる操作だけを", 12)
    svg.text(520, 226, "数点の例で動かして、", 12)
    svg.text(520, 244, "効くことを確かめる", 12)
    svg.text(20, 330, "交差した 4 点の巡回が、2-opt の 1 回で交差のない巡回になる。これが確かめられてから本番の問題へ持ち込む", 11, GRAY)
    return svg.render()


def fig_ch28_bitset() -> str:
    svg = Svg(720, 300)
    W = 50
    r, c = 1, 20
    i = r * W + c
    svg.text(20, 24, f"第28章: 訪問済みをビット集合で持つ（W={W} の盤面、マス ({r}, {c}) の例）", 13, INK, "start", "bold")
    cell = 9
    ox, oy = 30, 60
    for rr in range(4):
        for cc in range(24):
            hl = (rr, cc) == (r, c)
            svg.rect(ox + cc * cell, oy + rr * cell, cell, cell, ORANGE if hl else "#ffffff", LIGHT, 0.8)
    svg.text(ox, oy + 4 * cell + 16, "盤面（左上の一部）", 11, GRAY)
    box(svg, 290, 52, 150, 50, [f"i = r·W + c = {i}", "行優先で 1 列に並べる"], INK)
    box(svg, 490, 52, 200, 50, [f"visited[i>>6] = visited[{i >> 6}]", f"の {i & 63} ビット目（i&63）"], BLUE, "#eff6ff")
    svg.arrow(260, 77, 288, 77, INK, 1.5)
    svg.arrow(442, 77, 488, 77, INK, 1.5)
    words = (W * W + 63) // 64
    y = 160
    svg.text(30, y - 12, f"uint64 の配列 {words} 個（{W}×{W} = {W * W} マス分。bool の配列なら {W * W} バイト、ビット集合なら {words * 8} バイト）", 12)
    for k in range(3):
        x = 30 + k * 230
        svg.text(x, y + 8, f"visited[{k}]", 11, BLUE if k == i >> 6 else GRAY, "start", "bold")
        for b in range(64):
            hl = k == i >> 6 and b == (i & 63)
            svg.rect(x + b * 3.4, y + 16, 3.4, 22, ORANGE if hl else ("#dbeafe" if k == i >> 6 else "#f3f4f6"), "#ffffff", 0.3)
    svg.text(720 - 20, y + 32, "…", 14, GRAY, "end")
    svg.add(f'<text x="30" y="{y + 80}" font-family="Menlo, Consolas, monospace" font-size="13" fill="{INK}">visited[i&gt;&gt;6] |= 1 &lt;&lt; (i &amp; 63)   // 立てる</text>')
    svg.add(f'<text x="30" y="{y + 100}" font-family="Menlo, Consolas, monospace" font-size="13" fill="{INK}">visited[i&gt;&gt;6] &gt;&gt; (i &amp; 63) &amp; 1 // 調べる</text>')
    svg.text(20, 292, "小さく連続したメモリに収まるのでキャッシュに乗りやすく、探索のたびの初期化も配列 1 本を 0 で埋めるだけで済む", 11, GRAY)
    return svg.render()


def fig_ch29_weekly() -> str:
    import json

    log = json.loads((ROOT / "data/ch29/weekly_log.json").read_text(encoding="utf-8"))
    days = log["days"]
    pts = [(d["day"], d["score"] / 1000) for d in days]
    svg = Svg(720, 350)
    svg.text(20, 24, f"第29章: 模擬チームの 1 週間のスコア（data/ch29/weekly_log.json）", 13, INK, "start", "bold")
    tr = chart(svg, (80, 60, 380, 200), [(BLUE, pts)], "日", "スコア（千）", None, None, lambda v: f"{v:.0f}", [d["day"] for d in days])
    owner_col = {"reimu": RED, "marisa": ORANGE, "team": GREEN}
    best = -1
    for d in days:
        x, y = tr(d["day"], d["score"] / 1000)
        col = owner_col.get(d["owner"], GRAY)
        svg.circle(x, y, 6, col if d["score"] > best else "#ffffff", col, 2)
        best = max(best, d["score"])
    for k, d in enumerate(days):
        svg.text(490, 70 + k * 30, f"{d['day']} 日目 {d['owner']}", 11, owner_col.get(d["owner"], GRAY), "start", "bold")
        svg.text(490, 84 + k * 30, d["notes"][:22] + ("…" if len(d["notes"]) > 22 else ""), 10, INK)
    svg.text(20, 320, "丸の色 = その日の担当（赤 reimu、橙 marisa、緑 team）。白抜き = 前日より悪くなった日", 11, GRAY)
    svg.text(20, 338, "悪くなった日もログに残し、ロールバックして次の手を試す。毎日 1 つずつ確かめるので、何が効いたかを後から追える", 11, GRAY)
    return svg.render()


def fig_ch30_map() -> str:
    import re

    toc = (ROOT / "docs/00-toc.md").read_text(encoding="utf-8")
    parts: List[Tuple[str, List[str]]] = []
    for line in toc.splitlines():
        m = re.match(r"## 第(\d+)部：(.+)", line)
        if m and m.group(1) != "0":
            parts.append((m.group(2), []))
        m = re.match(r"### 第(\d+)章 (.+)", line)
        if m and parts:
            parts[-1][1].append(f"{m.group(1)} {re.sub(r'（.*?）', '', m.group(2))}")
    band_cols = ["#808080", "#804000", "#008000", "#00c0c0", "#0000ff", "#c0c000", "#ff8000", "#ff0000"]
    svg = Svg(760, 540)
    svg.text(20, 24, "第30章: この本で通ってきた道（レーティング帯と章、docs/00-toc.md から）", 13, INK, "start", "bold")
    for k, (name, chs) in enumerate(parts):
        col = band_cols[k % len(band_cols)]
        x, y = 20 + (k % 2) * 370, 46 + (k // 2) * 118
        svg.rect(x, y, 360, 110, col, col, 1.5, 0.08)
        svg.rect(x, y, 8, 110, col, "none", 0)
        svg.text(x + 18, y + 20, name, 12, col if k != 5 else "#8a8a00", "start", "bold")
        for j, ch in enumerate(chs[:5]):
            svg.text(x + 18, y + 40 + j * 16, f"第{ch.split(' ', 1)[0]}章 {ch.split(' ', 1)[1][:24]}", 11)
    svg.text(20, 532, "灰色の「まず動くもの」から、赤の「研究を取り込む」まで。次の 1 問は、地図のどこに当たるかを考えてから解き始める", 11, GRAY)
    return svg.render()


def fig_ch04_ahc001() -> str:
    g = load("ch04/ahc001_grow.py", "fig_ahc001")
    companies = g.read_problem(open(ROOT / "data/ch04/sample.txt", encoding="utf-8"))
    rects = g.solve(companies)
    cell, ox, oy = 15, 30, 40
    svg = Svg(500, 380)
    svg.text(ox, 24, "第4章: 企業ごとに矩形を広げる（20×20 のサンプル）", 13, INK, "start", "bold")
    for k in range(21):
        svg.line(ox + k * cell, oy, ox + k * cell, oy + 20 * cell, LIGHT, 1)
        svg.line(ox, oy + k * cell, ox + 20 * cell, oy + k * cell, LIGHT, 1)
    colors = [BLUE, ORANGE, GREEN]
    for i, (c, r) in enumerate(zip(companies, rects)):
        col = colors[i % 3]
        # y は下向きに描く（行 = y）
        svg.rect(ox + r.a * cell, oy + r.b * cell, (r.c - r.a) * cell, (r.d - r.b) * cell, col, col, 2, 0.25)
        svg.circle(ox + (c.x + 0.5) * cell, oy + (c.y + 0.5) * cell, 4, col)
        svg.text(ox + 20 * cell + 12, oy + 20 + i * 40, f"企業{i}: 希望 {c.r}", 12, col, "start", "bold")
        svg.text(ox + 20 * cell + 12, oy + 36 + i * 40, f"面積 {r.area()}", 12, col)
    svg.text(ox, oy + 20 * cell + 20, "点 = 企業の位置。先に置いた矩形が、後の企業の広がる場所を狭める", 11, GRAY)
    return svg.render()


def fig_ch05_nearest() -> str:
    g = load("ch05/greedy_delivery.py", "fig_delivery")
    depot, orders = g.read_problem(open(ROOT / "data/ch05/sample.txt", encoding="utf-8"))
    route, total = g.nearest_neighbor(depot, orders)
    pts = [depot] + list(orders)

    def length(r):
        seq = [depot] + [orders[i] for i in r] + [depot]
        return sum(g.dist(seq[k], seq[k + 1]) for k in range(len(seq) - 1))

    import itertools

    best = min(itertools.permutations(range(len(orders))), key=length)
    svg = Svg(640, 320)
    svg.text(20, 24, "第5章: 最近傍の貪欲と、全探索した最短（data/ch05/sample.txt）", 13, INK, "start", "bold")
    for k, (title, r, col) in enumerate(
        [(f"最近傍: {total:.2f}", route, ORANGE), (f"最短（全 24 通り）: {length(best):.2f}", list(best), GREEN)]
    ):
        x0 = 40 + k * 310
        box = (x0, 80, 240, 200)
        seq = [0] + [i + 1 for i in r]
        draw_tour(svg, box, pts, seq, col)
        svg.text(x0, 56, title, 13, col, "start", "bold")
        lo_x, hi_x = min(p[0] for p in pts), max(p[0] for p in pts)
        lo_y, hi_y = min(p[1] for p in pts), max(p[1] for p in pts)
        for i, p in enumerate(pts):
            x = x0 + (p[0] - lo_x) / (hi_x - lo_x) * 240
            y = 80 + 200 - (p[1] - lo_y) / (hi_y - lo_y) * 200
            svg.text(x + 7, y - 6, "デポ" if i == 0 else f"{i - 1}", 11, INK)
    svg.text(20, 305, "貪欲は「今いちばん近い点」へ進むので、最後に遠い道を戻ることになりやすい", 11, GRAY)
    return svg.render()


def fig_ch06_two_opt_move() -> str:
    svg = Svg(620, 240)
    svg.text(20, 24, "第6章: 2-opt — 交差する 2 本の辺 (a,b) (c,d) を (a,c) (b,d) に付け替える", 13, INK, "start", "bold")
    a, b, c, d = (60, 80), (220, 200), (60, 200), (220, 80)
    for k, (title, edges, col) in enumerate(
        [("前: a→b, c→d（交差している）", [(a, b), (c, d)], ORANGE), ("後: a→c, b→d（区間 b…c を反転）", [(a, c), (b, d)], GREEN)]
    ):
        dx = k * 320
        for p, q in edges:
            svg.line(p[0] + dx, p[1], q[0] + dx, q[1], col, 3)
        # 残りの巡回（点線）
        svg.line(a[0] + dx - 30, a[1] - 30, a[0] + dx, a[1], GRAY, 1.5, "4 3")
        svg.line(d[0] + dx, d[1], d[0] + dx + 30, d[1] - 30, GRAY, 1.5, "4 3")
        svg.add(
            f'<path d="M {b[0] + dx} {b[1]} C {b[0] + dx + 60} {b[1] + 20}, {c[0] + dx - 60} {c[1] + 20}, {c[0] + dx} {c[1]}" '
            f'fill="none" stroke="{GRAY}" stroke-width="1.5" stroke-dasharray="4 3"/>'
        )
        for name, p in zip("abcd", (a, b, c, d)):
            svg.circle(p[0] + dx, p[1], 5, INK)
            svg.text(p[0] + dx + (-16 if p[0] < 100 else 10), p[1] + 5, name, 14, INK, "start", "bold")
        svg.text(40 + dx, 60 - 20, title, 12, col, "start", "bold")
    svg.arrow(270, 140, 330, 140, INK, 2)
    svg.text(20, 230, "点線 = 巡回の残り。dist(a,c) + dist(b,d) < dist(a,b) + dist(c,d) なら採用する", 11, GRAY)
    return svg.render()


def fig_ch06_tsp40() -> str:
    t6 = load("ch06/two_opt.py", "fig_two_opt")
    t13 = load("ch13/tabu_tsp.py", "fig_tabu")
    pts = t6.read_points(open(ROOT / "data/common/tsp40.txt", encoding="utf-8"))
    init = list(range(len(pts)))
    random.Random(42).shuffle(init)
    two = t6.two_opt(pts, list(init))
    tabu, tabu_len = t13.tabu_search(pts, list(init))
    svg = Svg(720, 300)
    svg.text(20, 24, "第6・13章: 同じ初期解からの巡回（data/common/tsp40.txt、40 点）", 13, INK, "start", "bold")
    panels = [
        (f"ランダムな初期解: {t6.tour_length(pts, init):.2f}", init, GRAY),
        (f"2-opt 山登り: {t6.tour_length(pts, two):.2f}", two, ORANGE),
        (f"タブーサーチ: {tabu_len:.2f}", tabu, GREEN),
    ]
    for k, (title, tour, col) in enumerate(panels):
        x0 = 30 + k * 235
        svg.text(x0, 54, title, 12, col, "start", "bold")
        draw_tour(svg, (x0, 66, 200, 200), pts, tour, col)
    svg.text(20, 290, "2-opt は交差がなくなったところ（局所最適）で止まる。タブーは悪化も受け入れて、その先へ進む", 11, GRAY)
    return svg.render()


def fig_ch07_coarsen() -> str:
    c = load("ch07/coarsen.py", "fig_coarsen")
    grid = c.read_grid(open(ROOT / "data/ch07/sample.txt", encoding="utf-8"))
    greedy = c.greedy_per_block(grid)
    refined = c.refine(grid, greedy)
    cell, ox, oy = 20, 30, 44
    svg = Svg(620, 400)
    svg.text(20, 24, "第7章: 2×2 の和で粗く選び（○）、同じブロックの中で山登りする（●）", 13, INK, "start", "bold")
    hi = max(max(r) for r in grid)
    for i in range(16):
        for j in range(16):
            v = grid[i][j] / hi
            shade = int(255 - 150 * v)
            svg.rect(ox + j * cell, oy + i * cell, cell, cell, f"rgb({shade},{shade},255)", "#ffffff", 0.5)
    for k in range(5):
        svg.line(ox + k * 4 * cell, oy, ox + k * 4 * cell, oy + 16 * cell, INK, 2)
        svg.line(ox, oy + k * 4 * cell, ox + 16 * cell, oy + k * 4 * cell, INK, 2)
    for (gi, gj), (ri, rj) in zip(greedy, refined):
        gx, gy = ox + (gj + 0.5) * cell, oy + (gi + 0.5) * cell
        rx, ry = ox + (rj + 0.5) * cell, oy + (ri + 0.5) * cell
        if (gi, gj) != (ri, rj):
            svg.line(gx, gy, rx, ry, ORANGE, 2)
        svg.circle(gx, gy, 6, "none", ORANGE, 2)
        svg.circle(rx, ry, 4, ORANGE)
    x = ox + 16 * cell + 20
    svg.text(x, oy + 16, "色が濃いほど値が大きい", 12)
    svg.text(x, oy + 40, "太線 = 4×4 のブロック", 12)
    svg.circle(x + 6, oy + 60, 6, "none", ORANGE, 2)
    svg.text(x + 20, oy + 64, f"粗い貪欲: 合計 {c.pick_sum(grid, greedy)}", 12)
    svg.circle(x + 6, oy + 84, 4, ORANGE)
    svg.text(x + 20, oy + 88, f"山登り後: 合計 {c.pick_sum(grid, refined)}", 12)
    svg.text(x, oy + 120, "各ブロックの最大を", 12, GRAY)
    svg.text(x, oy + 136, "全部取ると 250", 12, GRAY)
    return svg.render()


def fig_ch09_sa() -> str:
    m = load("ch09/sa_intro_hc.py", "fig_sa")
    problem = m.read_problem(open(ROOT / "data/common/intro_hc_d365.txt", encoding="utf-8"))
    rng = random.Random(42)
    types = [rng.randint(1, 26) for _ in range(problem.days)]
    score = m.raw_score(problem, m.ScheduleState(types))
    steps, window, t0, t1 = 20000, 1000, m.T0, m.T1
    score_pts, accept_pts = [], []
    worse = accepted_worse = 0
    for step in range(steps + 1):
        if step % 200 == 0:
            score_pts.append((step, score / 1e6))  # 0 で切る前の値（序盤はマイナス）
        if step > 0 and step % window == 0:
            accept_pts.append((step - window / 2, 100.0 * accepted_worse / max(worse, 1)))
            worse = accepted_worse = 0
        if step == steps:
            break
        temp = t0 * (t1 / t0) ** (step / steps)  # 時間の代わりに手数で進める（図を毎回同じにするため）
        day, new_type = m.random_move(m.ScheduleState(types), rng)
        delta = m.delta_change(problem, types, day, new_type)
        if delta < 0:
            worse += 1
        if delta >= 0 or rng.random() < math.exp(delta / temp):
            types[day] = new_type
            score += delta
            if delta < 0:
                accepted_worse += 1
    svg = Svg(680, 330)
    svg.text(20, 24, f"第9章: 焼きなまし（D=365、ランダムな初期解から {steps} 手、温度 {t0:g} → {t1:g}）", 13, INK, "start", "bold")
    chart(svg, (70, 60, 240, 210), [(BLUE, score_pts)], "手数", "スコア（百万、0 で切る前）", None, None, lambda v: f"{v:.1f}")
    chart(svg, (410, 60, 240, 210), [(ORANGE, accept_pts)], "手数", "悪くなる手を受け入れた割合（%）", 0, None, lambda v: f"{v:.1f}")
    svg.text(20, 318, "温度が高い序盤は、悪くなる手も 1 割ほど受け入れる。温度が下がると、ほとんど受け入れなくなる", 11, GRAY)
    return svg.render()


def fig_ch10_beam() -> str:
    svg = Svg(700, 300)
    svg.text(20, 24, "第10章: ビームサーチ — 各層で候補を全部作り、評価の上位 k 個（ここでは 3 個）だけ残す", 13, INK, "start", "bold")
    rng = random.Random(3)
    levels = 4
    kept_prev = [(60, 160)]
    for lv in range(1, levels):
        x = 60 + lv * 170
        cands = []
        for pi, (px, py) in enumerate(kept_prev):
            for k in range(3 if lv > 1 else 4):
                cands.append((px, py, rng.random()))
        n = len(cands)
        order = sorted(range(n), key=lambda i: -cands[i][2])
        kept_idx = set(order[:3])
        new_kept = []
        for i, (px, py, sc) in enumerate(cands):
            y = 50 + (i + 0.5) * 220 / n
            keep = i in kept_idx
            svg.line(px, py, x, y, BLUE if keep else LIGHT, 2 if keep else 1)
            svg.circle(x, y, 6 if keep else 4, BLUE if keep else "#ffffff", BLUE if keep else GRAY, 1.5)
            if keep:
                new_kept.append((x, y))
        kept_prev = new_kept
        svg.text(x, 290, f"深さ {lv}: 候補 {n} → 残す 3", 11, INK, "middle")
    svg.circle(60, 160, 7, INK)
    svg.text(60, 290, "開始", 11, INK, "middle")
    return svg.render()


def shade(v: float, lo: float, hi: float) -> str:
    """lo → 薄い青、hi → 濃い青（1 色の濃淡なので、色の区別がつきにくくても読める）."""
    t = min(1.0, max(0.0, (v - lo) / (hi - lo)))
    a, b = (239, 246, 255), (30, 58, 138)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def fig_ch12_estimate() -> str:
    j = load("ch12/local_judge.py", "fig_judge")
    s = load("ch12/solver.py", "fig_solver")
    # local_judge.py の main と同じ順に乱数を使い、ジャッジを子プロセスにせず同じ会話をここで回す
    seed, q = 1, 1000
    rng = random.Random(seed)
    h, v = j.generate_weights(rng)
    solver = s.Solver()
    snaps: Dict[int, Tuple[List[List[float]], List[List[float]]]] = {}
    total, ratio_pts, window = 0.0, [], []
    for k in range(1, q + 1):
        while True:
            si, sj, ti, tj = (rng.randrange(j.N) for _ in range(4))
            if abs(si - ti) + abs(sj - tj) >= 10:
                break
        path, edges, predicted = solver.shortest_path(si, sj, ti, tj)
        b = j.path_length(h, v, si, sj, ti, tj, path)
        a = j.shortest(h, v, si, sj, ti, tj)
        total += 0.998 ** (q - k) * a / b
        window.append(a / b)
        if k % 50 == 0:
            ratio_pts.append((k, 100 * sum(window) / len(window)))
            window = []
        solver.update(edges, predicted, round(b * rng.uniform(0.9, 1.1)))
        if k in (100, 1000):
            snaps[k] = ([r[:] for r in solver.h], [r[:] for r in solver.v])
    assert round(2312311 * total) == 920496769, "図の再現が local_judge.py --seed 1 とずれた"

    def grid(x0: float, y0: float, hh, vv, title: str) -> None:
        cell = 200 / (j.N - 1)
        svg.text(x0, y0 - 10, title, 12, INK, "start", "bold")
        for i in range(j.N):
            for jj in range(j.N - 1):
                svg.line(x0 + jj * cell, y0 + i * cell, x0 + (jj + 1) * cell, y0 + i * cell, shade(hh[i][jj], 1000, 9000), 2.6)
        for i in range(j.N - 1):
            for jj in range(j.N):
                svg.line(x0 + jj * cell, y0 + i * cell, x0 + jj * cell, y0 + (i + 1) * cell, shade(vv[i][jj], 1000, 9000), 2.6)

    def err(k: int) -> float:
        eh, ev = snaps[k]
        diffs = [abs(eh[i][jj] - h[i][jj]) for i in range(j.N) for jj in range(j.N - 1)]
        diffs += [abs(ev[i][jj] - v[i][jj]) for i in range(j.N - 1) for jj in range(j.N)]
        return sum(diffs) / len(diffs)

    svg = Svg(760, 560)
    svg.text(20, 24, "第12章: 推定した辺の長さが育つ様子（local_judge.py --seed 1）", 13, INK, "start", "bold")
    grid(30, 70, h, v, "真の長さ（ソルバには見えない）")
    grid(280, 70, *snaps[100], f"100 クエリ後（平均誤差 {err(100):.0f}）")
    grid(530, 70, *snaps[1000], f"1000 クエリ後（平均誤差 {err(1000):.0f}）")
    for k in range(101):  # 色の目盛り
        svg.line(30 + k * 2, 296, 30 + k * 2, 306, shade(1000 + 80 * k, 1000, 9000), 2.2)
    svg.text(30, 322, "1000", 11, GRAY)
    svg.text(230, 322, "9000", 11, GRAY, "end")
    svg.text(240, 305, "辺の長さ。推定の初期値はすべて 5000（中くらいの青）で、通らない辺はそのまま残る", 11, GRAY)
    chart(svg, (90, 370, 600, 130), [(BLUE, ratio_pts)], "クエリ", "真の最短距離 / 自分の経路（%、50 クエリごとの平均）", None, 100, lambda v: f"{v:.0f}")
    svg.text(20, 548, "横に並ぶ辺・縦に並ぶ辺は行・列ごとに似た長さ。よく通る中央の辺から先に、真の濃淡に近づいていく", 11, GRAY)
    return svg.render()


def fig_ch16_wins() -> str:
    m = load("ch16/sa_multi_neighborhood.py", "fig_multi")
    problem = m.read_problem(open(ROOT / "data/common/intro_hc_d365.txt", encoding="utf-8"))
    rng = random.Random(42)
    state = m.ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    score = m.raw_score(problem, state)
    neighborhoods = [m.neighbor_change_day, m.neighbor_swap_days]
    weights, wins = [1.0, 1.0], [0, 0]
    steps = 20000
    win_pts: List[List[Tuple[float, float]]] = [[(0, 0)], [(0, 0)]]
    prob_pts: List[List[Tuple[float, float]]] = [[(0, 50)], [(0, 50)]]
    # sa_multi と同じ処理を、時間の代わりに手数で進める（図を毎回同じにするため）。boost と再ヒートは省く
    for step in range(1, steps + 1):
        temp = m.T0 * (m.T1 / m.T0) ** ((step - 1) / steps)
        idx = rng.choices(range(2), weights=weights, k=1)[0]
        move = neighborhoods[idx](state, rng)
        delta = m.move_delta(problem, state.types, move)
        if delta >= 0 or rng.random() < math.exp(delta / temp):
            m.apply_move(state.types, move)
            score += delta
            if delta > 0:
                wins[idx] += 1
        if step % m.WEIGHT_UPDATE_EVERY == 0:
            total = sum(wins) or 1
            weights = [max(0.2, w / total * 2) for w in wins]
            for i in range(2):
                win_pts[i].append((step, wins[i]))
                prob_pts[i].append((step, 100 * weights[i] / sum(weights)))
    assert score == m.raw_score(problem, state)
    svg = Svg(700, 370)
    svg.text(20, 24, f"第16章: 近傍ごとの勝ち数と選ばれる確率（D=365、{steps} 手）", 13, INK, "start", "bold")
    chart(svg, (70, 70, 230, 200), [(BLUE, win_pts[0]), (ORANGE, win_pts[1])], "手数", "改善した回数（累計）", 0, None, lambda v: f"{v:.0f}")
    chart(svg, (420, 70, 230, 200), [(BLUE, prob_pts[0]), (ORANGE, prob_pts[1])], "手数", "選ばれる確率（%）", 0, 100, lambda v: f"{v:.0f}")
    legend(svg, 200, 334, [(BLUE, "change_day")])
    legend(svg, 340, 334, [(ORANGE, "swap_days")])
    svg.text(20, 360, "1000 手ごとに勝ち数で重みを付け直す。改善を多く出す change_day に、手が多く回るようになる", 11, GRAY)
    return svg.render()


def fig_ch16_reheat() -> str:
    m = load("ch16/sa_multi_neighborhood.py", "fig_reheat")
    problem = m.read_problem(open(ROOT / "data/ch16/sample.txt", encoding="utf-8"))
    rng = random.Random(42)
    state = m.ScheduleState([rng.randint(1, 26) for _ in range(problem.days)])
    score = best = m.raw_score(problem, state)
    neighborhoods = [m.neighbor_change_day, m.neighbor_swap_days]
    weights, wins = [1.0, 1.0], [0, 0]
    boost, since, steps = 1.0, 0, 100000
    temp_pts, cur_pts, best_pts, reheats = [(0, math.log10(m.T0))], [(0, (score - 10**6) / 1000)], [(0, (best - 10**6) / 1000)], []
    # sa_multi と同じ処理（boost・再ヒート込み）を、時間の代わりに手数で進める
    for step in range(1, steps + 1):
        temp = m.T0 * (m.T1 / m.T0) ** ((step - 1) / steps) * boost
        idx = rng.choices(range(2), weights=weights, k=1)[0]
        move = neighborhoods[idx](state, rng)
        delta = m.move_delta(problem, state.types, move)
        if delta >= 0 or rng.random() < math.exp(delta / temp):
            m.apply_move(state.types, move)
            score += delta
            if delta > 0:
                wins[idx] += 1
        if score > best:
            best, since = score, 0
        else:
            since += 1
        boost = max(1.0, boost * (m.BOOST_DECAY_SLOW if since > m.SLOW_AFTER else m.BOOST_DECAY_FAST))
        if since >= m.STAGNANT_LIMIT:
            boost, since = m.REHEAT_BOOST, 0
            reheats.append(step)
        if step % m.WEIGHT_UPDATE_EVERY == 0:
            total = sum(wins) or 1
            weights = [max(0.2, w / total * 2) for w in wins]
        if step % 250 == 0:
            temp_pts.append((step, math.log10(temp)))
            cur_pts.append((step, (score - 10**6) / 1000))
            best_pts.append((step, (best - 10**6) / 1000))
    assert score == m.raw_score(problem, state) and reheats
    svg = Svg(720, 420)
    svg.text(20, 24, f"第16章: 再ヒート（data/ch16/sample.txt、{steps} 手で {len(reheats)} 回）", 13, INK, "start", "bold")
    ticks = [steps * k / 4 for k in range(5)]
    tr1 = chart(svg, (80, 60, 440, 120), [(ORANGE, temp_pts)], "", "温度 T（対数目盛り）", None, None, lambda v: f"{10 ** v:.0f}", ticks)
    tr2 = chart(svg, (80, 230, 440, 120), [(GRAY, cur_pts), (GREEN, best_pts)], "手数", "満足度（千）", None, None, lambda v: f"{v:.0f}", ticks)
    for st in reheats:
        x, _ = tr1(st, 0)
        svg.line(x, 60, x, 350, RED, 1, "4 3")
    legend(svg, 545, 80, [(ORANGE, "温度 T = 基準 × boost")])
    legend(svg, 545, 250, [(GRAY, "今の解"), (GREEN, "これまでの最良")])
    svg.line(545, 300, 563, 300, RED, 1, "4 3")
    svg.text(569, 304, "再ヒート", 12)
    svg.text(20, 396, f"best が {m.STAGNANT_LIMIT} 手更新されないと、温度を基準の {m.REHEAT_BOOST:g} 倍に上げる。今の解はいったん悪くなり、また冷えて戻る", 11, GRAY)
    svg.text(20, 412, "D=5 では最良にすぐ着くので、再ヒートしても best は変わらない。谷が多い問題で、別の谷へ移るきっかけになる", 11, GRAY)
    return svg.render()


def fig_ch18_seeds() -> str:
    m = load("ch18/multi_start_sa.py", "fig_multi_start")
    problem = m.read_problem(open(ROOT / "data/common/intro_hc_d365.txt", encoding="utf-8"))
    budget = 16000

    def run(seed: int, steps: int) -> int:  # sa_run を、時間の代わりに手数で回す
        rng = random.Random(seed)
        types = [rng.randint(1, 26) for _ in range(problem.days)]
        score = best = m.raw_score(problem, types)
        for step in range(steps):
            temp = m.T0 * (m.T1 / m.T0) ** (step / steps)
            day, new_type = rng.randrange(problem.days), rng.randint(1, 26)
            delta = m.delta_change(problem, types, day, new_type)
            if delta >= 0 or rng.random() < math.exp(delta / temp):
                types[day] = new_type
                score += delta
                best = max(best, score)
        return best

    counts = [1, 2, 4, 8]
    svg = Svg(640, 330)
    svg.text(20, 24, f"第18章: 合計 {budget} 手をシードで分けたときのスコア（D=365）", 13, INK, "start", "bold")
    runs = {k: [run(42 + s, budget // k) / 1e6 for s in range(k)] for k in counts}
    lo = min(min(r) for r in runs.values())
    hi = max(max(r) for r in runs.values())
    x0, y0, w, hgt = 80, 60, 360, 210
    pad = (hi - lo) * 0.1

    def ty(val: float) -> float:
        return y0 + hgt - (val - (lo - pad)) / (hi - lo + 2 * pad) * hgt

    for k in range(5):
        val = lo - pad + (hi - lo + 2 * pad) * k / 4
        svg.line(x0, ty(val), x0 + w, ty(val), LIGHT, 1)
        svg.text(x0 - 6, ty(val) + 4, f"{val:.2f}", 11, GRAY, "end")
    svg.line(x0, y0 + hgt, x0 + w, y0 + hgt, INK, 1)
    svg.line(x0, y0, x0, y0 + hgt, INK, 1)
    svg.text(x0, y0 - 10, "スコア（百万、0 で切る前）", 12)
    merged = []
    for c, k in enumerate(counts):
        x = x0 + (c + 0.5) * w / len(counts)
        svg.text(x, y0 + hgt + 16, f"{k} × {budget // k}", 11, GRAY, "middle")
        for val in runs[k]:
            svg.circle(x, ty(val), 4, "#ffffff", GRAY, 1.5)
        merged.append((x, ty(max(runs[k]))))
    svg.polyline(merged, BLUE, 2)
    for x, y in merged:
        svg.circle(x, y, 5, BLUE)
    svg.text(x0 + w / 2, y0 + hgt + 34, "シード数 × 1 本あたりの手数", 12, INK, "middle")
    svg.circle(470, 90, 4, "#ffffff", GRAY, 1.5)
    svg.text(482, 94, "1 本ずつの best", 12)
    svg.circle(470, 112, 5, BLUE)
    svg.text(482, 116, "マージ（max）", 12)
    svg.text(20, 318, "Intro HC は長く冷やすほど伸びる型なので、本数を増やして 1 本を短くすると、max を取っても下がる", 11, GRAY)
    return svg.render()


def fig_ch20_tree() -> str:
    m = load("ch20/mcts_toy.py", "fig_mcts")
    game = m.read_game(open(ROOT / "data/ch20/sample.txt", encoding="utf-8"))
    adj = m.build_adjacency(game)
    rng = random.Random(42)  # mcts_toy.py の main と同じ seed。1 手目の木
    root = m.MCTSNode(state=m.GameState(node=game.start, player=0), untried=list(adj[game.start]))
    m.mcts(root, adj, game, rng)
    chosen = m.select_move(root, adj)
    depth_max = 3
    pos: Dict[int, Tuple[float, float]] = {}
    leaves: List[m.MCTSNode] = []

    def collect(n, d):
        kids = list(n.children.values()) if d < depth_max else []
        if not kids:
            leaves.append(n)
        for c in kids:
            collect(c, d + 1)

    collect(root, 0)
    svg = Svg(720, 410)
    x0, w, top, gap = 50, 620, 70, 85

    def place(n, d) -> float:
        kids = list(n.children.values()) if d < depth_max else []
        x = x0 + (leaves.index(n) + 0.5) * w / len(leaves) if not kids else sum(place(c, d + 1) for c in kids) / len(kids)
        pos[id(n)] = (x, top + d * gap)
        return x

    place(root, 0)

    def draw(n, d, on_path: bool) -> None:
        x, y = pos[id(n)]
        for c in (n.children.values() if d < depth_max else []):
            cx, cy = pos[id(c)]
            hot = on_path and d == 0 and c.move == chosen
            svg.line(x, y + 16, cx, cy - 16, BLUE if hot else GRAY, 2.5 if hot else 1.2)
            draw(c, d + 1, hot)
        terminal = n.state.node == game.terminal
        stroke = BLUE if on_path else (GREEN if terminal else INK)
        svg.circle(x, y, 16, "#ffffff", stroke, 2.5 if on_path or terminal else 1.2)
        svg.text(x, y + 5, str(n.state.node), 13, stroke, "middle", "bold")
        label = f"{n.visits} 回" if n is root else f"{n.wins:.0f}/{n.visits}"
        svg.text(x, y + 32, label, 11, INK, "middle")

    svg.text(20, 24, f"第20章: 1 手目の MCTS の木（{m.ITERATIONS} 回、深さ {depth_max} まで）", 13, INK, "start", "bold")
    for d, s in enumerate(["今の位置", "先手の手", "後手の手", "先手の手"]):
        svg.text(14, top + d * gap + 5, s, 11, GRAY)
    draw(root, 0, True)
    svg.text(20, 380, "丸の数字 = 着くノード、下の数字 = その手を指した人の勝ち数/訪問数。緑はゴール（ノード 3）", 11, GRAY)
    svg.text(20, 398, "2 へ進むと相手が 3 に入って勝つ（18/18）ので、2 は 40 回で見限られ、訪問の多い 1 を選ぶ（青）", 11, GRAY)
    return svg.render()


def fig_ch25_gap() -> str:
    m = load("ch25/assignment_relax.py", "fig_assign")
    n, cost = m.read_cost(open(ROOT / "data/ch25/sample.txt", encoding="utf-8"))
    relaxed, lb = m.relaxed_lower_bound(cost)
    improved = m.swap_improve(cost, m.repair(cost))
    greedy = m.greedy_by_cost(cost)
    optimal, opt = m.brute_optimal(cost)
    svg = Svg(720, 380)
    svg.text(20, 24, "第25章: 緩和の下界と、整数解の差（data/ch25/sample.txt）", 13, INK, "start", "bold")
    cell, ox, oy = 44, 60, 80
    panels = [("緩和（列がかぶる）", relaxed, GRAY), ("修復 + 山登り", improved, ORANGE), ("最適（全探索）", optimal, GREEN)]
    svg.text(ox, oy - 26, "行 = 人、列 = 仕事、数字 = コスト", 12)
    for i in range(n):
        svg.text(ox - 10, oy + (i + 0.5) * cell + 4, f"{i}", 11, GRAY, "end")
        for jj in range(n):
            svg.text(ox + (jj + 0.5) * cell, oy - 6, f"{jj}", 11, GRAY, "middle")
            svg.rect(ox + jj * cell, oy + i * cell, cell, cell, "#ffffff", LIGHT, 1)
            svg.text(ox + (jj + 0.5) * cell, oy + (i + 0.5) * cell + 5, str(cost[i][jj]), 14)
    for k, (_, assign, col) in enumerate(panels):
        off = (k - 1) * 4
        for i, jj in enumerate(assign):
            svg.rect(ox + jj * cell + 4 + off + 4, oy + i * cell + 4 + off + 4, cell - 16, cell - 16, "none", col, 2)
    for k, (title, assign, col) in enumerate(panels):
        svg.rect(ox, oy + n * cell + 22 + k * 20, 12, 12, "none", col, 2)
        svg.text(ox + 20, oy + n * cell + 33 + k * 20, f"{title}: {m.assignment_cost(cost, assign)}", 12, col if col != GRAY else INK)
    # 数直線
    lx, rx, y = 330, 690, 170
    lo_v, hi_v = 6, 15

    def tx(val: float) -> float:
        return lx + (val - lo_v) / (hi_v - lo_v) * (rx - lx)

    svg.rect(tx(lb), y - 12, tx(improved_cost := m.assignment_cost(cost, improved)) - tx(lb), 24, LIGHT, "none", 0)
    svg.line(lx, y, rx, y, INK, 1)
    for val in range(lo_v, hi_v + 1):
        svg.line(tx(val), y - 3, tx(val), y + 3, INK, 1)
        svg.text(tx(val), y + 40, str(val), 11, GRAY, "middle")
    marks = [(lb, "下界", GRAY, -1), (opt, "最適", GREEN, 1), (improved_cost, "修復+山登り", ORANGE, -1),
             (m.assignment_cost(cost, greedy), "コスト順の貪欲", PURPLE, 1)]
    for val, name, col, side in marks:
        svg.circle(tx(val), y, 6, col)
        svg.text(tx(val), y - 22 if side < 0 else y + 24, f"{name} {val}", 12, col, "middle", "bold")
    svg.text(lx, y - 60, "最小化なので、最適は必ず [下界, 手元の解] の中", 12)
    svg.text(lx, y + 70, f"灰色の帯 = 伸びしろの上限 {improved_cost - lb}（実際の差は {improved_cost - opt}）", 12)
    svg.text(20, 368, "下界は「各行が最安の列を取る」解で、列 0・列 3 が 2 人ずつかぶるので実行可能ではない", 11, GRAY)
    return svg.render()


def fig_ch13_tabu() -> str:
    t = load("ch13/tabu_tsp.py", "fig_tabu2")
    pts = t.read_points(open(ROOT / "data/common/tsp40.txt", encoding="utf-8"))
    tour = list(range(len(pts)))
    random.Random(42).shuffle(tour)
    cur_pts: List[Tuple[float, float]] = []
    best_pts: List[Tuple[float, float]] = []
    # tabu_search の中を 1 反復ずつ見るため、反復数を 1 ずつ増やしながら呼ぶのは重いので、同じ処理をここで回す
    n = len(tour)
    cur = tour[:]
    cur_len = t.tour_length(pts, cur)
    best_len = cur_len
    tabu_until: Dict[Tuple[int, int], int] = {}
    for it in range(800):
        best_move = None
        for i in range(n):
            for k in range(i + 2, n if i > 0 else n - 1):
                a, b = cur[i], cur[(i + 1) % n]
                c, d = cur[k], cur[(k + 1) % n]
                new_len = cur_len - t.edge_dist(pts, a, b) - t.edge_dist(pts, c, d) + t.edge_dist(pts, a, c) + t.edge_dist(pts, b, d)
                is_tabu = tabu_until.get(t.edge_key(a, c), -1) >= it or tabu_until.get(t.edge_key(b, d), -1) >= it
                if is_tabu and new_len >= best_len - 1e-9:
                    continue
                if best_move is None or new_len < best_move[0]:
                    best_move = (new_len, i, k)
        if best_move is None:
            break
        new_len, i, k = best_move
        a, b, c, d = cur[i], cur[(i + 1) % n], cur[k], cur[(k + 1) % n]
        t.apply_reverse(cur, i, k)
        cur_len = new_len
        tabu_until[t.edge_key(a, b)] = it + 12
        tabu_until[t.edge_key(c, d)] = it + 12
        best_len = min(best_len, cur_len)
        if it >= 20:  # 最初の急降下は大きすぎるので省く
            cur_pts.append((it, cur_len))
            best_pts.append((it, best_len))
    assert abs(best_len - t.tabu_search(pts, tour[:])[1]) < 1e-6, "図の再現が tabu_search とずれた"
    svg = Svg(760, 320)
    svg.text(20, 24, "第13章: タブーサーチの巡回の長さ（data/common/tsp40.txt、反復 20〜800）", 13, INK, "start", "bold")
    chart(svg, (70, 60, 420, 200), [(GRAY, cur_pts), (GREEN, best_pts)], "反復", "巡回の長さ", None, None, lambda v: f"{v:.0f}")
    legend(svg, 510, 80, [(GRAY, "今の解（cur_len）"), (GREEN, "これまでの最良（best_len）")])
    svg.text(20, 310, "今の解は悪くなっても進み続け、ときどき最良を更新する。山登りなら、最初に悪くなる手前で止まっている", 11, GRAY)
    return svg.render()


def fig_ch19_lns() -> str:
    m = load("ch19/lns_tsp.py", "fig_lns")
    pts = m.read_points(open(ROOT / "data/common/tsp40.txt", encoding="utf-8"))
    with contextlib.redirect_stderr(io.StringIO()):
        tour, _, _ = m.lns(pts, random.Random(42), iterations=10)
    rng = random.Random(7)
    while True:  # 図で見えるように、6 点以上を壊して、修復で短くなった 1 回を選ぶ
        partial, removed = m.destroy_segment(tour, rng)
        repaired = m.repair_tour(pts, partial, removed)
        if len(removed) >= 6 and m.tour_length(pts, repaired) < m.tour_length(pts, tour) - 1:
            break
    svg = Svg(720, 300)
    svg.text(20, 24, f"第19章: LNS — 連続する {len(removed)} 点を外し（赤丸）、安い位置に入れ直す", 13, INK, "start", "bold")
    panels = [
        (f"壊す前: {m.tour_length(pts, tour):.2f}", tour, BLUE, removed),
        ("壊した後（赤丸を外した）", partial, GRAY, removed),
        (f"修復後: {m.tour_length(pts, repaired):.2f}", repaired, GREEN, removed),
    ]
    for k, (title, tr, col, hl) in enumerate(panels):
        x0 = 30 + k * 235
        svg.text(x0, 54, title, 12, col, "start", "bold")
        draw_tour(svg, (x0, 66, 200, 200), pts, tr, col, hl)
    svg.text(20, 290, "残した部分の並びはそのまま使い、外した点だけを入れ直す。良くなったときだけ採用する", 11, GRAY)
    return svg.render()


def fig_ch24_regret() -> str:
    b = load("ch24/bandit_compare.py", "fig_bandit")
    n, true_w, queries = b.load_sample(ROOT / "data/ch24/sample.txt")
    colors = {"greedy": GRAY, "epsilon_greedy": ORANGE, "ucb1": BLUE, "thompson": GREEN}
    series = []
    total_q = b.ROUNDS * len(queries)
    for name in b.STRATEGIES:
        cum = [0.0] * (total_q + 1)
        for seed in range(b.TRIALS):
            solver = b.Solver(n, list(true_w), name, random.Random(seed), b.EPSILON)
            noise = random.Random(seed + 1_000_000)
            acc, q = 0.0, 0
            for _ in range(b.ROUNDS):
                for s, t in queries:
                    path = solver.choose_path(s, t)
                    true_len = sum(true_w[k] for k in b.path_edges(path))
                    acc += true_len - b.dijkstra(n, true_w, s, t)[0]
                    solver.update(path, true_len * noise.uniform(1 - b.NOISE, 1 + b.NOISE))
                    q += 1
                    cum[q] += acc
        series.append((colors[name], [(q, cum[q] / b.TRIALS) for q in range(0, total_q + 1, 3)]))
    svg = Svg(640, 320)
    svg.text(20, 24, "第24章: 後悔（regret）の積み上がり（data/ch24/sample.txt、20 回の平均）", 13, INK, "start", "bold")
    chart(svg, (70, 60, 400, 200), series, "クエリ数", "後悔の合計", 0, None, lambda v: f"{v:.0f}")
    legend(svg, 490, 80, [(GRAY, "greedy"), (ORANGE, "ε-greedy"), (BLUE, "UCB1"), (GREEN, "Thompson")])
    svg.text(20, 310, "greedy は近道を試さないまま後悔が増え続ける。探索する戦略は、近道が分かると増え方がゆるやかになる", 11, GRAY)
    return svg.render()


FIGURES: Dict[str, Callable[[], str]] = {
    "ch01_daily.svg": fig_ch01_daily,
    "ch02_pipeline.svg": fig_ch02_pipeline,
    "ch03_state_move.svg": fig_ch03_state_move,
    "ch04_ahc001.svg": fig_ch04_ahc001,
    "ch05_nearest.svg": fig_ch05_nearest,
    "ch06_two_opt_move.svg": fig_ch06_two_opt_move,
    "ch06_tsp40.svg": fig_ch06_tsp40,
    "ch07_coarsen.svg": fig_ch07_coarsen,
    "ch08_vis.svg": fig_ch08_vis,
    "ch09_sa.svg": fig_ch09_sa,
    "ch10_beam.svg": fig_ch10_beam,
    "ch11_pipeline.svg": fig_ch11_pipeline,
    "ch12_estimate.svg": fig_ch12_estimate,
    "ch13_tabu.svg": fig_ch13_tabu,
    "ch14_uf.svg": fig_ch14_uf,
    "ch15_puzzle.svg": fig_ch15_puzzle,
    "ch16_reheat.svg": fig_ch16_reheat,
    "ch16_wins.svg": fig_ch16_wins,
    "ch17_territory.svg": fig_ch17_territory,
    "ch18_seeds.svg": fig_ch18_seeds,
    "ch19_lns.svg": fig_ch19_lns,
    "ch20_tree.svg": fig_ch20_tree,
    "ch21_timeline.svg": fig_ch21_timeline,
    "ch22_catalog.svg": fig_ch22_catalog,
    "ch23_hypotheses.svg": fig_ch23_hypotheses,
    "ch24_regret.svg": fig_ch24_regret,
    "ch25_gap.svg": fig_ch25_gap,
    "ch26_ga.svg": fig_ch26_ga,
    "ch27_transfer.svg": fig_ch27_transfer,
    "ch28_bitset.svg": fig_ch28_bitset,
    "ch29_weekly.svg": fig_ch29_weekly,
    "ch30_map.svg": fig_ch30_map,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="本文の図を作る")
    parser.add_argument("--out", default=str(ROOT / "docs" / "images"))
    parser.add_argument("names", nargs="*", help="作る図のファイル名（省略時は全部）")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGURES.items():
        if args.names and name not in args.names:
            continue
        (out / name).write_text(fn(), encoding="utf-8")
        print(f"wrote {out / name}", file=sys.stderr)


if __name__ == "__main__":
    main()
