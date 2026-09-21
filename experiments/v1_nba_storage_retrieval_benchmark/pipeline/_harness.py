"""Reusable harness: defensive nba_api calls + timing utilities.

Ports the `safe_rows` / `season_str` pattern from notebooks/initial_eda_v2.ipynb and adds
`perf_counter`-based timing helpers used by every benchmark stage. Import via the per-script
bootstrap that puts the experiment root on sys.path:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import config
    from pipeline._harness import safe_rows, season_str, bench, timer, percentile
"""
from __future__ import annotations

import statistics
import time
from contextlib import contextmanager

import polars as pl

import config


def season_str(end_year: int) -> str:
    """2025 -> '2024-25' (NBA season string keyed on END year)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def safe_rows(endpoint_cls, *, timeout: int | None = None, pause: float | None = None, **kwargs):
    """Call an nba_api endpoint defensively.

    Returns (n_rows, polars_df | None, status, elapsed_s). NEVER raises: on error returns
    (-1, None, "ExcType: msg", elapsed). Sleeps `pause` after every call (success or failure)
    to respect stats.nba.com rate limits. n_rows == 0 means a clean-but-empty frame; -1 means error.
    """
    timeout = config.API_TIMEOUT_S if timeout is None else timeout
    pause = config.API_PAUSE_S if pause is None else pause
    t0 = time.perf_counter()
    try:
        resp = endpoint_cls(timeout=timeout, **kwargs)
        pdf = resp.get_data_frames()[0]
        elapsed = time.perf_counter() - t0
        df = pl.from_pandas(pdf)
        time.sleep(pause)
        return len(df), df, "ok", elapsed
    except Exception as e:  # noqa: BLE001 - never abort a batch pull
        elapsed = time.perf_counter() - t0
        time.sleep(pause)
        return -1, None, f"{type(e).__name__}: {str(e)[:80]}", elapsed


@contextmanager
def timer():
    """Context manager. `with timer() as t: ...` then `t()` returns elapsed seconds."""
    t0 = time.perf_counter()
    yield lambda: time.perf_counter() - t0


def percentile(sorted_samples: list[float], p: float) -> float:
    """Linear-interpolated percentile of an already-sorted list."""
    if not sorted_samples:
        return float("nan")
    k = (len(sorted_samples) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_samples) - 1)
    frac = k - lo
    return sorted_samples[lo] * (1 - frac) + sorted_samples[hi] * frac


def bench(fn, *, reps: int | None = None, warmup: int | None = None, label: str = "") -> dict:
    """Time a zero-arg callable. Returns dict with p50/p95/mean/stdev/min in milliseconds.

    Runs `warmup` untimed iterations first (populate OS/page cache), then `reps` timed ones.
    Cold-vs-warm is controlled by the caller (pass warmup=0 for a cold measure).
    """
    reps = config.BENCH_REPS if reps is None else reps
    warmup = config.BENCH_WARMUP if warmup is None else warmup
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return {
        "label": label,
        "reps": reps,
        "mean_ms": round(statistics.fmean(samples), 4),
        "p50_ms": round(percentile(samples, 50), 4),
        "p95_ms": round(percentile(samples, 95), 4),
        "stdev_ms": round(statistics.pstdev(samples), 4) if len(samples) > 1 else 0.0,
        "min_ms": round(samples[0], 4),
    }
