"""S3 — Resolve the golden eval set, then benchmark every storage backend on retrieval.

Three responsibilities (see the SPEC / ../docs/findings/DECISIONS.md):

  1. resolve_eval()  — run each eval item's `canonical_sql` on the DuckDB warehouse (S2 built it)
     and freeze the answer as `expected_value` into a NEW file `eval_set_resolved.json`. The
     original `eval_set.json` is NEVER mutated. Optional public `known` anchors are checked with the
     soft `known_tolerance` and only *warn* — they are informational, never a gate.

  2. correctness — for EVERY store x EVERY eval item, run the SAME canonical_sql and compare to the
     resolved expected_value with the two-tier gate (numeric abs <= item.tolerance; counts exact via
     tolerance 0; strings case-insensitive). A store that returns a wrong value is written
     correct=false — NEVER silently dropped. -> results/correctness.csv

  3. timing — for every store x every eval item PLUS three extra OLAP workloads (corr, a partition-
     pruning season-range scan, and a full-season leaderboard group-by WITH the min-games qualifier)
     time a COLD pass (bench reps=5, warmup=0) and a WARM pass (bench defaults). -> results/timings.csv

NON-NEGOTIABLES honored here:
  * DuckDB (or native sqlite3) does ALL arithmetic — Python never computes a statistic; it only reads
    the scalar a query returns and compares numbers.
  * Every leaderboard workload applies config.MIN_GAMES_QUALIFIER.
  * Optional backends (duckdb's sqlite extension, lancedb, ...) degrade gracefully: a missing dep or a
    store that S2 did not build is SKIPPED with a printed note, never a crash.

Each backend is exposed through DuckDB so the canonical SQL runs verbatim (csv/parquet/feather/sqlite/
polars_mem/lancedb all become views/registered relations on a fresh in-memory DuckDB connection; the
`duckdb` store uses the native warehouse tables on their own connection). The `sqlite` store is ALSO
benchmarked through the native sqlite3 engine as a separate row labeled `sqlite_native`.

Run (from the repo root, with the uv venv active):
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s3_bench_retrieval.py
    python .../s3_bench_retrieval.py --quick                      # tiny reps, fast smoke
    python .../s3_bench_retrieval.py --stores duckdb,parquet_single,sqlite_native
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path

import duckdb
import polars as pl

import config
from pipeline._harness import bench, timer

# The five logical tables the eval set queries (see eval_set.json meta.tables). shotchart/pbp are
# scale payloads, not part of the correctness workload, so they are intentionally not exposed here.
TABLES = ["game_logs", "players", "player_season", "bbref_advanced", "player_crosswalk"]

# COLD bench params are fixed by the SPEC (reps=5, no warmup). WARM uses _harness.bench defaults
# (config.BENCH_REPS / BENCH_WARMUP). --quick shrinks both for a fast smoke.
COLD_REPS = 5
COLD_WARMUP = 0
QUICK_COLD_REPS = 2
QUICK_WARM_REPS = 4
QUICK_WARM_WARMUP = 1

# The full store roster: every candidate format + the native-sqlite reference row.
ALL_STORES = list(config.STORE_FORMATS) + ["sqlite_native"]

WAREHOUSE = config.STORES_DIR / "warehouse.duckdb"


# ============================================================================ engines
class DuckEngine:
    """A DuckDB connection where the five tables are queryable. `keep()` pins registered frames
    (polars / arrow) so they are not garbage-collected while the store is being benchmarked."""

    def __init__(self, con: "duckdb.DuckDBPyConnection"):
        self.con = con
        self._keep: dict = {}

    def keep(self, name: str, obj) -> None:
        self._keep[name] = obj

    def run(self, sql: str):
        return self.con.execute(sql).fetchall()

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:  # noqa: BLE001
            pass
        self._keep.clear()


class SqliteEngine:
    """A native stdlib-sqlite3 connection — the OLTP B-tree reference (row labeled `sqlite_native`)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def run(self, sql: str):
        return self.conn.execute(sql).fetchall()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass


