# experiments/ — Versioned Experiment Tree

> This directory holds **self-contained, versioned experiments**. Each one answers a specific
> question with its own data, pipeline, results, and docs, and lives entirely inside a single
> `vN_<name>/` folder. This file describes the shared convention; each experiment's own
> `CLAUDE.md` is the source of truth for that experiment's scope.

## Convention

- **One folder per experiment, version-prefixed:** `vN_<short_name>/` (e.g.
  `v1_nba_storage_retrieval_benchmark/`). The number is a monotonic experiment counter, not a
  code version.
- **Self-contained:** every `vN_` dir carries its own `config.py` (paths + contracts), `pipeline/`
  (numbered stage scripts), `data/` (raw pulls + built stores), `results/` (metrics + figures),
  an `eval_set.json` where correctness matters, and its own docs (`CLAUDE.md`, `README.md`,
  `ARCHITECTURE.md`, `DECISIONS.md`). Nothing an experiment needs lives outside its folder.
- **Each `vN_` dir has its own `CLAUDE.md`** — the local goals, scope, run order, and
  non-negotiables. Read it before touching anything inside that experiment.
- **Data + built stores are reproducible and git-ignored** (`data/.gitignore` excludes
  `raw/`, `stores/`, and all artifact extensions). Never commit real API pulls or built stores;
  they are rebuilt from the pipeline.
- **Findings flow to `main`; code does not.** As with the exploration notebooks, experiment
  code stays on its feature branch. Only distilled conclusions flow to `main` — as `CLAUDE.md`
  architecture-decision lines or docs — via a deps/docs PR. Experiment pipelines are **never**
  merged into `main`.
- **Dependencies are managed with uv** (`uv sync` / `uv add` / `uv lock`). Stage scripts are
  ordinary Python programs — see each experiment's `README.md` for how to run them.

## Index

| Version | Directory                          | Question it answers                                                                 | Status                                   |
|---------|------------------------------------|-------------------------------------------------------------------------------------|------------------------------------------|
| v1      | `v1_nba_storage_retrieval_benchmark` | Which storage format × retrieval path is the fastest **correct** "calculator" for NBA stats — and can a free local LLM draft the SQL? | Active — S1 raw data pulled; S2–S6 building |

See `v1_nba_storage_retrieval_benchmark/CLAUDE.md` for that experiment's goals, run order, and
the store × query matrix, and its `ARCHITECTURE.md` / `DECISIONS.md` for the design and rationale.
