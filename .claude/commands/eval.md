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
