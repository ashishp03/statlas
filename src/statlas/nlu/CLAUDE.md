# src/statlas/nlu — Context

## Section 1: Evergreen

**What this is:** Natural Language Understanding. Turns a question into a structured `Intent` (player, metric, aggregation, opponent, season, playoff flag). It extracts meaning — it never computes a number.

**Module map:**
- `__init__.py` — package marker
- `parser.py` — `Intent` dataclass; `parse()`; `METRIC_MAP` / `AVG_WORDS` / `TOTAL_WORDS` keyword maps; `_find_metric`, `_find_player_span`, `_find_opponent`; season/playoff extraction

**Architecture decisions (append-only, one line each):**
- v0 is rule-based (regex + keyword maps) so it runs with zero API keys
- Multi-word/symbol metric keys are matched first (longest-key-first) to avoid partial hits
- Default aggregation is `avg`; switches to `sum` only on explicit total-words without avg-words
- Player resolution tries nicknames → real names → fuzzy over capitalized tokens
- Phase-3 plan: replace `parse()` with an LLM function-calling version that returns the SAME `Intent`

**Non-negotiable constraints:**
- `parse()` returns an `Intent`, never a number
- Keep `Intent` fields stable (downstream depends on the contract)
- Record unresolved slots in `unresolved`; do not guess them

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
