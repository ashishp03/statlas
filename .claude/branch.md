# learning — Branch Context

> Branch overlay for `learning` (created 2026-06-13). The shared, canonical project context lives
> in the root `CLAUDE.md` (and subdirectory `CLAUDE.md` files) on `main`; THIS file adds only what
> is specific to the `learning` branch. Protected by `.gitattributes` (`merge=ours`) so it never
> merges across branches.

## Purpose
The `learning` branch is for **learning the concepts** behind Statlas — foundations-first study,
not product features. Follow `learning/roadmap.md`; write only toy / example code to cement ideas.

## Scope — what belongs on this branch
- `learning/` — roadmap, progress tracker, day logs, exercises, parked modules
- Toy "example-coding" exercises (attention from scratch, NL→SQL on a sample DB, embeddings demos)
- **Not** product/pipeline features — those belong on `main` or a feature branch
- **Not** nba_api EDA/data exploration — that belongs on the `data-exploration` branch

## Branch-specific instructions
- Entry point: `learning/roadmap.md` (foundations-first, ACTIVE). `learning/curriculum.md` is PARKED.
- Current focus: Stage 3 (transformers) — see `learning/days/day5/TODAY.md`.
- The scheduled "daily study coach" maintains `learning/progress.md` + `learning/days/dayN/` here.
- Commit only under `learning/`; commit when a real activity/exercise/notes lands (no empty daily commits).

## Subdirectory notes (branch-specific)
- `learning/days/` — the newest `dayN/` is the working context; copy `templates/day-template.md` for new days.

## Rolling log (most recent first)
- 2026-06-22 — Inherited the shared Claude Code automation setup from `main` via `git merge main`
  (uv-only Bash hook, branch-aware edit-guard hook, `data-source-scout` subagent, `run-notebook` skill,
  `context7` MCP). Resolved a `CLAUDE.md` conflict by taking `main`'s canonical "Branch model" wording
  (this branch carried a stale variant); `.claude/branch.md` preserved via `merge=ours`.
- 2026-06-13 — Adopted Option A branch model; learning-branch context moved here. Day 5: ran the
  nba_api EDA (now reference material), pivoted to foundations-first, authored `roadmap.md`,
  started Stage 3. Migrated env to uv. Generated the repo-wide `CLAUDE.md` tree.
