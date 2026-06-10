"""Command-line interface.

Usage:
    python -m statlas.cli "What was Wemby's plus/minus vs OKC in the playoffs?"
    python -m statlas.cli            # interactive mode
    python -m statlas.cli --rebuild  # rebuild the seed database first

Add --debug to see the structured Intent and the generated SQL (great for learning).
"""
from __future__ import annotations

import sys

from statlas.data.ingest import build_from_seed
from statlas.engine import ask, ensure_db


def _print_answer(question: str, debug: bool) -> None:
    ans = ask(question)
    print(f"\nQ: {question}")
    print(f"A: {ans.text}")
    if debug and ans.intent is not None:
        print("   --- debug ---")
        i = ans.intent
        player = i.player.full_name if i.player else None
        print(f"   intent: player={player} metric={i.metric} agg={i.aggregation} "
              f"opp={i.opponent_abbr} season={i.season} playoffs={i.playoffs_only}")
        if ans.result is not None:
            print(f"   sql: {ans.result.sql}")
            print(f"   params: {ans.result.params}")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    debug = "--debug" in args
    args = [a for a in args if a != "--debug"]

    if "--rebuild" in args:
        build_from_seed()
        args = [a for a in args if a != "--rebuild"]
    else:
        ensure_db()

    if args:
        _print_answer(" ".join(args), debug)
        return

    print("statlas — ask an NBA stats question (Ctrl-C / 'quit' to exit). Sample data only.")
    try:
        while True:
            q = input("\n> ").strip()
            if q.lower() in {"quit", "exit", "q"}:
                break
            if q:
                _print_answer(q, debug=True)
    except (KeyboardInterrupt, EOFError):
        print("\nbye.")


if __name__ == "__main__":
    main()
