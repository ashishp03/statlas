"""SQL safety guard — the allow-list gate every model/free SQL must pass before touching a warehouse.

Moved here from experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_sql_guard.py, where it
was built and battle-tested (see that experiment's docs/findings/DECISIONS.md for the original
design rationale). It is genuinely permanent, branch-agnostic infrastructure: `validate_sql` never
assumed anything about which storage format was being benchmarked, so it lives in src/ rather than
staying scoped to the one experiment that happened to build it first. `s4_text_to_sql.py` and
`ask.py` in that experiment now import it from here instead of holding their own copy.

NON-NEGOTIABLE (per the root CLAUDE.md architecture): no model-drafted or free-text SQL touches a
database until it clears `validate_sql`. The guard is intentionally paranoid and layered:

  1. one statement only         — strip a single trailing ';'; reject if any ';' remains
  2. read path only             — must start with SELECT or WITH
  3. no DML/DDL/side-effects    — reject a word-boundary hit on a banned keyword
  4. allow-listed tables only   — EVERY base relation in a FROM/JOIN position must be a known
                                  table (or a CTE defined in this same query). A paren/keyword-aware
                                  scan walks the whole comma-separated relation list — `FROM a, b`
                                  checks BOTH a and b — so table functions like read_parquet('/etc/...')
                                  and system catalogs (sqlite_master, pg_tables, information_schema.*)
                                  cannot hide as the 2nd+ entry of an implicit-join list
  5. it actually parses         — EXPLAIN on an in-memory DuckDB holding the five empty tables,
                                  with external file/network access disabled, as the final check

The module owns a default five-table `SCHEMA_DDL` matching the stable `game_logs` contract (see
CLAUDE.md's "game_logs schema stays byte-stable" decision) — also reused as the prompt schema by
s4_text_to_sql. Override the schema via `validate_sql(sql, allowed_tables=..., ...)` for a
different one. It needs NO on-disk data and is fully self-testing — run it directly:

    python src/statlas/query/sql_guard.py
"""
from __future__ import annotations

import re

# --- Allow-list --------------------------------------------------------------
ALLOWED_TABLES = {
    "game_logs",
    "players",
    "player_season",
    "bbref_advanced",
    "player_crosswalk",
}

# --- Canonical empty-table DDL (the ONLY schema the guard/parse step knows about) ------------
# Columns mirror data/raw parquet + eval_set.json meta. Reused verbatim by s4_text_to_sql as the
# prompt schema, so models and the guard agree on exactly one schema. "min" is quoted (it collides
# with the MIN() aggregate as a bare identifier in some engines).
SCHEMA_DDL = [
    'CREATE TABLE game_logs ('
    ' player_id BIGINT, season INTEGER, game_date DATE, opponent_abbr VARCHAR,'
    ' is_playoff INTEGER, "min" DOUBLE, pts DOUBLE, reb DOUBLE, ast DOUBLE, plus_minus DOUBLE'
    ')',
    'CREATE TABLE players (player_id BIGINT, full_name VARCHAR, team_abbr VARCHAR)',
    'CREATE TABLE player_season ('
    ' player_id BIGINT, player_name VARCHAR, team_abbr VARCHAR, season INTEGER, season_type VARCHAR,'
    ' age DOUBLE, gp INTEGER, "min" DOUBLE, pts DOUBLE, reb DOUBLE, ast DOUBLE, oreb DOUBLE, dreb DOUBLE,'
    ' stl DOUBLE, blk DOUBLE, tov DOUBLE, pf DOUBLE, fgm DOUBLE, fga DOUBLE, fg_pct DOUBLE,'
    ' fg3m DOUBLE, fg3a DOUBLE, fg3_pct DOUBLE, ftm DOUBLE, fta DOUBLE, ft_pct DOUBLE, plus_minus DOUBLE,'
    ' off_rating DOUBLE, def_rating DOUBLE, net_rating DOUBLE, usg_pct DOUBLE, ts_pct DOUBLE,'
    ' efg_pct DOUBLE, ast_pct DOUBLE, reb_pct DOUBLE, pace DOUBLE, pie DOUBLE, poss DOUBLE'
    ')',
    'CREATE TABLE bbref_advanced ('
    ' bbref_slug VARCHAR, full_name VARCHAR, season INTEGER, per DOUBLE, bpm DOUBLE, vorp DOUBLE, ws DOUBLE'
    ')',
    'CREATE TABLE player_crosswalk ('
    ' canonical_id BIGINT, nba_player_id BIGINT, bbref_slug VARCHAR, bdl_id BIGINT, full_name VARCHAR'
    ')',
]
SCHEMA_DDL_TEXT = ";\n".join(SCHEMA_DDL) + ";"   # single string for text-to-SQL prompts

