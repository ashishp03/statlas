#!/usr/bin/env bash
# PreToolUse(Bash) guard: keep DEPENDENCY management on uv.
# Blocks a bare `pip`/`jupyter` invocation (at command position) so packages are managed by uv
# (uv add / uv sync / uv lock) and notebooks run through the uv-provisioned jupyter.
# Running scripts directly with `python ...` is ALLOWED — the repo's uv `.venv` is on PATH.
#
# Allowed (NOT blocked):
#   python script.py       python -m pytest        .venv/bin/python ...
#   uv run python ...      uv add ...              uv pip install ...      uvx ...
# Blocked (steered to uv):
#   pip install foo        jupyter nbconvert ...   cd x && pip install foo
set -euo pipefail

cmd="$(jq -r '.tool_input.command // empty')"
[ -z "$cmd" ] && exit 0

# Match pip/pip3/jupyter only when it starts the command or follows a shell separator (; & |).
# Forms prefixed by `uv ` (uv pip / uv run jupyter) or a path don't match.
if printf '%s' "$cmd" | grep -Eq '(^|[;&|]+[[:space:]]*)(pip3?|jupyter)([[:space:]]|$)'; then
  echo "Blocked: manage packages with uv, and run jupyter through uv." >&2
  echo "  Use:  uv add <pkg>   |   uv sync   |   uv run --with jupyter jupyter nbconvert --execute ..." >&2
  echo "(Running scripts directly with 'python ...' is fine — the uv .venv is active.)" >&2
  exit 2
fi
exit 0
