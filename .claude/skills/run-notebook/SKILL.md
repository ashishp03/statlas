---
name: run-notebook
description: >
  Execute a Jupyter notebook end-to-end using the project's exact uv-managed
  incantation (uv run --with jupyter jupyter nbconvert --execute). Use when asked
  to run, re-run, or refresh a notebook in this repo.
argument-hint: "[path/to/notebook.ipynb]"
disable-model-invocation: true
allowed-tools: Bash
---

Execute the notebook at the path the user provided (default to the one currently
open or named in the request if no path is given).

Run **exactly** this — it is the only supported way to execute notebooks in statlas
(uv-managed env, Jupyter pulled in on demand, executed in place):

```bash
uv run --with jupyter jupyter nbconvert --to notebook --execute --inplace "<NOTEBOOK_PATH>"
```

Rules:
- Never use bare `python`/`jupyter` (a PreToolUse hook blocks it) — always go through `uv run`.
- `--inplace` writes outputs back into the same file; confirm the path before running
  if it's ambiguous.
- nba_api cells can be slow/flaky. If execution fails on a live-API cell, report the
  failing cell and the error rather than retrying blindly — it's usually a rate limit
  (re-run after a short wait), not a code bug.
- After it completes, report the executed path and a one-line status (cells run / any errors).