def exec_scalar(engine, sql: str):
    """Run `sql`, return (scalar, n_rows, err). scalar = first column of the first row (queries end
    in `... AS answer`). NEVER raises: on any failure returns (None, -1, 'ExcType: msg')."""
    try:
        rows = engine.run(sql)
        scalar = rows[0][0] if rows and len(rows[0]) else None
        return scalar, len(rows), None
    except Exception as e:  # noqa: BLE001 - a store that errors is recorded, never fatal
        return None, -1, f"{type(e).__name__}: {str(e)[:100]}"


# ============================================================================ path helpers
def _p(path: pathlib.Path) -> str:
    """SQL-safe string for a path literal (escape single quotes)."""
    return str(path).replace("'", "''")


def _first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None


def _sqlite_file():
    """Probe the conventional locations S2 may write the sqlite store to."""
    return _first_existing([
        config.STORES_DIR / "sqlite" / "warehouse.sqlite",
        config.STORES_DIR / "sqlite" / "warehouse.db",
        config.STORES_DIR / "sqlite" / "store.sqlite",
        config.STORES_DIR / "warehouse.sqlite",
        config.STORES_DIR / "sqlite.db",
        config.STORES_DIR / "warehouse.db",
    ])


def load_polars() -> dict:
    """Load the five tables into polars from the best available on-disk source (the in-memory
    upper-bound store). Prefers the parquet_single store (it carries the S2-built player_crosswalk,
    which is NOT in data/raw), then csv/feather stores, then raw parquet as a last resort."""
    frames: dict[str, pl.DataFrame] = {}
    for t in TABLES:
        src = _first_existing([
            config.STORES_DIR / "parquet_single" / f"{t}.parquet",
            config.STORES_DIR / "csv" / f"{t}.csv",
            config.STORES_DIR / "feather" / f"{t}.feather",
            config.RAW_DIR / f"{t}.parquet",
        ])
        if src is None:
            continue
        try:
            if src.suffix == ".parquet":
                frames[t] = pl.read_parquet(src)
            elif src.suffix == ".csv":
                frames[t] = pl.read_csv(src)
            elif src.suffix == ".feather":
                frames[t] = pl.read_ipc(src)
        except Exception as e:  # noqa: BLE001
            print(f"    (polars_mem: could not load {t} from {src.name}: {type(e).__name__})")
    return frames


# ============================================================================ store setup
def _expose(con, store: str, eng: DuckEngine) -> bool:
    """CREATE OR REPLACE VIEW (or register) the five tables on `con` for `store`. Returns True if at
    least one table was exposed (missing tables just make their dependent queries error -> recorded)."""
    exposed = 0

    if store == "csv":
        d = config.STORES_DIR / "csv"
        for t in TABLES:
            f = d / f"{t}.csv"
            if f.exists():
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_csv_auto('{_p(f)}')")
                exposed += 1

    elif store == "parquet_single":
        d = config.STORES_DIR / "parquet_single"
        for t in TABLES:
            f = d / f"{t}.parquet"
            if f.exists():
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('{_p(f)}')")
                exposed += 1

    elif store == "parquet_partitioned":
        d = config.STORES_DIR / "parquet_partitioned"
        for t in TABLES:
            dir_ = d / t
            single = d / f"{t}.parquet"
            if dir_.is_dir():
                glob = dir_ / "**" / "*.parquet"
                con.execute(
                    f"CREATE OR REPLACE VIEW {t} AS "
                    f"SELECT * FROM read_parquet('{_p(glob)}', hive_partitioning=true)")
                exposed += 1
            elif single.exists():  # small dims may be stored unpartitioned
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('{_p(single)}')")
                exposed += 1

    elif store == "feather":
        d = config.STORES_DIR / "feather"
        for t in TABLES:
            f = _first_existing([d / f"{t}.feather", d / f"{t}.arrow", d / f"{t}.ipc"])
            if f is not None:
                try:
                    df = pl.read_ipc(f)
                    eng.keep(t, df)
                    con.register(t, df)
                    exposed += 1
                except Exception as e:  # noqa: BLE001
                    print(f"    (feather: {t} unreadable: {type(e).__name__})")

    elif store == "polars_mem":
        for t, df in load_polars().items():
            eng.keep(t, df)
            con.register(t, df)
            exposed += 1

    elif store == "sqlite":
        f = _sqlite_file()
        if f is None:
            return False
        try:
            try:
                con.execute("INSTALL sqlite")
                con.execute("LOAD sqlite")
            except Exception:  # noqa: BLE001 - some builds ship it as sqlite_scanner
                con.execute("INSTALL sqlite_scanner")
                con.execute("LOAD sqlite_scanner")
            con.execute(f"ATTACH '{_p(f)}' AS sq (TYPE sqlite, READ_ONLY)")
        except Exception as e:  # noqa: BLE001
            print(f"    (sqlite via duckdb unavailable: {type(e).__name__}; sqlite_native still runs)")
            return False
        for t in TABLES:
            try:
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM sq.{t}")
                exposed += 1
            except Exception:  # noqa: BLE001 - table absent in the sqlite store
                pass

    elif store == "lancedb":
        return _expose_lancedb(con, eng)

    else:
        return False

    return exposed > 0


