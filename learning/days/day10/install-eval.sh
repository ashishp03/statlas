#!/usr/bin/env bash
# Installs the /eval slash command drafted on day 8.
# Extracts the command body from learning/days/day8/draft-eval-command.md (the block
# fenced with ````markdown) and writes it to .claude/commands/eval.md.
#
#   bash learning/days/day10/install-eval.sh
#
# Then type /eval in Claude Code. The harness self-bootstraps its DuckDB seed;
# verified green at 5/5 on 2026-09-20.
set -euo pipefail

SRC="learning/days/day8/draft-eval-command.md"
DEST=".claude/commands/eval.md"

if [ ! -f "$SRC" ]; then
  echo "error: $SRC not found — run this from the repo root on the 'learning' branch." >&2
  exit 1
fi

if [ ! -f "tests/run_eval.py" ]; then
  echo "note: tests/run_eval.py is missing on this branch (it lives on 'learning')."
  echo "      Either:  git switch learning"
  echo "          or:  git checkout refs/heads/learning -- tests/"
  echo "      Installing the command anyway."
fi

mkdir -p "$(dirname "$DEST")"
awk '/^````markdown$/{f=1;next} /^````$/{f=0} f' "$SRC" > "$DEST"

if [ ! -s "$DEST" ]; then
  echo "error: extracted an empty command file — check the fences in $SRC." >&2
  exit 1
fi

echo "wrote $DEST ($(wc -l < "$DEST") lines)"
echo "now type /eval in Claude Code"
