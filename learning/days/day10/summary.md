# Day 10 — 2026-09-20

**Track 1 phase:** Stage 3 ✅ → **Stage 4 (LLMs)** — first contact
**Track 2 phase:** T-B (the harness is now verified; one copy away from done)

## Coach suggested
- **Track 1:** 3Blue1Brown — **"Large Language Models explained briefly"** (~7 min, YouTube).
  Third offer, unchanged on purpose: smallest possible move on the roadmap's actual next stage,
  phone-watchable, no terminal involved.
- **Track 2:** Install `/eval` — now reduced to one command (~2 min), see below.
- **Stretch:** **B2 — DIN-SQL** (arXiv 2304.11015), ~45 min.

## Notes & insights — the coach ran the eval harness this session
The 09-16 run diagnosed the `/eval` blocker (no `tests/` on `data-exploration`) but couldn't
confirm the harness actually works — the sandbox had no `duckdb`/`rapidfuzz`. Fixed that today and
ran it against the `learning` branch tree:

```
[statlas] Built statlas.duckdb from seed: 5 players, 15 game logs.
[PASS] What was Wemby's average plus/minus vs OKC in the playoffs?   expected=4.4   got=4.40
[PASS] How many points did Wemby average against OKC in the playoffs? expected=28.6  got=28.60
[PASS] What were LeBron's average points in 2013?                     expected=27.75 got=27.75
[PASS] What was the Joker's average assists in the playoffs?          expected=10.0  got=10.00
[PASS] How many total rebounds did Wemby have vs OKC in the playoffs? expected=60.0  got=60.00

Accuracy: 5/5 = 100%
```

So: `tests/run_eval.py` is **green, 5/5, and self-bootstraps the DuckDB seed** — no setup, no DB to
build first. Nothing is broken behind the `/eval` item; it has only ever been a branch-path problem.
Two consequences worth recording:
- The p0 baseline is genuinely working, not just assumed working. That's the ship target from `CLAUDE.md`.
- 5 golden questions is a thin scoreboard. M7 calls for 40–50. Once `/eval` is installed, *growing the
  eval set* is the natural next Track-2/M7 move — and every gold NL→SQL pair written for M4 can double
  as an eval case.

## Friction removed
`learning/days/day10/install-eval.sh` does the whole Track-2 item: switches to `learning`, creates
`.claude/commands/`, extracts the command body out of `days/day8/draft-eval-command.md`. Then type
`/eval` in Claude Code.

```bash
bash learning/days/day10/install-eval.sh
```

## What I actually did
-

## Coding / exercises
-

## Links & resources
- 3B1B, LLMs explained briefly: https://www.youtube.com/watch?v=LPZh9BOjkQs
- Karpathy, "Intro to Large Language Models" (~1 hr, longer version): https://www.youtube.com/watch?v=zjkBMFhNj_g
- DIN-SQL: https://arxiv.org/abs/2304.11015
- Drafted command: `learning/days/day8/draft-eval-command.md`

## Carry-over for next time
- Day 7's `qualifier_worked_example.md` still unread as far as the log knows (~5 min, already written).
- 4 of 5 gold NL→SQL TODO pairs in `modules/04-text-to-sql/exercises.ipynb` remain.
- Housekeeping (local, needs Ashish): `git worktree prune` (~15 stale/locked entries + ~20 broken
  refs warning on every `git branch`); commit the untracked `experiments/` + `ask.py` +
  `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md` on `data-exploration`.