def _expose_lancedb(con, eng: DuckEngine) -> bool:
    """Optional columnar+vector store. Import defensively — lancedb may be uninstalled; if so, skip."""
    try:
        import lancedb  # noqa: F401
    except Exception:  # noqa: BLE001
        print("    (lancedb not installed — store skipped)")
        return False
    d = config.STORES_DIR / "lancedb"
    if not d.exists():
        return False
    try:
        db = lancedb.connect(str(d))
        names = set(db.table_names())
    except Exception as e:  # noqa: BLE001
        print(f"    (lancedb open failed: {type(e).__name__})")
        return False
    exposed = 0
    for t in TABLES:
        if t in names:
            try:
                arrow_tbl = db.open_table(t).to_arrow()
                eng.keep(t, arrow_tbl)
                con.register(t, arrow_tbl)
                exposed += 1
            except Exception:  # noqa: BLE001
                pass
    return exposed > 0


def setup_store(store: str):
    """Return a ready DuckEngine/SqliteEngine for `store`, or None if its artifacts are absent."""
    if store == "duckdb":
        if not WAREHOUSE.exists():
            return None
        try:
            con = duckdb.connect(str(WAREHOUSE), read_only=True)
        except Exception:  # noqa: BLE001
            try:
                con = duckdb.connect(str(WAREHOUSE))
            except Exception:  # noqa: BLE001
                return None
        return DuckEngine(con)

    if store == "sqlite_native":
        f = _sqlite_file()
        if f is None:
            return None
        try:
            conn = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
        except Exception:  # noqa: BLE001
            try:
                conn = sqlite3.connect(str(f))
            except Exception:  # noqa: BLE001
                return None
        return SqliteEngine(conn)

    # Every other backend runs on a fresh in-memory DuckDB with the five tables as views/relations.
    con = duckdb.connect()
    eng = DuckEngine(con)
    if not _expose(con, store, eng):
        eng.close()
        return None
    return eng


# ============================================================================ correctness gate
def check_correct(item: dict, got, err) -> bool:
    """Two-tier correctness gate against the resolved expected_value."""
    if err is not None:
        return False
    exp = item.get("expected_value")
    if exp is None:
        return False
    if item.get("answer_type") == "string":
        return str(got).strip().lower() == str(exp).strip().lower()
    # numeric (tolerance 0 => counts must be exact)
    tol = item.get("tolerance", 0) or 0
    try:
        return abs(float(got) - float(exp)) <= tol
    except (TypeError, ValueError):
        return False


