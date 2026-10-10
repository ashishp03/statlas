# main — Branch Context (Codex CLI)

> Branch overlay for `main` (the trunk), for Codex CLI. The shared, canonical project context lives
> in the root `AGENTS.md`; THIS file adds only what is specific to `main`. It is the Codex
> counterpart of `.claude/branch.md` — read that file for the full scope; the rules are identical.
> Protected by `.gitattributes` (`merge=ours`) so it never merges across branches.

## Purpose
`main` is the **trunk** — what every new branch inherits: toolchain, root docs, agent tooling
(`.claude/`, `.codex/`, `.agents/`), branch-model infra, and the permanent product code
(`src/statlas/`, `scripts/`, `tests/`).

## Scope — what belongs on this branch
- Permanent code only: `src/statlas/` (the engine), `scripts/` (task scripts the engine invokes),
  `tests/` (the eval scoreboard), plus toolchain, docs, and agent tooling.
- **Not** experiments/notebooks used for testing or probing, and **not** `learning/` study material.
  Proven code moves into `src/` or `scripts/` before it lands here.

## Branch-specific instructions
- Branch from `main` with `scripts/new-branch.sh <name> "purpose"`; PR back. Edit shared files here,
  flow them to branches with `git merge main`.
- Keep `src/statlas/entities/resolver.py` (nickname -> player) and `crosswalk.py` (nba <-> BBRef ids) distinct.

## Rolling log (most recent first)
- 2026-10-10 — Created this file (it did not exist, which left `AGENTS.md`'s `@.codex/branch.md`
  import pointing at nothing). Written by hand to match `.claude/branch.md`, not generated.
