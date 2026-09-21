"""S1 — Pull real modern-era NBA data (nba_api bulk + Basketball-Reference).

Writes normalized Parquet into data/raw/ and an ingest-metrics CSV into results/. This is the
ONE stateful, rate-limited step: it runs serially in the main loop (parallel API calls would trip
stats.nba.com throttling). Everything downstream reads the raw Parquet, never the live API.

Design choices (see ../docs/findings/DECISIONS.md):
  - BULK endpoints over per-entity loops: LeagueGameLog returns every player-game row for a season
    in ONE call (vs ~500 PlayerGameLog calls); LeagueDashPlayerStats returns a whole season at once.
  - V3 endpoints only (V2 are deprecated/empty).
  - Cache by output file: skip an endpoint whose Parquet already exists unless --refresh.

Run:
    uv run python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s1_pull.py
    uv run python .../s1_pull.py --limit-agg 3 --skip-scale --skip-bbref   # fast smoke pull
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path

import polars as pl

import config
from pipeline._harness import safe_rows, season_str, timer

METRICS: list[dict] = []


def _record(step, endpoint, params, n_rows, elapsed_s, status):
    METRICS.append({
        "step": step, "endpoint": endpoint, "params": params,
        "n_rows": n_rows, "api_elapsed_s": round(elapsed_s, 3), "status": status,
    })
    flag = "ok " if status == "ok" else "ERR"
    print(f"  [{flag}] {endpoint:28s} {params:38s} rows={n_rows:<8} {elapsed_s:6.2f}s")


def _dump(df: pl.DataFrame, name: str) -> dict:
    """Write a raw Parquet and measure its size + local read time (the 'cached' path)."""
    path = config.RAW_DIR / f"{name}.parquet"
    df.write_parquet(path)
    mb = path.stat().st_size / 1e6
    with timer() as t:
        _ = pl.read_parquet(path)
    read_ms = t() * 1000.0
    print(f"  -> wrote {name}.parquet  rows={df.height:<8} cols={df.width:<3} "
          f"{mb:6.2f} MB  local_read={read_ms:6.1f} ms")
    return {"dataset": name, "n_rows": df.height, "n_cols": df.width,
            "parquet_mb": round(mb, 3), "local_read_ms": round(read_ms, 2)}


def _select_present(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    return df.select([c for c in cols if c in df.columns])


# --------------------------------------------------------------------------- aggregates
def pull_aggregates(limit_agg: int | None, refresh: bool) -> list[dict]:
    """LeagueDashPlayerStats PerGame Base + Advanced -> player_season.parquet (30 seasons)."""
    from nba_api.stats.endpoints import leaguedashplayerstats as ldps

    out = config.RAW_DIR / "player_season.parquet"
    if out.exists() and not refresh:
        print("player_season.parquet cached — skip (use --refresh to repull)")
        return [{"dataset": "player_season", "cached": True}]

    years = config.AGG_SEASON_YEARS if not limit_agg else config.AGG_SEASON_YEARS[-limit_agg:]
    # Regular Season for all seasons; Playoffs only for the latest (so season_type has both values).
    plan = [(y, "Regular Season") for y in years] + [(config.AGG_END_YEAR, "Playoffs")]

    frames = []
    print(f"S1.aggregates — {len(plan)} season/type x 2 measures (Base+Advanced)")
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
        b = _select_present(base, config.PLAYER_SEASON_BASE_COLS)
        if adv is not None:
            a = _select_present(adv, config.PLAYER_SEASON_ADV_COLS)
            b = b.join(a, on="PLAYER_ID", how="left")
        b = b.with_columns(pl.lit(year).alias("season"), pl.lit(stype).alias("season_type"))
        frames.append(b)

    if not frames:
        print("!! no aggregate frames pulled")
        return [{"dataset": "player_season", "n_rows": 0}]

    df = pl.concat(frames, how="diagonal_relaxed")
    df = df.rename({c: c.lower() for c in df.columns})
    df = df.rename({"player_name": "player_name", "team_abbreviation": "team_abbr"})
    meta = _dump(df, "player_season")

    # players dim: every modern regular-season player, latest team.
    players = (df.filter(pl.col("season_type") == "Regular Season")
                 .select(["player_id", "player_name", "team_abbr", "season"])
                 .sort("season").group_by("player_id").last()
                 .select([pl.col("player_id"), pl.col("player_name").alias("full_name"), pl.col("team_abbr")]))
    _dump(players, "players")
    return [meta]


# --------------------------------------------------------------------------- game logs
def _normalize_game_logs(df: pl.DataFrame, year: int, is_playoff: int) -> pl.DataFrame:
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
    return df.select([c for c in config.GAME_LOGS_COLUMNS if c in df.columns])


def pull_game_logs(refresh: bool) -> list[dict]:
    """LeagueGameLog (player) -> game_logs.parquet (5 recent seasons, Regular + Playoffs)."""
    from nba_api.stats.endpoints import leaguegamelog as lgl

    out = config.RAW_DIR / "game_logs.parquet"
    if out.exists() and not refresh:
        print("game_logs.parquet cached — skip")
        return [{"dataset": "game_logs", "cached": True}]

    frames, sample_game_id = [], None
    print(f"S1.game_logs — {len(config.GAMELOG_YEARS)} seasons x (Regular + Playoffs)")
    for year in config.GAMELOG_YEARS:
        for stype, isp in (("Regular Season", 0), ("Playoffs", 1)):
            n, df, status, elapsed = safe_rows(
                lgl.LeagueGameLog, season=season_str(year), season_type_all_star=stype,
                player_or_team_abbreviation="P")
            _record("game_logs", "LeagueGameLog", f"{season_str(year)}/{stype}", n, elapsed, status)
            if df is None:
                continue
            if sample_game_id is None and "GAME_ID" in df.columns and df.height:
                sample_game_id = df["GAME_ID"][0]
            frames.append(_normalize_game_logs(df, year, isp))

    if not frames:
        print("!! no game-log frames pulled")
        return [{"dataset": "game_logs", "n_rows": 0}]
    df = pl.concat(frames, how="diagonal_relaxed")
    meta = _dump(df, "game_logs")
    if sample_game_id:
        (config.RAW_DIR / "sample_game_id.txt").write_text(str(sample_game_id))
    return [meta]


# --------------------------------------------------------------------------- scale test
def pull_scale(refresh: bool) -> list[dict]:
    """One season of league-wide ShotChartDetail + one game of PlayByPlayV3 (the scale payloads)."""
    from nba_api.stats.endpoints import playbyplayv3 as pbp3
    from nba_api.stats.endpoints import shotchartdetail as scd

    metas = []
    sc_out = config.RAW_DIR / "shotchart_sample.parquet"
    if sc_out.exists() and not refresh:
        print("shotchart_sample.parquet cached — skip")
    else:
        n, df, status, elapsed = safe_rows(
            scd.ShotChartDetail, team_id=0, player_id=0,
            season_nullable=season_str(config.SCALE_SHOTCHART_YEAR),
            season_type_all_star="Regular Season", context_measure_simple="FGA")
        _record("scale_shotchart", "ShotChartDetail", season_str(config.SCALE_SHOTCHART_YEAR), n, elapsed, status)
        if df is not None:
            metas.append(_dump(df, "shotchart_sample"))

    pbp_out = config.RAW_DIR / "pbp_sample.parquet"
    gid_file = config.RAW_DIR / "sample_game_id.txt"
    if pbp_out.exists() and not refresh:
        print("pbp_sample.parquet cached — skip")
    elif gid_file.exists():
        gid = gid_file.read_text().strip()
        n, df, status, elapsed = safe_rows(pbp3.PlayByPlayV3, game_id=gid, start_period=0, end_period=14)
        _record("scale_pbp", "PlayByPlayV3", f"game={gid}", n, elapsed, status)
        if df is not None:
            metas.append(_dump(df, "pbp_sample"))
    else:
        print("no sample_game_id — run game_logs first for PBP scale test")
    return metas


# --------------------------------------------------------------------------- basketball-reference
def pull_bbref(refresh: bool) -> list[dict]:
    """Basketball-Reference advanced totals -> bbref_advanced.parquet (PER/BPM/VORP/WS)."""
    out = config.RAW_DIR / "bbref_advanced.parquet"
    if out.exists() and not refresh:
        print("bbref_advanced.parquet cached — skip")
        return [{"dataset": "bbref_advanced", "cached": True}]
    try:
        from basketball_reference_web_scraper import client
        t0 = time.perf_counter()
        rows = client.players_advanced_season_totals(season_end_year=config.BBREF_YEAR)
        elapsed = time.perf_counter() - t0
        # BBRef dicts carry nested enum/list fields (positions, team) that polars can't ingest —
        # extract only the scalar advanced metrics we need.
        def _num(v):
            return float(v) if v is not None else None
        clean = [{
            "bbref_slug": r.get("slug"),
            "full_name": r.get("name"),
            "season": config.BBREF_YEAR,
            "per": _num(r.get("player_efficiency_rating")),
            "bpm": _num(r.get("box_plus_minus")),
            "vorp": _num(r.get("value_over_replacement_player")),
            "ws": _num(r.get("win_shares")),
        } for r in rows]
        df = (pl.from_dicts(clean)
                .filter(pl.col("bbref_slug").is_not_null())
                .unique(subset=["bbref_slug"], keep="first"))  # first row per player = combined 'TOT'
        _record("bbref", "players_advanced_season_totals", f"{config.BBREF_YEAR}", df.height, elapsed, "ok")
    except Exception as e:  # noqa: BLE001
        _record("bbref", "players_advanced_season_totals", f"{config.BBREF_YEAR}", -1, 0.0, f"{type(e).__name__}: {str(e)[:70]}")
        print(f"!! BBRef pull failed: {e}")
        return [{"dataset": "bbref_advanced", "n_rows": 0}]
    return [_dump(df, "bbref_advanced")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="ignore cache, repull everything")
    ap.add_argument("--limit-agg", type=int, default=None, help="only the N most-recent aggregate seasons")
    ap.add_argument("--skip-scale", action="store_true")
    ap.add_argument("--skip-bbref", action="store_true")
    args = ap.parse_args()

    print("=" * 78)
    print(f"S1 PULL — modern era agg={config.AGG_START_YEAR}-{config.AGG_END_YEAR} "
          f"gamelogs={config.GAMELOG_YEARS[0]}-{config.GAMELOG_YEARS[-1]}")
    print("=" * 78)

    summary = []
    with timer() as total:
        summary += pull_aggregates(args.limit_agg, args.refresh)
        summary += pull_game_logs(args.refresh)
        if not args.skip_scale:
            summary += pull_scale(args.refresh)
        if not args.skip_bbref:
            summary += pull_bbref(args.refresh)
    wall = total()

    if METRICS:
        pl.from_dicts(METRICS).write_csv(config.RESULTS_DIR / "ingest_metrics.csv")
    live = [m for m in METRICS if m["status"] == "ok"]
    errs = [m for m in METRICS if m["status"] != "ok"]
    print("=" * 78)
    print(f"S1 done in {wall:.1f}s — {len(live)} ok calls, {len(errs)} errors. "
          f"metrics -> results/ingest_metrics.csv")
    if errs:
        print(f"  ERRORS: {[e['endpoint'] + ':' + e['status'][:30] for e in errs][:6]}")
    print(f"  datasets: {[s.get('dataset') for s in summary]}")


if __name__ == "__main__":
    main()
