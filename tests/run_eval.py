"""Eval runner — the scoreboard.

Run:  python tests/run_eval.py

Compares the engine's computed value against known-correct answers in eval_set.json.
This is how you avoid shipping a confident liar: every change must keep accuracy high.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make `statlas` importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statlas.engine import ask, ensure_db  # noqa: E402

EVAL_FILE = Path(__file__).parent / "eval_set.json"


def main() -> int:
    ensure_db()
    data = json.loads(EVAL_FILE.read_text())
    tol = data.get("tolerance", 0.05)
    cases = data["cases"]

    passed = 0
    for c in cases:
        ans = ask(c["q"])
        got = ans.value
        exp = c["expected"]
        ok = got is not None and abs(got - exp) <= max(tol, tol * abs(exp))
        passed += ok
        status = "PASS" if ok else "FAIL"
        got_str = "None" if got is None else f"{got:.2f}"
        print(f"[{status}] {c['q']}\n        expected={exp}  got={got_str}")

    acc = passed / len(cases) if cases else 0.0
    print(f"\nAccuracy: {passed}/{len(cases)} = {acc:.0%}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
