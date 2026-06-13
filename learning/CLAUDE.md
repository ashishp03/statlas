# learning — Context

## Section 1: Evergreen

**What this is:** The study-tracking + curriculum system for the project owner (Ashish). Not product code — this is how learning is planned, logged, and committed. A scheduled "daily study coach" reads and updates these files.

**Module map:**
- `roadmap.md` — **ACTIVE** master guide: foundations-first, ground-up concept stack with example-coding exercises
- `curriculum.md` — **PARKED** advanced, build-focused module plan (revive after foundations)
- `progress.md` — master tracker: status table + module checklist + dated Daily log
- `README.md` — explains the system
- `days/` — per-day study logs (one folder per active day)
- `modules/` — parked homework modules (workbook + graded notebook)
- `templates/` — `day-template.md` source for new days

**Architecture decisions (append-only, one line each):**
- Two modes: foundations-first (`roadmap.md`, active) vs advanced build (`curriculum.md`, parked)
- `progress.md` is the single source of truth for current phase + history
- One folder per active study day, numbered + dated; created only when there's content
- Coach commits to the `learning` git branch ONLY when real work exists; stages only `learning/`; never pushes without asking
- Entry point reset to roadmap Stage 3 (transformers) — Stages 1–2 are revision given an MS in Data Science

**Non-negotiable constraints:**
- No empty daily commits or empty day folders
- Study commits touch only `learning/` (don't disturb other staged changes)
- Don't push to origin unless explicitly asked
- Known issue: stale `.git/index.lock` + `.git/HEAD.lock` block commits; manual fix `rm -f .git/index.lock .git/HEAD.lock` then commit

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; the dated study history lives in `progress.md`.

## Section 2: Rolling Session Log (last 2 sessions only)

_Project session log: root `CLAUDE.md`. Study-day history: `progress.md`._
