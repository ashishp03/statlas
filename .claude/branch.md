# data-exploration — Branch Context

> Branch overlay for `data-exploration` (created 2026-06-13). The shared, canonical project context lives
> in the root `CLAUDE.md` (and subdirectory `CLAUDE.md` files) on `main`; THIS file adds only what
> is specific to this branch. Protected by `.gitattributes` (`merge=ours`) so it never merges
> across branches.

## Purpose
Explore NBA data api, find its structure, restrcitions, and understand how to use it.

## Scope — what belongs on this branch
- Owns: `notebooks/` (`initial_eda*.ipynb`) — read-only exploration of NBA data sources.
- Belongs here: probing `nba_api` endpoints (history depth, columns, restrictions), evaluating
  alternative sources (Basketball-Reference, balldontlie, pbpstats, hoopR, shufinskiy, Kaggle), and
  documenting native-vs-derived metric availability.
- Does NOT belong here: product/pipeline code (`src/statlas/**`), warehouse-builder changes, or the
  golden eval set — those live on the product branch. Findings flow into `CLAUDE.md` architecture
  decisions on `main` via a deps/docs PR, never by merging notebooks into `main`.

## Branch-specific instructions
- Notebooks use **Polars** (convert nba_api pandas once with `pl.from_pandas`); run via **uv**
  (`uv run --with jupyter jupyter nbconvert --execute ...`), never bare `python`.
- Wrap every live API call in try/except + `time.sleep` to tolerate nba_api flakiness/rate limits;
  prefer **binary-searching** boundaries over asserting years.
- Use the **V3** box-score/play-by-play endpoints — the V2 variants are deprecated and return empty.
- balldontlie cells must no-op gracefully when `BALLDONTLIE_API_KEY` is unset.

## Subdirectory notes (branch-specific)
- TODO: `<path/>` — note (only if a folder needs branch-specific guidance; otherwise its shared
  `CLAUDE.md` already covers it)

## Rolling log (most recent first)
- 2026-06-21 — Built `notebooks/initial_eda_v2.ipynb`: empirically mapped endpoint history boundaries
  (LeagueDash/ShotChart/PBPv3 → 1996-97, tracking → 2013-14, LeagueLeaders → 1951-52), native-vs-derived
  advanced metrics (ratings/USG/TS/PIE native; PER/BPM/VORP/WS not NBA-provided), and alternative sources
  (added `basketball_reference_web_scraper` + `balldontlie` as deps). Found V2 box-score/PBP endpoints
  deprecated → use V3. Filled Scope + Branch-specific-instructions TODOs above.
- 2026-06-13 — branch created from main.