# Statements/keywords that mutate, load code, or touch the filesystem. Word-boundary + case-insensitive.
_BANNED = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "COPY",
    "PRAGMA", "INSTALL", "LOAD", "REPLACE", "GRANT", "TRUNCATE",
]
_BANNED_RE = re.compile(r"\b(" + "|".join(_BANNED) + r")\b", re.IGNORECASE)

# CTE names introduced by  WITH [RECURSIVE] name AS (   or   , name AS (
_CTE_RE = re.compile(r'(?is)(?:\bWITH\b(?:\s+RECURSIVE\b)?|,)\s+([A-Za-z_]\w*)\s+AS\s*\(')
_START_RE = re.compile(r"(?is)^\s*(select|with)\b")

# Characters that may appear in a bare (unquoted) SQL identifier.
_IDENT_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$"
)
# Keywords that END a FROM relation-list at the current paren depth: after one of these, a
# same-depth comma belongs to GROUP BY / ORDER BY / a set-op / etc., NOT to the relation list.
_FROM_TERMINATORS = frozenset({
    "WHERE", "GROUP", "HAVING", "ORDER", "LIMIT", "OFFSET", "WINDOW",
    "QUALIFY", "UNION", "INTERSECT", "EXCEPT", "FETCH", "RETURNING",
})
# Schemas we refuse even when a relation is schema-qualified (defense-in-depth over the allow-list,
# since the membership test only inspects the final dotted segment).
_DENIED_SCHEMAS = frozenset({"information_schema", "pg_catalog"})


def _read_relation_token(s: str, i: int) -> tuple[str, int]:
    """Read one (possibly quoted, possibly schema-qualified) identifier starting at s[i].

    Consumes bare word chars, "double"/`back`/[bracket] quoted segments, and dots joining them
    (so `information_schema.tables` comes back as ONE token). Returns (token, next_index).
    """
    n = len(s)
    out: list[str] = []
    while i < n:
        c = s[i]
        if c == '"':
            out.append('"')
            i += 1
            while i < n:
                if s[i] == '"':
                    if i + 1 < n and s[i + 1] == '"':   # escaped "" inside a quoted identifier
                        out.append('""')
                        i += 2
                        continue
                    out.append('"')
                    i += 1
                    break
                out.append(s[i])
                i += 1
        elif c == '`':
            out.append(c)
            i += 1
            while i < n and s[i] != '`':
                out.append(s[i])
                i += 1
            if i < n:
                out.append('`')
                i += 1
        elif c == '[':
            out.append(c)
            i += 1
            while i < n and s[i] != ']':
                out.append(s[i])
                i += 1
            if i < n:
                out.append(']')
                i += 1
        elif c in _IDENT_CHARS:
            while i < n and s[i] in _IDENT_CHARS:
                out.append(s[i])
                i += 1
        else:
            break
        if i < n and s[i] == '.':      # schema/catalog qualifier — keep reading the next segment
            out.append('.')
            i += 1
            continue
        break
    return "".join(out), i


