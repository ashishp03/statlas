# Statlas — Ground-Up Learning Roadmap (Foundations First)

> **Mode (set 2026-06-13):** learn-before-build. We are *not* building the product yet. The goal
> is to understand every concept Statlas needs — from the ground up — through intro videos,
> lectures, and papers, with small **example-coding** exercises to keep the hands warm. We start
> building properly only once the foundations feel solid. This doc is the master guide; the older
> `curriculum.md` (advanced, build-focused) is parked and will be revived at the build stage.

---

## Part 0 — Framing: what we're learning toward

### What StatMuse does
StatMuse is a **natural-language answer engine for sports/finance stats**. You type "What did
LeBron average in the 2013 playoffs?" and it returns the exact number, a sentence, and a little
visual card — not a chatbot guess. The hard part isn't chatting; it's being **exactly right every
time**. Under the hood, systems like this don't ask a language model to *recall* stats (models
hallucinate numbers). They:

1. **Understand** the question (which player, which stat, which filter, which season).
2. **Translate** it into a precise database query.
3. **Compute** the answer with a real database (the only component allowed to do math).
4. **Phrase** the result back in natural language + a chart.

### What Statlas does differently (our thesis)
- **Transparency.** Every answer shows the SQL and the rows it used — you can always audit *how*
  the number was produced. Trust, not vibes.
- **Open data + open stack.** Free public NBA data (`nba_api`), an embedded database (DuckDB),
  and (to start) free/local models. No black boxes, no paywalls.
- **Computation engine, not a "model that knows stats."** The LLM only handles *language*; the
  database does *all arithmetic*. This is the core architectural bet.
- **Eval-driven reliability.** A golden question→answer set is the scoreboard; we measure
  accuracy on every change instead of trusting demos.
- **Extensible.** v1 is simple stat lookups; the same pipeline later grows to advanced stats,
  player comparisons, correlations, and "explain why."

### The pipeline (memorize this — every topic below maps to one box)
```
question
  → [NLU]            understand intent + entities      ── concepts: NLP, embeddings, NER
  → [Text-to-SQL]    intent → a precise SQL query      ── concepts: LLMs, prompting, text-to-SQL
  → [Execution]      run SQL on DuckDB → exact number  ── concepts: SQL, analytical databases
  → [Generation]     number + rows → sentence + card   ── concepts: prompting, structured output
  → answer (+ transparency card)
```
Supporting concepts wrapping the whole thing: **RAG** (retrieve glossary/example queries to help
the SQL step), **Evaluation** (is it right?), and the **AI-tooling layer** (skills/tools/MCP/agents)
for how it's packaged.

---

## Part 1 — The concept stack, ground up

Each stage: **why it matters → resources (intro → deeper → paper) → an example-coding exercise**
that practices the idea on a *toy* problem (not Statlas itself).

### Stage 0 — Foundations check (skip what you already own)
You have an MS in Data Science, so most of this is review — use it as a checklist, not homework.
- **Python data stack:** numpy, pandas, plotting. ✔ if you can profile a dataframe fluently.
- **SQL fundamentals:** SELECT/WHERE/GROUP BY/JOIN/ORDER BY/LIMIT. ✔ if comfortable.
- **Probability & stats:** distributions, mean/median/variance, correlation. ✔.
- **ML basics:** train/val/test, loss, gradient descent, over/underfitting. ✔.

*If any are shaky, fix that one first — everything else builds on them.*

### Stage 1 — Neural networks & deep learning intuition
> **MS-DS note:** you almost certainly know this — **skip it.** Only do the micrograd exercise
> below if you've never implemented backprop *from scratch* and want to once. Otherwise jump to
> Stage 3.

**Why:** transformers are neural nets; you need the mental model of layers, weights, loss, and
backprop before attention makes sense.
- Intro (visual): **3Blue1Brown — Neural Networks** series (eps. 1–4). Best intuition for what a
  network *is* and how backprop works.
- Hands-on: **Karpathy, "The spelled-out intro to neural networks and backprop: building
  micrograd"** (video 1 of *Neural Networks: Zero to Hero*). You build an autograd engine by hand.
- **Example coding:** reproduce micrograd's `Value` class and train a tiny 2-layer net on a toy
  dataset (e.g. make_moons). Goal: feel forward + backward pass.

### Stage 2 — NLP foundations: words → vectors → language models
**Why:** the NLU box. "Wemby" → a player; "boards" → rebounds. This is embeddings + sequence
modeling.
- Lecture: **Stanford CS224N (Spring 2024)** Lectures 1–2 (Word Vectors, Language Models) and 3
  (Backprop/NN). Gold-standard NLP course, free on YouTube.
