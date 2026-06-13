# Statlas Learning Log

This folder tracks Ashish's study journey toward building **Statlas** — an AI-powered sports
stats answer engine (a better StatMuse). It's maintained partly by hand and partly by the
**daily study coach** scheduled task.

## How it works

- **`curriculum.md`** — the advanced, practice/paper/video-based module map (both tracks). Start here.
- **`modules/NN-name/`** — each module has a `workbook.md` (objectives, papers, theory) and a graded
  `exercises.ipynb` (homework cells with `assert`s). Every module ships a change into `src/statlas/`.
- **`progress.md`** — the master tracker. Top section shows the current module on each of the
  two tracks; below it is a dated log of what was suggested and what was actually completed.
- **`days/dayN/summary.md`** — one folder per active study day. Each day's `summary.md`
  captures: what the coach suggested, what you actually did, notes/insights, links, and any
  coding exercises. Days are numbered sequentially (`day1`, `day2`, …), each tagged with its
  calendar date.
- **`templates/day-template.md`** — the blank template each new day's `summary.md` is copied from.

## The two tracks

- **Track 1 — Conceptual AI/ML.** Phase 0 Orientation → 1 Transformers → 2 NLP/NLU →
  3 LLM app layer → 4 Text-to-SQL → 5 RAG → 6 Evaluation → 7 Visualization → Capstone.
- **Track 2 — AI tooling.** Phase A Orientation → B Claude Code → C Skills → D Tools/function
  calling → E MCP → F Agent SDK → G Cowork automation.

Each phase ends by shipping its small project before moving on.

## Git workflow

This lives on the `learning` branch. Commits happen **when there's something real to record** —
an activity finished, a coding exercise done, or new material/notes added. No empty daily
commits. The coach commits locally; pushing to `origin/learning` is manual unless you ask.

## How to give input

Just tell the coach (in chat or on the next scheduled run) what you actually completed. It
will update `progress.md`, fill in the day's `summary.md`, start a new day folder when needed,
and commit if the day produced something worth recording.
