# Statlas — 3-Week MVP Plan

**Written:** 2026-09-20 · **Target:** a demoable web app by 2026-10-09
**Budget:** Ashish ~1h × weekdays = **~15 hours**. Nick: async work packages, sized separately.

**Scope, explicitly (2026-09-20 correction):** "Minimal" means we compromise on the UI, on NBA-only,
and on anything extraneous — it does **not** mean compromise on the core architecture. Everything
`CLAUDE.md` specifies as the intended shape of Statlas is in scope and should execute. What's cut is
narrower than the previous draft of this plan implied.

**What stays exactly as intended — not simplified, not stubbed:**
- The full 5-stage pipeline from `CLAUDE.md`'s own description: `question → NLU (intent) →
  text-to-SQL → DuckDB execution → generation → answer card`. §1 below now includes the
  **generation** stage explicitly — it was missing from the first draft of this plan.
- The structured `Intent` contract between NLU and the query layer, and the rule-based gate that
  implements it — not a simplification for the MVP, the actual intended architecture.
- The LLM-drafted-SQL path for what the template can't express — this is `CLAUDE.md`'s own
  Phase-4 plan ("an LLM may draft SQL for complex queries, but it must pass allow-list validation
  before execution"), not a shortcut invented for the MVP.
- Every non-negotiable: the LLM never computes or recalls a stat: DuckDB does; nothing executes
  unvalidated; unresolved entities/metrics refuse rather than guess (already true today —
  `resolve_player()` refuses below `min_score=75`, verified in the code, not aspirational); every
  answer is auditable (SQL + rows exposed); free/open stack first (Ollama before the Claude API).

**What's compromised (the actual cuts):**
- **UI** — functional, not polished. See Week 3.
- **NBA only** — no other sport, matching the data actually in the warehouse.
- **Data** — only what's already ingested (§0 below); no new sources mid-sprint.
- **Roadmap Stages 5–7 (RAG, growing the eval past ~30, auto-visualization) and Track 2 tooling
  phases D–G (typed `run_sql` tool, MCP server, routing agent, Cowork automation)** — deferred, not
  dropped. The roadmap itself already sequences these *after* Stage 4 (LLMs) / text-to-SQL, so
  treating them as post-MVP is consistent with the plan you already had, not a new cut.

---

## 0. The one thing to understand before you start

You are not starting from scratch. You are **joining two halves that have never been connected**,
and both halves are load-bearing for the MVP — this isn't "keep the old code as reference," the
`learning`-branch pipeline is the deterministic front half of the architecture in §1.

| Half | Where it lives | What's in it |
|---|---|---|
| **The gate** | `learning` branch | `parser → planner`, a working rule-based Intent→SQL engine (`tests/run_eval.py` verified green 5/5 on 2026-09-20) — the MVP's first stop for every question |
| **The fallback** | `data-exploration` branch | Real 30-season DuckDB warehouse, a hardened SELECT-only guard, a full text-to-SQL harness, 16-question eval — where anything the gate can't resolve goes |

The `data-exploration` half is much further along than your log remembers. Specifically,
`experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py` **already contains**:

- `build_prompt(question)` — schema-grounded prompt, with the season convention and the min-games qualifier rule already written in
- `extract_sql(text)` — strips fences/prose out of model output
- `ollama_generate(model, prompt)` — the local-model call
- `execute_on_warehouse(sql)` — runs it on DuckDB
- `judge(got, item, meta)` — compares to expected with a 1e-7 tolerance
- `discover_models()`, scoring, report writing

It scored **16/16 in MOCK mode**. It has **never been run against a real model**. That is not a
building task — it's an *installing Ollama and typing one command* task.

**So week 1 is not "build text-to-SQL." Week 1 is "find out how good a free local model already is
at this, and fix the prompt until it's good enough."** That reframing is what makes 15 hours enough.

### The warehouse you already have

```
player_season   14,799 rows   1996-97 → 2025-26, incl. ts_pct, usg_pct, net_rating, pie...
game_logs      140,322 rows   player_id, season, game_date, opponent_abbr, is_playoff, min, pts, reb, ast, plus_minus
players          2,859 rows
player_crosswalk 2,859 rows   canonical_id ↔ nba / bbref / bdl
bbref_advanced     569 rows   per, bpm, vorp, ws
```

---

## 1. Architecture of the MVP

**Two paths, one gate, in front of everything.** The existing rule-based `parser.py`/`planner.py`
(the p0 scaffold, `learning` branch) is a real deterministic engine: regex/keyword NLU fills a
structured `Intent`, then a fixed SQL template — allow-listed to 5 metrics, parameterized filters —
answers it. Nothing free-form ever reaches SQL on that path, so it's instant, free, and can't be
injected. It's just *narrow*: single player, one of `pts/reb/ast/plus_minus/min`, avg/sum, optional
opponent/season/playoffs. No leaderboards, no advanced metrics, no comparisons.

The gate is simple: **try the rule-based path first. If it can resolve the question
(`Intent.is_answerable()`), answer it there — fast, free, zero risk. If it can't, fall through to
the LLM path.** This is exactly what `CLAUDE.md`'s own phase-4 note describes, and it's cheap to
keep — the parser, planner, and entity resolver already exist (~185 lines total) and the resolver's
schema already matches the real warehouse (`game_logs`, `players`), not just the old 5-player seed.

This is the full pipeline `CLAUDE.md` names — `question → NLU (intent) → text-to-SQL → DuckDB
execution → generation → answer card` — with NLU and text-to-SQL implemented as the two-path gate,
and **generation** (missing from the first draft of this plan) added back as its own explicit stage:
a formatter that turns a raw DuckDB result into a sentence. It is **template-based, not an LLM
call** — "who's the leader" questions return `{name, value}`; the formatter picks the template and
fills in numbers that are *already computed*. This satisfies the non-negotiable that the model never
computes or recalls a stat, while still giving the full pipeline `CLAUDE.md` describes, not a
truncated one.

```
question
   ↓
