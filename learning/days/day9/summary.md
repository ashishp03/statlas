# Day 9 — 2026-09-16

**Track 1 phase:** Stage 3 ✅ → **Stage 4 (LLMs)** — first contact
**Track 2 phase:** T-B (one command file away from done — with a branch caveat, see below)

## Coach suggested
- **Track 1:** 3Blue1Brown — **"Large Language Models explained briefly"** (~7 min, YouTube).
  Same as day 8, unchanged on purpose: it's the smallest possible move on the roadmap's *actual*
  next stage, it's phone-watchable, and Stage 4 has been "next" since June without being opened.
- **Track 2:** Install the `/eval` command (~5 min) — **but on the `learning` branch**, or after
  pulling `tests/` across. See the blocker below; this is new information.
- **Stretch:** **B2 — DIN-SQL** (arXiv 2304.11015), the highest-value paper in
  `study-plan-nlu-text-to-sql.md` (~45 min).

## Notes & insights
- **Found the likely reason the "2-minute paste" never landed.** The working tree is checked out
  on `data-exploration`, and **`tests/` does not exist on that branch** — `tests/run_eval.py` and
  `tests/eval_set.json` live only on `learning`. So pasting `.claude/commands/eval.md` and typing
  `/eval` on `data-exploration` fails with a missing-file error, which is a much worse first
  experience than a 2-minute task implies. Branch contents today:
  - `learning`: `src/`, `tests/`, `CLAUDE.md`, `pyproject.toml`, `learning/` ✅
  - `data-exploration`: `src/`, `experiments/`, `notebooks/`, `scripts/` — **no `tests/`**
- Two ways to unblock it, either is fine:
  ```bash
  # option A — do it on the branch that has the harness
  git switch learning && mkdir -p .claude/commands   # then paste, then /eval

  # option B — bring the harness onto data-exploration
  git checkout refs/heads/learning -- tests/         # then paste, then /eval
  ```
- The coach tried to pre-run `tests/run_eval.py` this session to confirm it goes green, but the
  sandbox has no `duckdb`/`rapidfuzz` installed and the install timed out — so the first honest
  run is still yours. If it errors rather than printing an accuracy line, that error *is* the
  day's finding, worth writing down here.

## What I actually did
-

## Coding / exercises
-

## Links & resources
- 3B1B, LLMs explained briefly: https://www.youtube.com/watch?v=LPZh9BOjkQs
- Karpathy, "Intro to Large Language Models" (~1 hr, the longer version): https://www.youtube.com/watch?v=zjkBMFhNj_g
- DIN-SQL: https://arxiv.org/abs/2304.11015
- The drafted command: `learning/days/day8/draft-eval-command.md`

## Carry-over for next time
- Day 7's `qualifier_worked_example.md` is still unread as far as the log knows (~5 min, already written).
- 4 of the 5 gold NL→SQL TODO pairs in `modules/04-text-to-sql/exercises.ipynb` remain.
- Housekeeping (local, needs Ashish): `git worktree prune` (~15 stale/locked entries, plus ~20
  broken refs now showing as warnings on every `git branch`); commit the untracked `experiments/`
  + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md` on `data-exploration`.
