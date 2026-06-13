# learning/days — Context

## Section 1: Evergreen

**What this is:** Per-day study logs, numbered sequentially and each tagged with its date. The latest day is the working context.

**Module map:**
- `day1/` … `day5/` — each holds `summary.md` (coach suggestion + what was done + notes); `day5/` also has `TODAY.md`, `eda/`, `exercises/`

**Architecture decisions (append-only, one line each):**
- New days are copied from `../templates/day-template.md`
- A day folder is created only when there's real content to record
- Days 1–4 carry coach suggestions with no completion reported; Day 5 is the first active worked day

**Non-negotiable constraints:**
- Don't create empty day folders
- Keep each day's date tag accurate

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
