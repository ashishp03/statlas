"""Entity resolver — maps human references to canonical IDs.

"Wemby", "the Joker", "KD" -> a real player_id.  This is HALF of StatMuse's accuracy.

v0 approach (Study Plan Phase 2): a nickname dictionary + fuzzy matching.
Later you can upgrade to an embedding-based / NER linker, but start here — a good
dictionary beats a fancy model for the head of the distribution.
"""
from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process

import duckdb

# Hand-curated nicknames -> canonical full name. Extend freely.
NICKNAMES = {
    "wemby": "Victor Wembanyama",
    "the alien": "Victor Wembanyama",
    "lebron": "LeBron James",
    "king james": "LeBron James",
    "bron": "LeBron James",
    "the joker": "Nikola Jokic",
    "joker": "Nikola Jokic",
    "kd": "Kevin Durant",
    "durantula": "Kevin Durant",
    "steph": "Stephen Curry",
    "chef curry": "Stephen Curry",
}

# Common team-name aliases -> abbreviation used in game_logs.opponent_abbr / players.team_abbr
TEAM_ALIASES = {
    "okc": "OKC", "thunder": "OKC", "oklahoma city": "OKC",
    "lakers": "LAL", "lal": "LAL", "los angeles lakers": "LAL",
    "nuggets": "DEN", "denver": "DEN", "den": "DEN",
    "warriors": "GSW", "golden state": "GSW", "gsw": "GSW",
    "suns": "PHX", "phoenix": "PHX", "phx": "PHX",
    "wolves": "MIN", "timberwolves": "MIN", "min": "MIN",
    "heat": "MIA", "miami": "MIA",
    "celtics": "BOS", "boston": "BOS",
    "bulls": "CHI", "chicago": "CHI",
    "knicks": "NYK", "new york": "NYK",
    "spurs": "SAS", "san antonio": "SAS",
}


@dataclass
class ResolvedPlayer:
    player_id: int
    full_name: str
    score: float  # match confidence 0-100


def _all_players(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    rows = con.execute("SELECT full_name, player_id FROM players").fetchall()
    return {name: pid for name, pid in rows}


def resolve_player(text: str, con: duckdb.DuckDBPyConnection, min_score: float = 75.0) -> ResolvedPlayer | None:
    """Find the best-matching player for a free-text reference.

    Strategy: (1) nickname lookup, (2) fuzzy match against real names.
    Returns None if nothing clears `min_score` — i.e. the engine should say "I don't know"
    rather than guess. Refusing to guess is a feature, not a bug.
    """
    if not text:
        return None
    key = text.strip().lower()
    players = _all_players(con)

    # 1) Exact nickname hit -> canonical name.
    canonical = NICKNAMES.get(key)
    if canonical and canonical in players:
        return ResolvedPlayer(players[canonical], canonical, 100.0)

    # 2) Fuzzy match the raw text against full names.
    match = process.extractOne(text, list(players.keys()), scorer=fuzz.WRatio)
    if match and match[1] >= min_score:
        name = match[0]
        return ResolvedPlayer(players[name], name, float(match[1]))

    return None


def resolve_team(text: str) -> str | None:
    """Map a team reference to its abbreviation, or None."""
    if not text:
        return None
    return TEAM_ALIASES.get(text.strip().lower())
