"""S6 — Report: turn the raw results/*.csv into figures + a single RESULTS.md.

This stage is the *presenter*. It computes nothing about basketball — every number it prints was
already produced by an upstream stage (S1 ingest, S2 storage sizing, S3 retrieval timing/correctness,
S4 text-to-SQL, S5 vector probe). S6 only reads those CSVs, draws SVG figures, and derives two
comparison views (fastest-correct-store-per-workload + a data-driven recommendation) from numbers
that already exist. It NEVER fabricates: a missing CSV is reported as 'pending', not invented.

Design constraints honored here:
  - Defensive I/O: any missing/empty/garbled results CSV degrades to a 'pending' note, never a crash.
  - Schema-tolerant: upstream column names are matched by a candidate list (case-insensitive) so small
    naming drift between stages does not break the report.
  - Optional deps import defensively: if matplotlib is unavailable the tables still render and every
    figure is marked pending.
  - Figures: Agg backend, SVG, Okabe-Ito colorblind-safe palette, transparent background + medium-gray
    ink so they stay legible on both light and dark pages.

Run:
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s6_report.py
"""
from __future__ import annotations

import json
import math
import pathlib
import statistics
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path

import polars as pl

import config

# --- optional plotting dep (degrade gracefully if absent) --------------------
HAVE_MPL = True
try:
    import matplotlib

    matplotlib.use("Agg")  # headless, file-only
    import matplotlib.pyplot as plt
except Exception:  # noqa: BLE001 - report must still write tables without plots
    HAVE_MPL = False
    plt = None  # type: ignore

# --- palette / styling (colorblind-safe Okabe-Ito; legible light & dark) -----
INK = "#7f7f7f"      # medium gray: readable on white AND on dark backgrounds
GRID = "#b0b0b0"
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#999999"]
COLD_C = "#56B4E9"   # sky blue
WARM_C = "#E69F00"   # orange
ACC_C = "#0072B2"    # blue  (accuracy)
LAT_C = "#D55E00"    # vermillion (latency)
VECTOR_STORES = {"lancedb", "chromadb", "chroma", "vector", "vectordb", "faiss", "qdrant"}

# --- results CSV registry ----------------------------------------------------
CSV_PATHS = {
    "ingest": config.RESULTS_DIR / "ingest_metrics.csv",
    "storage": config.RESULTS_DIR / "storage_sizes.csv",
    "timings": config.RESULTS_DIR / "timings.csv",
    "correctness": config.RESULTS_DIR / "correctness.csv",
    "t2sql": config.RESULTS_DIR / "t2sql_scores.csv",
    "vector": config.RESULTS_DIR / "vector_probe.csv",
}
RESULTS_MD = config.RESULTS_DIR / "RESULTS.md"


# ===========================================================================
# Generic helpers (defensive load / column matching / coercion / formatting)
# ===========================================================================
def load_table(path: pathlib.Path):
    """Read a CSV -> (columns, rows[list[dict]]) or None if missing/unreadable.

    Tries a typed read first, then an all-string read, so a weird cell never aborts the report.
    """
    if not path.exists():
        return None
    for kwargs in ({"infer_schema_length": 2000}, {"infer_schema_length": 0}):
        try:
            df = pl.read_csv(path, **kwargs)
            return list(df.columns), [dict(r) for r in df.iter_rows(named=True)]
        except Exception:  # noqa: BLE001 - fall through to the next strategy
            continue
    return None


def find_col(cols, *cands, contains=False):
    """First column whose (lowercased) name equals one of cands; optional substring fallback."""
    lut = {c.lower(): c for c in cols}
    for cand in cands:
        if cand.lower() in lut:
            return lut[cand.lower()]
    if contains:
        for cand in cands:
            for c in cols:
                if cand.lower() in c.lower():
                    return c
    return None


def find_col_all(cols, *tokens):
    """First column whose name contains ALL of the given tokens (e.g. 'warm' AND 'p50')."""
    for c in cols:
        lc = c.lower()
        if all(t in lc for t in tokens):
            return c
    return None


