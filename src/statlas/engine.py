"""Engine — orchestrates the full pipeline and composes a human answer.

    question
      -> nlu.parse           (language -> structured Intent)
      -> query.build_sql     (Intent -> validated SQL)
      -> query.run           (SQL -> exact number)   <-- the only math
      -> compose             (number -> sentence + answer card)

The "answer card" deliberately exposes the SQL and the games used, so you (and the user)
can always see HOW the number was produced. Transparency is what makes a stats engine
trustworthy instead of just another chatbot that sounds confident.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from statlas.data.ingest import DEFAULT_DB, build_from_seed
from statlas.nlu.parser import Intent, parse
from statlas.query.executor import QueryResult, run
from statlas.query.planner import PlanError, build_sql

METRIC_LABEL = {
    "pts": "points", "reb": "rebounds", "ast": "assists",
    "plus_minus": "plus/minus", "min": "minutes",
}


@dataclass
class Answer:
    text: str
    value: float | None = None
    intent: Intent | None = None
    result: QueryResult | None = None
    ok: bool = True
    # A tiny structured "card" you can later hand to a charting layer (Study Plan Phase 7).
    card: dict = field(default_factory=dict)


def _compose(intent: Intent, result: QueryResult) -> str:
    label = METRIC_LABEL.get(intent.metric, intent.metric)
    agg = "averaged" if intent.aggregation == "avg" else "had a total of"
    scope = []
    if intent.playoffs_only:
        scope.append("in the playoffs")
    if intent.opponent_abbr:
        scope.append(f"vs {intent.opponent_abbr}")
    if intent.season is not None:
        scope.append(f"in {intent.season}")
    scope_str = (" " + " ".join(scope)) if scope else ""

    if result.value is None or result.games == 0:
        return f"No matching games found for {intent.player.full_name}{scope_str}."

    val = round(result.value, 1)
    return (
        f"{intent.player.full_name} {agg} {val} {label}{scope_str} "
        f"(across {result.games} game{'s' if result.games != 1 else ''})."
    )


def ask(question: str, con: duckdb.DuckDBPyConnection | None = None) -> Answer:
    """Answer a natural-language sports question."""
    own_con = False
    if con is None:
        con = duckdb.connect(DEFAULT_DB)
        own_con = True
    try:
        intent = parse(question, con)
        if not intent.is_answerable():
            missing = ", ".join(intent.unresolved or ["something"])
            return Answer(
                text=f"I couldn't understand the {missing} in that question. "
                     f"Try naming a player and a stat (e.g. \"Wemby's +/- vs OKC in the playoffs\").",
                intent=intent,
                ok=False,
            )
        sql, params = build_sql(intent)
        result = run(con, sql, params)
        text = _compose(intent, result)
        card = {
            "player": intent.player.full_name,
            "metric": METRIC_LABEL.get(intent.metric, intent.metric),
            "aggregation": intent.aggregation,
            "value": None if result.value is None else round(result.value, 2),
            "games": result.games,
            "filters": {
                "opponent": intent.opponent_abbr,
                "season": intent.season,
                "playoffs_only": intent.playoffs_only,
            },
            "sql": result.sql,
        }
        return Answer(text=text, value=result.value, intent=intent, result=result, card=card)
    except PlanError as e:
        return Answer(text=f"I understood the question but couldn't build a safe query: {e}", ok=False)
    finally:
        if own_con:
            con.close()


def ensure_db():
    """Build the seed DB if it doesn't exist yet."""
    import os
    if not os.path.exists(DEFAULT_DB):
        build_from_seed()
