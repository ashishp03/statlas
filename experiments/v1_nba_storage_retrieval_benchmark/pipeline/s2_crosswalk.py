"""S2 — build the cross-source player crosswalk (nba_id <-> bbref_slug).

The crosswalk is the ONLY bridge between the two data sources: nba_api keys everything on an
integer ``player_id``; Basketball-Reference keys on a string ``bbref_slug``. To answer a
cross-source question (e.g. "Jokic's VORP") we must join them, and the join is by NAME because no
shared key exists.

Design (see ../docs/findings/DECISIONS.md):
  - Fuzzy-match nba_api ``players.full_name`` against BBRef ``bbref_advanced.full_name`` with
    rapidfuzz ``process.extractOne`` + ``fuzz.WRatio`` (token-aware, order-insensitive).
  - REFUSE-rather-than-guess: accept a slug ONLY when the match score >= ``MATCH_THRESHOLD`` (88);
    otherwise leave ``bbref_slug`` null. A wrong join silently corrupts a stat — worse than a null.
  - Output is a stable dim table written next to the other raw parquet so every store in S2 can
    materialize it and every downstream stage can join on ``nba_player_id`` <-> ``bbref_slug``.

Run:
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s2_crosswalk.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))  # repo src/ on path

import polars as pl

import config
from statlas.entities.resolver import best_match  # moved out of pipeline/ — permanent, reusable

# A wrong cross-source join is worse than none: only accept a fuzzy hit this confident.
MATCH_THRESHOLD = 88


def build_crosswalk() -> pl.DataFrame:
    """Read players + bbref_advanced from RAW_DIR, fuzzy-join, write player_crosswalk.parquet."""
    players = pl.read_parquet(config.RAW_DIR / "players.parquet")
    bbref = pl.read_parquet(config.RAW_DIR / "bbref_advanced.parquet")

    # {slug: name}; slugs are unique (S1 dedups on slug), so they make safe Mapping keys.
    choices = {
        slug: nm
        for slug, nm in zip(bbref["bbref_slug"].to_list(), bbref["full_name"].to_list())
        if slug is not None and nm is not None
    }

    # One extractOne per nba player. This IS a per-row loop, but it is the fuzzy-match itself
    # (mandated: extractOne + WRatio), not raw->store bulk movement — the loop is unavoidable here.
    slugs = [best_match(nm, choices, threshold=MATCH_THRESHOLD) for nm in players["full_name"].to_list()]

    cross = pl.DataFrame(
        {
            "canonical_id": players["player_id"],          # our stable key == nba id (for now)
            "nba_player_id": players["player_id"],
            "bbref_slug": pl.Series(slugs, dtype=pl.Utf8),  # null == REFUSED (below threshold)
            "bdl_id": pl.Series([None] * players.height, dtype=pl.Int64),  # balldontlie: unmapped
            "full_name": players["full_name"],
        }
    )

    out = config.RAW_DIR / "player_crosswalk.parquet"
    cross.write_parquet(out)

    matched = int(cross["bbref_slug"].is_not_null().sum())
    refused = cross.height - matched
    print(
        f"crosswalk: {cross.height} nba players -> {matched} matched to BBRef, "
        f"{refused} refused (WRatio < {MATCH_THRESHOLD}); {len(choices)} BBRef slugs available "
        f"-> wrote {out.name}"
    )
    return cross


def main():
    build_crosswalk()


if __name__ == "__main__":
    main()