def _jsonable(v):
    """Coerce a DB scalar to a JSON/CSV-friendly python value."""
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    try:
        import decimal
        if isinstance(v, decimal.Decimal):
            return float(v)
    except Exception:  # noqa: BLE001
        pass
    try:
        return float(v)
    except (TypeError, ValueError):
        return str(v)


# ============================================================================ resolve
def resolve_eval() -> dict:
    """Run every canonical_sql on the DuckDB warehouse, freeze expected_value into
    eval_set_resolved.json (eval_set.json untouched). Returns the resolved data dict."""
    if not WAREHOUSE.exists():
        print(f"!! warehouse not found at {WAREHOUSE} — run S2 (store builder) first.")
        sys.exit(1)

    with open(config.EVAL_SET, encoding="utf-8") as fh:
        data = json.load(fh)
    meta = data.get("meta", {})
    ktol = meta.get("known_tolerance", 0.1)

    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    eng = DuckEngine(con)
    print(f"resolve_eval — {len(data['items'])} items on {WAREHOUSE.name}")
    for item in data["items"]:
        scalar, _rows, err = exec_scalar(eng, item["canonical_sql"])
        if err is not None:
            print(f"  [ERR] {item['id']:32s} {err}")
            item["expected_value"] = None
            continue
        item["expected_value"] = _jsonable(scalar)
        # informational soft anchor check (never fatal)
        known = item.get("known")
        if known is not None:
            if item.get("answer_type") == "numeric":
                try:
                    if abs(float(scalar) - float(known)) > ktol:
                        print(f"  WARN {item['id']}: resolved {scalar} vs known {known} "
                              f"(> known_tolerance {ktol})")
                except (TypeError, ValueError):
                    print(f"  WARN {item['id']}: non-numeric resolved {scalar!r} vs known {known!r}")
            else:
                if str(scalar).strip().lower() != str(known).strip().lower():
                    print(f"  WARN {item['id']}: resolved {scalar!r} vs known {known!r}")
        print(f"  [ok ] {item['id']:32s} -> {item['expected_value']!r}")
    eng.close()

    out = config.EXP_ROOT / "eval_set_resolved.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    print(f"resolve_eval — wrote {out}")
    return data


# ============================================================================ extra OLAP workloads
def extra_workloads() -> list[dict]:
    """Three timing-only OLAP probes beyond the eval items. Leaderboard uses MIN_GAMES_QUALIFIER."""
    q = config.MIN_GAMES_QUALIFIER
    return [
        {"id": "olap_corr_min_pts", "workload": "OLAP",
         "sql": 'SELECT corr("min", "pts") AS answer FROM game_logs'},
        {"id": "olap_season_range_scan", "workload": "OLAP",
         "sql": ("SELECT AVG(pts) AS answer FROM game_logs "
                 "WHERE season BETWEEN 2023 AND 2025 AND is_playoff = 0")},
        {"id": "olap_leaderboard_minGP", "workload": "OLAP",
         "sql": ("SELECT player_id, AVG(pts) AS ppg FROM game_logs "
                 "WHERE season = 2025 AND is_playoff = 0 "
                 f"GROUP BY player_id HAVING COUNT(*) >= {q} ORDER BY ppg DESC LIMIT 1")},
    ]


