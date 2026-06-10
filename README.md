# statlas

An all-in-one hub for sports analytics — a natural-language sports stats engine (a "better StatMuse").

Ask a question in plain English, get an **exact** answer computed from a real database, with the SQL shown so you can trust it.

```
> What was Wemby's plus/minus vs OKC in the playoffs?
Victor Wembanyama averaged 4.4 plus/minus in the playoffs vs OKC (across 5 games).
```

> **Note:** v0 ships with small **sample data** (invented numbers) so it runs instantly with no API keys. Real NBA data plugs in at `data/ingest.py` (Study Plan Phase 4).

## The core idea

The LLM/parser **never computes a statistic.** It only turns language into a structured query. DuckDB (the SQL engine) does the math — exactly and reproducibly. That separation is what makes the answers trustworthy.

```
question
  -> nlu.parse        language  -> structured Intent      (the "NLU")
  -> query.build_sql  Intent    -> validated SQL           (safe text-to-SQL)
  -> query.run        SQL       -> exact number            (the ONLY math)
  -> engine.compose   number    -> sentence + answer card
```

## Quick start

```bash
pip install -r requirements.txt
export PYTHONPATH=src

# one-off question
python -m statlas.cli "How many points did LeBron average in 2013?"

# interactive mode (shows the parsed intent + SQL)
python -m statlas.cli

# run the eval scoreboard
python tests/run_eval.py
```

## Layout

```
src/statlas/
  data/        ingest.py + seed CSVs  -> builds the DuckDB warehouse (the "calculator")
  entities/    resolver.py            -> "Wemby"/"KD" -> player_id (nickname dict + fuzzy)
  nlu/         parser.py              -> question -> structured Intent (rule-based for now)
  query/       planner.py, executor.py-> Intent -> validated SQL -> exact number
  engine.py    orchestrates the pipeline and composes the answer card
  cli.py       terminal interface
tests/
  eval_set.json + run_eval.py         -> your accuracy scoreboard
```

## How this maps to the study plan

Each module is a deliberate seam where a learning phase upgrades a stub into the real thing:

- **Phase 2 (NLP/NLU):** `entities/resolver.py` — upgrade the nickname dict to an embedding/NER linker.
- **Phase 3 (LLM app layer):** `nlu/parser.py` — replace rule-based parsing with LLM function-calling that returns the same `Intent`.
- **Phase 4 (text-to-SQL):** `data/ingest.py` — swap sample data for `nba_api`; let an LLM draft SQL for complex queries, always validated by `planner.assert_safe`.
- **Phase 5 (RAG):** add a glossary + example-query retriever to improve parsing/SQL.
- **Phase 6 (eval):** grow `tests/eval_set.json` — it's your scoreboard.
- **Phase 7 (viz):** turn the `card` dict from `engine.ask()` into a shareable chart.

The interface between language and query stays fixed, so you can upgrade one stage at a time without rewriting the rest.
