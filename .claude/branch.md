# main — Branch Context

> Branch overlay for `main` (the trunk). The shared, canonical project context lives in the root
> `CLAUDE.md`; THIS file adds only what is specific to `main`. Protected by `.gitattributes`
> (`merge=ours`) so it never merges across branches.

## Purpose
`main` is the **trunk**: the shared source of truth for environment setup and project context. It
holds the toolchain (`pyproject.toml`, `uv.lock`, `.python-version`), the root `CLAUDE.md` +
`README.md`, and the branch-model infrastructure (`.gitattributes`, `scripts/`,
`.claude/branch.template.md`). No feature work happens here.

## Scope — what belongs on this branch
- Environment deps + lockfile (`pyproject.toml`, `uv.lock`, `.python-version`, `requirements.txt`)
- Root context/setup docs (`CLAUDE.md`, `README.md`) and the branch-model infra
- **Not** product/pipeline code — that lives on its own feature branch and is **not** merged back
  here (the build is paused; the p0 scaffold lives on the work branches)
- **Not** learning/study material — that lives on the `learning` branch
- **Not** nba_api EDA/data exploration — that belongs on a `data-exploration` branch

## Branch-specific instructions
- Treat `main` as docs + setup only. To start real work, branch off main:
  `scripts/new-branch.sh <name> "purpose"` (scaffolds this overlay from the template + commits).
- Edit shared files (root `CLAUDE.md`, `README.md`, toolchain) HERE; feature branches pull updates
  with `git merge main` (their own `.claude/branch.md` is preserved via `merge=ours`).

## Rolling log (most recent first)
- 2026-06-22 — Added the shared Claude Code automation setup (commit `5226551`): PreToolUse hooks
  (`guard-bash.sh` forces uv over bare python/pip/jupyter; `guard-edits.sh` protects `uv.lock`/`*.duckdb`
  and branch-aware-blocks `src/statlas/**` edits while on `data-exploration`), wired in `.claude/settings.json`;
  `data-source-scout` subagent; user-only `run-notebook` skill; `context7` MCP (`.mcp.json`). Lives on the
  trunk so feature branches inherit it via `git merge main` and new branches off `main` get it automatically.
- 2026-06-13 — Trunk seeded: brought the uv toolchain and the root context/setup docs
  (`CLAUDE.md`, `README.md`, branch-model infra) over from the `learning` snapshot. Product code
  and study material intentionally stay on their feature branches.
