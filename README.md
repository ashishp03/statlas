# statlas

An all-in-one hub for sports analytics — a natural-language sports stats engine (a "better StatMuse").

Ask a question in plain English, get an **exact** answer computed from a real database, with the SQL shown so you can trust it.

```
> What was Wemby's plus/minus vs OKC in the playoffs?
Victor Wembanyama averaged 4.4 plus/minus in the playoffs vs OKC (across 5 games).
```

> **Note:** v0 ships with small **sample data** (invented numbers) so it runs instantly with no API keys. Real NBA data plugs in at `data/ingest.py` (roadmap Stage 6, text-to-SQL).

## The core idea

The LLM/parser **never computes a statistic.** It only turns language into a structured query. DuckDB (the SQL engine) does the math — exactly and reproducibly. That separation is what makes the answers trustworthy.

```
question
  -> nlu.parse        language  -> structured Intent      (the "NLU")
  -> query.build_sql  Intent    -> validated SQL           (safe text-to-SQL)
  -> query.run        SQL       -> exact number            (the ONLY math)
  -> engine.compose   number    -> sentence + answer card
```

## Setup

This project uses [**uv**](https://docs.astral.sh/uv/) to manage Python, dependencies, and the virtual environment. You do **not** need to install Python or create a venv yourself — uv does both from the lockfile.

**1. Install uv** (one time, per machine):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Create the environment** from the lockfile:

```bash
uv sync                 # runtime + dev deps; reads .python-version + uv.lock
uv sync --extra llm     # add this if you want the optional Anthropic LLM deps
```

`uv sync` reads `.python-version` (the pinned interpreter, **3.13** — uv downloads it if missing), creates `.venv/`, and installs the exact versions from `uv.lock`. That's the whole setup.

### Daily use — you do not activate the venv

Run everything through `uv run`; it auto-uses `.venv` with no activation:

```bash
# one-off question
uv run statlas "How many points did LeBron average in 2013?"

# interactive mode (shows the parsed intent + SQL)
uv run statlas

# run the eval scoreboard
uv run python tests/run_eval.py
```

(If you prefer a classic activated shell: `source .venv/bin/activate` on macOS/Linux, `.venv\Scripts\activate` on Windows. Activation is only for terminals — notebooks ignore it; see below.)

### Managing dependencies

```bash
uv add geopandas        # add a runtime dependency (updates pyproject.toml + uv.lock)
uv add --dev pytest     # add a dev-only dependency
uv remove geopandas     # remove one
uv lock                 # re-resolve the lockfile
```

Commit `pyproject.toml`, `uv.lock`, and `.python-version` — together they let anyone reproduce your exact environment with one `uv sync`.

### Jupyter notebooks

Notebooks run a **kernel**, not your terminal's active venv — so activating does nothing for them. Register this project's venv as a kernel once:

```bash
uv run python -m ipykernel install --user --name statlas --display-name "Python (statlas .venv)"
```

Then in VS Code / JupyterLab pick the **`statlas` / `.venv/bin/python`** kernel (top-right of the notebook). To verify a notebook is on the right interpreter, run `import sys; print(sys.executable)` — it should end in `.venv/bin/python`. New packages added via `uv add` are picked up automatically; only re-run the `ipykernel install` command if you rebuild `.venv` (e.g. after changing the Python version).

### Changing the Python version

```bash
uv python pin 3.14      # rewrites .python-version (downloads it if needed)
uv sync                 # rebuilds .venv on the new version
# then re-run the `ipykernel install` command above
```

Keep the pin at or above the `requires-python` floor in `pyproject.toml`. **Caveat:** the pin is currently **3.13**, not the newest release — `gensim` (a compiled dependency) has no wheels for **3.14** yet and fails to build against its C API. 3.13 is the latest version the full dependency set supports; bump to 3.14+ only once `gensim` ships compatible wheels.

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

## How this maps to the learning roadmap

This is currently a **learning project in foundations-first mode** — the ground-up concept
stack (neural nets → NLP → transformers → LLMs → prompting → text-to-SQL → SQL → RAG → eval)
lives in [`learning/roadmap.md`](learning/roadmap.md), with `learning/progress.md` as the
tracker. The product build is paused; the rule-based scaffold above is the baseline.

When building resumes, each module is a deliberate seam where a roadmap stage upgrades a stub
into the real thing:

- **Stage 2 (NLP / embeddings):** `entities/resolver.py` — upgrade the nickname dict to an embedding/NER linker.
- **Stages 4–5 (LLMs + prompting):** `nlu/parser.py` — replace rule-based parsing with LLM tool-calling that returns the same `Intent`.
- **Stage 6 (text-to-SQL):** `data/ingest.py` — swap sample data for `nba_api`; let an LLM draft SQL for complex queries, always validated by `planner.assert_safe`.
- **Stage 7 (SQL / analytical DB):** the DuckDB query layer — window functions, aggregations, min-games qualifiers.
- **Stage 8 (RAG):** add a glossary + example-query retriever to improve parsing/SQL.
- **Stage 9 (eval):** grow `tests/eval_set.json` — it's your scoreboard.
- **Stage 10 (viz):** turn the `card` dict from `engine.ask()` into a shareable chart.

The interface between language and query stays fixed, so you can upgrade one stage at a time
without rewriting the rest.

## Branches & context files

This repo uses a **shared-core + per-branch-overlay** model so the context files stay consistent
across branches without merge pain:

- `main` is the trunk and the source of truth for shared files: the root `CLAUDE.md`, every
  subdirectory `CLAUDE.md`, this `README.md`, and the toolchain (`pyproject.toml`, `uv.lock`,
  `.python-version`). Edit these on `main`; flow them outward with `git merge main`.
- Every feature branch is created **from `main`** — `git switch -c <name> main`, or
  `scripts/new-branch.sh <name> "purpose"` — so it inherits all shared files automatically (a
  branch is a full snapshot of its parent; nothing is copied by hand).
- Branch-specific instructions + a rolling log live in **`.claude/branch.md`**: one file, same
  path on every branch, different content per branch. The root `CLAUDE.md` `@import`s it, so Claude
  always loads "shared core + this branch's specifics."
- `.claude/branch.md` is marked `merge=ours` in `.gitattributes`, so it never merges across
  branches. One-time per clone: `git config merge.ours.driver true`.
- Subdirectory `CLAUDE.md` files describe code and stay shared; put branch-specific notes about a
  folder inside `.claude/branch.md` rather than forking the subdir file.

Branches: `learning` (foundations-first study — see `learning/README.md`), `data-exploration`
(nba_api EDA), and feature branches off `main`.