- Reference book: **Jurafsky & Martin, *Speech and Language Processing* (3rd ed. draft, free
  online)** — chapters on vector semantics & embeddings as needed.
- **Example coding:** train word2vec-style embeddings on a small corpus (or load GloVe) and find
  nearest neighbors; cluster a few sports terms to see "rebounds/boards/rpg" land together.

### Stage 3 — Transformers & attention (the heart of it)
**Why:** every modern LLM is a transformer; text-to-SQL quality rides on it.
- Intro (visual): **Jay Alammar, "The Illustrated Transformer."** Read slowly, twice.
- Paper: **Vaswani et al., "Attention Is All You Need" (arXiv 1706.03762)** — read §3 with the
  Illustrated Transformer open beside it.
- Hands-on: **Karpathy, "Let's build GPT: from scratch, in code"** + his **nanoGPT** repo.
- **Example coding:** implement scaled dot-product attention and a causal mask from scratch in
  numpy/torch; then run nanoGPT on the tiny-shakespeare dataset and watch it learn.

### Stage 4 — LLMs: how the big models actually work
**Why:** you'll be *using* an LLM as the text-to-SQL engine; know tokenization, context windows,
pretraining vs. fine-tuning, sampling/temperature.
- Intro (talk): **Karpathy, "Intro to Large Language Models"** (1-hour overview) — the busy
  person's mental model.
- Course: **Hugging Face LLM Course**, chapters 1–4 (transformers, using models, tokenizers,
  fine-tuning), then 5–8 (datasets, classic NLP tasks). Free, hands-on.
- **Example coding:** use a small HF model for a non-Statlas task (sentiment or NER on a public
  dataset); experiment with tokenization and temperature to see their effects.

### Stage 5 — Prompting & the LLM application layer
**Why:** the glue. In-context learning, few-shot examples, **function/tool calling**, and
**structured (JSON) outputs** are how you get an LLM to emit a reliable Intent or SQL.
- Read: **Anthropic prompt-engineering docs** (`docs.claude.com`) — overview + tool use +
  structured outputs.
- Concept: **Toolformer (arXiv 2302.04761)** for the idea of models calling tools/functions.
- **Example coding:** write a prompt that makes an LLM (local or API later) turn a sentence into a
  strict JSON schema (e.g. `{player, metric, season}`); validate with Pydantic; handle failures.

### Stage 6 — Text-to-SQL ⭐ (the central skill)
**Why:** this *is* Statlas's core. NL question → correct SQL over our schema.
- Survey (orientation): **"Next-Generation Database Interfaces: A Survey of LLM-based
  Text-to-SQL" (arXiv 2406.08426)** — read the intro + the prompting/in-context section.
- Method: **DIN-SQL (Pourreza & Rafiei, arXiv 2304.11015)** — decomposed text-to-SQL: schema
  linking → classification → generation → self-correction. The pattern we'll copy.
- Benchmarks: **Spider (arXiv 1809.08887)** and **BIRD (arXiv 2305.03111)** — how the field
  measures correctness; skim the task setup and the "execution accuracy" metric.
