# learning/modules/04-text-to-sql — Context

## Section 1: Evergreen

**What this is:** Text-to-SQL module, built 2026-08-25 at Ashish's request for a focused NLU/text-to-SQL/SQL-engine study push. Papers (survey 2410.01066, DIN-SQL 2304.11015, Spider 1809.08887, BIRD 2305.03111, CHASE-SQL 2410.01943 stretch), math problems (set/bag equivalence, self-consistency probability, relational algebra), and a graded `exercises.ipynb` grounded in the repo's real `days/day5/eda` player-stats CSV via DuckDB. Ship target: the `assert_safe` validator + gold-set pattern feed `src/statlas/query/planner.py`'s Phase-4 LLM-SQL-draft path.

**Module map:**
- `workbook.md` — papers/theory/math problems + blanks
- `exercises.ipynb` — graded coding exercises (verified to execute cleanly end-to-end 2026-08-25; Exercise 2's GOLD list ships with 3 of 8 required pairs filled in as a TODO for Ashish)

**Architecture decisions (append-only, one line each):**
- Built alongside `05-computation-engine/` in the same session, both un-parked from `curriculum.md`'s stub table specifically for this request (M1/M2 precedent: MS-DS-level, paper+math+notebook homework style)
- Uses real project data (`learning/days/day5/eda/data/player_stats_2025-26_regular.csv`) instead of a toy Chinook DB so exercises double as Statlas domain practice
- `exec_match`'s and the gold set's qualifier example intentionally use STL (not REB/PTS) — it's the one stat where an unqualified query surfaces a genuine small-sample "leader" (3 GP), so the exercise demonstrates a real bug instead of a no-op

**Non-negotiable constraints:**
- Not the roadmap's next default suggestion (that's still Stage 4/LLMs per `progress.md`) — this is a parallel deep-dive Ashish asked for directly; both can be true

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

- **2026-08-25** — Module built from scratch (workbook + notebook), notebook execution-verified end-to-end (`jupyter nbconvert --execute`, all asserts pass with TODOs filled in for testing).
