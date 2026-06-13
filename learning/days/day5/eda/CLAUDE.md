# learning/days/day5/eda — Context

## Section 1: Evergreen

**What this is:** Exploratory data analysis on real `nba_api` NBA data — reference material for when product-building resumes (especially text-to-SQL and the schema design).

**Module map:**
- `EDA_report.md` — findings: source, coverage, columns, cleaning/joining needs, stats, figure index, the three v1 questions validated
- `data/` — cached pull CSVs (output/data folder — no own `CLAUDE.md`)
- `figs/` — generated PNG charts (output folder — no own `CLAUDE.md`)

**Architecture decisions (append-only, one line each):**
- Source `nba_api`, free, no key; core table `LeagueDashPlayerStats` (582×67), coverage floor 1996-97
- Data is clean: zero nulls, zero duplicate players; traded players pre-aggregated (`TEAM_COUNT`)
- Key reliability rule surfaced: leaderboards need a minimum-games qualifier
- Recommended v1 schema drops the `*_RANK` mirror columns; prefer one table with a `season_type` column

**Non-negotiable constraints:**
- `data/` and `figs/` are generated artifacts — regenerate from scripts, don't hand-edit
- EDA numbers describe a snapshot; re-pull for fresh data

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
