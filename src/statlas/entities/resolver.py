"""Fuzzy name resolution — refuse rather than guess.

Consolidates a pattern two places in experiments/v1_nba_storage_retrieval_benchmark independently
built (fuzzy-match a name against a set of candidates, accept only above a confidence threshold,
otherwise refuse):
  - pipeline/s2_crosswalk.py's `_match_slug` — bridges nba_api player_id <-> Basketball-Reference
    bbref_slug by name. Now imports `best_match` from here instead of holding its own copy.
  - ask.py's `resolve_player` — resolves a player name typed in a natural-language question against
    the real `players` table. Now imports `best_match_from_candidates` from here.

Both are instances of the same non-negotiable (root CLAUDE.md): entity resolution never guesses
below a confidence floor — an unresolved name returns None, never a wrong match, because a wrong
join/lookup silently corrupts a stat, which is worse than refusing.

Requires `rapidfuzz` (already a project dependency).
"""
from __future__ import annotations

from rapidfuzz import fuzz, process, utils


def best_match(
    name: str | None,
    choices: dict[str, str],
    threshold: int,
    scorer=fuzz.WRatio,
    processor=utils.default_process,
) -> str | None:
    """Best key in `choices` whose value fuzzy-matches `name`, or None if nothing clears `threshold`.

    `choices` maps {key: display_name} — e.g. {bbref_slug: full_name} or {player_id: full_name}.
    rapidfuzz matches `name` against the VALUES and, because `choices` is a Mapping, returns
    `(matched_value, score, matched_key)`, so the key comes back directly with no second lookup.

    Pure function, no I/O — unit-testable on a tiny synthetic dict. `threshold` has no default on
    purpose: callers must decide their own confidence bar (the two known call sites used 88 for a
    cross-source join and 85 for interactive question-answering — pick deliberately, don't inherit
    a number that was tuned for a different failure cost).
    """
    if name is None or not choices:
        return None
    res = process.extractOne(name, choices, scorer=scorer, processor=processor)
    if res is not None and res[1] >= threshold:
        return res[2]
    return None


def best_match_from_candidates(
    candidates: list[str],
    choices: dict[str, str],
    threshold: int,
    scorer=fuzz.WRatio,
) -> tuple[str, str] | None:
    """Try several candidate spans (e.g. capitalized substrings pulled from a free-text question)
    against `choices` and return the (candidate, matched_key) pair with the single best score
    across all of them, or None if none clears `threshold`.

    This is `resolve_player`'s pattern generalized: a free-text question rarely isolates the entity
    name cleanly, so the caller extracts several plausible spans and this picks the best-scoring one.
    """
    best_cand, best_key, best_score = None, None, 0
    for cand in candidates:
        res = process.extractOne(cand, choices, scorer=scorer)
        if res is not None and res[1] > best_score:
            best_cand, best_key, best_score = cand, res[2], res[1]
    if best_key is None or best_score < threshold:
        return None
    return best_cand, best_key


# --------------------------------------------------------------------------- self-test
def _selftest() -> int:
    choices = {"jokic-nikol01": "Nikola Jokic", "james-lebro01": "LeBron James"}
    fails = 0

    cases = [
        (best_match("Nikola Jokic", choices, threshold=88), "jokic-nikol01"),
        (best_match("Nikola Jokić", choices, threshold=88), "jokic-nikol01"),  # accented variant
        (best_match("Some Random Name", choices, threshold=88), None),        # below threshold -> refuse
        (best_match(None, choices, threshold=88), None),                      # no name -> refuse
        (best_match("Nikola Jokic", {}, threshold=88), None),                 # no choices -> refuse
    ]
    for got, expected in cases:
        ok = got == expected
        fails += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] best_match -> {got!r} (expected {expected!r})")

    got = best_match_from_candidates(
        ["How many points did LeBron James average"], choices, threshold=85
    )
    ok = got is not None and got[1] == "james-lebro01"
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] best_match_from_candidates -> {got!r}")

    print(f"{5 + 1 - fails}/6 cases behaved as expected" + ("" if fails == 0 else f"  ({fails} UNEXPECTED)"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
