# Day 5 — 2026-06-13

**Track 1 module:** M1 — Transformer internals   |   **Track 2 module:** T-B — Claude Code fundamentals

## Coach suggested
- **Track 1:** M1 session 1 is still the live target — *Attention Is All You Need* §3
  (arXiv 1706.03762) with the Annotated Transformer open beside it; fill the Q/K/V +
  causal-mask blanks in `modules/01-transformer-internals/workbook.md`, then pass
  exercises 1–2 (softmax + scaled dot-product attention) in `exercises.ipynb`.
  If session 1 is already done, advance to exercises 3–4 (multi-head + causal mask). ~75 min.
- **Track 2:** T-B — draft `CLAUDE.md` at the repo root (layout, how to run tests,
  what `parser.py`/`planner.py`/`executor.py` do). If already drafted, add a
  `.claude/commands/eval.md` slash command that runs the p0 eval set. ~30 min.
- **Stretch:** First ~30 min of Karpathy's "Let's build GPT" (bigram model section).

## What I actually did
- Verified the real data source (`nba_api`) end-to-end; confirmed all three v1 questions are answerable.
- Ran a full **EDA** on real 2025-26 NBA data → `days/day5/eda/` (report + 6 figures + cached CSVs).
- **Pivoted to foundations-first**: decided to learn all required concepts from the ground up before
  building. Created `learning/roadmap.md` as the new master guide; parked `curriculum.md`.
- **Completed roadmap Stage 3 — Transformers & attention** (the `TODAY.md` checklist, all 5 steps):
  watched 3B1B "Attention visually explained," read the Illustrated Transformer, read *Attention Is
  All You Need* §3.1–3.2, then implemented `softmax`, `scaled_dot_product_attention`, and `causal_mask`
  from scratch in numpy in `exercises/attention_from_scratch.ipynb` — **all three ✅ test cells pass.**
- **Set up the local env with uv**: installed uv on the Mac, bumped the pinned Python to **3.13**
  (3.14 blocked — `gensim` has no 3.14 wheels), ran `uv sync`, and registered `.venv` as a Jupyter
  kernel so notebooks resolve project deps. Wrote a full uv setup guide into the README and reconciled
  its study-plan section with `roadmap.md`.

## Notes & insights
- Data source = `nba_api` (official stats.nba.com wrapper), **free, no API key**; only constraint is
  informal rate-limiting → cache pulls.
- Core table `LeagueDashPlayerStats`: 582 players × 67 cols, **zero nulls, zero dup players**.
  Coverage floor = **1996-97** (older seasons need `LeagueLeaders`, reliable back to ~1979-80).
- Reliability rule discovered: **leaderboards need a min-games qualifier** (Jokić "led" playoff
  rebounds in 6 GP; Wemby was the true leader over 21 GP).
- Claude Max ≠ general API access (separate billing) → plan to start the LLM step with a free local
  model (Ollama).
- **Softmax stability:** subtract each row's max before `exp` — softmax is invariant to a per-row
  constant shift, so this prevents `exp(big)` → `inf`/`nan` with no change to the result. Do it with
  `np.max(x, axis=-1, keepdims=True)` (vectorized, no in-place row loop — the loop silently fails on
  1-D inputs). Softmax in attention is **always `axis=-1`** (per-query/per-row), not matrix-wide.
- **uv/Jupyter:** notebooks run a *kernel*, not the terminal's active venv — register the project
  `.venv` as a kernel (`uv run python -m ipykernel install --user --name statlas`) and select it.

## Coding / exercises
- EDA scripts (pulls + profiling + figures) run in-session; raw data cached to `eda/data/`.
- **Stage 3 exercise done:** `exercises/attention_from_scratch.ipynb` — `softmax` (stable),
  `scaled_dot_product_attention` (scale by √d, additive mask), `causal_mask` (`np.triu(..., k=1)`);
  all ✅ tests pass.
- Next: roadmap Stage 4 (LLMs) → Stage 5 (prompting & function calling); example-coding =
  sentence → strict JSON with Pydantic validation.

## Links & resources
- Master guide: learning/roadmap.md  (full resource index inside)
- Karpathy Zero to Hero: https://karpathy.ai/zero-to-hero.html
- CS224N (2024): https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D
- Illustrated Transformer: https://jalammar.github.io/illustrated-transformer/
- Text-to-SQL survey (2024): https://arxiv.org/abs/2406.08426

## Carry-over for next time
- Foundations-first mode. **Stage 3 (transformers) complete.** Next: roadmap Stage 4 (LLMs:
  tokenization, context windows, sampling/temperature) → Stage 5 (prompting, tool calling,
  structured JSON output). Load-bearing stages remaining: 5, 6 (text-to-SQL), 7 (SQL).