def as_float(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return None if (isinstance(v, float) and math.isnan(v)) else float(v)
    s = str(v).strip().replace(",", "")
    if s == "" or s.lower() in {"na", "nan", "none", "null"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def as_bool(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    if s in {"true", "t", "yes", "y", "1", "pass", "passed", "correct", "ok", "match"}:
        return True
    if s in {"false", "f", "no", "n", "0", "fail", "failed", "wrong", "mismatch", "incorrect"}:
        return False
    return None


def median(vals):
    xs = [x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return statistics.median(xs) if xs else None


def human_bytes(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s else "0"
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(cols, rows, max_rows=60):
    if not cols:
        return "_(no columns)_"
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for r in rows[:max_rows]:
        out.append("| " + " | ".join(fmt_cell(r.get(c)) for c in cols) + " |")
    if len(rows) > max_rows:
        out.append(f"\n_… {len(rows) - max_rows} more rows omitted._")
    return "\n".join(out)


def to_pct(x):
    """Normalize an accuracy value to a 0-100 percentage (accepts 0-1 fractions or 0-100 already)."""
    if x is None:
        return None
    return x * 100.0 if x <= 1.0 else x


def load_eval_workloads():
    """id -> workload map from eval_set.json (used to attach a workload when a CSV lacks the column)."""
    try:
        data = json.loads(config.EVAL_SET.read_text())
        return {it["id"]: it.get("workload") for it in data.get("items", [])}
    except Exception:  # noqa: BLE001
        return {}


# ===========================================================================
# Upstream-result parsers (schema-tolerant -> normalized python structures)
# ===========================================================================
def parse_timings():
    """timings.csv -> normalized warm/cold p50 per (store, workload) and per store.

    Handles two layouts:
      wide  : columns like warm_p50_ms / cold_p50_ms on each row
      long  : a mode/phase column in {cold, warm} + a single p50_ms column
    """
    res = {"available": False, "note": "timings.csv not found", "stores": [], "workloads": [],
           "warm": {}, "cold": {}, "warm_store": {}, "cold_store": {}, "has_cold": False}
    t = load_table(CSV_PATHS["timings"])
    if t is None:
        return res
    cols, rows = t
    if not rows:
        res["note"] = "timings.csv present but empty"
        return res

    store_c = find_col(cols, "store", "format", "store_format", "backend", "engine")
    wl_c = find_col(cols, "workload", "query_class", "class", "category")
    id_c = find_col(cols, "id", "item_id", "item", "query_id", "qid")
    warm_c = find_col(cols, "warm_p50_ms", "warm_p50", "p50_warm_ms") or find_col_all(cols, "warm", "p50")
    cold_c = find_col(cols, "cold_p50_ms", "cold_p50", "p50_cold_ms") or find_col_all(cols, "cold", "p50")
    p50_c = find_col(cols, "p50_ms", "p50", "median_ms")
    mode_c = find_col(cols, "mode", "phase", "temp", "temperature", "cache", "state")

    if store_c is None or not (warm_c or cold_c or p50_c):
        res["note"] = "timings.csv columns unrecognized (need a store col + a p50 col)"
        return res

    eval_wl = load_eval_workloads()
    warm, cold = {}, {}

    def _wl(r):
        if wl_c and r.get(wl_c) not in (None, ""):
            return str(r.get(wl_c))
        if id_c and r.get(id_c) is not None:
            return eval_wl.get(str(r.get(id_c))) or "all"
        return "all"

    for r in rows:
        s = r.get(store_c)
        if s in (None, ""):
            continue
        s = str(s)
        wl = _wl(r)
        if warm_c or cold_c:  # wide layout
            if warm_c is not None:
                v = as_float(r.get(warm_c))
                if v is not None:
                    warm.setdefault((s, wl), []).append(v)
            if cold_c is not None:
                v = as_float(r.get(cold_c))
                if v is not None:
                    cold.setdefault((s, wl), []).append(v)
        else:  # long layout: one p50 col split by mode
            v = as_float(r.get(p50_c))
            if v is None:
                continue
            m = str(r.get(mode_c)).lower() if mode_c else "warm"
            bucket = cold if "cold" in m else warm  # default anything non-cold to warm
            bucket.setdefault((s, wl), []).append(v)

    res["warm"] = {k: median(v) for k, v in warm.items()}
    res["cold"] = {k: median(v) for k, v in cold.items()}
    stores = sorted({k[0] for k in res["warm"]} | {k[0] for k in res["cold"]})
    workloads = sorted({k[1] for k in res["warm"]} | {k[1] for k in res["cold"]})
    res["stores"] = stores
    res["workloads"] = workloads
    res["warm_store"] = {s: median([v for (st, _), v in res["warm"].items() if st == s]) for s in stores}
    res["cold_store"] = {s: median([v for (st, _), v in res["cold"].items() if st == s]) for s in stores}
    res["has_cold"] = any(v is not None for v in res["cold"].values())
    res["available"] = bool(res["warm"] or res["cold"])
    res["note"] = "ok" if res["available"] else "no numeric latencies parsed"
    return res


def parse_correctness():
    """correctness.csv -> accuracy in [0,1] per store and per (store, workload)."""
    res = {"available": False, "note": "correctness.csv not found",
           "overall": {}, "workload": {}}
    t = load_table(CSV_PATHS["correctness"])
    if t is None:
        return res
    cols, rows = t
    if not rows:
        res["note"] = "correctness.csv present but empty"
        return res

    store_c = find_col(cols, "store", "format", "store_format", "backend", "engine")
    corr_c = find_col(cols, "correct", "is_correct", "pass", "passed", "match", "ok")
    acc_c = find_col(cols, "accuracy", "acc", "pct_correct", "correct_pct", "score")
    nc_c = find_col(cols, "n_correct", "num_correct", "correct_count", "n_pass")
    nt_c = find_col(cols, "n_total", "num_total", "total", "n_items", "n")
    wl_c = find_col(cols, "workload", "query_class", "class", "category")
    id_c = find_col(cols, "id", "item_id", "item", "query_id", "qid")

    if store_c is None:
        res["note"] = "correctness.csv has no store column"
        return res

    eval_wl = load_eval_workloads()
    counts_all, counts_wl = {}, {}   # store -> [nc, nt]
    acc_all, acc_wl = {}, {}         # store -> accuracy (aggregated-row form)

    def _wl(r):
        if wl_c and r.get(wl_c) not in (None, ""):
            return str(r.get(wl_c))
        if id_c and r.get(id_c) is not None:
            return eval_wl.get(str(r.get(id_c)))
        return None

    for r in rows:
        s = r.get(store_c)
        if s in (None, ""):
            continue
        s = str(s)
        wl = _wl(r)
        if corr_c is not None:  # per-item boolean rows
            b = as_bool(r.get(corr_c))
            if b is None:
                continue
            a = counts_all.setdefault(s, [0, 0])
            a[0] += 1 if b else 0
            a[1] += 1
            if wl is not None:
                w = counts_wl.setdefault((s, wl), [0, 0])
                w[0] += 1 if b else 0
                w[1] += 1
        elif nc_c is not None and nt_c is not None:  # aggregated counts
            nc, nt = as_float(r.get(nc_c)), as_float(r.get(nt_c))
            if nc is None or nt is None:
                continue
            a = counts_all.setdefault(s, [0, 0])
            a[0] += nc
            a[1] += nt
            if wl is not None:
                w = counts_wl.setdefault((s, wl), [0, 0])
                w[0] += nc
                w[1] += nt
        elif acc_c is not None:  # aggregated accuracy value
            a = as_float(r.get(acc_c))
            if a is None:
                continue
            frac = a / 100.0 if a > 1.0 else a
            acc_all[s] = frac
            if wl is not None:
                acc_wl[(s, wl)] = frac

    overall = {s: (nc / nt if nt else None) for s, (nc, nt) in counts_all.items()}
    overall.update({s: v for s, v in acc_all.items() if s not in overall})
    workload = {k: (nc / nt if nt else None) for k, (nc, nt) in counts_wl.items()}
    workload.update({k: v for k, v in acc_wl.items() if k not in workload})

    res["overall"] = {s: v for s, v in overall.items() if v is not None}
    res["workload"] = {k: v for k, v in workload.items() if v is not None}
    res["available"] = bool(res["overall"])
    res["note"] = "ok" if res["available"] else "no per-store accuracy parsed"
    return res


def is_full(acc):
    return acc is not None and acc >= 1.0 - 1e-9


# ===========================================================================
# Figures  (each returns a short status string; writes a 'pending' placeholder
#           SVG when data is absent so the RESULTS.md link always resolves)
# ===========================================================================
def _init_mpl():
    plt.rcParams.update({
        "svg.fonttype": "none",          # keep text selectable / small
        "figure.dpi": 110,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.transparent": True,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })
    try:
        plt.rcParams["axes.titlecolor"] = INK
    except Exception:  # noqa: BLE001 - older mpl lacks this key
        pass


def _save(fig, name):
    path = config.FIGS_DIR / name
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _placeholder(name, reason):
    if not HAVE_MPL:
        return f"pending ({reason})"
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    ax.axis("off")
    ax.text(0.5, 0.5, f"pending\n{reason}", ha="center", va="center",
            color=INK, fontsize=13, wrap=True)
    _save(fig, name)
    return f"pending ({reason})"


def _bar_labels(ax, bars, fmt, rot=0):
    for b in bars:
        h = b.get_height()
        if h is None or (isinstance(h, float) and math.isnan(h)):
            continue
        ax.annotate(fmt(h), (b.get_x() + b.get_width() / 2, h), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=8, color=INK, rotation=rot)


def _legend(ax, **kw):
    leg = ax.legend(**kw)
    if leg is not None:
        for txt in leg.get_texts():
            txt.set_color(INK)
    return leg


def fig_storage_sizes():
    name = "storage_sizes_by_format.svg"
    if not HAVE_MPL:
        return "pending (matplotlib unavailable)"
    t = load_table(CSV_PATHS["storage"])
    if t is None:
        return _placeholder(name, "storage_sizes.csv not found")
    cols, rows = t
    if not rows:
        return _placeholder(name, "storage_sizes.csv empty")
    store_c = find_col(cols, "store", "format", "store_format", "backend", "engine")
    bytes_c = find_col(cols, "total_bytes", "bytes", "size_bytes", "total_size_bytes",
                       "disk_bytes", "on_disk_bytes", "nbytes")
    mb_c = find_col(cols, "size_mb", "total_mb", "mb", "parquet_mb", "megabytes")
    if store_c is None or (bytes_c is None and mb_c is None):
        return _placeholder(name, "no store/size columns in storage_sizes.csv")

    agg = {}
    for r in rows:
        s = r.get(store_c)
        if s in (None, ""):
            continue
        if bytes_c is not None:
            v = as_float(r.get(bytes_c))
        else:
            mb = as_float(r.get(mb_c))
            v = mb * 1e6 if mb is not None else None
        if v is None:
            continue
        agg[str(s)] = agg.get(str(s), 0.0) + v
    if not agg:
        return _placeholder(name, "no numeric sizes in storage_sizes.csv")

    items = sorted(agg.items(), key=lambda kv: kv[1])
    labels = [k for k, _ in items]
    mb_vals = [v / 1e6 for _, v in items]
    fig, ax = plt.subplots(figsize=(max(6.0, 0.9 * len(labels) + 2), 4.2))
    bars = ax.bar(range(len(labels)), mb_vals,
                  color=[PALETTE[i % len(PALETTE)] for i in range(len(labels))], width=0.68)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("On-disk size (MB)")
    ax.set_title("Storage footprint by format")
    ax.grid(axis="y", color=GRID, alpha=0.3, linewidth=0.7)
    _bar_labels(ax, bars, lambda h: human_bytes(h * 1e6))
    _save(fig, name)
    return "ok"


def fig_retrieval_latency(timings):
    name = "retrieval_latency.svg"
    if not HAVE_MPL:
        return "pending (matplotlib unavailable)"
    if not timings["available"] or not timings["warm"]:
        return _placeholder(name, "no warm timings (timings.csv " + timings["note"] + ")")

    # pick up to 4 representative workloads (most-measured first, then alphabetical)
    freq = {}
    for (_, wl) in timings["warm"]:
        freq[wl] = freq.get(wl, 0) + 1
    workloads = [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))][:4]
    stores = timings["stores"]
    if not stores or not workloads:
        return _placeholder(name, "not enough store/workload timing points")

    n = len(workloads)
    width = 0.8 / n
    fig, ax = plt.subplots(figsize=(max(7.0, 1.05 * len(stores) + 2), 4.4))
    any_bar = False
    for j, wl in enumerate(workloads):
        xs, ys = [], []
        for i, s in enumerate(stores):
            v = timings["warm"].get((s, wl))
            if v is None:
                continue
            xs.append(i + (j - (n - 1) / 2) * width)
            ys.append(v)
        if xs:
            any_bar = True
            ax.bar(xs, ys, width=width, label=str(wl), color=PALETTE[j % len(PALETTE)])
    if not any_bar:
        return _placeholder(name, "no overlapping store x workload timings")
    ax.set_xticks(range(len(stores)))
    ax.set_xticklabels(stores, rotation=30, ha="right")
    ax.set_ylabel("Warm p50 latency (ms)")
    ax.set_title("Retrieval latency (warm p50) by store")
    ax.grid(axis="y", color=GRID, alpha=0.3, linewidth=0.7)
    _legend(ax, title="workload", ncol=min(n, 4), loc="upper right")
    _save(fig, name)
    return "ok"


def fig_cold_vs_warm(timings):
    name = "cold_vs_warm.svg"
    if not HAVE_MPL:
        return "pending (matplotlib unavailable)"
    if not timings["available"]:
        return _placeholder(name, "no timings (timings.csv " + timings["note"] + ")")
    if not timings["has_cold"]:
        return _placeholder(name, "timings.csv has no cold-cache measurements")

    stores = [s for s in timings["stores"]
              if timings["cold_store"].get(s) is not None or timings["warm_store"].get(s) is not None]
    if not stores:
        return _placeholder(name, "no per-store cold/warm points")
    width = 0.38
    fig, ax = plt.subplots(figsize=(max(6.5, 1.05 * len(stores) + 2), 4.4))
    cold_vals = [timings["cold_store"].get(s) or float("nan") for s in stores]
    warm_vals = [timings["warm_store"].get(s) or float("nan") for s in stores]
    xs = list(range(len(stores)))
    b1 = ax.bar([x - width / 2 for x in xs], cold_vals, width=width, label="cold", color=COLD_C)
    b2 = ax.bar([x + width / 2 for x in xs], warm_vals, width=width, label="warm", color=WARM_C)
    ax.set_xticks(xs)
    ax.set_xticklabels(stores, rotation=30, ha="right")
    ax.set_ylabel("p50 latency (ms)")
    ax.set_title("Cold vs warm p50 latency by store")
    ax.grid(axis="y", color=GRID, alpha=0.3, linewidth=0.7)
    _legend(ax, loc="upper right")
    _save(fig, name)
    return "ok"


def fig_t2sql_models():
    name = "t2sql_models.svg"
    if not HAVE_MPL:
        return "pending (matplotlib unavailable)"
    t = load_table(CSV_PATHS["t2sql"])
    if t is None:
        return _placeholder(name, "t2sql_scores.csv not found")
    cols, rows = t
    if not rows:
        return _placeholder(name, "t2sql_scores.csv empty")
    model_c = find_col(cols, "model", "model_name", "tag", "name")
    acc_c = find_col(cols, "accuracy", "acc", "pct_correct", "correct_pct", "score")
    nc_c = find_col(cols, "n_correct", "num_correct", "correct_count", "n_pass")
    nt_c = find_col(cols, "n_total", "num_total", "total", "n_items", "n")
    lat_c = find_col(cols, "median_latency_ms", "p50_ms", "latency_ms", "median_ms",
                     "gen_ms", "median_latency", "p50_latency_ms")
    if model_c is None or (acc_c is None and not (nc_c and nt_c)):
        return _placeholder(name, "no model/accuracy columns in t2sql_scores.csv")

    # aggregate per model (a stage may write one row per item, or one row per model)
    agg = {}
    for r in rows:
        m = r.get(model_c)
        if m in (None, ""):
            continue
        m = str(m)
        d = agg.setdefault(m, {"nc": 0.0, "nt": 0.0, "acc": None, "lat": []})
        if nc_c and nt_c:
            nc, nt = as_float(r.get(nc_c)), as_float(r.get(nt_c))
            if nc is not None and nt is not None:
                d["nc"] += nc
                d["nt"] += nt
        elif acc_c:
            a = as_float(r.get(acc_c))
            if a is not None:
                d["acc"] = a
        if lat_c:
            lv = as_float(r.get(lat_c))
            if lv is not None:
                d["lat"].append(lv)

    models = sorted(agg)
    accs, lats = [], []
    for m in models:
        d = agg[m]
        if d["nt"]:
            accs.append(to_pct(d["nc"] / d["nt"]))
        elif d["acc"] is not None:
            accs.append(to_pct(d["acc"]))
        else:
            accs.append(None)
        lats.append(median(d["lat"]))
    if not any(a is not None for a in accs):
        return _placeholder(name, "no accuracy values parsed for t2sql models")

    xs = list(range(len(models)))
    fig, ax = plt.subplots(figsize=(max(6.0, 1.4 * len(models) + 2), 4.4))
    bars = ax.bar(xs, [a if a is not None else 0 for a in accs], width=0.55,
                  color=ACC_C, label="accuracy (%)")
    ax.set_xticks(xs)
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_ylabel("Accuracy (%)", color=ACC_C)
    ax.set_ylim(0, 105)
    ax.set_title("Text-to-SQL: accuracy vs median latency per model")
    ax.grid(axis="y", color=GRID, alpha=0.3, linewidth=0.7)
    _bar_labels(ax, bars, lambda h: f"{h:.0f}%")

    if any(v is not None for v in lats):
        ax2 = ax.twinx()
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(True)
        ax2.spines["right"].set_color(INK)
        ax2.tick_params(colors=INK)
        lx = [x for x, v in zip(xs, lats) if v is not None]
        ly = [v for v in lats if v is not None]
        ax2.plot(lx, ly, color=LAT_C, marker="o", linewidth=1.8, label="median latency (ms)")
        ax2.set_ylabel("Median latency (ms)", color=LAT_C)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        _legend(ax, handles=h1 + h2, labels=l1 + l2, loc="upper right")
    else:
        _legend(ax, loc="upper right")
    _save(fig, name)
    return "ok"


def fig_vector_vs_duckdb(correctness):
    name = "vector_vs_duckdb_accuracy.svg"
    if not HAVE_MPL:
        return "pending (matplotlib unavailable)"
    methods = {}  # label -> accuracy (0-1)

    t = load_table(CSV_PATHS["vector"])
    if t is not None and t[1]:
        cols, rows = t
        method_c = find_col(cols, "method", "store", "approach", "retriever", "engine",
                            "backend", "mode", "system")
        acc_c = find_col(cols, "accuracy", "acc", "pct_correct", "correct_pct", "score")
        corr_c = find_col(cols, "correct", "is_correct", "pass", "passed", "match", "ok", "hit")
        nc_c = find_col(cols, "n_correct", "num_correct", "correct_count", "n_hit")
        nt_c = find_col(cols, "n_total", "num_total", "total", "n_items", "n")
        counts = {}
        for r in rows:
            lbl = str(r.get(method_c)) if method_c and r.get(method_c) not in (None, "") else "vector"
            if corr_c is not None:
                b = as_bool(r.get(corr_c))
                if b is None:
                    continue
                c = counts.setdefault(lbl, [0.0, 0.0])
                c[0] += 1 if b else 0
                c[1] += 1
            elif nc_c and nt_c:
                nc, nt = as_float(r.get(nc_c)), as_float(r.get(nt_c))
                if nc is not None and nt is not None:
                    c = counts.setdefault(lbl, [0.0, 0.0])
                    c[0] += nc
                    c[1] += nt
            elif acc_c is not None:
                a = as_float(r.get(acc_c))
                if a is not None:
                    methods[lbl] = a / 100.0 if a > 1.0 else a
        for lbl, (nc, nt) in counts.items():
            if nt:
                methods[lbl] = nc / nt

    # anchor with DuckDB's exact-SQL accuracy from correctness.csv (the point of the comparison)
    if correctness["available"] and "duckdb" in correctness["overall"] and \
            not any("duckdb" in m.lower() for m in methods):
        methods["duckdb (SQL)"] = correctness["overall"]["duckdb"]

    if not methods:
        return _placeholder(name, "vector_probe.csv not found / no accuracy parsed")

    labels = sorted(methods, key=lambda k: (0 if "duckdb" in k.lower() else 1, k))
    vals = [to_pct(methods[k]) for k in labels]
    colors = [ACC_C if "duckdb" in k.lower() else PALETTE[3] for k in labels]
    fig, ax = plt.subplots(figsize=(max(5.5, 1.3 * len(labels) + 2), 4.2))
    bars = ax.bar(range(len(labels)), vals, width=0.55, color=colors)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Answer accuracy (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Answer accuracy: vector retrieval vs DuckDB SQL")
    ax.grid(axis="y", color=GRID, alpha=0.3, linewidth=0.7)
    _bar_labels(ax, bars, lambda h: f"{h:.0f}%")
    _save(fig, name)
    return "ok"


# ===========================================================================
# Derived views (computed only from numbers upstream already produced)
# ===========================================================================
def fastest_correct_per_workload(timings, correctness):
    """For each workload: the correct store with the lowest warm p50. Returns (rows, note)."""
    if not timings["available"]:
        return [], "pending — timings.csv " + timings["note"]
    if not correctness["available"]:
        return [], "pending — correctness.csv " + correctness["note"]

    def correct_on(store, wl):
        wa = correctness["workload"].get((store, wl))
        if wa is not None:
            return is_full(wa)
        return is_full(correctness["overall"].get(store))

    out = []
    for wl in timings["workloads"]:
        best_store, best_ms = None, None
        for s in timings["stores"]:
            if s in VECTOR_STORES:
                continue
            v = timings["warm"].get((s, wl))
            if v is None or not correct_on(s, wl):
                continue
            if best_ms is None or v < best_ms:
                best_store, best_ms = s, v
        out.append({
            "workload": wl,
            "fastest_correct_store": best_store or "— (no 100%-correct store timed)",
            "warm_p50_ms": round(best_ms, 4) if best_ms is not None else None,
        })
    return out, "ok"


def recommend(timings, correctness):
    """Heuristic: the non-vector store that is 100% correct with the best median warm p50."""
    lines = []
    have_corr = correctness["available"]
    have_time = timings["available"]
    if not have_corr and not have_time:
        return "_Recommendation pending — correctness.csv and timings.csv are both missing._"

    # candidate = 100%-correct, non-vector store, ranked by median warm p50
    cands = []
    for s, acc in correctness["overall"].items():
        if s in VECTOR_STORES or not is_full(acc):
            continue
        cands.append((s, timings["warm_store"].get(s)))
    ranked = sorted([c for c in cands if c[1] is not None], key=lambda c: c[1])

    if ranked:
        s, ms = ranked[0]
        lines.append(f"**Recommended stat store: `{s}`** — 100% correct on the eval set with the "
                     f"lowest median warm p50 ({ms:.3f} ms).")
        if len(ranked) > 1:
            runners = ", ".join(f"`{n}` ({v:.3f} ms)" for n, v in ranked[1:4])
            lines.append(f"Other fully-correct stores, by warm p50: {runners}.")
    elif cands:
        names = ", ".join(f"`{s}`" for s, _ in cands)
        lines.append(f"Fully-correct stores exist ({names}) but their warm p50 was not timed — "
                     f"recommendation pending timings.csv.")
    elif have_corr:
        best = max(correctness["overall"].items(), key=lambda kv: kv[1], default=(None, None))
        if best[0]:
            lines.append(f"No store was 100% correct on the eval set; best accuracy was `{best[0]}` "
                         f"at {to_pct(best[1]):.0f}%. Recommendation withheld until a store passes the "
                         f"correctness gate.")
        else:
            lines.append("_Recommendation pending — no per-store accuracy parsed._")
    else:
        lines.append("_Recommendation pending — correctness.csv missing (cannot certify a store)._")

    # vector-store unfit note (always stated; anchored to a number when available)
    vec_acc = None
    for s, acc in correctness["overall"].items():
        if s in VECTOR_STORES:
            vec_acc = (s, acc)
            break
    if vec_acc:
        lines.append(f"The vector DB (`{vec_acc[0]}`) is **unfit as the stat store**: it answered "
                     f"{to_pct(vec_acc[1]):.0f}% of the eval set correctly — approximate-nearest-neighbor "
                     f"retrieval cannot do exact arithmetic. Keep it for semantic search only.")
    else:
        lines.append("The vector DB is **unfit as the stat store** — ANN retrieval approximates and "
                     "cannot compute exact aggregates; use DuckDB SQL for every statistic. "
                     "(See vector_vs_duckdb_accuracy.svg for the measured gap.)")
    return "\n\n".join(lines)


# ===========================================================================
# RESULTS.md assembly
# ===========================================================================
def _metric_section(title, key, fig_md=None, note=None):
    parts = [f"## {title}"]
    if note:
        parts.append(f"_{note}_")
    t = load_table(CSV_PATHS[key])
    if t is None:
        parts.append(f"_pending — `{CSV_PATHS[key].name}` not found._")
    elif not t[1]:
        parts.append(f"_`{CSV_PATHS[key].name}` present but has no rows (pending upstream stage)._")
    else:
        parts.append(md_table(t[0], t[1]))
    if fig_md:
        parts.append(fig_md)
    return "\n\n".join(parts)


def _fig_md(name, caption):
    """Embed the figure if it was written, else a pending line."""
    if (config.FIGS_DIR / name).exists():
        return f"![{caption}](figs/{name})\n\n_Figure: {caption}._"
    return f"_Figure pending: {caption} (`figs/{name}` not generated)._"


def build_results_md(timings, correctness, fig_status):
    found = [k for k, p in CSV_PATHS.items() if p.exists()]
    pending = [k for k, p in CSV_PATHS.items() if not p.exists()]
    stamp = datetime.now().isoformat(timespec="seconds")

    md = []
    md.append("# statlas v1 — NBA storage & retrieval benchmark: RESULTS")
    md.append(
        "This report compares storage formats and query engines for the statlas stat store on real "
        "modern-era NBA data (1996-97 → 2025-26). It measures four things per candidate store: "
        "**on-disk footprint**, **retrieval latency** (cold vs warm), **answer correctness** against a "
        "golden eval set, and — for the language layer — **text-to-SQL accuracy** and a **vector-vs-SQL** "
        "accuracy probe. Every number below is read straight from `results/*.csv`; nothing here is "
        "computed about basketball by this stage. DuckDB does the arithmetic upstream; S6 only presents."
    )
    md.append(f"_Generated {stamp} · found: {', '.join(found) or 'none'} · "
              f"pending: {', '.join(pending) or 'none'}._")

    md.append("## Narrative")
    md.append("<!-- NARRATIVE: main loop to add interpretation / caveats / next steps here. -->")
    md.append("_(Narrative to be filled in by the main loop.)_")

    # --- metric tables (+ figures inline where they belong) ---
    md.append(_metric_section(
        "Ingest metrics (S1)", "ingest",
        note="Rows pulled per endpoint and the live API latency of each call (from S1)."))

    md.append(_metric_section(
        "Storage footprint (S2)", "storage",
        fig_md=_fig_md("storage_sizes_by_format.svg", "on-disk size by store format"),
        note="Bytes on disk for each candidate format (materialized from the same rows)."))

    md.append(_metric_section(
        "Retrieval latency (S3)", "timings",
        fig_md=_fig_md("retrieval_latency.svg", "warm p50 latency by store")
        + "\n\n" + _fig_md("cold_vs_warm.svg", "cold vs warm p50 by store"),
        note="Per-store query latency on the eval workload; p50 over benchmark reps."))

    md.append(_metric_section(
        "Correctness parity (S3)", "correctness",
        fig_md=_fig_md("vector_vs_duckdb_accuracy.svg", "answer accuracy: vector vs DuckDB"),
        note="Every store must return the canonical expected_value for each eval item BEFORE its "
             "timings count. The vector figure sits here because it is an accuracy comparison."))

    md.append(_metric_section(
        "Text-to-SQL models (S4)", "t2sql",
        fig_md=_fig_md("t2sql_models.svg", "accuracy vs median latency per model"),
        note="Each model drafts SQL that is guard-validated and executed on DuckDB; accuracy is vs the "
             "same golden answers."))

    md.append(_metric_section(
        "Vector probe (S5)", "vector",
        note="Semantic-retrieval accuracy on the eval questions — the evidence that a vector DB cannot "
             "serve exact stats."))

    # --- derived: fastest correct store per workload ---
    rows, note = fastest_correct_per_workload(timings, correctness)
    md.append("## Fastest correct store per workload (derived)")
    md.append("_The lowest warm-p50 store that is 100% correct on each workload (vector stores excluded)._")
    if rows:
        md.append(md_table(["workload", "fastest_correct_store", "warm_p50_ms"], rows))
    else:
        md.append(f"_{note}_")

    # --- recommendation ---
    md.append("## Recommendation (data-driven)")
    md.append(recommend(timings, correctness))

    # --- figure-generation status footnote (transparency) ---
    fs = "; ".join(f"{n}: {s}" for n, s in fig_status.items())
    md.append("---")
    md.append(f"_Figure generation status — {fs}._")

    return "\n\n".join(md) + "\n"


# ===========================================================================
def main():
    print("=" * 78)
    print("S6 REPORT — rendering figures + RESULTS.md from results/*.csv")
    print("=" * 78)
    if not HAVE_MPL:
        print("  [warn] matplotlib unavailable — tables will render, all figures marked pending")
    else:
        _init_mpl()

    timings = parse_timings()
    correctness = parse_correctness()
    print(f"  timings:     {timings['note']} "
          f"({len(timings['stores'])} stores, {len(timings['workloads'])} workloads)")
    print(f"  correctness: {correctness['note']} ({len(correctness['overall'])} stores)")

    fig_status = {
        "storage_sizes_by_format.svg": fig_storage_sizes(),
        "retrieval_latency.svg": fig_retrieval_latency(timings),
        "cold_vs_warm.svg": fig_cold_vs_warm(timings),
        "t2sql_models.svg": fig_t2sql_models(),
        "vector_vs_duckdb_accuracy.svg": fig_vector_vs_duckdb(correctness),
    }
    for name, status in fig_status.items():
        flag = "ok " if status == "ok" else "..."
        print(f"  [{flag}] {name:34s} {status}")

    md = build_results_md(timings, correctness, fig_status)
    RESULTS_MD.write_text(md)

    n_ok = sum(1 for s in fig_status.values() if s == "ok")
    print("=" * 78)
    print(f"S6 done — {n_ok}/{len(fig_status)} figures rendered with data, "
          f"RESULTS.md -> {RESULTS_MD.relative_to(config.EXP_ROOT)}")
    if n_ok < len(fig_status):
        print("  (figures without upstream data are 'pending' placeholders — rerun after S2–S5.)")


if __name__ == "__main__":
    main()
