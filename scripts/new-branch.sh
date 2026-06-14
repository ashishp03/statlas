#!/usr/bin/env bash
# Create a new feature branch off main, with its own branch-context overlay.
#
# Usage:
#   scripts/new-branch.sh <branch-name> ["one-line purpose"]
#
# What it does:
#   1. branches <branch-name> off an up-to-date main (so it inherits the shared CLAUDE.md tree,
#      uv.lock, src/, tests/ — everything on main)
#   2. scaffolds .claude/branch.md from .claude/branch.template.md, filling in name/date/purpose
#   3. commits that overlay so the branch is ready to work on
set -euo pipefail

branch="${1:?usage: scripts/new-branch.sh <branch-name> [\"purpose\"]}"
purpose="${2:-TODO: describe what this branch is for}"
today="$(date +%Y-%m-%d)"

git switch main
git pull --ff-only 2>/dev/null || true     # refresh main if a remote exists; ignore if none
git switch -c "$branch"

mkdir -p .claude
cp .claude/branch.template.md .claude/branch.md
# BSD (macOS) and GNU sed both accept -i with a backup suffix:
sed -i.bak \
  -e "s|{{BRANCH}}|$branch|g" \
  -e "s|{{DATE}}|$today|g" \
  -e "s|{{PURPOSE}}|$purpose|g" \
  .claude/branch.md
rm -f .claude/branch.md.bak

git add .claude/branch.md
git commit -m "chore($branch): scaffold branch context (.claude/branch.md)"

echo "✅ Branch '$branch' created off main with .claude/branch.md."
echo "   Edit .claude/branch.md (Scope / instructions), then start working."
