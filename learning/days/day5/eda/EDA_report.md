# Statlas EDA — NBA stats data (Day 5, 2026-06-13)

Exploratory pass on the data source *before* building the pipeline. Goal: know exactly what
we're working with — coverage, columns, quality, what needs cleaning/joining, and the shape of
the numbers — so the text-to-SQL layer is built on solid ground.

All data pulled live this session. Raw CSVs in `./data/`, figures in `./figs/`.

---

## 0. Which API, and is it free?

**Source: the `nba_api` Python package** (`pip install nba_api`) — an open-source wrapper around
the **official NBA Stats endpoints at stats.nba.com** (the same backend that powers NBA.com's
stat pages). Specifically this EDA used three endpoints:

- `LeagueDashPlayerStats` — one row per player, full season aggregates (the core v1 table)
- `LeagueDashTeamStats` — team-level aggregates (used for the historical trend)
- `LeagueLeaders` — leaderboards, reaches further back in history

**Cost: completely free. No API key, no signup, no quota tier.** It's official-source data
served over public HTTP. The only catch is informal **rate limiting** — hammer it with rapid
calls from one IP and stats.nba.com will throttle you, so in production we cache pulls (as I did
here) and add small delays between requests. That's the only "cost."

> Note this is *separate* from the LLM question — see the bottom of this report for Claude Max
> vs. API access.

---

## 1. What's available & how far back

| Endpoint | History floor | Notes |
|---|---|---|
| `LeagueDashPlayerStats` (our core table) | **1996-97 → present** | Returns 0 rows before 1996-97. Richest column set. |
| `LeagueDashTeamStats` | 1996-97 → present | Same floor; team-level. |
| `LeagueLeaders` | **~1979-80 reliably** (3PT era); basic stats deeper but flaky pre-1980 | Use this if we ever want pre-1996 leaderboards. |

**Practical takeaway:** for a rich, consistent, column-complete dataset, **treat 1996-97 as the
start of "modern" coverage.** That's ~30 seasons — plenty for v1. Deep history (Wilt, Bird,
Magic) exists but only as basic stats via a different, less consistent endpoint; defer it.

Other endpoints available for later phases (not pulled today): per-game game logs
(`PlayerGameLog`), box scores, play-by-play, shot charts (x/y coordinates, 1996+), and player
tracking / hustle stats (2013+).

---

## 2. The core table: columns

`LeagueDashPlayerStats` (PerGame) returns **582 players × 67 columns** for 2025-26. The 67 split
cleanly into three groups:

- **Identity (6):** `PLAYER_ID`, `PLAYER_NAME`, `NICKNAME`, `TEAM_ID`, `TEAM_ABBREVIATION`, `AGE`
- **Stats (~28):** `GP, W, L, W_PCT, MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, FTM, FTA,
  FT_PCT, OREB, DREB, REB, AST, TOV, STL, BLK, BLKA, PF, PFD, PTS, PLUS_MINUS`, plus
  `NBA_FANTASY_PTS, DD2` (double-doubles), `TD3` (triple-doubles)
- **`*_RANK` mirror columns (~30):** a precomputed league rank for almost every stat
  (`PTS_RANK`, `REB_RANK`, …). Useful, but redundant with what SQL can compute — **drop these
  for v1** to keep the schema legible for the LLM.

`PerMode` controls the meaning of the numbers: `PerGame` (averages — what we want for "averaged"
questions), `Totals`, `Per36`, `Per100Possessions`. We pull both `PerGame` and would keep
`Totals` if we want "how many total X" questions.

---

## 3. Data quality — what needs cleaning

Good news: **the data is remarkably clean.**

- **Nulls: zero.** No missing values in any of the 67 columns for 2025-26.
- **Duplicates: zero.** Exactly one row per `PLAYER_ID` — even for traded players (see below).
- **Types:** numeric columns import as numbers; only the 6 identity fields are text.

Three real gotchas to handle:

1. **Traded players are pre-aggregated to ONE row.** `TEAM_COUNT` flags how many teams a player
   suited up for this season: 510 played for 1 team, **66 for 2, 5 for 3, 1 for 4.** Their single
   row is the *season-wide* average and `TEAM_ABBREVIATION` shows only their **latest** team
   (e.g. Anfernee Simons listed as CHI). So "averages" are correct, but **"how did player X do
   *for team Y*" is not answerable from this table** — that needs a per-team split pull. Fine to
   defer; just don't promise team-split answers in v1.

2. **`FG3_PCT` = 0, not null, for non-shooters.** 43 players attempted 0 threes; their 3P% shows
   as `0.000`. Harmless for storage, but **never rank/recommend by a percentage without a
   minimum-attempts filter** or a 0% "shooter" who took no threes will pollute results.

3. **Small-sample leaders.** This bites immediately: the **playoff rebounding "leader" is Jokić
   at 13.2 — but over only 6 games** (Denver exited early), while Wembanyama posted 10.7 over 21
   games. Raw leaderboards reward tiny samples. **v1 should apply a minimum-games qualifier**
   (the NBA uses ~58 GP / 70% for regular-season titles; playoffs need a lower, round-aware
   threshold). This is the single most important correctness rule for a stats engine.

---

## 4. Joining / merging

