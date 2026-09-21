#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) guard: protect generated/locked files everywhere.
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

# NOTE: this used to also block src/statlas/** on data-exploration ("product code doesn't belong
# here"). Dropped 2026-09-20: data-exploration now builds real src/statlas/ content directly
# (learning will never merge to main, so there's no cross-branch collision risk to guard against).
exit 0
