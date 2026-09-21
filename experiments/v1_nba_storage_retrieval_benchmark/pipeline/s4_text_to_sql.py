"""S4 — Text-to-SQL benchmark (does a free/open LLM draft SQL our guard + DuckDB will accept?).

For every available Ollama model in `config.T2SQL_MODELS` x every eval item we: build a schema-grounded
prompt, generate ONE SELECT (temperature 0), strip fences/prose, run it through `statlas.query.sql_guard.validate_sql`,
and — only if it clears the guard — execute it read-only on the DuckDB warehouse and score the answer
against the resolved `expected_value` (two-tier tolerance from the eval set).

A deterministic MOCK model (returns each item's `canonical_sql`) ALWAYS runs, even with Ollama down or no
matching tags installed. It proves the guard -> execute -> compare plumbing end-to-end and gives the real
models a correctness ceiling to compare against.

Outputs:
  results/t2sql_scores.csv   — model,item,guard_pass,exec_ok,correct,latency_ms,eval_count,sql
  results/t2sql_examples.md  — the shared prompt template + a few drafted-SQL samples with verdicts

Reads EXP_ROOT/eval_set_resolved.json if present, else eval_set.json. Never raises out of main().

    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s4_text_to_sql.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))  # repo src/ on path

import config
from statlas.query.sql_guard import SCHEMA_DDL_TEXT, validate_sql  # moved out of pipeline/ — permanent, reusable

# Generation timeout: 7-8B models on CPU are slow; keep generous but bounded. Tag discovery is quick.
GEN_TIMEOUT_S = 180
TAGS_TIMEOUT_S = 3.0
N_EXAMPLES = 6                       # sample rows to render into t2sql_examples.md
WAREHOUSE = config.STORES_DIR / "warehouse.duckdb"


# --------------------------------------------------------------------------- eval set
def load_eval() -> tuple[list[dict], dict]:
    """Prefer the resolved eval set (expected_value filled by S3); fall back to the raw golden set."""
    resolved = config.EXP_ROOT / "eval_set_resolved.json"
    path = resolved if resolved.exists() else config.EVAL_SET
    try:
        doc = json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        print(f"!! could not read eval set ({path.name}): {e}")
        return [], {}
    print(f"eval set: {path.name}  ({len(doc.get('items', []))} items)")
    return doc.get("items", []), doc.get("meta", {})


# --------------------------------------------------------------------------- ollama (urllib only)
def _http_get_json(url: str, timeout: float):
    import urllib.request
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict, timeout: float):
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def discover_models() -> list[str]:
    """GET /api/tags and intersect installed tags with config.T2SQL_MODELS. Any failure -> []."""
    try:
        doc = _http_get_json(config.OLLAMA_HOST + "/api/tags", TAGS_TIMEOUT_S)
        installed = [m.get("name", "") for m in doc.get("models", [])]
    except Exception as e:  # noqa: BLE001 - Ollama down / not installed -> no models
        print(f"ollama tag discovery failed ({type(e).__name__}: {str(e)[:60]}) -> MOCK only")
        return []
    installed_set = set(installed)
    base = {n.split(":")[0] for n in installed}
    picked = [w for w in config.T2SQL_MODELS if w in installed_set or w.split(":")[0] in base]
    print(f"ollama installed: {sorted(installed_set) or '(none)'}  -> using: {picked or '(none)'}")
    return picked


def ollama_generate(model: str, prompt: str) -> tuple[str | None, float, str | None]:
    """POST /api/generate (stream=false, temperature 0). Returns (response|None, latency_ms, err|None)."""
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}}
    t0 = time.perf_counter()
    try:
        doc = _http_post_json(config.OLLAMA_HOST + "/api/generate", payload, GEN_TIMEOUT_S)
        return doc.get("response", ""), (time.perf_counter() - t0) * 1000.0, None
    except Exception as e:  # noqa: BLE001
        return None, (time.perf_counter() - t0) * 1000.0, f"{type(e).__name__}: {str(e)[:80]}"


# --------------------------------------------------------------------------- prompt + extraction
def build_prompt(question: str) -> str:
    """Schema-grounded, rules-first prompt asking for exactly one read-only SELECT."""
    return (
        "You are a precise text-to-SQL engine for an NBA statistics database running on DuckDB.\n"
        "Translate the question into ONE read-only SQL query over this schema:\n\n"
        f"{SCHEMA_DDL_TEXT}\n\n"
        "Rules:\n"
        "- Output EXACTLY one SQL SELECT statement and nothing else — no prose, no markdown, no comments.\n"
        "- Read-only only: never INSERT/UPDATE/DELETE or any DDL.\n"
        "- Alias the single result column AS answer.\n"
        "- `season` is the END year as an integer (the 2024-25 season is 2025).\n"
        "- Regular season vs playoffs: game_logs.is_playoff is 0/1; player_season.season_type is "
        "'Regular Season' or 'Playoffs'.\n"
        f"- For any leaderboard / 'who led' question, require gp >= {config.MIN_GAMES_QUALIFIER} "
        "(the minimum-games qualifier).\n\n"
        f"Question: {question}\n"
        "SQL:"
    )


def extract_sql(text: str | None) -> str:
    """Pull a single SQL statement out of model output: strip ``` fences, prose, trailing commentary."""
    if not text:
        return ""
    import re
    t = text.strip()
    fence = re.search(r"```(?:sql)?\s*(.+?)```", t, re.DOTALL | re.IGNORECASE)
    if fence:
        t = fence.group(1).strip()
    start = re.search(r"(?is)\b(select|with)\b", t)
    if start:
        t = t[start.start():]
    semi = t.find(";")
    if semi != -1:                       # drop anything the model appended after the statement
        t = t[:semi + 1]
    return t.strip()


# --------------------------------------------------------------------------- execution + scoring
def execute_on_warehouse(sql: str) -> tuple[object, bool, int, str | None]:
    """Run guard-approved `sql` read-only on the warehouse. Returns (value, exec_ok, n_rows, err)."""
    if not WAREHOUSE.exists():
        return None, False, 0, "warehouse missing"
    try:
        import duckdb
    except Exception as e:  # noqa: BLE001
        return None, False, 0, f"duckdb unavailable: {type(e).__name__}"
    con = None
    try:
        con = duckdb.connect(str(WAREHOUSE), read_only=True)   # DuckDB does the arithmetic, never Python
        rows = con.execute(sql).fetchall()
        value = rows[0][0] if rows and len(rows[0]) > 0 else None
        return value, True, len(rows), None
    except Exception as e:  # noqa: BLE001
        return None, False, 0, f"{type(e).__name__}: {str(e)[:100]}"
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:  # noqa: BLE001
                pass


def _compare(got, expected, answer_type: str, tol: float) -> bool:
    try:
        if got is None:
            return False
        if answer_type == "numeric":
            return abs(float(got) - float(expected)) <= float(tol)
        return str(got).strip().lower() == str(expected).strip().lower()
    except Exception:  # noqa: BLE001
        return False


def judge(got, item: dict, meta: dict):
    """Two-tier scoring. Returns (correct: bool|None, basis: str).

    Primary GATE: compare to the resolved expected_value within item['tolerance']. If unresolved
    (still null pre-S3) fall back to the informational 'known' public anchor within meta
    ['known_tolerance']; if neither exists, correctness is unknown (None)."""
    atype = item.get("answer_type", "numeric")
    expected = item.get("expected_value", None)
    if expected is not None:
        return _compare(got, expected, atype, item.get("tolerance", 0)), "gate"
    known = item.get("known", None)
    if known is not None:
        ktol = meta.get("known_tolerance", 0.1) if atype == "numeric" else 0
        return _compare(got, known, atype, ktol), "known"
    return None, "unresolved"


# --------------------------------------------------------------------------- per-model run
def run_model(label: str, is_mock: bool, items: list[dict], meta: dict) -> tuple[list[dict], list[dict]]:
    """Evaluate one model (or MOCK) over every item. Returns (score_rows, example_rows)."""
    rows, examples = [], []
    print(f"\n--- model: {label}{' (mock)' if is_mock else ''} — {len(items)} items ---")
    for item in items:
        prompt = build_prompt(item["question"])
        if is_mock:
            t0 = time.perf_counter()
            raw = item.get("canonical_sql", "")
            latency, gen_err = (time.perf_counter() - t0) * 1000.0, None
        else:
            raw, latency, gen_err = ollama_generate(label, prompt)

        sql = extract_sql(raw)
        if not sql:
            guard_pass, reason = False, gen_err or "no SQL produced"
        else:
            guard_pass, reason = validate_sql(sql)

        value, exec_ok, n_rows, exec_err = (None, False, 0, None)
        correct, basis = None, "n/a"
        if guard_pass:
            value, exec_ok, n_rows, exec_err = execute_on_warehouse(sql)
            if exec_ok:
                correct, basis = judge(value, item, meta)

        rows.append({
            "model": label,
            "item": item["id"],
            "guard_pass": bool(guard_pass),
            "exec_ok": bool(exec_ok),
            "correct": "" if correct is None else str(bool(correct)).lower(),
            "latency_ms": round(latency, 2),
            "eval_count": int(n_rows),
            "sql": sql,
        })
        note = exec_err or reason if not (guard_pass and exec_ok) else basis
        print(f"  [{item['id']:34s}] guard={guard_pass!s:5} exec={exec_ok!s:5} "
              f"correct={correct} {latency:7.1f}ms  {note}")

        examples.append({
            "model": label, "item": item["id"], "question": item["question"], "prompt": prompt,
            "sql": sql, "guard_pass": guard_pass, "guard_reason": reason,
            "exec_ok": exec_ok, "value": value, "expected": item.get("expected_value"),
            "known": item.get("known"), "correct": correct, "basis": basis,
        })
    return rows, examples


# --------------------------------------------------------------------------- outputs
def write_scores(rows: list[dict]) -> None:
    path = config.RESULTS_DIR / "t2sql_scores.csv"
    cols = ["model", "item", "guard_pass", "exec_ok", "correct", "latency_ms", "eval_count", "sql"]
    try:
        import csv
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})
        print(f"\nwrote {len(rows)} rows -> results/{path.name}")
    except Exception as e:  # noqa: BLE001
        print(f"!! failed to write scores csv: {e}")


def write_examples(examples: list[dict]) -> None:
    path = config.RESULTS_DIR / "t2sql_examples.md"
    # Prefer a spread of items; always include at least the MOCK samples that ran.
    picked = examples[:N_EXAMPLES]
    lines = [
        "# S4 Text-to-SQL — prompt + SQL samples",
        "",
        "Every model receives the same schema-grounded template below; only the trailing question "
        "changes. Each candidate SQL must clear `statlas.query.sql_guard.validate_sql` before it is executed "
        "read-only on the DuckDB warehouse.",
        "",
        "## Prompt template",
        "",
        "```text",
        build_prompt("<QUESTION>"),
        "```",
        "",
        "## Samples",
        "",
    ]
    for ex in picked:
        verdict = "unresolved" if ex["correct"] is None else ("correct" if ex["correct"] else "WRONG")
        lines += [
            f"### `{ex['model']}` — {ex['item']}",
            "",
            f"**Q:** {ex['question']}",
            "",
            "```sql",
            ex["sql"] or "(no SQL extracted)",
            "```",
            "",
            f"- guard_pass: `{ex['guard_pass']}`" + ("" if ex["guard_pass"] else f" — {ex['guard_reason']}"),
            f"- exec_ok: `{ex['exec_ok']}`  |  value: `{ex['value']}`  |  expected: `{ex['expected']}`"
            + (f"  |  known: `{ex['known']}`" if ex.get("known") is not None else ""),
            f"- verdict: **{verdict}** (basis: {ex['basis']})",
            "",
        ]
    try:
        path.write_text("\n".join(lines))
        print(f"wrote {len(picked)} samples -> results/{path.name}")
    except Exception as e:  # noqa: BLE001
        print(f"!! failed to write examples md: {e}")


