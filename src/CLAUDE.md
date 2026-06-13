# src — Context

## Section 1: Evergreen

**What this is:** Source root. Holds the importable `statlas` Python package (src-layout: `pyproject.toml` resolves packages via `where = ["src"]`). No code lives directly in this folder.

**Module map:**
- `statlas/` — the engine package (all importable code)

**Architecture decisions (append-only, one line each):**
- src-layout: tests and benches import the *installed* `statlas` package, not loose local files
- Nothing importable lives outside `statlas/`

**Non-negotiable constraints:**
- Keep all package code under `statlas/`; no top-level scripts here

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
