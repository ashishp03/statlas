# DRAFT — `.claude/commands/eval.md`

This is the **T-B ship item** ("`CLAUDE.md` + slash command"), written out so the only work left
is a copy. It has been the single open Track-2 item on the board since early September and has
never landed, so the coach drafted it rather than assigning it again.

## How to install (~2 min, on whichever branch has `tests/`)

```bash
mkdir -p .claude/commands
# paste the block below into .claude/commands/eval.md
```

Then in Claude Code, type `/eval`.

## The file

````markdown
---
description: Run the Statlas p0 eval set and report accuracy
allowed-tools: Bash(python tests/run_eval.py), Read
---

Run the project's golden eval set and report the scoreboard.

1. Run: `python tests/run_eval.py`
2. Report the accuracy line verbatim (`Accuracy: X/Y = Z%`).
3. For every `[FAIL]` case, show the question, the expected value and the value the
   engine returned.
4. For each failure, say which pipeline stage is the likely culprit —
   `parser` (intent misread), `planner` (wrong SQL / wrong filter), `executor`
   (right SQL, wrong number), or `data` (the seed rows don't support the question) —
   and point at the file.
5. Do NOT edit `tests/eval_set.json` to make a case pass. The eval set is the
   scoreboard; moving the goalposts defeats the purpose. If a case looks genuinely
   wrong, say so and stop.

$ARGUMENTS
````

## Notes on the design

- `allowed-tools` is scoped to the exact command so the slash command can't wander.
- Step 5 encodes the project's own reliability rule — a `CLAUDE.md` non-negotiable
  ("the engine refuses to guess") applies to the eval harness too: an eval you can
  edit to green is not an eval.
- `$ARGUMENTS` at the end lets `/eval only the playoff questions` work without a
  second command.
- Runner reference: `tests/run_eval.py` reads `tests/eval_set.json`, calls
  `statlas.engine.ask()` per case, and compares with a tolerance (default 0.05,
  overridable per eval-set via the `tolerance` key).

## Definition of done

`/eval` prints an accuracy percentage in Claude Code. That checks off **T-B** and opens
**T-C (Skills)**.
