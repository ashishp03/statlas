"""NLU parser — turns a question into a structured Intent.

THIS is StatMuse's "NLU": Natural Language Understanding. It extracts meaning/intent
and structured slots (player, metric, aggregation, opponent, season, playoff flag) from
a sentence. It does NOT compute anything.

v0 is rule-based (regex + keyword maps) so the project runs with zero API keys.
Study Plan Phase 3: swap `parse` for an LLM function-calling version that returns the
SAME Intent dataclass. The rest of the pipeline won't change — that's the point of
keeping a clean structured interface between language and query.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import duckdb

from statlas.entities.resolver import (
    NICKNAMES,
    TEAM_ALIASES,
    ResolvedPlayer,
    resolve_player,
    resolve_team,
)

# Metric keyword -> column in game_logs.
METRIC_MAP = {
    "points": "pts", "pts": "pts", "ppg": "pts", "scoring": "pts",
    "rebounds": "reb", "reb": "reb", "boards": "reb", "rpg": "reb",
    "assists": "ast", "ast": "ast", "dimes": "ast", "apg": "ast",
    "plus/minus": "plus_minus", "plus minus": "plus_minus",
    "+/-": "plus_minus", "plusminus": "plus_minus",
    "minutes": "min", "min": "min",
}

# Aggregation keywords. Default depends on phrasing (see parse()).
AVG_WORDS = {"average", "avg", "per game", "mean", "ppg", "rpg", "apg"}
TOTAL_WORDS = {"total", "how many", "sum", "combined", "in total"}


@dataclass
class Intent:
    player: ResolvedPlayer | None = None
    metric: str | None = None              # a game_logs column, e.g. "plus_minus"
    aggregation: str = "avg"               # "avg" | "sum"
    opponent_abbr: str | None = None
    season: int | None = None
    playoffs_only: bool = False
    raw_question: str = ""
    # Diagnostics so you can SEE what the NLU understood (great for learning/debugging).
    unresolved: list[str] | None = None

    def is_answerable(self) -> bool:
        return self.player is not None and self.metric is not None


def _find_metric(q: str) -> str | None:
    # Check multi-word/symbol keys first to avoid partial hits.
    for key in sorted(METRIC_MAP, key=len, reverse=True):
        if key in q:
            return METRIC_MAP[key]
    return None


def _find_player_span(q: str, con: duckdb.DuckDBPyConnection) -> ResolvedPlayer | None:
    """Try nickname keys and real names that appear in the text, then fall back to fuzzy."""
    # 1) Known nicknames present as substrings.
    for nick in sorted(NICKNAMES, key=len, reverse=True):
        if nick in q:
            r = resolve_player(nick, con)
            if r:
                return r
    # 2) Real names present as substrings.
    names = [r[0] for r in con.execute("SELECT full_name FROM players").fetchall()]
    for name in sorted(names, key=len, reverse=True):
        if name.lower() in q:
            return resolve_player(name, con)
    # 3) Fuzzy over capitalized tokens (rough heuristic).
    caps = re.findall(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?", q)
    for cand in sorted(caps, key=len, reverse=True):
        r = resolve_player(cand, con)
        if r:
            return r
    return None


def _find_opponent(q: str) -> str | None:
    for alias in sorted(TEAM_ALIASES, key=len, reverse=True):
        # match against "vs okc", "against the thunder", or bare alias
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return resolve_team(alias)
    return None


def parse(question: str, con: duckdb.DuckDBPyConnection) -> Intent:
    """Rule-based NLU. Returns a structured Intent (never a number)."""
    q = f" {question.lower().strip()} "
    unresolved: list[str] = []

    player = _find_player_span(question, con)  # use original case for name matching
    if player is None:
        unresolved.append("player")

    metric = _find_metric(q)
    if metric is None:
        unresolved.append("metric")

    # Aggregation: average vs total. Default to avg, the most common ask.
    aggregation = "avg"
    if any(w in q for w in TOTAL_WORDS) and not any(w in q for w in AVG_WORDS):
        aggregation = "sum"

    opponent = _find_opponent(q)

    season_match = re.search(r"\b(19|20)\d{2}\b", q)
    season = int(season_match.group(0)) if season_match else None

    playoffs_only = any(w in q for w in ("playoff", "playoffs", "postseason", "series"))

    return Intent(
        player=player,
        metric=metric,
        aggregation=aggregation,
        opponent_abbr=opponent,
        season=season,
        playoffs_only=playoffs_only,
        raw_question=question,
        unresolved=unresolved or None,
    )
