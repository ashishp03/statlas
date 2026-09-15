# Worked example — the min-games qualifier, in one query

**Pre-run for you on 2026-09-13.** Nothing to set up: this was executed against
`learning/days/day5/eda/data/player_stats_2025-26_regular.csv` with DuckDB. Read it, then
(optionally) re-run it yourself — it's a one-liner.

This is study-plan item **B5c (DuckDB window functions)** made concrete, and it's also the repo's
reliability rule ("leaderboards need a minimum-games qualifier") written in SQL.

---

## The query

```sql
SELECT PLAYER_NAME, GP, FG3A, FG3_PCT,
       RANK() OVER (ORDER BY FG3_PCT DESC) AS rk
FROM read_csv_auto('learning/days/day5/eda/data/player_stats_2025-26_regular.csv')
WHERE GP >= 40 AND FG3A >= 3.0
QUALIFY rk <= 5
ORDER BY rk;
```

## Why 3P% and not PPG

I ran the PPG version first (top 5 scorers, `GP >= 40`). The qualifier changed **nothing** —
Doncic 33.5, SGA 31.1, Edwards 28.8, Brown 28.7, Maxey 28.3, with or without it. Because these
columns are already *per-game averages*, a low-minutes player can't inflate a counting-stat
average much.

Rate stats are where the rule earns its keep:

### Without a qualifier — garbage

| Player | GP | 3PA/g | 3P% | rk |
|---|---|---|---|---|
| Trayce Jackson-Davis | 53 | 0.0 | 1.000 | 1 |
| Mark Williams | 60 | 0.0 | 1.000 | 1 |
| Harrison Ingram | 7 | 0.1 | 1.000 | 1 |
| Jaxson Hayes | 66 | 0.0 | 1.000 | 1 |
| Walker Kessler | 5 | 1.6 | 0.750 | 5 |

Four bigs who made about one three all season, tied at 100%.

### With `GP >= 40 AND FG3A >= 3.0` — a real answer

| Player | GP | 3PA/g | 3P% | rk |
|---|---|---|---|---|
| Luke Kennard | 78 | 3.1 | 0.478 | 1 |
| Bobby Portis | 67 | 4.4 | 0.456 | 2 |
| Cam Spencer | 72 | 4.5 | 0.449 | 3 |
| Jaylon Tyson | 66 | 4.5 | 0.446 | 4 |
| Rui Hachimura | 68 | 3.9 | 0.443 | 5 |

---

## The three things to take away

1. **`RANK() OVER (ORDER BY ...)`** — computes a rank per row without collapsing the rows, unlike
   `GROUP BY`. Ties share a rank and the next rank is skipped (note the four `1`s, then `5`).
2. **`QUALIFY`** — filters on a window-function result. `WHERE` runs *before* windows are computed,
   so `WHERE rk <= 5` is an error; `QUALIFY` is the clause that exists to fix that.
   Logical order: `FROM -> WHERE -> GROUP BY -> HAVING -> WINDOW -> QUALIFY -> ORDER BY -> LIMIT`.
3. **The qualifier is a product decision, not SQL trivia.** For Statlas this means the planner has
   to know *which stats are rates* and attach a volume threshold to those. A counting-stat
   leaderboard survives without one; a percentage leaderboard does not.

## Statlas implication (the bit worth an argument)

`GP >= 40` and `FG3A >= 3.0` are invented thresholds. The NBA's own rule for 3P% leaders is a
**total-attempts** minimum (82 made threes, historically), not a per-game one. So a real
implementation needs a small table of qualifier rules per metric — exactly the sort of thing the
text-to-SQL layer must *not* be allowed to hallucinate. Candidate for the allow-list.

## If you want to keep going

Paste the query into `modules/04-text-to-sql/exercises.ipynb` as a gold NL->SQL pair:
NL = *"Who led the league in three-point percentage in 2025-26?"* -> this SQL. That closes one of
the 5 TODO pairs in exercise 1.
