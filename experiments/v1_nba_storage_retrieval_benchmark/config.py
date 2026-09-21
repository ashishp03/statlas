"""Shared configuration + contracts for experiment v1 (NBA storage/retrieval benchmark).

Every pipeline stage imports this module. It is the SINGLE SOURCE OF TRUTH for:
  - which seasons we pull (the "modern era" scope, Decision D2 — REVISIT later)
  - on-disk paths (raw cache, store artifacts, results)
  - the canonical `game_logs` schema (kept byte-stable with src/statlas seed)
  - the min-games qualifier for leaderboards (correctness rule)
  - the text-to-SQL model shortlist

Run stages from the repo root, e.g.:
    uv run python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s1_pull.py
"""
from __future__ import annotations

import pathlib

# --- Paths -------------------------------------------------------------------
EXP_ROOT = pathlib.Path(__file__).resolve().parent            # v1_nba_storage_retrieval_benchmark/
DATA_DIR = EXP_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STORES_DIR = DATA_DIR / "stores"
RESULTS_DIR = EXP_ROOT / "results"
FIGS_DIR = RESULTS_DIR / "figs"
EVAL_SET = EXP_ROOT / "eval_set.json"

for _d in (RAW_DIR, STORES_DIR, RESULTS_DIR, FIGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Scope (Decision D2 — modern era only; REVISIT before productionizing) ---
# Seasons are identified by their END year: 2025 == the "2024-25" season.
AGG_START_YEAR = 1997       # 1996-97 -> first modern-era season (LeagueDash floor)
AGG_END_YEAR = 2026         # 2025-26 -> latest complete season as of 2026-07
AGG_SEASON_YEARS = list(range(AGG_START_YEAR, AGG_END_YEAR + 1))   # 30 seasons of aggregates

# Full game logs are heavier; pull a recent window for the row-wise workloads.
GAMELOG_YEARS = list(range(2022, AGG_END_YEAR + 1))               # 2021-22 .. 2025-26 (5 seasons)

# Scale-test payloads: one season each.
SCALE_SHOTCHART_YEAR = 2025     # 2024-25 league-wide shot chart (~100k+ rows)
SCALE_PBP_YEAR = 2025           # one 2024-25 game's play-by-play (V3)
BBREF_YEAR = 2025               # 2024-25 advanced totals (PER/BPM/VORP/WS)

# --- Canonical schema (MUST match src/statlas/data/seed/game_logs.csv) -------
GAME_LOGS_COLUMNS = [
    "player_id", "season", "game_date", "opponent_abbr", "is_playoff",
    "min", "pts", "reb", "ast", "plus_minus",
]
PLAYERS_COLUMNS = ["player_id", "full_name", "team_abbr"]

# Curated season-aggregate columns (drop the ~30 *_RANK mirror cols from nba_api).
PLAYER_SEASON_BASE_COLS = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "AGE", "GP", "MIN",
    "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT",
    "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "PF", "PTS", "PLUS_MINUS",
]
PLAYER_SEASON_ADV_COLS = [
    "PLAYER_ID", "OFF_RATING", "DEF_RATING", "NET_RATING", "USG_PCT",
    "TS_PCT", "EFG_PCT", "AST_PCT", "REB_PCT", "PACE", "PIE", "POSS",
]

# --- Reliability rule (correctness) ------------------------------------------
MIN_GAMES_QUALIFIER = 58     # ~70% of 82; every leaderboard must HAVING gp >= this

# --- nba_api politeness ------------------------------------------------------
API_PAUSE_S = 0.6            # sleep between live calls (respect stats.nba.com throttling)
API_TIMEOUT_S = 30

# --- Storage candidates (S2/S3) — "test many options, not just DuckDB/Parquet"
STORE_FORMATS = [
    "csv",                  # baseline (current cache format)
    "parquet_single",       # columnar file, one file/table
    "parquet_partitioned",  # Hive-partitioned by season -> partition pruning
    "feather",              # Arrow IPC, zero-copy mmap
    "duckdb",               # embedded OLAP engine (the incumbent "calculator")
    "sqlite",               # B-tree row-store (OLTP reference point), + index
    "polars_mem",           # in-memory dataframe (no-disk upper bound)
    "lancedb",              # columnar + vector hybrid
]

# --- Text-to-SQL model shortlist (S4) — free/open weights, Ollama tags -------
T2SQL_MODELS = [
    "qwen2.5-coder:7b",     # Apache-2.0, strong code+SQL (default)
    "sqlcoder:7b",          # defog, purpose-built text-to-SQL
    "llama3.1:8b",          # general-purpose baseline
]
EMBED_MODEL = "nomic-embed-text"   # Ollama embedding model for S5 (fallback: all-MiniLM-L6-v2)
OLLAMA_HOST = "http://127.0.0.1:11434"

# --- Bench knobs -------------------------------------------------------------
BENCH_REPS = 25
BENCH_WARMUP = 3
