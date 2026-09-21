# v1 — Architecture

Five views of the experiment: the end-to-end pipeline, the data path, the cross-source id crosswalk,
the multi-agent build loop that produced it, and the guarded text-to-SQL flow. Each diagram is
followed by a short "logic and flow" note.

## 1. End-to-end pipeline (S1 → S6)

```mermaid
flowchart TD
    API["nba_api + Basketball-Reference<br/>(live, rate-limited)"] --> S1["S1 · s1_pull.py<br/>bulk pull → normalize"]
    S1 --> RAW[("data/raw/*.parquet")]
    RAW --> S2["S2 · s2_build_stores.py<br/>materialize 8 formats"]
    S2 --> STORES[("data/stores/*")]
    EVAL["eval_set.json<br/>(golden questions)"] --> S3["S3 · s3_retrieval.py<br/>resolve_eval → parity gate → timed workload"]
    STORES --> S3
    EVAL --> S4["S4 · s4_text2sql.py<br/>model SQL → guard → DuckDB → compare"]
    STORES --> S4
    RAW --> S5["S5 · s5_vector.py<br/>embed → vector DB → semantic retrieval"]
    S3 --> RES[("results/*.csv")]
    S4 --> RES
    S5 --> RES
    RES --> S6["S6 · s6_report.py<br/>aggregate → tables + figures"]
    S6 --> FIGS[("results/figs/*")]
```

**Logic and flow:** Data enters once through S1, the only stateful, rate-limited stage, and is
frozen as normalized Parquet in `data/raw/`. Everything downstream reads that cache — never the live
API. S2 fans the raw tables out into every candidate storage format; S3/S4/S5 are independent
evaluation stages that each consume the stores (and the golden `eval_set.json`) and emit metrics
CSVs. S6 is a pure reducer: it reads only `results/*.csv` and renders the final tables and figures.
The strict left-to-right dependency means any stage can be re-run in isolation once its inputs exist.

## 2. Data sources → raw Parquet → stores → query routing

```mermaid
flowchart LR
    subgraph Sources
      A1["nba_api<br/>LeagueDash / LeagueGameLog"]
      A2["nba_api<br/>ShotChart / PlayByPlayV3"]
      A3["Basketball-Reference<br/>advanced totals"]
    end
    A1 --> P1["player_season.parquet<br/>game_logs.parquet<br/>players.parquet"]
    A2 --> P2["shotchart_sample.parquet<br/>pbp_sample.parquet"]
    A3 --> P3["bbref_advanced.parquet"]
    P1 --> ST{{"8 store formats"}}
    P2 --> ST
    P3 --> ST
    ST --> Q1["OLTP row-wise<br/>game_logs point lookup + filter"]
    ST --> Q2["OLAP column-wise<br/>leaderboards · min-games qualifier · league aggregates"]
    ST --> Q3["cross-source JOIN<br/>bbref × player_crosswalk"]
    ST --> Q4["scale probe<br/>shotchart / pbp"]
```

**Logic and flow:** Three source families collapse into a handful of normalized Parquet tables with
stable, `src/statlas`-compatible schemas (`game_logs` columns are kept byte-stable). S2 replicates
those tables into each of the eight formats — `csv`, `parquet_single`, `parquet_partitioned`,
`feather`, `duckdb`, `sqlite` (+index), `polars_mem`, `lancedb`. Every store then answers the same
four workload classes, so latency differences are attributable to the format, not the query. The
row-wise (OLTP) and column-wise (OLAP) split is the axis most likely to separate a B-tree row store
(sqlite) from a columnar engine (duckdb/parquet).

## 3. The id crosswalk join (nba_player_id ↔ bbref_slug)

```mermaid
flowchart TD
    N["nba players<br/>(player_id, full_name)"] --> M{{"fuzzy name match<br/>(rapidfuzz score)"}}
    B["bbref rows<br/>(bbref_slug, full_name)"] --> M
    M -->|"score ≥ threshold"| X["player_crosswalk<br/>canonical_id · nba_player_id · bbref_slug · bdl_id · full_name"]
    M -->|"score < threshold"| R["REFUSE<br/>(leave unmapped — never guess)"]
    X --> J["JOIN bbref_advanced b<br/>ON b.bbref_slug = x.bbref_slug<br/>WHERE x.nba_player_id = ?"]
    J --> ANS["cross-source answer<br/>(e.g. Jokić VORP 2024-25)"]
```

**Logic and flow:** Basketball-Reference keys players by `bbref_slug`; nba_api keys them by integer
`player_id`. To answer a question like "Jokić's VORP" — a metric only BBRef provides — the two
sources must be bridged. A fuzzy full-name match (rapidfuzz) proposes pairings; only pairings at or
above the score threshold are written into `player_crosswalk`, and anything below is **refused**
(left unmapped) rather than guessed, honoring the repo's refuse-rather-than-guess rule. Queries then
join through the crosswalk on `bbref_slug`, filtered by the caller's `nba_player_id`, so an unmatched
player simply yields no row instead of a wrong number.

## 4. Multi-agent build / verify / review loop

```mermaid
sequenceDiagram
    participant O as Main loop (orchestrator)
    participant E as Executor agent
    participant V as Verifier agent
    participant R as Reviewer agent
    participant FS as Repo (files)
    O->>E: build module (spec + file allow-list)
    E->>FS: write ONLY the named files
    E-->>O: build summary
    O->>V: verify module
    V->>FS: compile + self-check on synthetic data
    V-->>O: pass / fail + findings
    alt verification fails
        O->>E: revise (findings)
        E->>FS: patch named files
    else passes
        O->>R: review the diff
        R-->>O: findings (ranked)
        opt findings worth fixing
            O->>E: apply fixes
        end
    end
    O->>O: advance to next module (S1 … S6)
```

**Logic and flow:** The experiment is assembled by an orchestrator that dispatches one **build
module** at a time, each with a tight spec and an explicit allow-list of files (so agents never
collide on ownership). An executor writes only its named files and reports back; a verifier
compile-checks and exercises pure functions on tiny synthetic frames (never the live API or full
data); a reviewer inspects the diff and ranks findings. Failures loop back to the same executor for a
revision before the orchestrator advances. This is why each stage is small, single-file, and imports
shared contracts from `config.py`/`_harness.py` rather than duplicating them.

## 5. Guarded text-to-SQL flow

```mermaid
sequenceDiagram
    participant Q as NL question (eval_set)
    participant M as Ollama model (T2SQL_MODELS)
    participant G as s4_sql_guard (SELECT-only allow-list)
    participant D as DuckDB (the calculator)
    participant C as Compare vs expected_value
    Q->>M: prompt (schema + question)
    M-->>G: drafted SQL
    alt not SELECT-only / disallowed token
        G-->>C: REJECT — refuse, no execution
    else passes allow-list
        G->>D: execute validated SQL
        D-->>C: result row (all arithmetic happens here)
    end
    C-->>C: within item.tolerance? → pass / fail
```

**Logic and flow:** A natural-language eval question is handed to a local open-weight model with the
table schemas; the model returns candidate SQL and nothing else. That SQL never runs blindly — it
first passes `s4_sql_guard`, which enforces SELECT-only queries against an allow-list of
tables/columns/aggregations; anything with a disallowed token (DDL/DML, multiple statements,
unknown columns) is rejected and scored as a refusal, no execution. Only validated SQL reaches
DuckDB, which performs every computation, and the returned scalar is compared to the item's resolved
`expected_value` under its exact `tolerance` (the two-tier policy — 1e-7 for exact-rational metrics,
0 for counts/strings). The model contributes language; the database remains the sole calculator.
