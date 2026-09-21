# Day 11 — 2026-09-21

**Track 1 phase:** Stage 3 ✅ → **Stage 4 (LLMs)** — first contact (unchanged, offered 4th time on purpose)
**Track 2 phase:** MVP build sprint — **Session 1 of 15** (Week 1: "how good is a free local model, actually?")

## Coach suggested
- **Track 1:** 3Blue1Brown — **"Large Language Models explained briefly"** (~7 min, YouTube). Same
  small, phone-watchable offer as the last few runs — Stage 4 has been "next" since June and this
  closes it.
- **Track 2:** `MVP-3-WEEK-PLAN.md` **Session 1 — "Unblock and install."** Run the repo cleanup from
  `claude-code-setup.md` (~10 min, fixes the ~27 broken git refs), then `git switch -c mvp
  data-exploration` + `git checkout refs/heads/learning -- tests/` (the eval harness) + the rule-based
  gate (`src/statlas/nlu`, `src/statlas/query`, `src/statlas/entities`, `src/statlas/__init__.py`),
  install Ollama (`brew install ollama && ollama serve`), `ollama pull qwen2.5-coder:7b`, and write +
  commit `src/statlas/types.py` (the `AnswerCard` contract). ~45-60 min total.
- **Stretch:** Session 2 — run `experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py`
  against the real model once installed. Don't fix anything yet — just write down the score
  ("qwen2.5-coder:7b scored N/16").

## What I actually did
-

## Notes & insights
- First session of the restructured plan (mode changed 2026-09-20). This is genuinely the first
  hands-on-keyboard step of the sprint — everything before this was scoping. `ollama list` showing
  the model and `types.py` committed on the new `mvp` branch is the concrete "done" signal.

## Coding / exercises
-

## Links & resources
- [3Blue1Brown — Large Language Models explained briefly](https://www.youtube.com/watch?v=LPZh9BOjkQs)
- `learning/MVP-3-WEEK-PLAN.md` §6 "First action" (the exact command block for Session 1)
- `learning/claude-code-setup.md` §1 (repo cleanup)

## Carry-over for next time
-
