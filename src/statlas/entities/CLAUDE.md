# src/statlas/entities — Context

## Section 1: Evergreen

**What this is:** The entity resolver — maps human references ("Wemby", "the Joker", "KD", "thunder") to canonical `player_id` / team abbreviation. This is half of a stats engine's accuracy.

**Module map:**
- `__init__.py` — package marker
- `resolver.py` — `NICKNAMES`, `TEAM_ALIASES`, `ResolvedPlayer`, `resolve_player()`, `resolve_team()`

**Architecture decisions (append-only, one line each):**
- v0 = curated nickname dictionary + rapidfuzz `WRatio` fuzzy match against full names
- Exact nickname hit scores 100; fuzzy match must clear `min_score` (default 75)
- Below threshold returns `None` — the engine then says "I don't know" rather than guessing
- A good dictionary beats a fancy model for the head of the distribution; embedding/NER linker is a later upgrade

**Non-negotiable constraints:**
- Prefer refusing over a wrong match
- The resolver maps identities only — it never queries or computes stats
- Extend `NICKNAMES` / `TEAM_ALIASES` freely; keep keys lowercase

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
