# pipeline/ — Stage Scripts

Numbered, single-purpose stages plus the shared contracts they all import. Run them in order
(see `../README.md`); each reads the previous stage's artifacts and writes into `../results/`.

## Modules

| Module                | Role (one line)                                                                                          |
|-----------------------|----------------------------------------------------------------------------------------------------------|
| `config.py`           | Single source of truth: paths, modern-era season scope, canonical schemas, `STORE_FORMATS`, `T2SQL_MODELS`, `EMBED_MODEL`/`OLLAMA_HOST`, `MIN_GAMES_QUALIFIER`, bench knobs. Imported by every stage — never redefine a constant. |
| `_harness.py`         | Reusable helpers: `safe_rows` (defensive nba_api call), `season_str`, `timer()`, `percentile`, and `bench(fn, reps, warmup, label)` returning p50/p95/mean/stdev/min in ms. |
| `s1_pull.py`          | Pull modern-era data (nba_api bulk + Basketball-Reference) → normalize → `data/raw/*.parquet`; write `results/ingest_metrics.csv`. The one stateful, rate-limited step. |
| `s2_build_stores.py`  | Materialize `data/raw` into every `STORE_FORMATS` entry under `data/stores/`; record build time + on-disk size. |
| `s3_retrieval.py`     | `resolve_eval` (run each `canonical_sql` on the DuckDB store to fill `expected_value`) → correctness parity gate across all stores → timed retrieval workload. |
| `s4_text2sql.py`      | Text-to-SQL bake-off: each `T2SQL_MODELS` model drafts SQL → `s4_sql_guard` (SELECT-only allow-list) → DuckDB executes → compare to `expected_value`. |
| `s5_vector.py`        | Embed with `EMBED_MODEL` via Ollama → index in a real vector DB (lancedb / optional chromadb) → evaluate semantic retrieval. |
| `s6_report.py`        | Aggregate all `results/*.csv` into final tables + figures under `results/figs/`. |

Helpers `resolve_eval` and `s4_sql_guard` are used by S3/S4 respectively (a module or function
within those stages); optional deps (duckdb sqlite scanner, pyarrow/polars feather, lancedb,
chromadb, urllib/requests for Ollama) are imported defensively so a missing one degrades gracefully.

## Data flow

```
live API ──S1──▶ data/raw/*.parquet ──S2──▶ data/stores/{csv,parquet,feather,duckdb,sqlite,…}
                                                     │
        eval_set.json ──▶ S3 (resolve_eval + parity gate + timing) ──▶ results/*.csv
                          S4 (model SQL → guard → DuckDB → compare) ──▶ results/*.csv
        data/raw ───────▶ S5 (embed → vector DB → semantic retrieval) ─▶ results/*.csv
                                                     │
                                          S6 (aggregate) ──▶ results/figs/*
```

## Bootstrap import pattern

Put this at the top of every stage script so the experiment root is on `sys.path` and `config` +
the harness import cleanly:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import config
from pipeline._harness import bench, timer, season_str  # add safe_rows / percentile as needed
```
