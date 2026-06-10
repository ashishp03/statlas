"""Query planner — turns a structured Intent into VALIDATED SQL.

This is the safe, deterministic version of "text-to-SQL". Because the Intent is already
structured, we build SQL from a fixed template with an allow-list of columns. There is no
free-form model output here, so there's nothing to inject and nothing to hallucinate.

Study Plan Phase 4: you can let an LLM draft SQL directly for queries too complex for the
template — but ALWAYS run it through a validator like `assert_safe` before executing.
"""
from __future__ import annotations

from statlas.nlu.parser import Intent

ALLOWED_METRICS = {"pts", "reb", "ast", "plus_minus", "min"}
ALLOWED_AGG = {"avg": "AVG", "sum": "SUM"}


class PlanError(Exception):
    pass


def assert_safe(metric: str, aggregation: str) -> None:
    """Allow-list validation. Reject anything not explicitly permitted."""
    if metric not in ALLOWED_METRICS:
        raise PlanError(f"metric '{metric}' is not allowed")
    if aggregation not in ALLOWED_AGG:
        raise PlanError(f"aggregation '{aggregation}' is not allowed")


def build_sql(intent: Intent) -> tuple[str, list]:
    """Return (sql, params). Parameterized to avoid any injection."""
    if not intent.is_answerable():
        raise PlanError(f"intent not answerable; unresolved={intent.unresolved}")

    assert_safe(intent.metric, intent.aggregation)
    agg_fn = ALLOWED_AGG[intent.aggregation]

    where = ["player_id = ?"]
    params: list = [intent.player.player_id]

    if intent.opponent_abbr:
        where.append("opponent_abbr = ?")
        params.append(intent.opponent_abbr)
    if intent.season is not None:
        where.append("season = ?")
        params.append(intent.season)
    if intent.playoffs_only:
        where.append("is_playoff = 1")

    # metric/agg are allow-listed above, so safe to inline. Filters are parameterized.
    sql = (
        f"SELECT {agg_fn}({intent.metric}) AS value, COUNT(*) AS games "
        f"FROM game_logs WHERE {' AND '.join(where)}"
    )
    return sql, params