- **Regular ⇄ Playoffs:** same schema, joinable on `PLAYER_ID`. Of 582 regular-season players,
  **230 also have playoff rows; 0 playoff players are missing from the regular season** (as
  expected). Rather than join, the cleaner design is **one table with a `season_type` column**
  (`'regular'` / `'playoffs'`) — the text-to-SQL layer then filters instead of picking tables.
- **Multi-season:** pulling 1996-97…2025-26 and stacking gives a `(player, season, season_type)`
  panel. Add a `season` column on ingest; `PLAYER_ID` is stable across seasons, so career queries
  just `GROUP BY player`.
- **Players table:** the repo's existing `players` table joins on `PLAYER_ID`. The dash endpoint
  already carries `PLAYER_NAME`/`TEAM_ABBREVIATION`, so for v1 a separate players table is
  optional — but it's the natural home for nicknames (the entity resolver).

**Recommended v1 schema** (drop the `*_RANK` clutter):
`player_season_stats(player_id, player_name, team_abbr, team_count, season, season_type,
age, gp, min, pts, reb, ast, oreb, dreb, stl, blk, tov, pf, fgm, fga, fg_pct, fg3m, fg3a,
fg3_pct, ftm, fta, ft_pct, plus_minus)`

---

## 5. Statistical snapshot (2025-26 regular season, per-game)

| Stat | mean | median | std | min | max |
|---|---|---|---|---|---|
| PTS | 9.2 | 7.8 | 6.4 | 0.0 | **33.5** (Dončić) |
| REB | 3.6 | 3.1 | 2.4 | 0.0 | 12.9 |
| AST | 2.1 | 1.6 | 1.8 | 0.0 | 10.7 |
| MIN | 19.7 | 20.0 | 8.9 | 1.5 | 38.0 |
| GP  | 45.8 | 51 | 24.9 | 1 | 82 |
| AGE | 26.2 | 25 | 4.2 | 19 | 41 |

Scoring is **right-skewed** — most players cluster low (median 7.8) with a long star tail
(fig 01). GP is bimodal-ish: a wall of low-GP fringe/two-way players plus a bump near a full
82-game slate. **367 players cleared 40 GP; 234 cleared ~58** — that's the realistic "qualified"
pool for leaderboards.

**Correlations** (fig 06): PTS strongly tracks MIN (0.83) and FGA (~0.9) — minutes and shot
volume drive scoring, as expected. AST correlates with TOV (more playmaking → more turnovers).
FG_PCT is *negatively* related to FG3A (bigs who don't shoot threes finish at higher % inside).
AGE is essentially uncorrelated with production — talent, not age, sets the ceiling.

---

## 6. Figures (`./figs/`)

1. **`01_ppg_distribution.png`** — scoring distribution; the right-skew and star tail.
2. **`02_top15_ppg.png`** — top 15 scorers (Dončić 33.5, SGA 31.1, Edwards 28.8…).
3. **`03_min_vs_pts.png`** — minutes vs points, colored by assists; the strong linear core.
4. **`04_reg_vs_playoff_ppg.png`** — regular vs playoff PPG for the 230 two-season players, vs a
   y=x line (who rises/falls in the postseason).
5. **`05_history_scoring_3pa.png`** — the 3-point revolution: team scoring 96.9 → 115.6 and 3PA
   16.8 → 37.0 per game since 1996-97.
6. **`06_correlation_heatmap.png`** — correlation matrix of the core per-game stats.

---

## 7. The three v1 questions — already answerable

All three validated directly against the pulled data, confirming the dataset supports v1:

| Question | Answer (2025-26) | Query shape |
|---|---|---|
| What did Jalen Brunson average? | 26.0 PTS, 3.3 REB, 6.8 AST (74 GP), NYK | single-player lookup |
| Who averaged the most points? | Luka Dončić, 33.5 PPG | `ORDER BY pts DESC LIMIT 1` |
| Playoffs rebounding leader? | Jokić 13.2 (6 GP) — **but** apply a min-games filter → Wembanyama 10.7 / 21 GP | filter + leaderboard + qualifier |

---

## Appendix — Claude Max vs. API access (your question)

**A Claude Max subscription is not the same as API access, and historically did not give you
programmatic API calls.** Max (and Pro) are consumer plans for the Claude apps and Claude Code;
the **Anthropic API is billed separately** through the developer Console at standard per-token
rates. As of a **June 15, 2026** change, Max plans *do* include a monthly **Agent-SDK credit**
($100 on Max 5x, $200 on Max 20x) for programmatic/Agent-SDK usage billed at API rates — but
once that credit is spent it's pay-as-you-go, and it's distinct from a general API key for
arbitrary `anthropic` SDK calls. **Verify your current entitlement in the Console before
relying on it.**

**For Statlas, this doesn't block us today** — we did pure EDA, no LLM. When we wire up the
text-to-SQL step, your stated preference was "start with something free," so the clean path is a
**local open-source model via Ollama** (e.g. Llama 3.1 / Qwen2.5-Coder) — zero cost, runs
offline, good enough for templated NBA-schema SQL — with the option to swap in the Claude API
later for harder queries.

*Sources for the Max/API note:*
- https://claude.com/pricing
- https://zed.dev/blog/anthropic-subscription-changes
- https://www.techtimes.com/articles/317625/20260602/anthropic-ends-subscription-subsidy-agents-june-15-credit-pool-replaces-flat-rate-access.htm