[ cache lookup ]                          ← Nick (a local model takes 2-5s; caching makes the demo feel real)
   ↓ miss
[ NLU — RULE-BASED GATE: parser.py → planner.py ]   ← exists (Ashish owns tuning it)
   ↓ Intent.is_answerable() ?
   ├── YES → build_sql (template, allow-listed) → DuckDB execute → AnswerCard(path="rule")
   │
   └── NO  ↓
       [ NLU/text-to-SQL — build_prompt + few-shot ]   ← Ashish
          ↓
       [ LLM provider: Ollama | Claude ]  ← Nick (one interface, two impls)
          ↓
       [ extract_sql ]                    ← exists
          ↓
       [ validate_sql — SELECT-only guard ] ← Nick hardens it
          ↓ reject → repair loop (once) → still bad → REFUSE
       [ DuckDB execute ]                 ← exists
          ↓
       AnswerCard(path="llm")
   ↓
[ GENERATION — format_answer(): number → sentence ]   ← Ashish, template-based, no LLM
   ↓
AnswerCard { answer, sql, rows, refused, reason, path }
   ↓
[ FastAPI /api/ask ] → [ web UI ]         ← Nick
```

**The non-negotiables from `CLAUDE.md` still hold and are all satisfied by this design:** the model
only writes language (SQL text and, in generation, the sentence shape — never the number), DuckDB
does every arithmetic operation, nothing executes without passing the allow-list guard, and an
unresolvable question returns a refusal rather than a number.
The rule-based gate doesn't weaken any of that — it's strictly *more* conservative than the LLM path,
since it never generates free-form SQL at all.

**Why this is worth the extra plumbing, not just extra safety:** the transparency card is the whole
product idea (`CLAUDE.md`: "every answer carries the SQL and the rows it came from"). Showing
`path: "rule"` vs `path: "llm"` on the card *is* that idea, made visible — it tells the person asking
exactly how sure the system is. That's a better demo than a single path, not just a safer one.

### The contract — write this on day 1, before anything else

This is the single most important structural decision, because it's what lets two people work in
parallel without blocking each other:

```python
# src/statlas/types.py
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass
class AnswerCard:
    question: str
    answer: str | float | None      # the number/name, or None if refused
    unit: str | None = None         # "PPG", "TS%", ...
    sql: str | None = None          # the SQL that was actually executed
    rows: list[dict] = field(default_factory=list)   # what the query returned
    refused: bool = False
    reason: str | None = None       # why, if refused
    path: Literal["rule", "llm"] | None = None   # which engine answered
    model: str | None = None        # only set when path == "llm"
    latency_ms: float | None = None
    cached: bool = False

