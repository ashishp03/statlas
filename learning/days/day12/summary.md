# Day 12 — 2026-09-22

**Track 1 phase:** Stage 3 ✅ → **Stage 4 (LLMs)** — first contact (unchanged, offered 5th time on purpose)
**Track 2 phase:** MVP build sprint — **Session 1 of 15** (unchanged from day11, not yet started)

## Coach suggested
- **Track 1:** 3Blue1Brown — "Large Language Models explained briefly" (~7 min, YouTube). Same small,
  phone-watchable offer as the last few runs. Noted that MVP Session 1 (below) covers the same ground
  hands-on if today ends up being a one-track day — running a real local LLM is arguably a better
  Stage-4 first contact than the video.
- **Track 2:** `MVP-3-WEEK-PLAN.md` Session 1 — "Unblock and install." Repo cleanup from
  `claude-code-setup.md` (~10 min), then `git switch -c mvp data-exploration` + pull in the eval
  harness (`tests/`) and the rule-based gate (`src/statlas/nlu`, `src/statlas/query`,
  `src/statlas/entities`, `src/statlas/__init__.py`) from `learning`, install Ollama
  (`brew install ollama && ollama serve`), `ollama pull qwen2.5-coder:7b`, and write + commit
  `src/statlas/types.py` (the `AnswerCard` contract). ~45-60 min total — fine to split across two
  sittings.
- **Stretch:** Session 2 — run `experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py`
  against the real model once installed. Don't fix anything yet — just write down the score.

## What I actually did
-

## Notes & insights
- Second day offering MVP Session 1 unchanged (day11 also unstarted — no rush, one day is not a gap).
  This coach run hit a stale `.git/index.lock` in the main checkout while trying to write; committed
  via git plumbing (custom index + commit-tree + update-ref) instead of the normal `git add`/`git
  commit` flow. Worth a check locally for a leftover git process, and the `git worktree prune`
  Session 1's cleanup step already covers.

## Coding / exercises
-

## Links & resources
- [3Blue1Brown — Large Language Models explained briefly](https://www.youtube.com/watch?v=LPZh9BOjkQs)
- `learning/MVP-3-WEEK-PLAN.md` §6 "First action" (exact command block for Session 1)
- `learning/claude-code-setup.md` §1 (repo cleanup)

## Carry-over for next time
-
