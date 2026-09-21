# Claude Code in VS Code — setup & repo cleanup

Run once. Roughly 30 minutes total, most of it in §1.

---

## 1. Fix the repo first (~10 min) — do this before anything else

Your `.git` directory has accumulated **24 empty (broken) ref files and 4 junk test branches**, plus
~30 stale worktree registrations. This is why every `git branch` prints a wall of
`warning: ignoring broken ref ...`, and it's been noise in every Claude Code session for months.
It also makes Claude's git output harder to read, which costs you real tokens and attention.

**Look before you delete:**

```bash
cd ~/Desktop/Projects/statlas

# the 24 broken (0-byte) refs — these are leftover .lock files from crashed git processes
find .git/refs -type f -empty | sort

# the 4 junk branches from old probe/test sessions
git branch | grep -E '_cointest|coachtest|testfile|_probe'

# the stale worktrees (~30, most pointing at /tmp dirs that no longer exist)
git worktree list
```

**Then clean:**

```bash
cd ~/Desktop/Projects/statlas

# 1. remove every empty ref file (all 24 are broken locks; real refs are never empty)
find .git/refs -type f -empty -delete

# 2. remove the junk test refs
rm -f .git/refs/deltest.tmp .git/refs/overwritetest
rm -f .git/refs/heads/_cointest .git/refs/heads/coachtest

# 3. stale worktrees — the 'locked' marker files block prune, so clear them first.
#    (Safe: your only real working tree is ~/Desktop/Projects/statlas itself.)
rm -f .git/worktrees/*/locked
git worktree prune -v

# 4. a stray probe file left in the object store by an earlier automated session
rm -f .git/objects/probe_test2

# 5. verify — this should now print NO warnings
git branch -a
git fsck --no-progress 2>&1 | head -20
```

After this, `git branch -a` should show exactly: `data-exploration`, `learning`, `learning-nlu`,
`main`, and the `origin/*` remotes. Nothing else.

> If `git fsck` reports dangling commits, that's normal and harmless — those are the coach's old
> automated commits. `git gc` will clear them if it bothers you.

---

## 2. Claude Code in VS Code

Two pieces, and it's worth knowing they're separate:

**The extension** — Cmd+Shift+X → search "Claude Code" → Install. If it doesn't appear afterwards,
run `Developer: Reload Window` from the Command Palette.

**The CLI** — the extension bundles its own private copy for the chat panel, but typing `claude` in
the integrated terminal needs the standalone install:

```bash
# check whether you already have it
claude --version

# if not:
npm install -g @anthropic-ai/claude-code
```

Then open the integrated terminal (Cmd+`) and run `claude`. It auto-detects the IDE and gets you
diff viewing and diagnostic sharing.

**Run `/terminal-setup` once.** It writes a Shift+Enter keybinding for multi-line input, sets
`terminal.integrated.gpuAcceleration: "off"` (which fixes garbled text in the integrated terminal —
a common and confusing problem), and adjusts scroll sensitivity for fullscreen mode.

The extension and CLI share conversation history, so `claude --resume` in the terminal picks up a
panel conversation.

---

## 3. Make sessions less annoying

**Check your existing hooks aren't fighting you.** `.claude/hooks/guard-bash.sh` currently steers
bare `python`/`pip`/`jupyter` toward `uv`. Per the 2026-07-18 note, you relaxed the rule so plain
`python` runs files and `uv` only manages dependencies — confirm the hook actually reflects that,
or it'll block commands the plan tells you to run:

```bash
cat .claude/hooks/guard-bash.sh | head -40
```

**Install the `/eval` command** — it's been drafted since 09-15 and verified green 5/5 on 09-20:

```bash
git switch learning              # or: git checkout refs/heads/learning -- tests/
bash learning/days/day10/install-eval.sh
```

**Permissions.** If you're approving the same commands repeatedly, add the safe ones to
`.claude/settings.json` so you stop being interrupted:

```json
{
  "permissions": {
    "allow": [
      "Bash(python tests/run_eval.py)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(uv run:*)",
      "Bash(ollama list)",
      "Bash(pytest:*)"
    ]
  }
}
```

**Point `CLAUDE.md` at the new branch.** Once you create `mvp`, its `.claude/branch.md` should say
what the branch is for. The repo's branch-overlay model already handles this — run
`scripts/new-branch.sh` or copy `.claude/branch.template.md` manually.

---

## 4. Kickoff prompt

Paste this into Claude Code in the repo root, after the cleanup in §1. It's written to make Claude
read the ground truth before proposing anything, which is the failure mode worth guarding against
here — the repo's own docs are partly out of date relative to what's on disk.

```
Read these, in this order, before doing anything:
  1. learning/MVP-3-WEEK-PLAN.md          — the plan we're executing
  2. CLAUDE.md                             — architecture constraints (non-negotiable)
  3. experiments/v1_nba_storage_retrieval_benchmark/SUMMARY.md
  4. experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py
  5. experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_sql_guard.py

Context: I'm building the 3-week MVP in that plan. I have ~1 hour a day. A collaborator
(strong SWE, security + AI infrastructure background) owns the service layer, the SQL guard,
the provider abstraction and the web UI — see learning/NICK-BRIEF.md for the file-level
ownership map. Don't touch his files.

Today is Session 1. Do these, in order, and stop after each for me to confirm:

  1. Create the `mvp` branch from `data-exploration`, and bring `tests/` across from `learning`.
  2. Write `src/statlas/types.py` containing the AnswerCard dataclass exactly as specified in
     the plan's §1. Nothing else in that file.
  3. Tell me the exact commands to install Ollama and pull qwen2.5-coder:7b on macOS, and how
     to verify the model responds.

Rules for this whole project:
  - The LLM writes SQL. DuckDB does every arithmetic operation. Never compute or recall a stat.
  - Nothing executes without passing validate_sql first.
  - If a question can't be answered, refuse — never invent a number.
  - Reuse what exists in experiments/ rather than rewriting it. build_prompt, extract_sql,
    validate_sql and execute_on_warehouse all already work.
  - When you're unsure whether something exists, read the file. Several docs in this repo are
    out of date relative to what's actually on disk.
```

### A second prompt worth keeping — for Session 3 (failure triage)

```
Run the text-to-SQL eval against the local model and produce a failure analysis.

  python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py

For every failure, show me: the question, the SQL the model generated, the SQL the eval set
expects, and your classification of the root cause from exactly this list:

  hallucinated-column | wrong-season-convention | missing-qualifier |
  wrong-table | valid-sql-wrong-intent | malformed-output

Then give me a count by category, sorted descending. Do not fix anything yet — I want to see
the distribution before we change the prompt.
```

---

## 5. If something breaks

| Symptom | Fix |
|---|---|
| Garbled text in the integrated terminal | `/terminal-setup` (sets `gpuAcceleration: off`) |
| `claude` not found in terminal, but the panel works | You have the extension but not the standalone CLI — §2 |
| `warning: ignoring broken ref` | §1 wasn't run, or was run partially |
| A bash command gets blocked unexpectedly | `.claude/hooks/guard-bash.sh` — §3 |
| `/eval` errors on a missing file | You're on a branch without `tests/`. `git switch learning`, or `git checkout refs/heads/learning -- tests/` |

**Sources:** [Use Claude Code in VS Code](https://code.claude.com/docs/en/vs-code) ·
[Configure your terminal](https://code.claude.com/docs/en/terminal-config) ·
[All settings](https://code.claude.com/docs/en/settings-reference)
