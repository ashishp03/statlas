# Day 8 — 2026-09-15

**Track 1 phase:** Stage 3 ✅ → **Stage 4 (LLMs)** — first contact
**Track 2 phase:** T-B (last item now drafted, needs a 2-min copy)

## Coach suggested
- **Track 1:** 3Blue1Brown — **"Large Language Models explained briefly"** (~7 min, YouTube).
  Pure watching, no setup. This is the front door to **Stage 4**, which has been "next" since
  June and has never actually been opened. Deliberately *not* a coding item.
- **Track 2:** Copy `day8/draft-eval-command.md` into `.claude/commands/eval.md` and run `/eval`
  (~5 min). The command is already written — the remaining work is a paste. Landing it checks
  off **T-B** and opens **T-C (Skills)**.
- **Stretch:** **B2 — DIN-SQL** (arXiv 2304.11015), the highest-value paper in
  `study-plan-nlu-text-to-sql.md` (~45 min).

## What I actually did
-

## Notes & insights
-

## Coding / exercises
- `day8/draft-eval-command.md` — full `.claude/commands/eval.md` slash command, written by the
  coach (frontmatter + scoped `allowed-tools` + failure-triage steps + "don't edit the eval set
  to make it pass" rule).

## Links & resources
- 3B1B, LLMs explained briefly: https://www.youtube.com/watch?v=LPZh9BOjkQs
- Karpathy, "Intro to Large Language Models" (~1 hr, the longer version): https://www.youtube.com/watch?v=zjkBMFhNj_g
- DIN-SQL: https://arxiv.org/abs/2304.11015
- Runner the slash command wraps: `tests/run_eval.py` + `tests/eval_set.json`

## Carry-over for next time
- Day 7's `qualifier_worked_example.md` is still unread as far as the log knows (5 min).
- 4 of the 5 gold NL→SQL TODO pairs in `modules/04-text-to-sql/exercises.ipynb` remain.
- Housekeeping (local, needs Ashish): `git worktree prune` (~15 stale entries); commit the
  untracked `experiments/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md` on
  `data-exploration`; `learning/days/day7/` is untracked in the `data-exploration` working tree.
