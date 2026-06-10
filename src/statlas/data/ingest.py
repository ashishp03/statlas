"""Data layer — builds the DuckDB stats warehouse.

Two modes:
  1. SEED (default): loads the small sample CSVs in seed/. Runs instantly, no network.
     The sample data is ILLUSTRATIVE — invented numbers so the engine has something to query.
  2. nba_api (Study Plan Phase 4): swap in real NBA data. Stub provided in `ingest_nba_api`.

DuckDB is an embedded OLAP database: one file, no server, very fast aggregations.
This is the "calculator" — every exact stat is computed here, never by an LLM.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import duckdb

SEED_DIR = Path(__file__).parent / "seed"
# The DB is a generated artifact (gitignored). Default to a temp path so it works on any
# filesystem; override with STATLAS_DB to keep it in the repo locally if you prefer.
DEFAULT_DB = os.environ.get("STATLAS_DB", str(Path(tempfile.gettempdir()) / "statlas.duckdb"))


def connect(db_path: str = DEFAULT_DB) -> duckdb.DuckDBPyConnection:
    """Open (or create) the DuckDB warehouse."""
    return duckdb.connect(db_path)


def build_from_seed(db_path: str = DEFAULT_DB) -> str:
    """Create tables and load the sample CSVs. Returns the db path."""
    con = connect(db_path)
    players_csv = (SEED_DIR / "players.csv").as_posix()
    logs_csv = (SEED_DIR / "game_logs.csv").as_posix()

    con.execute("DROP TABLE IF EXISTS players;")
    con.execute("DROP TABLE IF EXISTS game_logs;")

    # read_csv_auto infers types; we materialize into real tables.
    con.execute(f"CREATE TABLE players AS SELECT * FROM read_csv_auto('{players_csv}');")
    con.execute(f"CREATE TABLE game_logs AS SELECT * FROM read_csv_auto('{logs_csv}');")

    n_players = con.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    n_logs = con.execute("SELECT COUNT(*) FROM game_logs").fetchone()[0]
    con.close()
    print(f"[statlas] Built {db_path} from seed: {n_players} players, {n_logs} game logs.")
    return db_path


def ingest_nba_api(*args, **kwargs):  # noqa: D401
    """STUB — Study Plan Phase 4.

    Replace seed data with real data using the free `nba_api` package, e.g.:

        from nba_api.stats.endpoints import playergamelog
        log = playergamelog.PlayerGameLog(player_id=1629029, season='2024-25')
        df = log.get_data_frames()[0]
        # ...normalize columns to match the game_logs schema, then load into DuckDB.

    Keep the SAME schema (player_id, season, game_date, opponent_abbr, is_playoff,
    min, pts, reb, ast, plus_minus) so the rest of the pipeline doesn't change.
    """
    raise NotImplementedError("Wire up nba_api here during Study Plan Phase 4.")


if __name__ == "__main__":
    build_from_seed()
