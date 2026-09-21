"""S2 — materialize the five canonical tables into every candidate storage format.

The experiment's question is "which store is best for our NL->SQL answer engine?", so we write the
SAME five tables into EACH ``config.STORE_FORMATS`` and let S3 benchmark retrieval + parity across
them. This stage only BUILDS the stores (and records their on-disk footprint); it does not query.

Tables (raw parquet in ``config.RAW_DIR`` is the single source):
    game_logs, players, player_season, bbref_advanced, player_crosswalk

Formats (``config.STORE_FORMATS``):
    csv                  one <table>.csv per table (row-store text baseline)
    parquet_single       one <table>.parquet per table (columnar file)
    parquet_partitioned  Hive dir partitioned by season for season-bearing tables; single file else
    feather              one <table>.feather per table via polars write_ipc (uncompressed => mmap)
    duckdb               warehouse.duckdb, CREATE TABLE <t> AS SELECT * FROM read_parquet(raw)
    sqlite               warehouse.sqlite via stdlib sqlite3 + indexes (row-store OLTP reference)
    polars_mem           no disk; load_polars() returns {table: DataFrame} (in-RAM upper bound)
    lancedb              lancedb/ columnar tables (game_logs + player_season; optional dep)

All raw->store movement stays inside DuckDB / Polars / pyarrow — the only place we touch Python
tuples is the sqlite ``executemany`` (a C-level batch, not a hand-written per-row loop).

Records ``results/storage_sizes.csv`` (format, table, bytes, build_s); directory sizes are counted
recursively for the partitioned + lancedb stores.

Run:
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s2_build_stores.py
    python .../s2_build_stores.py --formats csv,parquet_single   # subset (dev)
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path

import polars as pl

import config
from pipeline._harness import timer

# The five canonical tables, and which of them carry a ``season`` column (=> partitionable).
TABLES = ["game_logs", "players", "player_season", "bbref_advanced", "player_crosswalk"]
SEASON_TABLES = {"game_logs", "player_season", "bbref_advanced"}


# --------------------------------------------------------------------------- small utilities
def raw_path(table: str) -> pathlib.Path:
    return config.RAW_DIR / f"{table}.parquet"


def _path_size(p: pathlib.Path) -> int:
    """Bytes on disk: a single file's size, or the recursive sum for a directory (0 if absent)."""
    p = pathlib.Path(p)
    if not p.exists():
        return 0
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def _fresh_dir(p: pathlib.Path) -> pathlib.Path:
    """Remove ``p`` if present, then recreate it — idempotent rebuilds, no stale partitions."""
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _rec(fmt: str, table: str, path: pathlib.Path, secs: float) -> dict:
    return {"format": fmt, "table": table, "bytes": _path_size(path), "build_s": round(secs, 4)}


# --------------------------------------------------------------------------- multi-file stores
def _build_multifile(fmt: str, ext: str, write_fn, records: list[dict]) -> None:
    """csv / parquet_single / feather: one file per table under STORES_DIR/<fmt>/."""
    d = _fresh_dir(config.STORES_DIR / fmt)
    for t in TABLES:
        df = pl.read_parquet(raw_path(t))
        path = d / f"{t}.{ext}"
        with timer() as tm:
            write_fn(df, path)
        records.append(_rec(fmt, t, path, tm()))


def build_csv(records: list[dict]) -> None:
    _build_multifile("csv", "csv", lambda df, p: df.write_csv(p), records)


def build_parquet_single(records: list[dict]) -> None:
    _build_multifile("parquet_single", "parquet", lambda df, p: df.write_parquet(p), records)


def build_feather(records: list[dict]) -> None:
    # Uncompressed Arrow IPC so the file is zero-copy mmap-able (the whole point of this candidate).
    _build_multifile("feather", "feather", lambda df, p: df.write_ipc(p, compression="uncompressed"), records)


def build_parquet_partitioned(records: list[dict]) -> None:
    """Hive-partition season-bearing tables by season; write the rest as a single parquet file."""
    import pyarrow.parquet as pq

    fmt = "parquet_partitioned"
    d = _fresh_dir(config.STORES_DIR / fmt)
    for t in TABLES:
        df = pl.read_parquet(raw_path(t))
        if t in SEASON_TABLES:
            target = d / t  # dataset dir: <table>/season=YYYY/*.parquet
            with timer() as tm:
                pq.write_to_dataset(df.to_arrow(), root_path=str(target), partition_cols=["season"])
            records.append(_rec(fmt, t, target, tm()))
        else:
            path = d / f"{t}.parquet"
            with timer() as tm:
                df.write_parquet(path)
            records.append(_rec(fmt, t, path, tm()))


