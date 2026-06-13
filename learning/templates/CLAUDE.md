# learning/templates — Context

## Section 1: Evergreen

**What this is:** Templates for the study system.

**Module map:**
- `day-template.md` — copied to create each new `days/dayN/summary.md`; sections: Coach suggested / What I actually did / Notes & insights / Coding / Links / Carry-over

**Architecture decisions (append-only, one line each):**
- Keep template section headers in sync with what `progress.md` and the coach expect to fill

**Non-negotiable constraints:**
- Don't rename sections without updating the coach workflow

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