# --------------------------------------------------------------------------- main
def main() -> None:
    print("=" * 78)
    print("S4 TEXT-TO-SQL benchmark")
    print("=" * 78)
    try:
        items, meta = load_eval()
        if not items:
            print("no eval items — nothing to do")
            write_scores([])
            return
        if not WAREHOUSE.exists():
            print(f"NOTE: {WAREHOUSE} not found — SQL will guard-check but exec_ok will be False "
                  "(run S2 to build the warehouse first).")

        models = discover_models()
        all_rows, all_examples = [], []

        # MOCK always runs first (correctness ceiling + plumbing proof).
        rows, examples = run_model("MOCK", True, items, meta)
        all_rows += rows
        all_examples += examples

        for model in models:
            rows, examples = run_model(model, False, items, meta)
            all_rows += rows
            all_examples += examples

        write_scores(all_rows)
        write_examples(all_examples)

        # Tiny summary per model.
        print("\nsummary (guard_pass / exec_ok / correct out of items):")
        for label in ["MOCK"] + models:
            mr = [r for r in all_rows if r["model"] == label]
            gp = sum(r["guard_pass"] for r in mr)
            ex = sum(r["exec_ok"] for r in mr)
            co = sum(r["correct"] == "true" for r in mr)
            print(f"  {label:22s} guard={gp:2d}  exec={ex:2d}  correct={co:2d}  / {len(mr)}")
        print("=" * 78)
    except Exception as e:  # noqa: BLE001 - main must NEVER raise (benchmark stage)
        import traceback
        print(f"!! S4 text-to-sql aborted defensively: {type(e).__name__}: {e}")
        print(traceback.format_exc()[:1500])


if __name__ == "__main__":
    main()