# --------------------------------------------------------------------------- single-file stores
def build_duckdb(records: list[dict]) -> None:
    """Load every table into warehouse.duckdb straight from parquet (no Python row handling).

    Per-table ``bytes`` is the file-size delta after CHECKPOINT, so the rows sum to the on-disk
    footprint while ``build_s`` stays an accurate per-table load time.
    """
    import duckdb

    dbfile = config.STORES_DIR / "warehouse.duckdb"
    if dbfile.exists():
        dbfile.unlink()
    con = duckdb.connect(str(dbfile))
    running = 0
    try:
        for t in TABLES:
            rp = str(raw_path(t)).replace("'", "''")
            with timer() as tm:
                con.execute(f"CREATE TABLE {t} AS SELECT * FROM read_parquet('{rp}')")
                con.execute("CHECKPOINT")
            cur = dbfile.stat().st_size
            records.append({"format": "duckdb", "table": t, "bytes": max(cur - running, 0),
                            "build_s": round(tm(), 4)})
            running = cur
    finally:
        con.close()


# polars dtype -> sqlite column affinity (sqlite is dynamically typed; the declared type only
# affects storage affinity + index behavior). Temporal columns are stringified before insert.
def _sqlite_type(dt) -> str:
    if dt in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
              pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Boolean):
        return "INTEGER"
    if dt in (pl.Float32, pl.Float64):
        return "REAL"
    return "TEXT"


def _is_temporal(dt) -> bool:
    return dt in (pl.Date, pl.Time) or isinstance(dt, (pl.Datetime, pl.Duration))


def _sqlite_castable(df: pl.DataFrame) -> pl.DataFrame:
    """Stringify temporal columns — sqlite3 has no date type and dropped its date adapters in 3.12."""
    temporal = [c for c, dt in zip(df.columns, df.dtypes) if _is_temporal(dt)]
    if temporal:
        df = df.with_columns([pl.col(c).cast(pl.Utf8) for c in temporal])
    return df


# Indexes that make the OLTP-style lookups in the eval set fast on the row-store.
_SQLITE_INDEXES = {
    "game_logs": 'CREATE INDEX idx_gl_player_season ON game_logs(player_id, season)',
    "player_season": 'CREATE INDEX idx_ps_season_type ON player_season(season, season_type)',
}


def build_sqlite(records: list[dict]) -> None:
    """Build warehouse.sqlite with stdlib sqlite3: typed CREATE TABLE + batch executemany + indexes."""
    import sqlite3

    dbfile = config.STORES_DIR / "warehouse.sqlite"
    if dbfile.exists():
        dbfile.unlink()
    con = sqlite3.connect(str(dbfile))
    running = 0
    try:
        for t in TABLES:
            df = _sqlite_castable(pl.read_parquet(raw_path(t)))
            cols = df.columns
            coldefs = ", ".join(f'"{c}" {_sqlite_type(dt)}' for c, dt in zip(cols, df.dtypes))
            placeholders = ", ".join(["?"] * len(cols))
            with timer() as tm:
                con.execute(f'DROP TABLE IF EXISTS "{t}"')
                con.execute(f'CREATE TABLE "{t}" ({coldefs})')
                # df.rows() materializes tuples in Rust; executemany is a single C-level batch.
                con.executemany(f'INSERT INTO "{t}" VALUES ({placeholders})', df.rows())
                if t in _SQLITE_INDEXES:
                    con.execute(_SQLITE_INDEXES[t])
                con.commit()
            cur = dbfile.stat().st_size
            records.append({"format": "sqlite", "table": t, "bytes": max(cur - running, 0),
                            "build_s": round(tm(), 4)})
            running = cur
    finally:
        con.close()


# --------------------------------------------------------------------------- in-memory store
def load_polars() -> dict[str, pl.DataFrame]:
    """polars_mem store: read every table's raw parquet into an in-RAM dict (no disk artifact)."""
    return {t: pl.read_parquet(raw_path(t)) for t in TABLES}


def build_polars_mem(records: list[dict]) -> None:
    """No disk write. Record each table's in-RAM footprint (estimated_size) as the 'no-disk' bound."""
    for t in TABLES:
        with timer() as tm:
            df = pl.read_parquet(raw_path(t))
        records.append({"format": "polars_mem", "table": t,
                        "bytes": int(df.estimated_size()), "build_s": round(tm(), 4)})


