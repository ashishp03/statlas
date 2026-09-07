# Statlas — Study Plan: NLU & Text-to-SQL (reading / watching only)

**Created 2026-09-06.** Coding exercises deliberately left out — they already live in
`learning/modules/02-nlu-entity-resolution/exercises.ipynb`,
`learning/modules/04-text-to-sql/exercises.ipynb`, and
`learning/modules/05-computation-engine/exercises.ipynb`. This file is the **consume list**:
what to read, what to watch, in what order, and what to take away from each.

Sourced from the existing M2 / M4 / M5 workbooks + `roadmap.md` Stages 2, 5, 6, 7 — consolidated
so the whole NLU→SQL half of the project is one linear list instead of four.

**Everything here is free.** Nothing needs an API key.

---

## How to use this

Two parts, and **Part B is the load-bearing one.** If you only ever do half of this, do Part B.

Each item has a **size** (S = under 30 min, M = 30–75 min, L = 75+ min) so you can match the item
to the block of time you actually have, rather than skipping a session because you don't have
90 minutes. Sizes assume "read for the takeaway," not "read every equation."

Each item also has a **takeaway** — the one thing you should be able to say afterward without
looking it up. If you can say it, you're done with that item; don't perfectionist it.

**Skip rules.** You have an MS in DS. Items marked *(skim / revision)* are there for completeness
— skip them unless something feels shaky. Stage 3 (transformers) is already done, so this plan
starts downstream of it.

---

# Part A — NLU: question → structured meaning

The job: `"how many boards did Wemby average vs OKC"` → `Intent(player=..., metric=reb,
agg=avg, opponent=OKC)`. Two sub-problems that people conflate but shouldn't: **entity
resolution** (which player is "Wemby"?) and **intent parsing** (what is being asked?).

## A1 — Vector semantics *(skim / revision)*

| | |
|---|---|
| **Size** | M (2 lectures, ~80 min if watched; ~20 min if you skim the notes) |
| **What** | Stanford **CS224N (Spring 2024)** Lectures 1–2 — Word Vectors, Language Models |
| **Link** | https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D |
| **Backup** | Jurafsky & Martin, *SLP* 3rd ed. draft — the vector-semantics chapter. https://web.stanford.edu/~jurafsky/slp3/ |
| **Takeaway** | Why cosine over dot product, and why distributional similarity puts "rebounds / boards / rpg" near each other. |

*This is the one to skip if it's revision.* Its only job is to make A2 land.

## A2 — Contextual & sentence embeddings

**A2a — BERT.** *(M)*
Devlin et al., *BERT: Pre-training of Deep Bidirectional Transformers* (2019) — arXiv **1810.04805**.
https://arxiv.org/abs/1810.04805
Read **§3 only** (pre-training objectives + the fine-tuning setup). Skip the results tables.
**Takeaway:** what a *contextual* embedding buys you over a static one — "Jordan" the player vs
"Jordan" the country get different vectors because the surrounding tokens differ.

**A2b — Sentence-BERT.** *(S)*
Reimers & Gurevych (2019) — arXiv **1908.10084**. https://arxiv.org/abs/1908.10084
Short and immediately practical.
**Takeaway:** why you *cannot* just cosine-compare raw BERT `[CLS]` vectors for similarity, and why
mean-pooling with a siamese training objective fixes it. This is the paper that justifies the
embedding path in `resolver.py`.

## A3 — Entity linking (the "Wemby" problem)

**A3a — Neural Entity Linking survey.** *(M, skim)*
Sevgili et al. (2022) — arXiv **2006.00575**. https://arxiv.org/abs/2006.00575
Skim for the framing only; don't read it end to end.
**Takeaway:** the two-stage split — **candidate generation** (cheap, high recall, narrow 500
players to 10) vs **ranking** (expensive, high precision, pick 1 of 10). Knowing which stage is
your bottleneck is the whole game; on a small NBA roster it's ranking, not generation.

**A3b — rapidfuzz scorers.** *(S, docs)*
https://rapidfuzz.github.io/RapidFuzz/
Read what `WRatio` and `token_sort_ratio` actually compute.
**Takeaway:** you can't claim an embedding resolver "beat the baseline" if you don't know what the
baseline does. This is 15 minutes that makes a later result meaningful.

## A4 — Intent parsing & structured output

This is the **⭐ weak spot** flagged in `progress.md` (M3), and it's the box that turns A1–A3 into
an actual `Intent` object.

**A4a — Anthropic prompt engineering + tool use + structured outputs.** *(M, docs)*
https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
Read the overview, then the **tool use** and **structured output / JSON** pages.
**Takeaway:** how you constrain a model to emit a schema rather than prose — and what you do on the
~5% of calls where it doesn't. (Answer: validate and retry, never parse-and-hope.)