# ============================================================================ bench one workload
def _bench_one(eng, store, item_id, workload, sql, quick, corr_rows, time_rows, item=None):
    """Run one (store x workload): record correctness (if `item` given) and cold/warm timings."""
    got, nrows, err = exec_scalar(eng, sql)

    if corr_rows is not None and item is not None:
        correct = check_correct(item, got, err)
        corr_rows.append({
            "store": store, "item": item_id, "workload": workload,
            "correct": correct,
            "got": (err if err is not None else _jsonable(got)),
            "expected": item.get("expected_value"),
        })

    if err is not None:  # query unsupported/failed on this store — record, don't time, don't crash
        time_rows.append({
            "store": store, "item": item_id, "workload": workload,
            "cold_p50_ms": None, "warm_p50_ms": None, "warm_p95_ms": None,
            "warm_mean_ms": None, "warm_stdev_ms": None, "rows": -1,
        })
        return

    fn = lambda: eng.run(sql)  # noqa: E731 - zero-arg callable for the harness
    if quick:
        cold = bench(fn, reps=QUICK_COLD_REPS, warmup=COLD_WARMUP, label=f"{store}:{item_id}:cold")
        warm = bench(fn, reps=QUICK_WARM_REPS, warmup=QUICK_WARM_WARMUP, label=f"{store}:{item_id}:warm")
    else:
        cold = bench(fn, reps=COLD_REPS, warmup=COLD_WARMUP, label=f"{store}:{item_id}:cold")
        warm = bench(fn, label=f"{store}:{item_id}:warm")  # harness defaults (reps=25, warmup=3)

    time_rows.append({
        "store": store, "item": item_id, "workload": workload,
        "cold_p50_ms": cold["p50_ms"], "warm_p50_ms": warm["p50_ms"], "warm_p95_ms": warm["p95_ms"],
        "warm_mean_ms": warm["mean_ms"], "warm_stdev_ms": warm["stdev_ms"], "rows": nrows,
    })


def _write_csv(path: pathlib.Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="tiny bench reps for a fast smoke run")
    ap.add_argument("--stores", type=str, default=None,
                    help="comma-separated subset of stores to benchmark (default: all)")
    args = ap.parse_args()

    print("=" * 78)
    print("S3 RESOLVE + BENCH")
    print("=" * 78)

    data = resolve_eval()
    items = data["items"]
    extras = extra_workloads()

    stores = ALL_STORES
    if args.stores:
        want = {s.strip() for s in args.stores.split(",") if s.strip()}
        stores = [s for s in ALL_STORES if s in want]
        unknown = want - set(ALL_STORES)
        if unknown:
            print(f"  (ignoring unknown store(s): {sorted(unknown)})")

    corr_rows: list[dict] = []
    time_rows: list[dict] = []
    skipped: list[str] = []

    print("-" * 78)
    print(f"benchmarking {len(stores)} store(s) x {len(items)} eval items + {len(extras)} OLAP extras "
          f"({'QUICK' if args.quick else 'full'} reps)")
    for store in stores:
        with timer() as t:
            eng = setup_store(store)
        if eng is None:
            skipped.append(store)
            print(f"  SKIP {store:22s} (artifacts not found / backend unavailable)")
            continue
        print(f"  bench {store:22s} (setup {t() * 1000:6.1f} ms)")
        try:
            for item in items:
                _bench_one(eng, store, item["id"], item["workload"], item["canonical_sql"],
                           args.quick, corr_rows, time_rows, item=item)
            for ex in extras:  # timing only (no expected_value to gate on)
                _bench_one(eng, store, ex["id"], ex["workload"], ex["sql"],
                           args.quick, corr_rows=None, time_rows=time_rows, item=None)
        finally:
            eng.close()

    _write_csv(config.RESULTS_DIR / "correctness.csv", corr_rows,
               ["store", "item", "workload", "correct", "got", "expected"])
    _write_csv(config.RESULTS_DIR / "timings.csv", time_rows,
               ["store", "item", "workload", "cold_p50_ms", "warm_p50_ms", "warm_p95_ms",
                "warm_mean_ms", "warm_stdev_ms", "rows"])

    # summary
    print("=" * 78)
    by_store: dict[str, list[int]] = {}
    for r in corr_rows:
        c = by_store.setdefault(r["store"], [0, 0])
        c[1] += 1
        if r["correct"]:
            c[0] += 1
    for store, (ok, tot) in by_store.items():
        flag = "OK " if ok == tot else "!! "
        print(f"  {flag}{store:22s} correctness {ok}/{tot}")
    if skipped:
        print(f"  skipped: {skipped}")
    print(f"S3 done — correctness.csv ({len(corr_rows)} rows), timings.csv ({len(time_rows)} rows) "
          f"-> {config.RESULTS_DIR}")


if __name__ == "__main__":
    main()
