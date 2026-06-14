# Statlas — Learning Branch

This is the **`learning` branch** of Statlas — an AI-powered sports-stats answer engine (a better
StatMuse). This branch is for **learning the concepts** from the ground up, *not* building product
features. It's maintained partly by hand and partly by the scheduled **daily study coach**.

> Branch-specific context (scope, current focus, rolling log) lives in `.claude/branch.md`. The
> shared, project-wide context is the root `CLAUDE.md` on `main`. See "Branches & context files"
> in the root `README.md` for how the branch model works.

## How it works

- **`roadmap.md`** — the ACTIVE master guide: a foundations-first, ground-up concept stack
  (neural nets → NLP → transformers → LLMs → prompting → text-to-SQL → SQL → RAG → eval), each
  stage with intro videos/lectures/papers and small example-coding exercises. **Start here.**
- **`curriculum.md`** — the older advanced, build-focused module map. **PARKED** until the
  foundations feel solid.
- **`progress.md`** — the master tracker: the current stage plus a dated log of what was suggested
  and what was actually completed.
- **`days/dayN/summary.md`** — one folder per active study day (numbered, date-tagged): what the
  coach suggested, what you did, notes/insights, links, and exercises. When present,
  `days/dayN/TODAY.md` is the explicit step-by-step checklist for that day.
- **`days/dayN/exercises/`** — hands-on toy notebooks (e.g. attention from scratch) with built-in
  self-check `assert` cells. Skill-builders, not product code.
- **`modules/`** — parked homework modules from the advanced plan.
- **`templates/day-template.md`** — the blank template each new day's `summary.md` is copied from.

## Scope of this branch

Learn concepts and write toy/example code only. Product/pipeline features belong on `main` or a
feature branch; nba_api data exploration belongs on the `data-exploration` branch.

## Git workflow

This lives on the `learning` branch (created off `main`, so it carries the full shared `CLAUDE.md`
tree and the uv toolchain). Commit **only under `learning/`**, and only when there's something real
to record — an activity finished, a coding exercise done, or notes/material added. No empty daily
commits. The coach commits locally; pushing to `origin/learning` is manual unless you ask. Pull
shared updates from `main` with `git merge main` — your `.claude/branch.md` is preserved
(`merge=ours`).

## How to give input

Just tell the coach what you actually completed. It updates `progress.md`, fills in the day's
`summary.md`, starts a new day folder when needed, and commits if the day produced something worth
recording.
