---
name: write-chapter
description: >-
  Write yukkuri-heuristics book chapters (Yukkuri Reimu/Marisa dialogue,
  Python/Go code, hands-on exercises). Use when the user asks to write,
  draft, or edit a chapter (docs/NN.md), section, or hands-on for this repo.
---

# Write Chapter (yukkuri-heuristics)

Repo-local skill for authoring chapters of **ゆっくり霊夢・魔理沙が教えるヒューリスティック競技プログラミング**.

## Critical conventions

- **「ゆっくり」= ゆっくり霊夢・ゆっくり魔理沙の掛け合い解説**。学習速度の「ゆっくり」ではない。
- **Languages**: Python and Go — same algorithm in both; keep file names aligned.
- **Audience**: AHC (AtCoder Heuristic Contest) learners; follow rating bands in `docs/00-toc.md`.

## Before writing

1. Read the chapter outline in [`docs/00-toc.md`](../../../docs/00-toc.md).
2. Read style reference [`docs/00.md`](../../../docs/00.md) (dialogue tone, code density, repo layout).
3. If updating an existing chapter, read the full `docs/NN.md` first.
4. Check [`reference.md`](reference.md) for chapter→file mapping and section template.

Determine chapter number `N` from the user request. File: `docs/NN.md` (zero-padded, e.g. `01`, `08`).

## Writing workflow

Copy and track:

```
Chapter N progress:
- [ ] Outline from toc.md confirmed
- [ ] docs/NN.md drafted (all sections)
- [ ] Python code added under python/chNN/
- [ ] Go code added under go/chNN/
- [ ] Sample data under data/ (if needed)
- [ ] Code executed and verified
- [ ] Chapter summary and exercises included
```

### Step 1: Structure the chapter

Each chapter follows **toc.md** subsections (`N.1`, `N.2`, …). Per chapter type:

| Part | Typical content |
|------|-----------------|
| Intro (0–1) | Conventions, AHC overview, environment |
| Technique (2–30) | Concept → hands-on → Python → Go → exercise |
| Rating band | Match difficulty to color in toc (Gray→Red) |

Every **technique chapter** must include:

1. **掛け合い解説** — Reimu asks, Marisa explains
2. **ハンズオン** — runnable steps referencing repo paths
3. **Python / Go 実装** — working code, not snippets only
4. **演習** — 1–3 tasks the reader can do alone

### Step 2: Write dialogue

**Characters**

| Role | Speaker | Voice |
|------|---------|-------|
| Reader proxy | 霊夢 | 「〜なの？」「〜なの」— questions, misunderstandings, recap |
| Explainer | 魔理沙 | 「〜だぜ」「〜なんだ」— definitions, intuition, code |

**Per-section flow**

```
霊夢: question
魔理沙: explanation
霊夢: follow-up / misconception
魔理沙: code or example
(optional) 霊夢: restate understanding
```

Format:

```markdown
**霊夢**: セリフ

**魔理沙**: セリフ
```

End the chapter with **章末まとめ** (blockquote bullet list).

### Step 3: Write code (many code blocks)

- Prefer **many code blocks** in the markdown; readers expect copy-pasteable examples.
- Reuse templates from `python/templates/` and `go/templates/` before inventing new boilerplate.
- New chapter code lives in:
  - `python/chNN/<name>.py`
  - `go/chNN/<name>.go`
- Pair names across languages: `greedy.py` ↔ `greedy.go`.
- Sample input: `data/<problem>/sample.txt` or `data/chNN/sample.txt`.
- First line comment: `# python/chNN/foo.py` or `// go/chNN/foo.go`.

Show Python and Go **side by side** in the prose when teaching the same logic.

### Step 4: Hands-on section

Follow the 4 steps from chapter 0:

1. 読む → 2. 写す（clone + run）→ 3. 改変（one parameter at a time）→ 4. コンテスト形式（timer, best-so-far output）

Include exact commands:

```bash
python python/chNN/solution.py < data/chNN/sample.txt
go run go/chNN/solution.go < data/chNN/sample.txt
```

### Step 5: Verify

Run all new/changed code before finishing:

```bash
python python/chNN/<file>.py < data/...    # if stdin-driven
go run go/chNN/<file>.go < data/...
./tools/run.sh template io                 # when using templates only
```

Optional validation:

```bash
./.cursor/skills/write-chapter/scripts/validate-chapter.sh NN
```

Fix compile/runtime errors; do not leave placeholder `...` in committed code files.

## Scope control

**Do**

- Match section list in `docs/00-toc.md` for the requested chapter
- Link official AHC docs when mentioning rating rules or contest format
- Keep diffs focused on the requested chapter and its code/data

**Do not**

- Rewrite unrelated chapters
- Change `docs/00-toc.md` unless the user asks
- Commit unless explicitly requested
- Edit `README.md` unless asked
- Use 「ゆっくり」to mean slow-paced learning

## File layout (this repo)

```text
docs/NN.md              # chapter body
python/chNN/*.py        # chapter solutions
go/chNN/*.go
data/                   # sample inputs
python/templates/       # shared templates (chapter 0)
go/templates/
tools/run.sh
```

## Additional resources

- Section template, chapter index, checklist: [reference.md](reference.md)
- Completed example: [docs/00.md](../../../docs/00.md)