- **Example coding:** download the Spider *sample* or the Chinook SQLite DB; hand-write 10 NL→SQL
  pairs; then prompt a model to generate SQL from the schema and check execution accuracy on a
  toy set. (This is exactly Statlas in miniature, on someone else's data.)

### Stage 7 — SQL & analytical databases (the computation engine)
**Why:** the box that does the math. Window functions and aggregations are how leaderboards,
rankings, per-game splits, and "min-games qualifiers" get computed *correctly*.
- Learn: **DuckDB docs** (it's the engine in the repo) — CTEs, `GROUP BY`, `QUALIFY`, window
  functions (`RANK() OVER`, `AVG() OVER`).
- Drill: any solid "SQL window functions" tutorial; practice on the cached EDA CSVs in
  `days/day5/eda/data/`.
- **Example coding:** load the EDA CSV into DuckDB and write, by hand, the SQL for the three v1
  questions — including a leaderboard with a `HAVING gp >= 58` qualifier. (Pure SQL, no LLM.)

### Stage 8 — RAG (retrieval-augmented generation)
**Why:** to feed the SQL step the right context — a glossary ("double-double" = …) and similar
solved example queries — without stuffing everything into the prompt.
- Paper: **Lewis et al., "Retrieval-Augmented Generation…" (arXiv 2005.11401)** — the original RAG.
- Concept: embeddings + vector similarity search; chunking; why retrieval beats fine-tuning for
  facts that change.
- **Example coding:** build a tiny semantic search: embed ~50 NBA glossary terms, retrieve the
  top-k for a query. (Reuses Stage 2 embeddings.)

### Stage 9 — Evaluation & reliability
**Why:** a stats engine lives or dies on *being right*. You can't improve what you don't measure.
- Concept: golden eval sets, execution accuracy, regression testing, hallucination control,
  confidence/"I don't know."
- Reference: the EDA already surfaced a real reliability rule — **min-games qualifiers** for
  leaderboards (Jokić "led" playoff rebounds in 6 games; Wemby was the real leader over 21).
- **Example coding:** extend the repo's `tests/eval_set.json` idea — write 15 question→expected
  pairs and a script that scores accuracy within a tolerance.

### Stage 10 — Visualization & answer presentation (lighter)
**Why:** the "answer card" — turning a number + rows into a sentence and a small chart.
- You already did real EDA viz this session (`days/day5/eda/figs/`). When the time comes, the
  skill is: pick the chart for the question type (bar for leaders, line for trends, scatter for
  comparisons) and auto-generate it.

### Side track — AI tooling (learn alongside, lighter touch)
The *packaging* layer: **skill / tool / MCP / connector / plugin / agent.** Read the orientation
on `docs.claude.com` and `modelcontextprotocol.io` and write one-line definitions of each, mapped
to where they'd fit in Statlas. Deepen only when we start building.

---

## Part 2 — "Example coding while learning" (a running list)
Keep a `learning/playground/` folder. None of these are Statlas — they're skill-builders:
1. micrograd reimplementation + tiny net (Stage 1)
2. embedding nearest-neighbors on a small corpus (Stage 2)
3. attention-from-scratch + nanoGPT on tiny-shakespeare (Stage 3)
4. HF model for NER/sentiment on a public dataset (Stage 4)
5. sentence → strict JSON with Pydantic validation (Stage 5)
6. NL→SQL on Chinook/Spider-sample with an execution-accuracy check (Stage 6)
7. DuckDB window-function drills on the EDA CSVs (Stage 7)
8. tiny semantic search over a glossary (Stage 8)
9. a 15-question eval harness (Stage 9)

---

## Part 3 — Suggested order & "am I ready to build?"
Rough sequence (flexible, no deadlines): **0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → (8, 9 in parallel) →
10.** Stages 3, 5, 6, 7 are the load-bearing ones for Statlas; spend the most time there.

You'll know you're ready to build the real thing when you can, without looking it up:
- explain attention and why the DB (not the LLM) must compute the numbers;
- write the three v1 SQL queries by hand, with a qualifier;
- prompt a model to emit valid JSON / SQL and validate it;
- describe how you'd measure whether an answer is correct.

When those feel easy, we un-park `curriculum.md` and build the vertical slice.

---

## Resource index (all free)
- 3Blue1Brown Neural Networks: https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
- Karpathy, Neural Networks: Zero to Hero: https://karpathy.ai/zero-to-hero.html · code: https://github.com/karpathy/nn-zero-to-hero
- Karpathy, "Let's build GPT": https://www.youtube.com/watch?v=kCc8FmEb1nY · nanoGPT: https://github.com/karpathy/nanoGPT
- Stanford CS224N (Spring 2024): https://web.stanford.edu/class/cs224n/ · videos: https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D
- Jurafsky & Martin, SLP (free 3rd-ed draft): https://web.stanford.edu/~jurafsky/slp3/
- Jay Alammar, The Illustrated Transformer: https://jalammar.github.io/illustrated-transformer/
- Attention Is All You Need: https://arxiv.org/abs/1706.03762
- Hugging Face LLM Course: https://huggingface.co/learn/llm-course/
- Anthropic prompt engineering: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- Toolformer: https://arxiv.org/abs/2302.04761
- Text-to-SQL survey (2024): https://arxiv.org/abs/2406.08426
- DIN-SQL: https://arxiv.org/abs/2304.11015
- Spider: https://arxiv.org/abs/1809.08887 · BIRD: https://arxiv.org/abs/2305.03111
- RAG (Lewis et al. 2020): https://arxiv.org/abs/2005.11401
- DuckDB docs: https://duckdb.org/docs/ · Model Context Protocol: https://modelcontextprotocol.io