**A4b — Toolformer.** *(M)*
Schick et al. (2023) — arXiv **2302.04761**. https://arxiv.org/abs/2302.04761
**Takeaway:** the conceptual origin of "the model decides *when* to call a tool." Relevant because
Statlas's design is exactly this — the LLM never computes, it decides which query to ask for.

**A4c — Hugging Face LLM Course, ch. 1–2.** *(L, optional)*
https://huggingface.co/learn/llm-course/
Only if you want hands-on tokenizer/pipeline familiarity before Part B. Otherwise skip — Part B
doesn't depend on it.

---

# Part B — Text-to-SQL ⭐ (the central skill)

This is Statlas. Do this part even if Part A stalls.

## B1 — Orientation: the survey

*(L — but read only the intro + prompting section, which makes it M)*
Mohammadjafari et al., *From Natural Language to SQL: Review of LLM-based Text-to-SQL Systems*
(2024) — arXiv **2410.01066**. https://arxiv.org/abs/2410.01066

Read: **intro**, then the **prompting / in-context-learning section**, then just *look at* the
taxonomy figure. Do not read the whole survey; surveys are maps, not roads.

> Note: `roadmap.md` cites a different survey (arXiv **2406.08426**, *Next-Generation Database
> Interfaces*) while the M4 workbook cites 2410.01066. **Either works** — same territory. Pick one
> and don't re-read the other.

**Takeaway:** the field's vocabulary — schema linking, in-context learning, execution accuracy,
self-correction. You need these words before DIN-SQL will read cleanly.

## B2 — The method to copy: DIN-SQL

*(M — this is the single highest-value paper in the plan)*
Pourreza & Rafiei, *DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction*
(2023) — arXiv **2304.11015**. https://arxiv.org/abs/2304.11015

**Takeaway:** the four-stage pipeline —
**schema linking → difficulty classification → SQL generation → self-correction**.
The insight worth internalizing: you don't ask the model for SQL. You *decompose* the ask, and you
give the hard questions more scaffolding than the easy ones. This is the architecture
`query/planner.py`'s Phase-4 path is eventually going to be.

## B3 — How correctness is measured

**B3a — Spider.** *(S — skim the task setup + the metric definition)*
Yu et al. (2018) — arXiv **1809.08887**. https://arxiv.org/abs/1809.08887
**Takeaway:** the definition of **execution accuracy**, and why the field abandoned string/AST
matching — two SQL queries can be written completely differently and be semantically identical.

**B3b — BIRD.** *(M — skim, focus on §"why this is harder")*
Li et al. (2023) — arXiv **2305.03111**. https://arxiv.org/abs/2305.03111
**Takeaway:** three reasons BIRD is harder than Spider — **dirty/noisy real values, required
external knowledge, and efficiency scoring**. The third one matters directly to Statlas: a query
that returns the right answer via a full scan is still a worse query.

**You should be able to say, unprompted, why BIRD is harder than Spider and why execution accuracy
beats string match.** That pair of sentences is the definition-of-done for B3.

## B4 — Reliability: catching a bad query before it becomes a wrong answer

This is the part that makes Statlas *trustworthy* rather than merely working, and it's where the
project's "never fabricate a number" rule gets its teeth.

**B4a — Execution-guided decoding.** *(S)*
Wang et al. (2018) — arXiv **1807.03100**. https://arxiv.org/abs/1807.03100
**Takeaway:** partially execute a draft and let the *database's own runtime errors* (type mismatch,
empty result) prune bad candidates during generation. Free signal you're otherwise throwing away.

**B4b — Self-consistency.** *(M)*
Wang et al. (2022) — arXiv **2203.11171**. https://arxiv.org/abs/2203.11171
**Takeaway:** sample *k* candidates, marginalize over the **answer**, not the text. For SQL this
means voting on execution *results*, not on query strings — which is strictly better, because it
collapses all the string-different-but-equal forms into one vote.

**B4c — CHASE-SQL.** *(S, stretch, skim only)*
Pourreza et al. (2024) — arXiv **2410.01943**. https://arxiv.org/abs/2410.01943
**Takeaway:** what current SOTA looks like — multi-path candidate generation plus a *learned*
selector. Essentially B4b industrialized. Read it last or not at all.

## B5 — The engine underneath (why the DB, not the model, does the math)

