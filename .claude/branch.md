# main — Branch Context

> Branch overlay for `main` (the trunk). The shared, canonical project context lives in the root
> `CLAUDE.md`; THIS file adds only what is specific to `main`. Protected by `.gitattributes`
> (`merge=ours`) so it never merges across branches.

## Purpose
`main` is the **trunk**: what every new branch inherits. It holds the toolchain (`pyproject.toml`,
`uv.lock`, `.python-version`), the root docs (`CLAUDE.md`, `AGENTS.md`, `README.md`), the agent
tooling (`.claude/`, `.codex/`, `.agents/`), the branch-model infra (`.gitattributes`, `scripts/`,
`.claude/branch.template.md`), and the permanent product code. A person who branches from `main`
should not have to re-set-up any AI tooling or re-derive any proven code.

## Scope — what belongs on this branch
- `src/statlas/` — the engine (NLU, query planning, entity resolution, the SQL guard, data access).
  What makes statlas run.
- `scripts/` — task scripts the engine invokes or imports (ingest, branch scaffolding, etc.).
- `tests/` — the eval set and `run_eval.py`, the scoreboard.
- Toolchain, root docs, and agent tooling listed above.
- **Not** experiments or notebooks used for testing, probing, or planning — permanent code is never
  developed there. When something proves out and the project needs it, it moves into `src/` or
  `scripts/` first, then lands here.
- **Not** `learning/` study material — `learning` never merges to `main`.

## Branch-specific instructions
- Feature work happens on a branch cut from `main` (`scripts/new-branch.sh <name> "purpose"`), then
  comes back through a PR. Edit shared files here, then flow them to branches with `git merge main`.
- `src/statlas/entities/` holds two different things: `resolver.py` (nickname -> player, used by the
  rule-based parser) and `crosswalk.py` (nba <-> Basketball-Reference id matching). Keep the names distinct.
- `src/statlas/data/seed/*.csv` are the illustrative seed data the eval harness bootstraps from.

## Rolling log (most recent first)
- 2026-10-10 — Rewrote this overlay: it had been replaced by `data-exploration`'s overlay when PR #3
  merged. Landed the rule-based gate (`parser`, `planner`, `executor`, `engine`, `ingest`, `cli`) and
  `tests/` on `main` (they previously lived only on `learning`), and renamed the crosswalk matcher
  to `entities/crosswalk.py` to free `resolver.py` for the nickname resolver. Updated the branch-model
  bullets in `CLAUDE.md`/`AGENTS.md` to match: permanent code lives in `src/`+`scripts/` on `main`.