# --------------------------------------------------------------------------- columnar+vector store
def build_lancedb(records: list[dict]) -> None:
    """Write game_logs + player_season as lancedb columnar tables (no vectors). Optional dependency."""
    try:
        import lancedb
    except Exception as e:  # noqa: BLE001 — optional dep: degrade, never crash the whole build
        print(f"  [skip] lancedb unavailable ({type(e).__name__}: {str(e)[:60]}) — skipping store")
        return

    d = _fresh_dir(config.STORES_DIR / "lancedb")
    db = lancedb.connect(str(d))
    for t in ("game_logs", "player_season"):
        df = pl.read_parquet(raw_path(t))
        with timer() as tm:
            db.create_table(t, df.to_arrow(), mode="overwrite")
        records.append(_rec("lancedb", t, d / f"{t}.lance", tm()))


# --------------------------------------------------------------------------- orchestration
_BUILDERS = {
    "csv": build_csv,
    "parquet_single": build_parquet_single,
    "parquet_partitioned": build_parquet_partitioned,
    "feather": build_feather,
    "duckdb": build_duckdb,
    "sqlite": build_sqlite,
    "polars_mem": build_polars_mem,
    "lancedb": build_lancedb,
}


def _ensure_crosswalk() -> None:
    """player_crosswalk.parquet is produced by s2_crosswalk; build it on demand if absent."""
    if raw_path("player_crosswalk").exists():
        return
    print("player_crosswalk.parquet missing — building it first (s2_crosswalk)")
    from pipeline.s2_crosswalk import build_crosswalk
    build_crosswalk()


def build_all(formats: list[str] | None = None) -> list[dict]:
    """Materialize every table into every requested format; write results/storage_sizes.csv."""
    _ensure_crosswalk()
    missing = [t for t in TABLES if not raw_path(t).exists()]
    if missing:
        raise FileNotFoundError(f"raw parquet missing for tables {missing} — run s1_pull first")

    formats = formats or config.STORE_FORMATS
    records: list[dict] = []
    for fmt in formats:
        fn = _BUILDERS.get(fmt)
        if fn is None:
            print(f"  [skip] unknown format '{fmt}' (not in _BUILDERS)")
            continue
        print(f"[build] {fmt}")
        try:
            fn(records)
        except Exception as e:  # noqa: BLE001 — one store's failure must not sink the rest
            print(f"  !! {fmt} failed: {type(e).__name__}: {e}")

    if records:
        out = config.RESULTS_DIR / "storage_sizes.csv"
        (pl.from_dicts(records)
           .select(["format", "table", "bytes", "build_s"])
           .write_csv(out))
        print(f"\nstorage sizes -> {out}")
    return records


def _print_summary(records: list[dict]) -> None:
    if not records:
        print("no stores built.")
        return
    agg: dict[str, dict] = {}
    for r in records:
        a = agg.setdefault(r["format"], {"bytes": 0, "build_s": 0.0, "n": 0})
        a["bytes"] += r["bytes"]
        a["build_s"] += r["build_s"]
        a["n"] += 1
    print("=" * 62)
    print(f"{'format':22s} {'tables':>6s} {'size_MB':>10s} {'build_s':>10s}")
    print("-" * 62)
    for fmt, a in sorted(agg.items(), key=lambda kv: kv[1]["bytes"], reverse=True):
        print(f"{fmt:22s} {a['n']:>6d} {a['bytes'] / 1e6:>10.2f} {a['build_s']:>10.2f}")
    print("=" * 62)
    print("note: polars_mem 'size' is an in-RAM estimate, not a disk footprint.")


def main():
    ap = argparse.ArgumentParser(description="Build every storage-format store for the benchmark.")
    ap.add_argument("--formats", type=str, default=None,
                    help="comma-separated subset of config.STORE_FORMATS (default: all)")
    args = ap.parse_args()
    formats = [f.strip() for f in args.formats.split(",")] if args.formats else None

    print("=" * 62)
    print(f"S2 BUILD STORES — {len(formats or config.STORE_FORMATS)} formats x {len(TABLES)} tables")
    print("=" * 62)
    with timer() as total:
        records = build_all(formats)
    _print_summary(records)
    print(f"S2 done in {total():.1f}s")


if __name__ == "__main__":
    main()
