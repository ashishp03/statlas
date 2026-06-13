# Statlas — Advanced Curriculum

A practice-, paper-, and video-based curriculum for building **Statlas** (an AI sports-stats
answer engine). Written for someone with an MS in Data Science: it skips intro hand-holding,
goes straight to primary sources, and every module **ships a change into the actual repo**.

> **How to use this.** Each module has two files in `learning/modules/NN-name/`:
> - `workbook.md` — objectives, the paper/video reading list, theory notes, and the exercise
>   brief with a "Definition of done" + a ship target (a real file in `src/statlas/`).
> - `exercises.ipynb` — runnable, homework-style cells with `# TODO` blocks and `assert`s that
>   act as auto-grading. Fundamentals are pure-Python/numpy (no GPU); heavier bits (torch,
>   embeddings, LLM calls) are clearly marked **optional** so the core always runs offline.
>
> Order is **sequential but advanced** — same spine as the original plan, harder rungs. Dip
> back into Track 1 fundamentals only as reference when an exercise exposes a gap.

---

## Track 1 — Conceptual AI/ML (the engine's brain)

Rough cadence ~60–90 min/session. Each module ends by shipping its project.

| # | Module | Core papers / sources | You ship → repo seam |
|---|--------|------------------------|----------------------|
| **M1** | **Transformer internals** | *Attention Is All You Need* (Vaswani 2017); *The Annotated Transformer*; Karpathy "Let's build GPT" + nanoGPT | From-scratch attention; nanoGPT run notes |
| **M2** | **NLU & entity resolution** | *BERT* (Devlin 2019); *Sentence-BERT* (Reimers 2019); rapidfuzz docs | Embedding-based `entities/resolver.py` + eval set |
| **M3** | **LLM app layer** | Anthropic/OpenAI function-calling & structured-output docs; *Toolformer* (Schick 2023); Pydantic/instructor | LLM `nlu/parser.py` returning the same `Intent` |
| **M4** | **Text-to-SQL** | *Spider* (Yu 2018); *BIRD* (Li 2023); *DIN-SQL* (Pourreza 2023); arXiv **2410.01066** (CHASE-SQL) | LLM SQL-draft path in `query/planner.py` w/ `assert_safe` |
| **M5** | **Computation engine & reliability** | execution-guided decoding (Wang 2018); self-consistency (Wang 2022) | Hardened `query/executor.py`: validate → run → verify |
| **M6** | **RAG** | *RAG* (Lewis 2020); *ColBERT*/late-interaction; reranking | glossary + example-query retriever feeding M3/M4 |
| **M7** | **Evaluation & reliability** | *HELM* ideas; execution-accuracy metric from Spider | 40–50 Q eval set + `tests/` accuracy harness |
| **M8** | **Visualization** | Vega-Lite grammar; answer-card patterns | auto answer cards from `Answer.card` |
| **Capstone** | **NBA ask-anything demo** | — | end-to-end: question → grounded answer + card |

### Module focus notes
- **M3 / M4 / M5 are your stated weak spots** ("LLM stuff, text-to-SQL, computation engine").
  They're sequenced where they belong, but each workbook front-loads the highest-leverage paper
  and a from-scratch exercise so you build intuition, not just glue code.
- The repo's existing rule-based `parser.py` and template `planner.py` are your **baselines**:
  every LLM upgrade is measured against them on the M7 eval set, so you can prove the model
  actually helps before trusting it.

---

## Track 2 — AI tooling (keeping an agent *in* the project)

Your "how to keep an Agent in the project" goal lives here. Each maps to a concrete artifact.

| Phase | Topic | Source | You ship |
|-------|-------|--------|----------|
| **T-B** | Claude Code workflows | docs.claude.com/claude-code | repo `CLAUDE.md` + a slash command |
| **T-C** | Skills | Skills docs | a `nba-query` skill wrapping `engine.ask` |
| **T-D** | Tools / function calling | tool-use docs | expose `run_sql` as a typed tool |
| **T-E** | **MCP** | modelcontextprotocol.io | `statmuse-clone` MCP server exposing `query_stats` |
| **T-F** | **Agent SDK — the resident agent** | Claude Agent SDK docs | a routing agent that lives in `src/statlas/agent/` |
| **T-G** | Cowork automation | scheduled-task docs | scheduled "stat of the day" |

> Track 2 is lighter per session (~30–45 min). Phase A orientation (defining
> skill/tool/MCP/connector/plugin/agent) is folded into T-B — define each term *in terms of
> your repo* rather than in the abstract.

---

## "Resident agent" thread (your priority, woven across modules)

Keeping an agent usefully *inside* a project is a recurring design question, so it gets a
through-line instead of one lecture:
1. **M3** — function calling: the agent's hands (it can call `parse`).
2. **M4/M5** — tools it can trust: SQL drafting gated by validation = an agent that can't lie.
3. **T-E** — MCP server: the standard socket other agents/clients plug into.
4. **T-F** — Agent SDK routing agent: the loop that decides *which* tool to call, with the
   answer-card as its audit trail. This is the capstone of "agent in the project."

---

*Modules built so far: M1, M2. The rest are stubs in this index and get fully fleshed out as
you reach them — tell the coach when you finish one and the next gets built.*
