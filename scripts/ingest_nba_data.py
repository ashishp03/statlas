"""ingest_nba_data.py — pull real NBA data (nba_api bulk + Basketball-Reference) to local Parquet.

Adapted from experiments/v1_nba_storage_retrieval_benchmark/pipeline/s1_pull.py, which proved this
pull mechanism against real, modern-era data (safe/paced calls, bulk endpoints over per-entity
loops, V3-not-V2, cache-by-output-file). That original script hardcoded ITS OWN experiment's season
scope (explicitly tagged "Decision D2, REVISIT" in that experiment's docs) — this version keeps the
mechanism but takes the scope as CLI arguments instead, since the mechanism is permanent and the
scope is a per-run choice. Uses `statlas.data.nba_client` (src/statlas/data/nba_client.py) for the
actual defensive API calls.

Run from the repo root, e.g.:
    python scripts/ingest_nba_data.py --out-dir data/nba_raw \\
        --agg-start-year 1997 --agg-end-year 2026 \\
        --gamelog-start-year 2022 --gamelog-end-year 2026 \\
        --bbref-year 2025 --shotchart-year 2025

    # fast smoke pull
    python scripts/ingest_nba_data.py --out-dir /tmp/nba_smoke --limit-agg 3 --skip-scale --skip-bbref
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))  # repo src/ on path

import polars as pl

from statlas.data.nba_client import GAME_LOGS_COLUMNS, safe_rows, season_str

# Curated season-aggregate columns (drop the ~30 *_RANK mirror columns nba_api also returns).
PLAYER_SEASON_BASE_COLS = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "AGE", "GP", "MIN",
    "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT",
    "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "PF", "PTS", "PLUS_MINUS",
]
PLAYER_SEASON_ADV_COLS = [
    "PLAYER_ID", "OFF_RATING", "DEF_RATING", "NET_RATING", "USG_PCT",
    "TS_PCT", "EFG_PCT", "AST_PCT", "REB_PCT", "PACE", "PIE", "POSS",
]

METRICS: list[dict] = []


def _record(step, endpoint, params, n_rows, elapsed_s, status):
    METRICS.append({
        "step": step, "endpoint": endpoint, "params": params,
        "n_rows": n_rows, "api_elapsed_s": round(elapsed_s, 3), "status": status,
    })
    flag = "ok " if status == "ok" else "ERR"
    print(f"  [{flag}] {endpoint:28s} {params:38s} rows={n_rows:<8} {elapsed_s:6.2f}s")


def _dump(df: pl.DataFrame, name: str, out_dir: pathlib.Path) -> dict:
    path = out_dir / f"{name}.parquet"
    df.write_parquet(path)
    mb = path.stat().st_size / 1e6
    print(f"  -> wrote {name}.parquet  rows={df.height:<8} cols={df.width:<3} {mb:6.2f} MB")
    return {"dataset": name, "n_rows": df.height, "n_cols": df.width, "parquet_mb": round(mb, 3)}


def _select_present(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    return df.select([c for c in cols if c in df.columns])


# --------------------------------------------------------------------------- aggregates
def pull_aggregates(
    years: list[int],
    out_dir: pathlib.Path,
    *,
    playoff_year: int | None = None,
    limit_agg: int | None = None,
    refresh: bool = False,
    base_cols: list[str] = PLAYER_SEASON_BASE_COLS,
    adv_cols: list[str] = PLAYER_SEASON_ADV_COLS,
) -> list[dict]:
    """LeagueDashPlayerStats PerGame Base + Advanced -> player_season.parquet."""
    from nba_api.stats.endpoints import leaguedashplayerstats as ldps

    out = out_dir / "player_season.parquet"
    if out.exists() and not refresh:
        print("player_season.parquet cached — skip (use --refresh to repull)")
        return [{"dataset": "player_season", "cached": True}]

    years = years if not limit_agg else years[-limit_agg:]
    playoff_year = playoff_year if playoff_year is not None else (years[-1] if years else None)
    # Regular Season for all seasons; Playoffs only for one (so season_type has both values).
    plan = [(y, "Regular Season") for y in years]
    if playoff_year is not None:
        plan.append((playoff_year, "Playoffs"))

    frames = []
    print(f"aggregates — {len(plan)} season/type x 2 measures (Base+Advanced)")
    for year, stype in plan:
        base_n, base, base_s, base_e = safe_rows(
            ldps.LeagueDashPlayerStats, season=season_str(year), season_type_all_star=stype,
            per_mode_detailed="PerGame", measure_type_detailed_defense="Base")
        _record("agg_base", "LeagueDashPlayerStats", f"{season_str(year)}/{stype}/Base", base_n, base_e, base_s)
        adv_n, adv, adv_s, adv_e = safe_rows(
            ldps.LeagueDashPlayerStats, season=season_str(year), season_type_all_star=stype,
            per_mode_detailed="PerGame", measure_type_detailed_defense="Advanced")
        _record("agg_adv", "LeagueDashPlayerStats", f"{season_str(year)}/{stype}/Adv", adv_n, adv_e, adv_s)
        if base is None:
            continue
        b = _select_present(base, base_cols)
        if adv is not None:
            a = _select_present(adv, adv_cols)
            b = b.join(a, on="PLAYER_ID", how="left")
        b = b.with_columns(pl.lit(year).alias("season"), pl.lit(stype).alias("season_type"))
        frames.append(b)

    if not frames:
        print("!! no aggregate frames pulled")
        return [{"dataset": "player_season", "n_rows": 0}]

    df = pl.concat(frames, how="diagonal_relaxed")
    df = df.rename({c: c.lower() for c in df.columns})
    df = df.rename({"team_abbreviation": "team_abbr"})
    meta = _dump(df, "player_season", out_dir)

    players = (df.filter(pl.col("season_type") == "Regular Season")
                 .select(["player_id", "player_name", "team_abbr", "season"])
                 .sort("season").group_by("player_id").last()
                 .select([pl.col("player_id"), pl.col("player_name").alias("full_name"), pl.col("team_abbr")]))
    _dump(players, "players", out_dir)
    return [meta]


# --------------------------------------------------------------------------- game logs
def _normalize_game_logs(df: pl.DataFrame, year: int, is_playoff: int, columns: list[str]) -> pl.DataFrame:
    keep = {"PLAYER_ID": "player_id", "GAME_DATE": "game_date", "MATCHUP": "matchup",
            "MIN": "min", "PTS": "pts", "REB": "reb", "AST": "ast", "PLUS_MINUS": "plus_minus"}
    df = _select_present(df, list(keep)).rename({k: v for k, v in keep.items() if k in df.columns})
    df = df.with_columns(
        pl.lit(year).alias("season"),
        pl.lit(is_playoff).alias("is_playoff"),
        pl.col("game_date").str.strptime(pl.Date, "%Y-%m-%d", strict=False),
        pl.col("matchup").str.split(" ").list.last().alias("opponent_abbr"),
    )
    for c in ("min", "pts", "reb", "ast", "plus_minus"):
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False))
    return df.select([c for c in columns if c in df.columns])


def pull_game_logs(
    years: list[int],
    out_dir: pathlib.Path,
    *,
    refresh: bool = False,
    columns: list[str] = GAME_LOGS_COLUMNS,
) -> list[dict]:
    """LeagueGameLog (player) -> game_logs.parquet, matching the stable game_logs schema."""
    from nba_api.stats.endpoints import leaguegamelog as lgl

    out = out_dir / "game_logs.parquet"
    if out.exists() and not refresh:
        print("game_logs.parquet cached — skip")
        return [{"dataset": "game_logs", "cached": True}]

    frames, sample_game_id = [], None
    print(f"game_logs — {len(years)} seasons x (Regular + Playoffs)")
    for year in years:
        for stype, isp in (("Regular Season", 0), ("Playoffs", 1)):
            n, df, status, elapsed = safe_rows(
                lgl.LeagueGameLog, season=season_str(year), season_type_all_star=stype,
                player_or_team_abbreviation="P")
            _record("game_logs", "LeagueGameLog", f"{season_str(year)}/{stype}", n, elapsed, status)
            if df is None:
                continue
            if sample_game_id is None and "GAME_ID" in df.columns and df.height:
                sample_game_id = df["GAME_ID"][0]
            frames.append(_normalize_game_logs(df, year, isp, columns))

    if not frames:
        print("!! no game-log frames pulled")
        return [{"dataset": "game_logs", "n_rows": 0}]
    df = pl.concat(frames, how="diagonal_relaxed")
    meta = _dump(df, "game_logs", out_dir)
    if sample_game_id:
        (out_dir / "sample_game_id.txt").write_text(str(sample_game_id))
    return [meta]


# --------------------------------------------------------------------------- scale test
def pull_scale(shotchart_year: int, out_dir: pathlib.Path, *, refresh: bool = False) -> list[dict]:
    """One season of league-wide ShotChartDetail + one game of PlayByPlayV3 (the scale payloads)."""
    from nba_api.stats.endpoints import playbyplayv3 as pbp3
    from nba_api.stats.endpoints import shotchartdetail as scd

    metas = []
    sc_out = out_dir / "shotchart_sample.parquet"
    if sc_out.exists() and not refresh:
        print("shotchart_sample.parquet cached — skip")
    else:
        n, df, status, elapsed = safe_rows(
            scd.ShotChartDetail, team_id=0, player_id=0,
            season_nullable=season_str(shotchart_year),
            season_type_all_star="Regular Season", context_measure_simple="FGA")
        _record("scale_shotchart", "ShotChartDetail", season_str(shotchart_year), n, elapsed, status)
        if df is not None:
            metas.append(_dump(df, "shotchart_sample", out_dir))

    pbp_out = out_dir / "pbp_sample.parquet"
    gid_file = out_dir / "sample_game_id.txt"
    if pbp_out.exists() and not refresh:
        print("pbp_sample.parquet cached — skip")
    elif gid_file.exists():
        gid = gid_file.read_text().strip()
        n, df, status, elapsed = safe_rows(pbp3.PlayByPlayV3, game_id=gid, start_period=0, end_period=14)
        _record("scale_pbp", "PlayByPlayV3", f"game={gid}", n, elapsed, status)
        if df is not None:
            metas.append(_dump(df, "pbp_sample", out_dir))
    else:
        print("no sample_game_id — run game logs first for a PBP scale test")
    return metas


# --------------------------------------------------------------------------- basketball-reference
def pull_bbref(bbref_year: int, out_dir: pathlib.Path, *, refresh: bool = False) -> list[dict]:
    """Basketball-Reference advanced totals -> bbref_advanced.parquet (PER/BPM/VORP/WS)."""
    out = out_dir / "bbref_advanced.parquet"
    if out.exists() and not refresh:
        print("bbref_advanced.parquet cached — skip")
        return [{"dataset": "bbref_advanced", "cached": True}]
    try:
        from basketball_reference_web_scraper import client
        t0 = time.perf_counter()
        rows = client.players_advanced_season_totals(season_end_year=bbref_year)
        elapsed = time.perf_counter() - t0

        def _num(v):
            return float(v) if v is not None else None

        clean = [{
            "bbref_slug": r.get("slug"),
            "full_name": r.get("name"),
            "season": bbref_year,
            "per": _num(r.get("player_efficiency_rating")),
            "bpm": _num(r.get("box_plus_minus")),
            "vorp": _num(r.get("value_over_replacement_player")),
            "ws": _num(r.get("win_shares")),
        } for r in rows]
        df = (pl.from_dicts(clean)
                .filter(pl.col("bbref_slug").is_not_null())
                .unique(subset=["bbref_slug"], keep="first"))  # first row per player = combined 'TOT'
        _record("bbref", "players_advanced_season_totals", f"{bbref_year}", df.height, elapsed, "ok")
    except Exception as e:  # noqa: BLE001
        _record("bbref", "players_advanced_season_totals", f"{bbref_year}", -1, 0.0, f"{type(e).__name__}: {str(e)[:70]}")
        print(f"!! BBRef pull failed: {e}")
        return [{"dataset": "bbref_advanced", "n_rows": 0}]
    return [_dump(df, "bbref_advanced", out_dir)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", required=True, type=pathlib.Path, help="directory to write *.parquet into")
    ap.add_argument("--agg-start-year", type=int, default=1997, help="first season (end-year) for aggregates")
    ap.add_argument("--agg-end-year", type=int, default=2026, help="last season (end-year) for aggregates")
    ap.add_argument("--gamelog-start-year", type=int, default=None,
                     help="first season for game logs (default: agg-end-year - 4)")
    ap.add_argument("--gamelog-end-year", type=int, default=None, help="default: agg-end-year")
    ap.add_argument("--shotchart-year", type=int, default=None, help="default: agg-end-year")
    ap.add_argument("--bbref-year", type=int, default=None, help="default: agg-end-year")
    ap.add_argument("--refresh", action="store_true", help="ignore cache, repull everything")
    ap.add_argument("--limit-agg", type=int, default=None, help="only the N most-recent aggregate seasons")
    ap.add_argument("--skip-scale", action="store_true")
    ap.add_argument("--skip-bbref", action="store_true")
    args = ap.parse_args()

    gamelog_end = args.gamelog_end_year or args.agg_end_year
    gamelog_start = args.gamelog_start_year or (gamelog_end - 4)
    shotchart_year = args.shotchart_year or args.agg_end_year
    bbref_year = args.bbref_year or args.agg_end_year

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"INGEST — agg={args.agg_start_year}-{args.agg_end_year} "
          f"gamelogs={gamelog_start}-{gamelog_end} -> {args.out_dir}")
    print("=" * 78)

    summary = []
    t0 = time.perf_counter()
    summary += pull_aggregates(list(range(args.agg_start_year, args.agg_end_year + 1)), args.out_dir,
                                limit_agg=args.limit_agg, refresh=args.refresh)
    summary += pull_game_logs(list(range(gamelog_start, gamelog_end + 1)), args.out_dir, refresh=args.refresh)
    if not args.skip_scale:
        summary += pull_scale(shotchart_year, args.out_dir, refresh=args.refresh)
    if not args.skip_bbref:
        summary += pull_bbref(bbref_year, args.out_dir, refresh=args.refresh)
    wall = time.perf_counter() - t0

    if METRICS:
        pl.from_dicts(METRICS).write_csv(args.out_dir / "ingest_metrics.csv")
    live = [m for m in METRICS if m["status"] == "ok"]
    errs = [m for m in METRICS if m["status"] != "ok"]
    print("=" * 78)
    print(f"done in {wall:.1f}s — {len(live)} ok calls, {len(errs)} errors. "
          f"metrics -> {args.out_dir / 'ingest_metrics.csv'}")
    if errs:
        print(f"  ERRORS: {[e['endpoint'] + ':' + e['status'][:30] for e in errs][:6]}")
    print(f"  datasets: {[s.get('dataset') for s in summary]}")


if __name__ == "__main__":
    main()
