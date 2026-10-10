# src/statlas — Context

## Section 1: Evergreen

**What this is:** The Statlas engine package. Orchestrates the full natural-language → answer pipeline and composes the human-readable answer + transparency card. Sub-packages own each pipeline stage.

**Module map:**
- `__init__.py` — package marker / re-exports
- `engine.py` — `ask()` orchestrator (parse → build_sql → run → compose), `Answer` dataclass, `_compose()` sentence builder, `card` assembly, DB connection lifecycle, `ensure_db()`
- `cli.py` — command-line entry: one-shot or interactive, `--debug` (prints Intent + SQL), `--rebuild` (rebuild seed DB)
- `nlu/` — language → `Intent`
- `query/` — `Intent` → validated SQL → exact number
- `data/` — DuckDB warehouse builder
- `entities/` — reference → canonical id resolver

**Architecture decisions (append-only, one line each):**
- Pipeline order is fixed: `question → parse → build_sql → run → compose`
- `engine.ask()` owns the DuckDB connection (opens its own if none passed) and closes what it opens
- `Answer` carries `text, value, intent, result, ok, card`; `card` exposes SQL + games for auditability
- `_compose()` only phrases the executor's number — it never recomputes or rounds away the source of truth (beyond display rounding)

**Non-negotiable constraints:**
- The engine must not compute stats itself — delegate to `query.run`
- Preserve the `Intent` contract so NLU implementations are swappable
- Unanswerable intents return a helpful "I don't know," never a guess

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