**B5a — DuckDB SIGMOD demo paper.** *(S — it's a 4-page demo paper)*
Raasveldt & Mühleisen (2019). https://duckdb.org/pdf/SIGMOD2019-demo-duckdb.pdf
**Takeaway:** why an embeddable **columnar, vectorized** engine is the right calculator for
leaderboard-shaped queries.

**B5b — CMU 15-445, "Query Execution 1" (Andy Pavlo).** *(L, ~80 min)*
https://www.youtube.com/watch?v=I0QdCSu06_o
**Takeaway:** Volcano/iterator (one tuple per `next()`) vs **vectorized** (a batch of ~1–2k values
per call) execution, and why per-tuple virtual dispatch destroys modern CPUs. This is the lecture
that makes DuckDB stop being a black box.

**B5c — DuckDB window functions docs.** *(S, docs — most immediately useful item in Part B)*
https://duckdb.org/docs/sql/window_functions
**Takeaway:** `RANK() OVER`, `AVG() OVER (PARTITION BY ...)`, and especially **`QUALIFY`** — which
is how the repo's min-games-qualifier reliability rule gets expressed cleanly. Also lock in the
logical processing order: `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`, which is
why `HAVING` can reference an aggregate and `WHERE` can't.

---

# Suggested order

The honest ordering, given where the project actually is:

1. **B1** survey (intro + prompting only) — vocabulary
2. **B2** DIN-SQL — the architecture *(if you do one thing, do this)*
3. **B5c** DuckDB window functions docs — immediately usable, and short
4. **B3a** Spider — the metric
5. **B4a** execution-guided decoding — short, high leverage
6. **B3b** BIRD — the harder benchmark
7. **B4b** self-consistency
8. **A2b** Sentence-BERT — opens Part A cheaply
9. **A3a** entity-linking survey (skim) + **A3b** rapidfuzz docs
10. **A4a** Anthropic tool-use / structured-output docs
11. **A2a** BERT §3, **A4b** Toolformer, **B5a/B5b** DuckDB internals — in whatever order
12. **B4c** CHASE-SQL, **A1** CS224N, **A4c** HF course — optional tail

Rationale for putting B before A: Part A's payoff (a better resolver) is an *accuracy* upgrade to
something that already works. Part B's payoff is the thing that doesn't exist yet.

**Rough total:** ~14–18 hours of reading/watching for the full list; ~5 hours for items 1–7, which
is the genuinely load-bearing core.

---

# Resource index (flat list, all free)

**NLU**

- CS224N Spring 2024 · https://web.stanford.edu/class/cs224n/ · videos: https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D
- Jurafsky & Martin, SLP 3rd ed. draft · https://web.stanford.edu/~jurafsky/slp3/
- BERT · https://arxiv.org/abs/1810.04805
- Sentence-BERT · https://arxiv.org/abs/1908.10084
- Neural Entity Linking survey · https://arxiv.org/abs/2006.00575
- rapidfuzz docs · https://rapidfuzz.github.io/RapidFuzz/
- Anthropic prompt engineering · https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- Toolformer · https://arxiv.org/abs/2302.04761
- Hugging Face LLM Course · https://huggingface.co/learn/llm-course/

**Text-to-SQL**

- Survey (2024) · https://arxiv.org/abs/2410.01066 · alt: https://arxiv.org/abs/2406.08426
- DIN-SQL · https://arxiv.org/abs/2304.11015
- Spider · https://arxiv.org/abs/1809.08887
- BIRD · https://arxiv.org/abs/2305.03111
- CHASE-SQL · https://arxiv.org/abs/2410.01943
- Execution-guided decoding · https://arxiv.org/abs/1807.03100
- Self-consistency · https://arxiv.org/abs/2203.11171

**Engine**

- DuckDB SIGMOD 2019 demo · https://duckdb.org/pdf/SIGMOD2019-demo-duckdb.pdf
- CMU 15-445 Query Execution 1 · https://www.youtube.com/watch?v=I0QdCSu06_o
- DuckDB window functions · https://duckdb.org/docs/sql/window_functions
- DuckDB docs · https://duckdb.org/docs/

---

# When you want the coding back

It's already written and waiting — nothing to build:

- `learning/modules/02-nlu-entity-resolution/` — workbook + graded notebook (eval set, char-ngram
  resolver, threshold sweep) + hand-worked math problems
- `learning/modules/04-text-to-sql/` — workbook + notebook (gold NL→SQL pairs, `assert_safe`
  allow-list validator, `exec_match` scorer, schema-linking heuristic), grounded in the real day5
  EDA CSV via DuckDB. **3 of 8 gold pairs are filled in; 5 are an intentional TODO.**
- `learning/modules/05-computation-engine/` — workbook + notebook (vectorized-vs-row-at-a-time
  timing, window-function drills, second-pass `assert_safe`)

Both notebooks were execution-verified end-to-end when they shipped on 2026-08-25.

**Gap to know about:** module `03-nlu-intent-parsing` was started on a `learning-nlu` worktree but
**was never committed** — only M2 exists on that branch. If you want an intent-parsing module
(the A4 material as exercises), it needs to be rebuilt.