def answer(question: str) -> AnswerCard: ...
```

Ashish implements `answer()` — including the gate itself: try `parser.parse` + `planner.build_sql`
first, fall through to the LLM path on `PlanError` or `not intent.is_answerable()`. Nick builds the
server and UI against a **stub** that returns a hard-coded `AnswerCard` — so the frontend can be
finished before the engine works, and neither of you ever sits waiting on the other. Agree on this
file first, commit it, then diverge.

### Branch strategy — stop the juggling

The branch split has cost you more time than any technical problem in this repo. Collapse it:

```bash
git switch -c mvp data-exploration                                   # start from the half with the real data
git checkout refs/heads/learning -- tests/                            # the eval harness
git checkout refs/heads/learning -- src/statlas/nlu src/statlas/query src/statlas/entities src/statlas/__init__.py
                                                                       # the rule-based gate (parser/planner/resolver)
```

**Everything for the next 3 weeks happens on `mvp`.** One branch, two people, normal PRs. `learning`
and `data-exploration` stay frozen as history.

---

## 2. Ashish's 15 sessions

Each session is ~1 hour and ends with something you can point at. If a day doesn't happen, the
plan slides — nothing here is time-critical, and the order matters more than the dates.

### Week 1 — how good is a free local model, actually?

| # | Session | Definition of done |
|---|---|---|
| **1** | **Unblock and install.** Run the repo cleanup in `claude-code-setup.md` (~10 min — it fixes the 27 broken git refs that warn on every command). Create the `mvp` branch. `brew install ollama && ollama serve`, then `ollama pull qwen2.5-coder:7b`. Write `src/statlas/types.py` (the contract above) and commit it. | `ollama list` shows the model; `types.py` is committed on `mvp` |
| **2** | **Get your first real number.** `python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py` against the real model. Don't fix anything. Just watch it and write the score down. | A number: "qwen2.5-coder:7b scored N/16" |
| **3** | **Read the failures like data.** For each miss, classify the cause: hallucinated column / wrong season convention / missing qualifier / wrong table / valid SQL but wrong intent. Tally them. | A table of failure counts by category in `learning/days/dayN/summary.md` |
| **4** | **Fix the top category.** Whatever came first in that tally, fix it in `build_prompt` — usually by adding 3-4 few-shot examples showing the right pattern. Re-run. | A before/after score, and you can say *why* it moved |
| **5** | **Second model, pick a winner.** `ollama pull sqlcoder:7b` (or `qwen2.5-coder:14b` if you have the RAM). Run both. Choose one and write down the reason. | Week-1 ship: a chosen model + a documented accuracy number |

> **If a session goes badly:** the fallback micro-task is always "add one more few-shot example and
> re-run the eval." It takes 15 minutes and always moves something.

### Week 2 — turn a benchmark script into an engine

| # | Session | Definition of done |
|---|---|---|
| **6** | **Promote it out of `experiments/` and wire the gate.** Create `src/statlas/sql_agent.py` with `answer(question) -> AnswerCard`. Inside: try `parser.parse` + `planner.build_sql` first (port from `learning` branch — point the entity resolver's queries at the real `players`/`game_logs` tables, no logic changes needed); on `PlanError`/unresolved, fall through to the LLM path, importing `build_prompt`/`extract_sql`/`validate_sql`/`execute_on_warehouse` rather than rewriting them. Set `path` on the returned card either way. | `answer("How many points did LeBron average in 2013?")` returns `path="rule"`; a leaderboard question returns `path="llm"` |
| **7** | **Repair loop.** On guard rejection or DuckDB error, re-prompt **once** with the error text appended. Cap at one retry — two retries is where latency stops being demoable. | Eval re-run showing the delta from repair alone |
| **8** | **Qualifier metadata.** Your own day-7 finding: the min-games qualifier is a *no-op* on per-game counting stats but *decisive* on rate stats (unqualified 3P% leaders were four bigs at 100% on one attempt). Encode per-metric thresholds as a dict in code — planner-owned, never model-generated. | `QUALIFIERS = {"fg3_pct": {"min_gp": 40, "min_fg3a": 3.0}, ...}` enforced post-hoc |
| **9** | **The refusal path.** After a failed repair, return `AnswerCard(refused=True, reason=...)`. Test it with deliberately impossible questions ("who had the best vibes in 2019?"). | Three nonsense questions all refuse cleanly, none invent a number |
| **10** | **Grow the eval 16 → 30.** Add leaderboard questions, rate-stat questions, multi-season comparisons, and 3-4 that *should* refuse. Run it. | Week-2 ship: `answer()` + a real accuracy number on 30 questions |

### Week 3 — make it a thing you can show someone

Nick owns the server and frontend files. Your sessions here are about the *content* of what's shown.

| # | Session | Definition of done |
|---|---|---|
| **11** | **Wire `answer()` into Nick's stub endpoint.** Delete the stub, import the real thing. | `curl localhost:8000/api/ask -d '{"q":"..."}'` returns a real card |
| **12** | **The generation stage.** `format_answer()` — this is the pipeline's fifth stage from `CLAUDE.md` (`... → DuckDB execution → generation → answer card`), not a cosmetic afterthought. Template-based, not an LLM call: `33.4954` → "33.5 PPG", percentages, ordinals, player names from ids, season labels (`2025` → `2024-25`), and full-sentence phrasing for the leaderboard shape ("X led the league with Y"). | A formatting function with tests; the UI shows sentences, not raw JSON |
| **13** | **Pick the demo questions.** 6 questions that show range: a simple average, a leaderboard with a qualifier, a head-to-head, a rate stat where the qualifier matters, a playoff split, and one that refuses. Verify each. | 6 questions that reliably work, hard-coded as UI chips |
| **14** | **Failure polish.** Make the refusal state look deliberate rather than broken. Add the latency indicator. Check what happens with an empty query, a 500-word query, a non-NBA query. | No state of the UI looks like a crash |
| **15** | **Ship.** README with a GIF, the final eval number, and the honest limitations list. Then, optionally, swap in the Claude API behind Nick's provider interface and re-run the eval to see the gap. | **A URL you can open in front of someone** |

---

## 3. Nick's track

See `NICK-BRIEF.md` — a standalone document you can send him as-is. Summary of the split:

| Ashish (data scientist) | Nick (SWE / security / AI eng) |
|---|---|
| Prompt design, few-shot selection | SELECT-only guard hardening + adversarial tests |
| Eval set design and measurement | FastAPI service + the web UI |
| Qualifier metadata, statistical correctness | LLM provider abstraction (Ollama ↔ Claude) |
| Answer formatting and semantics | Caching, CI, packaging, the demo running on his machine too |

**File-level ownership** so you never merge-conflict: Ashish owns `src/statlas/sql_agent.py`,
`prompts/`, `tests/eval_set*.json`. Nick owns `src/statlas/guard/`, `src/statlas/providers/`,
`server/`, `web/`, `.github/`. `types.py` is shared and changes only by agreement.

---

## 4. Resources

### Tier 0 — the load-bearing minimum (~2.5 hours total)

These fit inside 3 weeks. Watch/read them **outside** the build hour — on a commute, over coffee.
Protect the build hour for building; that's the whole reason the last three months didn't move.

| # | Resource | Time | Why this one |
|---|---|---|---|
| 1 | [3Blue1Brown — *Large Language Models explained briefly*](https://www.youtube.com/watch?v=LPZh9BOjkQs) | 7 min | Stage 4 has been "next" since June. This closes it. Phone-watchable. |
| 2 | [DuckDB — Window Functions](https://duckdb.org/docs/sql/window_functions) | 20 min | `RANK() OVER`, `QUALIFY`, clause order. Every leaderboard question in your eval set is this. |
| 3 | [DIN-SQL (arXiv 2304.11015)](https://arxiv.org/abs/2304.11015) — §3 only | 30 min | The single highest-value idea for your accuracy: decompose hard questions before generating SQL. Read §3, skip the rest. |
| 4 | [Spider (arXiv 1809.08887)](https://arxiv.org/abs/1809.08887) §1 + [BIRD (arXiv 2305.03111)](https://arxiv.org/abs/2305.03111) abstract | 25 min | Defines **execution accuracy** — the metric your eval harness already implements. Tells you what score is actually good. |
| 5 | [Ollama — structured outputs](https://ollama.com/blog/structured-outputs) | 20 min | How to force SQL-only output instead of post-hoc regex extraction. Directly improves week-1 numbers. |
| 6 | [Anthropic — tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use) | 20 min | For the week-3 API swap, and it's Track-2 phase D whether you formalize it or not. |

### Tier 1 — the shelf (after the MVP ships)

Genuinely valuable, genuinely does not fit in 15 hours. Do not start these in weeks 1-3.

- **Text-to-SQL survey** — [arXiv 2410.01066](https://arxiv.org/abs/2410.01066). The map of the field. (Note: `roadmap.md` cites 2406.08426 for the same purpose — pick one, don't read both.)
- **Self-consistency** — [arXiv 2203.11171](https://arxiv.org/abs/2203.11171). Sample *n* SQL drafts, execute all, take the majority result. The cheapest accuracy win after few-shot, and it fits your architecture perfectly since execution is already cheap.
- **Execution-guided decoding** — [arXiv 1807.03100](https://arxiv.org/abs/1807.03100). Use runtime errors to steer generation. Your repair loop is the poor man's version.
- **CHASE-SQL** — [arXiv 2410.01943](https://arxiv.org/abs/2410.01943). Current-generation multi-path approach.
- **Sentence-BERT** — [arXiv 1908.10084](https://arxiv.org/abs/1908.10084). For *dynamic* few-shot retrieval (your S5 probe found 94% relevance) and for the entity resolver.
- **CMU 15-445 — Query Execution I** ([YouTube](https://www.youtube.com/watch?v=RxdcEQJLrSc)) + the [DuckDB SIGMOD paper](https://duckdb.org/pdf/SIGMOD2019-duckdb.pdf). What the calculator is doing underneath.
- **RAG** — [Lewis et al., arXiv 2005.11401](https://arxiv.org/abs/2005.11401). For the glossary/example-retrieval layer in v2.

### Exercises

**There are no separate exercises in this plan, on purpose.** You have 15 hours and four graded
notebooks (`modules/01`, `02`, `04`, `05`) that already exist and haven't been opened since August.
Adding homework on top of a build plan at 1h/day is how the last three months went.

Every session above *is* the exercise — each has a definition of done that fails loudly if you
didn't understand the thing. If you want deliberate practice, the four unfinished gold NL→SQL pairs
in `modules/04-text-to-sql/exercises.ipynb` are the right size for a low-energy day, and they feed
directly into session 10's eval set.

---

## 5. Honest risk assessment

| Risk | Likelihood | What to do |
|---|---|---|
| **The local 7B model is just bad at this** (< 8/16) | Moderate | Don't grind. Switch to the Claude API in week 2 instead of week 3 — the point of the plan is a working product, and you already said you'd get there once you understood the shape. Nick's provider interface makes this a one-line change. |
| **Week 3 frontend slips** | Moderate | It's the last week for a reason. A polished CLI plus a real accuracy number is still a legitimate MVP; the UI is the part you can cut. |
| **Sessions don't happen** | Based on the last 3 months — likely | The plan is ordered, not dated. Sessions 1-5 are the ones that matter most; everything after compounds from them. Missing a week costs a week, not the project. |
| **Gate threshold gets fuzzy** | Moderate | `Intent.is_answerable()` is a clean boolean today (player + metric both resolved); keep it that way. Resist the urge to make the rule-based path "smarter" mid-sprint — if a question needs more than the fixed template, that's what the LLM path is for. Growing the rule-based path is a v2 idea, not an MVP one. |

**The honest version:** 15 hours to a demoable web app is tight but real, and only because the
warehouse, the guard, and the harness already exist. If you're going to lose time anywhere, lose it
in week 3 (polish), not week 1 (finding out where you actually stand).

---

## 6. First action

Session 1, in order. About an hour:

```bash
cd ~/Desktop/Projects/statlas
# 1. repo cleanup — see claude-code-setup.md §1 (fixes 27 broken refs, ~10 min)
# 2. one branch
git switch -c mvp data-exploration
git checkout refs/heads/learning -- tests/
# 3. the model
brew install ollama && ollama serve &
ollama pull qwen2.5-coder:7b
# 4. the contract
#    write src/statlas/types.py (AnswerCard, above), commit
```

Then session 2 is one command, and you'll have a number for the first time.
