# learning/modules — Context

## Section 1: Evergreen

**What this is:** Advanced homework modules from the build-focused `curriculum.md`. Each module pairs theory with a graded notebook and ships a change into `src/statlas/`. Mostly on hold while in foundations-first mode (`roadmap.md` is the default active plan) — but M4 and M5 were built 2026-08-25 as a direct, parallel request from Ashish for NLU/text-to-SQL/SQL-engine study material, so they're live even though the mode is still foundations-first overall.

**Module map:**
- `01-transformer-internals/` — attention from scratch + nanoGPT
- `02-nlu-entity-resolution/` — BERT / Sentence-BERT; embedding resolver
- `04-text-to-sql/` — Spider/BIRD/DIN-SQL/CHASE-SQL; `assert_safe` + exec-accuracy scorer (built 2026-08-25)
- `05-computation-engine/` — DuckDB vectorized execution, execution-guided decoding, self-consistency (built 2026-08-25)

**Architecture decisions (append-only, one line each):**
- Each module = `workbook.md` (papers/theory) + `exercises.ipynb` (graded code) + a concrete ship target in `src/statlas/`
- Parked overall; M4/M5 are the exception, built on direct request — revive the rest once roadmap foundations feel solid

**Non-negotiable constraints:**
- Don't treat these as the current plan; `roadmap.md` is active

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
