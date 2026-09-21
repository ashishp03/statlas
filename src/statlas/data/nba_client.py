"""Defensive nba_api calling primitives — safe against rate limits/flakiness, never raises.

Moved out of experiments/v1_nba_storage_retrieval_benchmark/pipeline/_harness.py (which also had
benchmark-timing helpers — those stayed in the experiment since they're benchmark-specific, not
part of "how to safely call nba_api", which is genuinely permanent regardless of which experiment
or script is doing the calling).

Two hard-won lessons baked in here (see experiments/v1_nba_storage_retrieval_benchmark's
docs/findings/DECISIONS.md for the original rationale): nba_api is rate-limited and intermittently
flaky, so every call must be wrapped and paced — a crashed batch pull is worse than one missing
endpoint; and seasons are identified by their END year everywhere in this project (2025 means the
"2024-25" season) — `season_str` is the single place that convention turns into the string nba_api
actually wants.
"""
from __future__ import annotations

import time

import polars as pl

DEFAULT_API_TIMEOUT_S = 30
DEFAULT_API_PAUSE_S = 0.6   # sleep between live calls (respect stats.nba.com throttling)

# The stable game_logs contract (MUST match src/statlas/data/seed/game_logs.csv) — the one
# schema every branch/experiment agrees never to change without a coordinated migration.
GAME_LOGS_COLUMNS = [
    "player_id", "season", "game_date", "opponent_abbr", "is_playoff",
    "min", "pts", "reb", "ast", "plus_minus",
]
PLAYERS_COLUMNS = ["player_id", "full_name", "team_abbr"]


def season_str(end_year: int) -> str:
    """2025 -> '2024-25' (NBA season string keyed on END year)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def safe_rows(
    endpoint_cls,
    *,
    timeout: int = DEFAULT_API_TIMEOUT_S,
    pause: float = DEFAULT_API_PAUSE_S,
    **kwargs,
):
    """Call an nba_api endpoint defensively.

    Returns (n_rows, polars_df | None, status, elapsed_s). NEVER raises: on error returns
    (-1, None, "ExcType: msg", elapsed). Sleeps `pause` after every call (success or failure) to
    respect stats.nba.com rate limits. n_rows == 0 means a clean-but-empty frame; -1 means error.
    """
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


# --------------------------------------------------------------------------- self-test
def _selftest() -> int:
    fails = 0

    ok = season_str(2025) == "2024-25"
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] season_str(2025) -> {season_str(2025)!r}")

    ok = season_str(1997) == "1996-97"
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] season_str(1997) -> {season_str(1997)!r}")

    # safe_rows must never raise, even when the endpoint itself blows up.
    class _BoomEndpoint:
        def __init__(self, **kwargs):
            raise RuntimeError("simulated nba_api failure")

    n, df, status, elapsed = safe_rows(_BoomEndpoint, pause=0.0)
    ok = n == -1 and df is None and "RuntimeError" in status and elapsed >= 0
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] safe_rows degrades on exception -> "
          f"n={n} status={status!r}")

    class _OkEndpoint:
        def __init__(self, **kwargs):
            pass

        def get_data_frames(self):
            import pandas as pd
            return [pd.DataFrame({"PLAYER_ID": [1, 2], "PTS": [10.0, 20.0]})]

    n, df, status, elapsed = safe_rows(_OkEndpoint, pause=0.0)
    ok = n == 2 and df is not None and status == "ok"
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] safe_rows returns a polars frame on success -> "
          f"n={n} status={status!r}")

    total = 4
    print(f"{total - fails}/{total} cases behaved as expected" + ("" if fails == 0 else f"  ({fails} UNEXPECTED)"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
