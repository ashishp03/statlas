#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) guard: protect generated/locked files everywhere,
# and enforce branch scope (no product code on the data-exploration branch).
set -euo pipefail

path="$(jq -r '.tool_input.file_path // empty')"
[ -z "$path" ] && exit 0

# 1) Never hand-edit generated or locked files (any branch).
case "$path" in
  *uv.lock|*.duckdb|*.duckdb.wal)
    echo "Blocked: '$path' is generated/locked — don't hand-edit it." >&2
    echo "  Dependencies: use 'uv add' / 'uv lock' (regenerates uv.lock)." >&2
    echo "  DuckDB files are built by the warehouse builder, not edited." >&2
    exit 2 ;;
esac

# 2) Branch scope: product/pipeline code does not belong on data-exploration.
#    Branch-aware so this rule is a no-op on the product / main branches.
branch="$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
if [ "$branch" = "data-exploration" ]; then
  case "$path" in
    *src/statlas/*)
      echo "Blocked: '$path' is product code (src/statlas/**) — out of scope on 'data-exploration'." >&2
      echo "  This branch is read-only NBA data exploration; product changes live on the product branch." >&2
      exit 2 ;;
  esac
fi
exit 0
