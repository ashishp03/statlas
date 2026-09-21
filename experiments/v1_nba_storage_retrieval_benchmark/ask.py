"""ask.py — the MAIN interactive entry point: ask NBA questions against the REAL warehouse.

This is the little end-to-end engine the whole experiment builds toward: it takes a natural-language
question, turns it into a VALIDATED SELECT (rule-based NLU; DuckDB does the math), runs it on the real
30-season warehouse built by S2, and prints the answer WITH the SQL it ran (the "transparency card").

Two ways to run it (uv .venv is active, so plain python works):

    # one-shot
    python experiments/v1_nba_storage_retrieval_benchmark/ask.py "How many points did LeBron average in 2025?"

    # interactive REPL — type questions, Ctrl-D / 'quit' to exit
    python experiments/v1_nba_storage_retrieval_benchmark/ask.py

Prereq: run S2 once so the warehouse exists:
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s2_build_stores.py

Supported question shape (rule-based NLU, no API keys):
    "<how many|what> <metric> did <player> <average|total> in <year> [vs <team>] [in the playoffs]?"
    metrics: points/pts, rebounds/reb, assists/ast, minutes/min, plus-minus
It resolves the player against the real `players` table with rapidfuzz, and REFUSES (no guess) when it
can't find the player or metric. Leaderboard / advanced-metric questions are out of rule-based scope —
that's where the LLM text-to-SQL path (s4) takes over.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # experiment root on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # repo src/ on path

import duckdb

import config

# The SELECT-only guard, entity resolver, and rule-based NLU/query-builder this experiment built are
# now permanent, reusable modules in src/statlas (see that package's docstrings for why).
from statlas.query.sql_guard import validate_sql
from statlas.entities.resolver import best_match_from_candidates
from statlas.nlu.query_builder import build_sql as _build_sql_for_player, find_metric, name_candidates

WAREHOUSE = config.STORES_DIR / "warehouse.duckdb"


def open_con() -> duckdb.DuckDBPyConnection:
    if not WAREHOUSE.exists():
        raise SystemExit(f"warehouse not found at {WAREHOUSE}\n  build it first: "
                         f"python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s2_build_stores.py")
    return duckdb.connect(str(WAREHOUSE), read_only=True)


def resolve_player(question: str, con: duckdb.DuckDBPyConnection) -> tuple[str, int] | None:
    """Fuzzy-resolve a player name from the question against the real players table. Refuse if weak."""
    rows = con.execute("SELECT full_name, player_id FROM players").fetchall()
    choices = {player_id: name for name, player_id in rows}   # {key: display_name} for the resolver
    match = best_match_from_candidates(name_candidates(question), choices, threshold=85)
    if match is None:   # refuse rather than guess
        return None
    _, player_id = match
    return choices[player_id], player_id


def build_sql(question: str, con: duckdb.DuckDBPyConnection):
    """Return (sql, meta_dict) or (None, reason_str). Resolves the player here (needs a live `con`),
    then delegates the actual SQL-building to the warehouse-agnostic statlas.nlu.query_builder."""
    q = f" {question.lower().strip()} "
    if find_metric(q) is None:
        return None, "I couldn't identify a metric (try points/rebounds/assists/minutes/plus-minus)."
    player = resolve_player(question, con)
    if player is None:
        return None, "I couldn't confidently resolve the player (I refuse to guess)."
    name, pid = player
    sql, meta = _build_sql_for_player(question, pid)
    meta["player"] = name
    meta["player_id"] = pid
    return sql, meta


def answer(question: str, con: duckdb.DuckDBPyConnection) -> None:
    sql, meta = build_sql(question, con)
    if sql is None:
        print(f"  🤷 {meta}")           # meta is the refusal reason here
        return
    ok, reason = validate_sql(sql, allowed_tables={"game_logs", "players", "player_season",
                                                   "bbref_advanced", "player_crosswalk"})
    if not ok:
        print(f"  ⛔ SQL blocked by guard: {reason}")
        return
    row = con.execute(sql).fetchone()
    value, games = (row[0], row[1]) if row else (None, 0)
    if value is None or games == 0:
        print(f"  🤷 No rows matched (player={meta['player']}, season={meta['season']}). "
              f"Data covers game logs {config.GAMELOG_YEARS[0]}-{config.GAMELOG_YEARS[-1]}.")
        return
    span = []
    if meta["season"]:
        span.append(str(meta["season"]))
    if meta["opponent"]:
        span.append(f"vs {meta['opponent']}")
    if meta["playoffs"]:
        span.append("playoffs")
    label = {"AVG": "per game", "SUM": "total"}[meta["agg"]]
    pretty = round(value, 2)
    print(f"  🏀 {meta['player']} — {pretty} {meta['metric']} ({label})"
          f"{(' ' + ', '.join(span)) if span else ''}  over {games} game(s)")
    print(f"     SQL: {sql}")


REPL_HELP = (
    "Ask an NBA question, e.g.:\n"
    "  How many points did LeBron James average in 2025?\n"
    "  total rebounds for Nikola Jokic in 2024\n"
    "  assists for Stephen Curry vs OKC in 2025\n"
    "  what did Giannis average in the playoffs in 2025\n"
    "Type 'quit' or Ctrl-D to exit."
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ask NBA questions against the real statlas warehouse.")
    ap.add_argument("question", nargs="*", help="a question; omit for interactive REPL")
    args = ap.parse_args()
    con = open_con()
    n = con.execute("SELECT COUNT(*) FROM game_logs").fetchone()[0]
    if args.question:
        answer(" ".join(args.question), con)
        return
    print(f"statlas ask — {n:,} game-log rows loaded. {REPL_HELP}\n")
    while True:
        try:
            q = input("ask> ").strip()
        except EOFError:
            print()
            break
        if not q:
            continue
        if q.lower() in {"quit", "exit", ":q"}:
            break
        answer(q, con)


if __name__ == "__main__":
    main()
