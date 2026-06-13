# src/statlas/data — Context

## Section 1: Evergreen

**What this is:** The data layer. Builds the DuckDB warehouse — the "calculator" every exact stat is computed against. Two modes: seed CSVs (offline, instant) and real `nba_api` ingest.

**Module map:**
- `__init__.py` — package marker
- `ingest.py` — `connect()`, `build_from_seed()`, `ingest_nba_api()` (stub), `DEFAULT_DB`, `SEED_DIR`
- `seed/` — illustrative sample CSVs (`players.csv`, `game_logs.csv`); output/data folder, no own `CLAUDE.md`

**Architecture decisions (append-only, one line each):**
- DuckDB is an embedded single-file OLAP DB; default path is a temp file, overridable via `STATLAS_DB`
- Seed mode loads CSVs with `read_csv_auto` and materializes real tables; no network
- Seed numbers are ILLUSTRATIVE/invented — for plumbing, not accuracy
- Real ingest uses `nba_api` (free, no key); keep the SAME `game_logs` schema so the pipeline doesn't change
- Cache `nba_api` pulls — stats.nba.com rate-limits rapid calls

**Non-negotiable constraints:**
- Keep the `game_logs` column schema stable across seed and real data
- Never present seed numbers as real stats
- All computation happens in DuckDB, not in Python

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