def _iter_relations(san: str):
    """Yield EVERY base-relation identifier in a FROM/JOIN position of `san` (the comment-stripped,
    string-blanked SQL) — including comma-separated relation lists (`FROM a, b` yields a AND b) and
    relations inside nested subqueries / set-ops.

    Derived tables (`FROM (SELECT ...) x`) are NOT yielded as relations; the walk continues into the
    subquery, so its own inner FROM relations are scanned. Paren depth is tracked so commas inside
    function calls / IN-lists / GROUP BY are never mistaken for relation-list separators.
    """
    n = len(san)
    depth = 0
    from_active: set[int] = set()   # paren depths currently inside a FROM relation-list
    expect = False                  # True => the next relation token must be recorded/checked
    i = 0
    while i < n:
        c = san[i]
        if c.isspace():
            i += 1
        elif c == "(":
            expect = False          # a '(' where a relation is expected is a derived table
            depth += 1
            i += 1
        elif c == ")":
            from_active.discard(depth)
            depth = depth - 1 if depth > 0 else 0
            expect = False
            i += 1
        elif c == ",":
            if depth in from_active:
                expect = True       # another relation follows in this comma list
            i += 1
        elif c == '"' or c == "`" or c == "[" or c == "_" or c.isalpha():
            tok, i = _read_relation_token(san, i)
            if expect:
                yield tok
                expect = False
            else:
                up = tok.upper()
                if up == "FROM" or up == "JOIN":
                    from_active.add(depth)
                    expect = True
                elif up in _FROM_TERMINATORS:
                    from_active.discard(depth)
        else:
            i += 1                  # operators, digits, blanked '' literals, etc.


def _sanitize(sql: str) -> str:
    """Return `sql` with comments removed and single-quoted string *contents* blanked.

    Used only for the STRUCTURAL checks (statement count, start token, banned-keyword scan, table
    scan) so a ';' or the word DROP hiding inside a string literal or a `-- comment` can never trip
    a false reject — nor be used to smuggle something past us. Double-quoted identifiers are kept
    intact (they may name a table). The EXPLAIN step still runs against the ORIGINAL sql.
    """
    out: list[str] = []
    i, n = 0, len(sql)
    NORMAL, SQ, DQ, LINE, BLOCK = 0, 1, 2, 3, 4
    state = NORMAL
    while i < n:
        c = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if state == NORMAL:
            if c == "'":
                state = SQ
                out.append("'")
            elif c == '"':
                state = DQ
                out.append('"')
            elif c == "-" and nxt == "-":
                state = LINE
                i += 2
                continue
            elif c == "/" and nxt == "*":
                state = BLOCK
                i += 2
                continue
            else:
                out.append(c)
        elif state == SQ:
            if c == "'":
                if nxt == "'":          # escaped '' inside the string
                    i += 2
                    continue
                state = NORMAL
                out.append("'")
            # else: drop the string content
        elif state == DQ:
            out.append(c)
            if c == '"':
                if nxt == '"':          # escaped "" inside a quoted identifier
                    out.append('"')
                    i += 2
                    continue
                state = NORMAL
        elif state == LINE:
            if c == "\n":
                state = NORMAL
                out.append("\n")
        elif state == BLOCK:
            if c == "*" and nxt == "/":
                state = NORMAL
                i += 2
                continue
        i += 1
    return "".join(out)


def _explain_ok(sql: str) -> tuple[bool, str]:
    """Final gate: does DuckDB parse `sql` as a pure SELECT over the five empty tables?

    DuckDB is imported defensively — if it is unavailable we degrade to static-only checks rather
    than crash (the layers above already enforce SELECT-only + allow-listed tables). External file
    and network access are disabled so binding a table function can never read a real file.
    """
    try:
        import duckdb
    except Exception as e:  # noqa: BLE001 - optional dep, degrade gracefully
        return True, f"ok (duckdb unavailable, static-only: {type(e).__name__})"
    con = None
    try:
        con = duckdb.connect(":memory:")
        try:
            con.execute("SET enable_external_access=false")  # belt-and-suspenders
        except Exception:  # noqa: BLE001 - older/newer duckdb may name it differently
            pass
        for ddl in SCHEMA_DDL:
            con.execute(ddl)
        con.execute("EXPLAIN " + sql)   # plans only; never executes / mutates
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, f"parse/explain failed: {type(e).__name__}: {str(e)[:120]}"
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:  # noqa: BLE001
                pass


