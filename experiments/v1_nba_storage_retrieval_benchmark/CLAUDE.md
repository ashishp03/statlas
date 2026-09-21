# v1 — NBA Storage / Retrieval Benchmark

> Self-contained experiment. Everything it needs lives in this folder. This file is the local
> source of truth for goals, scope, run order, and the non-negotiables inherited from the repo.
> See `ARCHITECTURE.md` for diagrams, `DECISIONS.md` for the dated rationale log, and `README.md`
> for the quickstart.

## Goals

statlas's core bet is that **the database is the calculator** — the LLM only handles language,
the store does every arithmetic. This experiment stress-tests that calculator:

1. **Storage bake-off** — materialize the same NBA data into **many** on-disk/in-memory formats and
   measure build size + query latency across realistic workloads (not just assume DuckDB/Parquet win).
2. **Retrieval correctness first** — every store must return the golden `eval_set.json` answers
   within tolerance **before** its timings count. Speed is meaningless without parity.
3. **Text-to-SQL model bake-off** — can a **free, local** LLM (via Ollama) draft SQL that passes the
   SELECT-only guard and executes to the correct number? Compare a shortlist of open-weight models.
4. **A real vector layer** — embed and index in an actual vector DB, to see whether semantic
   retrieval has a place in the product's text-to-SQL path.

## Scope — modern era only (Decision D2, REVISIT)

Seasons are keyed on their **end year** (`2025` == the "2024-25" season).

- **Aggregates:** 1996-97 → 2025-26 (`AGG_SEASON_YEARS`, 30 seasons) — the LeagueDash history floor.
- **Game logs:** 2021-22 → 2025-26 (`GAMELOG_YEARS`, 5 recent seasons) — the row-wise workload.
- **Scale probes:** one season of league-wide shot charts + one game of play-by-play (V3).
- **Cross-source:** 2024-25 Basketball-Reference advanced totals (PER/BPM/VORP/WS).

**Deferred (REVISIT):** deep history back to 1951-52 (LeagueLeaders), and full-league
play-by-play / tracking data at scale. Those are separate axes; get a clean, fast, correct
benchmark on the modern era first.

## Run order (S1 → S6)

Dependencies are installed with uv (`uv sync`); the stage scripts are ordinary Python programs —
run them from the repo root, in order:

```
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s1_pull.py
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s2_build_stores.py
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s3_retrieval.py
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text2sql.py
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s5_vector.py
python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s6_report.py
```

- **S1 `s1_pull.py`** — pull modern-era NBA data (nba_api bulk endpoints + Basketball-Reference)
  into `data/raw/*.parquet`; write `results/ingest_metrics.csv`. The one rate-limited step.
  *(Raw data is already pulled; a re-run is a cached no-op unless `--refresh`.)*
- **S2 `s2_build_stores.py`** — materialize `data/raw` into every format in `STORE_FORMATS` under
  `data/stores/`; record build time + on-disk size.
- **S3 `s3_retrieval.py`** — resolve `eval_set.json` expected values on the DuckDB store, run the
  **correctness parity gate** across all stores, then the **timed** retrieval workload.
- **S4 `s4_text2sql.py`** — for each model in `T2SQL_MODELS`, draft SQL for each eval question,
  validate through the SELECT-only guard (`s4_sql_guard`), execute on DuckDB, compare to expected.
- **S5 `s5_vector.py`** — embed with `EMBED_MODEL` via Ollama, index in a real vector DB
  (lancedb / optional chromadb), evaluate semantic retrieval.
- **S6 `s6_report.py`** — aggregate all `results/*.csv` into the final tables + figures (`results/figs/`).

> Note: uv is used for **dependency management only** (`uv sync` / `uv add` / `uv lock`). The uv
> `.venv` is active, so stages run as plain `python <path>` — there is no `uv run` execution rule.

## Inherited non-negotiables

These come straight from the root `CLAUDE.md` and hold everywhere in this experiment:

- **DuckDB does all arithmetic.** Python never computes a statistic; every number comes from a query.
- **Model-drafted SQL is guarded.** Any free/model SQL must pass the **SELECT-only allow-list**
  guard (`s4_sql_guard`) before it touches the DB.
- **Leaderboards apply the min-games qualifier** (`MIN_GAMES_QUALIFIER = 58`) — tiny samples must
  not win.
- **Refuse rather than guess.** An unresolved player/metric (e.g. a crosswalk match below threshold)
  returns "I don't know," never a fabricated value.
- **Everything is auditable.** Expose the SQL and the rows used; `eval_set.json` is the correctness
  backbone.

## Store × query matrix

Each store format (rows) is measured against each workload (columns). Correctness parity is a gate
before any timing counts.

| Store (`STORE_FORMATS`) | OLTP row-wise (`game_logs` point lookup + filter) | OLAP column-wise (leaderboards, league aggregates, min-games qualifier) | Cross-source JOIN (`bbref_advanced` × `player_crosswalk`) | Scale probe (shotchart / pbp) |
|---|---|---|---|---|
| `csv` (baseline)        | ✓ | ✓ | ✓ | ✓ |
| `parquet_single`        | ✓ | ✓ | ✓ | ✓ |
| `parquet_partitioned` (by season) | ✓ | ✓ | ✓ | ✓ |
| `feather` (Arrow IPC)   | ✓ | ✓ | ✓ | ✓ |
| `duckdb` (incumbent)    | ✓ | ✓ | ✓ | ✓ |
| `sqlite` (+ index)      | ✓ | ✓ | ✓ | ✓ |
| `polars_mem` (no-disk upper bound) | ✓ | ✓ | ✓ | ✓ |
| `lancedb` (columnar + vector) | ✓ | ✓ | ✓ | ✓ |

## Where results land

- `data/raw/*.parquet` — normalized source cache (git-ignored, reproducible).
- `data/stores/*` — the built store artifacts, one per format (git-ignored).
- `results/*.csv` — per-stage metrics (`ingest_metrics.csv` from S1; retrieval / t2sql / vector
  metrics from S3–S5).
- `results/figs/*` — figures produced by S6.
