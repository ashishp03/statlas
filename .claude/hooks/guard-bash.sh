#!/usr/bin/env bash
# PreToolUse(Bash) guard: enforce the uv-managed environment.
# Blocks a bare `python`/`pip`/`jupyter` invocation (at command position) so work
# always runs against the locked uv env, never system Python.
#
# Allowed (NOT blocked) because the interpreter isn't at a command boundary:
#   uv run python ...      uv pip install ...      .venv/bin/python ...
#   uv run jupyter ...     uvx ...
# Blocked:
#   python script.py       pip install foo         jupyter nbconvert ...
#   cd x && pip install foo
set -euo pipefail

cmd="$(jq -r '.tool_input.command // empty')"
[ -z "$cmd" ] && exit 0

# Match python/python3/pip/pip3/jupyter only when it starts the command or follows
# a shell separator (; & |). Forms prefixed by `uv run `, `uv `, or a path don't match.
if printf '%s' "$cmd" | grep -Eq '(^|[;&|]+[[:space:]]*)(python3?|pip3?|jupyter)([[:space:]]|$)'; then
  echo "Blocked: run this through uv, not bare python/pip/jupyter." >&2
  echo "  Use:  uv run <cmd>   |   uv add <pkg>   |   uv run --with jupyter jupyter nbconvert --execute ..." >&2
  echo "(statlas pins Python 3.12 via uv; bare python may hit the wrong interpreter.)" >&2
  exit 2
fi
exit 0
