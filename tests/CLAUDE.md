# tests — Context

## Section 1: Evergreen

**What this is:** The accuracy scoreboard. A golden set of questions with known-correct answers (computed from seed data) plus a runner. This is the reliability gate (roadmap Stage 9) — run it after every change and watch accuracy.

**Module map:**
- `eval_set.json` — cases (`q` → `expected`) + a `tolerance`; the golden set
- `run_eval.py` — runs each question through `engine.ask` and scores within tolerance

**Architecture decisions (append-only, one line each):**
- Expected values are derived from the seed data so the set is deterministic
- Comparison is tolerance-based (floating-point safe)
- Grow toward 40–50 questions as features land; this set defines "correct"

**Non-negotiable constraints:**
- Keep cases deterministic against the seed data
- A change that lowers accuracy is a regression, not a trade-off, unless explicitly noted
- Run before declaring any pipeline change done

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