def validate_sql(sql, allowed_tables=ALLOWED_TABLES, allowed_columns=None):
    """Validate a candidate SQL string. Returns (ok: bool, reason: str).

    `allowed_tables` overrides the default allow-list (identifiers are compared case-insensitively;
    CTE names defined in the query are auto-allowed). `allowed_columns` is accepted for API stability
    and forward-compat — column safety is currently enforced by the EXPLAIN step, which binds every
    referenced column against the fixed empty schema and fails on anything unknown.

    The FROM/JOIN scan (`_iter_relations`) is paren- and keyword-aware and walks the FULL
    comma-separated relation list, so an implicit join (`FROM a, b`) checks every relation, not
    just the first — a system catalog / table function cannot ride in as a 2nd+ list entry.

    KNOWN LIMITATION: the scan is token-based (not a full SQL parser), so the SQL-standard
    `EXTRACT(... FROM col)` / `SUBSTRING(... FROM ...)` / `TRIM(... FROM ...)` read `col` as a table
    and are conservatively rejected. Our workload filters on integer `season` directly, so this does
    not affect it.
    """
    if not isinstance(sql, str):
        return False, "sql must be a string"
    raw = sql.strip()
    if not raw:
        return False, "empty sql"
    if raw.endswith(";"):
        raw = raw[:-1].rstrip()        # strip exactly one trailing statement terminator

    san = _sanitize(raw).strip()
    if not san:
        return False, "no SQL after stripping comments"

    # 1) single statement only
    if ";" in san:
        return False, "multiple statements are not allowed"

    # 2) read path only
    if not _START_RE.match(san):
        return False, f"must start with SELECT or WITH (got {san[:24]!r})"

    # 3) no DML / DDL / side-effecting statements
    m = _BANNED_RE.search(san)
    if m:
        return False, f"banned keyword: {m.group(1).upper()}"

    # 4) allow-listed tables only (+ CTE names defined in this query). Scan EVERY relation in the
    #    FROM/JOIN clause, including comma-separated implicit joins (`FROM a, b`), so a system
    #    catalog or table function cannot ride in as the 2nd+ entry of the list.
    allowed = {t.lower() for t in allowed_tables}
    allowed |= {name.lower() for name in _CTE_RE.findall(san)}
    for tok in _iter_relations(san):
        parts = [p.strip('"`[]').lower() for p in tok.split(".")]
        if len(parts) >= 2 and parts[-2] in _DENIED_SCHEMAS:
            return False, f"system schema not allowed: {parts[-2]}"
        ident = parts[-1]              # compare on the final segment (drop quotes + schema prefix)
        if ident not in allowed:
            return False, f"table not allowed: {ident}"

    # 5) it parses as a pure SELECT over the known schema
    ok, reason = _explain_ok(raw)
    if not ok:
        return False, reason
    return True, "ok"


