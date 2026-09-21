"""Rule-based NLU -> validated SQL over the stable `game_logs` schema.

Moved here from experiments/v1_nba_storage_retrieval_benchmark/ask.py, which proved this pattern
end-to-end against the real 30-season warehouse: it takes a natural-language question, resolves a
metric + optional filters, and builds a SELECT against `game_logs` — the exact schema the root
CLAUDE.md pins as byte-stable so upgrades never ripple downstream:

    player_id, season, game_date, opponent_abbr, is_playoff, min, pts, reb, ast, plus_minus

This module is warehouse-agnostic on purpose: it never opens a connection or resolves a player
name itself (that's `statlas.entities.resolver`'s job, given a live DB's own `players` table).
`build_sql` takes an already-resolved `player_id`, so it is a pure function you can unit-test with
no DuckDB, no on-disk warehouse, nothing — matching the root architecture rule that NLU/parsing
never touches data, it only produces the query the database will run.

Any SQL this builds MUST still pass `statlas.query.sql_guard.validate_sql` before execution —
this module only builds candidate SQL; it is not the safety boundary.
"""
from __future__ import annotations

import re

METRIC_MAP = {
    "points": "pts", "point": "pts", "pts": "pts", "ppg": "pts", "scoring": "pts", "scored": "pts",
    "rebounds": "reb", "rebound": "reb", "boards": "reb", "reb": "reb", "rpg": "reb",
    "assists": "ast", "assist": "ast", "dimes": "ast", "ast": "ast", "apg": "ast",
    "minutes": "min", "minute": "min", "min": "min", "mpg": "min",
    "plus minus": "plus_minus", "plus/minus": "plus_minus", "plusminus": "plus_minus", "+/-": "plus_minus",
}
AVG_WORDS = ("average", "avg", "per game", "mean", "ppg", "rpg", "apg", "mpg")
TOTAL_WORDS = ("total", "combined", "in total", "altogether", "sum of")
# Small opponent alias set (extend freely) — kept here rather than a DB table because it maps
# free-text aliases to the fixed team_abbr allow-list, which is a language-layer concern.
TEAM_ALIASES = {
    "okc": "OKC", "thunder": "OKC", "lakers": "LAL", "lal": "LAL", "warriors": "GSW", "gsw": "GSW",
    "celtics": "BOS", "boston": "BOS", "bos": "BOS", "nuggets": "DEN", "den": "DEN", "bucks": "MIL",
    "heat": "MIA", "knicks": "NYK", "suns": "PHX", "mavs": "DAL", "mavericks": "DAL",
}

# Capitalized-span regex used to pull player-name candidates out of a free-text question, for
# callers that then hand the candidates to statlas.entities.resolver.best_match_from_candidates.
NAME_CANDIDATE_RE = re.compile(r"[A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+)*")


def find_metric(q: str) -> str | None:
    for key in sorted(METRIC_MAP, key=len, reverse=True):
        if key.replace(" ", "").replace("/", "").replace("+", "").replace("-", "").isalnum():
            if re.search(rf"\b{re.escape(key)}\b", q):
                return METRIC_MAP[key]
        elif key in q:
            return METRIC_MAP[key]
    return None


def find_opponent(q: str) -> str | None:
    for alias in sorted(TEAM_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return TEAM_ALIASES[alias]
    return None


def name_candidates(question: str) -> list[str]:
    """Plausible Capitalized-span player-name candidates from free text, longest first."""
    caps = NAME_CANDIDATE_RE.findall(question)
    return sorted(set(caps), key=len, reverse=True) or [question]


def build_sql(question: str, player_id: int) -> tuple[str, dict] | tuple[None, str]:
    """Build a `game_logs` SELECT for `question` about the already-resolved `player_id`.

    Returns (sql, meta) on success or (None, reason) when the question doesn't name a metric this
    rule-based layer understands. All inlined values are type-checked ints or allow-listed tokens
    (season is regex-matched to \\d{4}, opponent comes from TEAM_ALIASES, player_id is the caller's
    already-resolved int) — there is no injection surface, and `sql_guard.validate_sql` re-validates
    before anything executes.
    """
    q = f" {question.lower().strip()} "
    metric = find_metric(q)
    if metric is None:
        return None, "I couldn't identify a metric (try points/rebounds/assists/minutes/plus-minus)."

    agg = "AVG"
    if any(w in q for w in TOTAL_WORDS) and not any(w in q for w in AVG_WORDS):
        agg = "SUM"

    where = [f"player_id = {int(player_id)}"]
    ym = re.search(r"\b(19|20)\d{2}\b", q)
    season = int(ym.group(0)) if ym else None
    if season is not None:
        where.append(f"season = {season}")
    opp = find_opponent(q)
    if opp is not None:
        where.append(f"opponent_abbr = '{opp}'")           # opp is from the fixed TEAM_ALIASES allow-list
    playoffs = any(w in q for w in ("playoff", "playoffs", "postseason", "series"))
    include_all = any(w in q for w in ("career", "including playoff", "all games", "regular and playoff"))
    if playoffs:
        where.append("is_playoff = 1")
    elif not include_all:
        where.append("is_playoff = 0")   # default: regular season (matches convention + the eval set)

    sql = (f"SELECT {agg}({metric}) AS answer, COUNT(*) AS games "
           f"FROM game_logs WHERE {' AND '.join(where)}")
    meta = {"metric": metric, "agg": agg, "season": season, "opponent": opp, "playoffs": playoffs}
    return sql, meta


# --------------------------------------------------------------------------- self-test
def _selftest() -> int:
    fails = 0

    ok, reason = find_metric(" how many points did lebron average in 2025 "), "pts"
    fails += 0 if ok == reason else 1
    print(f"  [{'PASS' if ok == reason else 'FAIL'}] find_metric -> {ok!r}")

    ok = find_opponent(" assists for curry vs okc in 2025 ")
    fails += 0 if ok == "OKC" else 1
    print(f"  [{'PASS' if ok == 'OKC' else 'FAIL'}] find_opponent -> {ok!r}")

    sql, meta = build_sql("How many points did LeBron James average in 2025?", player_id=2544)
    checks = [
        sql is not None,
        "player_id = 2544" in (sql or ""),
        "season = 2025" in (sql or ""),
        "is_playoff = 0" in (sql or ""),
        meta.get("metric") == "pts",
        meta.get("agg") == "AVG",
    ]
    ok = all(checks)
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] build_sql basic -> sql={sql!r} meta={meta!r}")

    sql2, reason2 = build_sql("tell me about the weather", player_id=2544)
    ok2 = sql2 is None and isinstance(reason2, str)
    fails += 0 if ok2 else 1
    print(f"  [{'PASS' if ok2 else 'FAIL'}] build_sql refuses unknown metric -> {reason2!r}")

    total = 4
    print(f"{total - fails}/{total} cases behaved as expected" + ("" if fails == 0 else f"  ({fails} UNEXPECTED)"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
