"""Query executor — runs the validated SQL on DuckDB and returns raw numbers.

This is the ONLY place a statistic is ever computed. The number that comes out of here
is ground truth (given the data); nothing downstream is allowed to alter it.
"""
from __future__ import annotations

from dataclasses import dataclass

import duckdb


@dataclass
class QueryResult:
    value: float | None
    games: int
    sql: str
    params: list


def run(con: duckdb.DuckDBPyConnection, sql: str, params: list) -> QueryResult:
    row = con.execute(sql, params).fetchone()
    value, games = (row[0], row[1]) if row else (None, 0)
    return QueryResult(value=value, games=games, sql=sql, params=params)