# --------------------------------------------------------------------------- self-test
def _selftest() -> int:
    positives = [
        ("point lookup aggregate",
         "SELECT AVG(pts) AS answer FROM game_logs WHERE player_id = 2544 AND season = 2025 AND is_playoff = 0"),
        ("leaderboard with qualifier + string literal",
         "SELECT player_name AS answer FROM player_season WHERE season = 2025 "
         "AND season_type = 'Regular Season' AND gp >= 58 ORDER BY pts DESC LIMIT 1"),
        ("cross-source join",
         "SELECT b.vorp AS answer FROM bbref_advanced b JOIN player_crosswalk x "
         "ON b.bbref_slug = x.bbref_slug WHERE x.nba_player_id = 203999 AND b.season = 2025"),
        ("nested subquery difference",
         "SELECT (SELECT AVG(pts) FROM game_logs WHERE player_id = 2544 AND season = 2025 AND is_playoff = 0) "
         "- (SELECT AVG(pts) FROM game_logs WHERE player_id = 201939 AND season = 2025 AND is_playoff = 0) AS answer"),
        ("CTE via WITH", "WITH q AS (SELECT pts FROM game_logs WHERE player_id = 2544) "
                         "SELECT AVG(pts) AS answer FROM q"),
        ("no-FROM scalar", "SELECT 1 AS answer"),
        ("legit comma-join (both allow-listed)",
         "SELECT p.full_name AS answer FROM players p, game_logs g "
         "WHERE p.player_id = g.player_id AND g.season = 2025 LIMIT 1"),
        ("trailing semicolon stripped", "SELECT COUNT(*) AS answer FROM players;"),
        ("semicolon inside a string literal",
         "SELECT full_name AS answer FROM players WHERE full_name = 'a;b'"),
        ("banned word only inside a comment",
         "SELECT pts AS answer FROM game_logs -- todo: DROP later\nWHERE player_id = 2544"),
    ]
    negatives = [
        ("bare DROP", "DROP TABLE game_logs"),
        ("stacked statements", "SELECT * FROM game_logs; DROP TABLE players"),
        ("UPDATE", "UPDATE game_logs SET pts = 0 WHERE player_id = 1"),
        ("INSERT", "INSERT INTO players VALUES (1, 'x', 'BOS')"),
        ("COPY exfiltration", "COPY game_logs TO '/tmp/out.csv'"),
        ("PRAGMA", "PRAGMA table_info('game_logs')"),
        ("ATTACH", "ATTACH 'evil.db' AS e"),
        ("table function read_parquet", "SELECT * FROM read_parquet('/etc/passwd')"),
        ("system catalog", "SELECT * FROM game_logs UNION SELECT table_name, 1, 1, 1, 1, 1, 1, 1, 1, 1 FROM duckdb_tables()"),
        ("unknown table", "SELECT * FROM secret_salaries"),
        ("not a query", "EXPLAIN SELECT 1"),
        ("empty", "   "),
        # comma-join allow-list bypass (the fixed defect): only the 1st relation used to be checked
        ("comma-join sqlite_master", "SELECT * FROM players p, sqlite_master m"),
        ("comma-join catalog as answer", "SELECT m.sql AS answer FROM players p, sqlite_master m"),
        ("comma-join pg_tables", "SELECT * FROM players, pg_tables"),
        ("comma-join information_schema", "SELECT * FROM game_logs, information_schema.tables"),
        ("comma-join unknown table", "SELECT * FROM players, secret_salaries"),
        ("three-way comma join", "SELECT * FROM players, game_logs, sqlite_master"),
        ("subquery then comma catalog", "SELECT * FROM (SELECT 1) x, sqlite_master m"),
        ("schema-qualified catalog", "SELECT * FROM pg_catalog.pg_tables"),
    ]

    fails = 0
    print("=" * 78)
    print("s4_sql_guard self-test")
    print("=" * 78)
    for label, sql in positives:
        ok, reason = validate_sql(sql)
        mark = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"  [{mark}] expect-ALLOW  {label:38s} -> ok={ok}  {'' if ok else '(' + reason + ')'}")
    for label, sql in negatives:
        ok, reason = validate_sql(sql)
        mark = "PASS" if not ok else "FAIL"
        if ok:
            fails += 1
        print(f"  [{mark}] expect-REJECT {label:38s} -> ok={ok}  ({reason})")
    print("-" * 78)
    total = len(positives) + len(negatives)
    print(f"{total - fails}/{total} cases behaved as expected"
          + ("" if fails == 0 else f"  ({fails} UNEXPECTED)"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
