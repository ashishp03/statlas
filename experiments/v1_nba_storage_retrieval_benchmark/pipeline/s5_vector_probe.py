"""S5 — Vector-store probe: the WRONG tool for exact stats, the RIGHT tool for example retrieval.

This stage builds a semantic vector index over one "stat card" per player_season row and runs
two experiments that, together, are the finding:

  EXPERIMENT A  (mode='stat_lookup')  — MISUSE a vector store as a stat store.
      For every eval item we embed the question, retrieve the top-1 nearest stat card, and try to
      read the answer straight out of that card's text (parse a number for numeric items, read the
      player name for leaderboard/string items). We then compare to the *resolved* expected_value
      (two-tier tolerance). Expected result: LOW accuracy. Even when retrieval returns the right
      player, the card's rounded PerGame number != the exact DuckDB rational; counts and VORP can't
      be parsed at all; and the "minimum 58 games" leaderboard is a HARD MISS because a similarity
      index has no notion of a HAVING qualifier or an ORDER BY … LIMIT. That miss IS the point.

  EXPERIMENT B  (mode='fewshot')      — the LEGIT role: few-shot example retrieval for text-to-SQL.
      We hand-write a handful of (question -> SQL) examples spanning OLTP (row-wise game_logs) and
      OLAP (column-wise player_season leaderboards), embed the example *questions*, and for each eval
      question retrieve the top-2 nearest examples. We record whether a SAME-workload example was
      retrieved. Here semantic similarity shines: the nearest example is almost always the right
      *shape* of query to show an LLM. We never EXECUTE the example SQL — retrieval only.

Design / non-negotiables honored:
  - DuckDB does ALL arithmetic: expected_value is resolved by running each item's canonical_sql on a
    DuckDB view over the raw Parquet (Python never computes a stat). Reading a *pre-computed* number
    out of a card string in Experiment A is the misuse being demonstrated, not a computation.
  - Any SQL is passed through a SELECT-only allow-list guard before it touches the DB. We try the
    shared pipeline.s4_sql_guard if that sibling stage exists yet; otherwise a local SELECT-only
    fallback guard is applied (fail-closed).
  - The script ALWAYS runs: every optional dependency (Ollama/requests, sentence-transformers,
    lancedb, chromadb, duckdb) is imported defensively and degrades gracefully — the guaranteed path
    is a deterministic hashing bag-of-words embedding indexed by a numpy brute-force cosine search.

Outputs:
  results/vector_probe.csv     — one row per (experiment, eval item)
  results/vector_findings.md   — the written-up finding, computed from this run's numbers

Run:
    python experiments/v1_nba_storage_retrieval_benchmark/pipeline/s5_vector_probe.py
    python .../s5_vector_probe.py --backend hash --index numpy --limit-cards 2000   # fast smoke
    python .../s5_vector_probe.py --backend ollama                                  # force Ollama
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # experiment root on path

import numpy as np
import polars as pl

import config
from pipeline._harness import bench, timer, season_str

# --- optional deps (defensive) ----------------------------------------------------------------
try:
    import duckdb  # embedded OLAP engine — used ONLY to resolve expected_value from canonical_sql
except Exception:  # pragma: no cover - degrade gracefully
    duckdb = None

try:
    import requests  # preferred HTTP client for Ollama
except Exception:  # pragma: no cover
    requests = None

import urllib.request as _urllib
import urllib.error as _urlerr


# ==============================================================================================
#  Stat cards — one human-readable string per player_season row (the vector corpus)
# ==============================================================================================
CARD_TEXT_TEMPLATE = ("{name}, {season} {stype}: {pts} pts, {reb} reb, {ast} ast, "
                      "net_rating {net}, usg {usg}")


def _fmt(v, nd: int = 1) -> str:
    """Render a stat for a card; None/NaN -> 'na' so the parser fails on it (a real gap)."""
    if v is None:
        return "na"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "na"
    if f != f:  # NaN
        return "na"
    return f"{f:.{nd}f}"


def build_cards(df: pl.DataFrame, limit: int | None = None) -> tuple[list[str], list[dict]]:
    """Return (card_strings, card_metadata) parallel lists over player_season rows."""
    if limit:
        df = df.head(limit)
    cards: list[str] = []
    metas: list[dict] = []
    for r in df.iter_rows(named=True):
        name = r.get("player_name") or "Unknown"
        text = CARD_TEXT_TEMPLATE.format(
            name=name,
            season=season_str(int(r["season"])),
            stype=r.get("season_type", ""),
            pts=_fmt(r.get("pts")), reb=_fmt(r.get("reb")), ast=_fmt(r.get("ast")),
            net=_fmt(r.get("net_rating")), usg=_fmt(r.get("usg_pct"), nd=3),
        )
        cards.append(text)
        metas.append({"player_name": name, "season": int(r["season"]),
                      "season_type": r.get("season_type", "")})
    return cards, metas


# ==============================================================================================
#  Embedding backends — Ollama -> sentence-transformers -> deterministic hashing (always works)
# ==============================================================================================
def _http_post_json(url: str, payload: dict, timeout: float):
    """POST JSON, return parsed dict; raise on any failure (caller decides fallback)."""
    data = json.dumps(payload).encode("utf-8")
    if requests is not None:
        resp = requests.post(url, data=data, headers={"Content-Type": "application/json"},
                             timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    req = _urllib.Request(url, data=data, headers={"Content-Type": "application/json"})
    with _urllib.urlopen(req, timeout=timeout) as r:  # noqa: S310 - localhost Ollama
        return json.loads(r.read().decode("utf-8"))


def _http_get_ok(url: str, timeout: float) -> bool:
    try:
        if requests is not None:
            return requests.get(url, timeout=timeout).status_code == 200
        with _urllib.urlopen(url, timeout=timeout) as r:  # noqa: S310
            return r.status == 200
    except Exception:
        return False


class HashingEmbedder:
    """Deterministic signed bag-of-words hashing embedding. No deps, always available."""

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hash-bow:{dim}"

    def _one(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            v[idx] += sign
        return v

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self._one(t) for t in texts]).astype(np.float32)


class SentenceTransformerEmbedder:
    """all-MiniLM-L6-v2 via sentence-transformers, if installed."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer  # may raise -> caller falls back
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.name = "st:all-MiniLM-L6-v2"

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, show_progress_bar=False), dtype=np.float32)


class OllamaEmbedder:
    """config.EMBED_MODEL via a local Ollama server. Prefers batch /api/embed, falls back to
    per-item /api/embeddings (the endpoint named in the spec)."""

    def __init__(self, host: str = config.OLLAMA_HOST, model: str = config.EMBED_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self.name = f"ollama:{model}"
        self._batch_ok = True  # optimistic; flipped off if /api/embed 404s

    def _embed_batch(self, texts: list[str]) -> np.ndarray | None:
        try:
            out = _http_post_json(f"{self.host}/api/embed",
                                  {"model": self.model, "input": texts},
                                  timeout=config.API_TIMEOUT_S)
            embs = out.get("embeddings")
            if embs and len(embs) == len(texts):
                return np.asarray(embs, dtype=np.float32)
        except Exception:
            pass
        return None

    def _embed_single(self, text: str) -> np.ndarray:
        out = _http_post_json(f"{self.host}/api/embeddings",
                              {"model": self.model, "prompt": text},
                              timeout=config.API_TIMEOUT_S)
        return np.asarray(out["embedding"], dtype=np.float32)

    def embed(self, texts: list[str]) -> np.ndarray:
        vecs: list[np.ndarray] = []
        chunk = 64
        for i in range(0, len(texts), chunk):
            part = texts[i:i + chunk]
            got = self._embed_batch(part) if self._batch_ok else None
            if got is None:
                self._batch_ok = False  # server has no /api/embed — use the single endpoint
                got = np.vstack([self._embed_single(t) for t in part]).astype(np.float32)
            vecs.append(got)
        return np.vstack(vecs).astype(np.float32)

    def probe(self) -> bool:
        """Return True iff the server is up AND the model returns a usable vector."""
        if not _http_get_ok(f"{self.host}/api/tags", timeout=2.0):
            return False
        try:
            v = self.embed(["probe"])
            return v.ndim == 2 and v.shape[0] == 1 and v.shape[1] > 0
        except Exception:
            return False


def get_embedder(pref: str = "auto"):
    """Pick an embedding backend. Never raises: always returns something with .embed/.name."""
    if pref in ("auto", "ollama"):
        try:
            emb = OllamaEmbedder()
            if emb.probe():
                print(f"  embedder: {emb.name} (local Ollama)")
                return emb
            if pref == "ollama":
                print("  !! Ollama requested but unreachable/model missing -> hashing fallback")
        except Exception as e:  # noqa: BLE001
            print(f"  !! Ollama backend error ({type(e).__name__}) -> next")
    if pref in ("auto", "st"):
        try:
            emb = SentenceTransformerEmbedder()
            print(f"  embedder: {emb.name}")
            return emb
        except Exception:
            if pref == "st":
                print("  !! sentence-transformers requested but unavailable -> hashing fallback")
    emb = HashingEmbedder()
    print(f"  embedder: {emb.name} (deterministic fallback)")
    return emb


# ==============================================================================================
#  Vector index — lancedb / chromadb if present, else numpy brute-force cosine (guaranteed)
# ==============================================================================================
class NumpyIndex:
    """L2-normalized matrix; cosine similarity == dot product; top-k by argpartition."""

    name = "numpy-bruteforce"

    def __init__(self, vectors: np.ndarray):
        v = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.mat = v / norms

    def query(self, qvec: np.ndarray, k: int = 1) -> list[tuple[int, float]]:
        q = np.asarray(qvec, dtype=np.float32).reshape(-1)
        n = np.linalg.norm(q) or 1.0
        sims = self.mat @ (q / n)
        k = max(1, min(k, sims.shape[0]))
        top = np.argpartition(-sims, k - 1)[:k]
        top = top[np.argsort(-sims[top])]
        return [(int(i), float(sims[i])) for i in top]


def _try_lance(vectors: np.ndarray):
    try:
        import tempfile
        import lancedb
        v = np.asarray(vectors, dtype=np.float32)
        db = lancedb.connect(tempfile.mkdtemp(prefix="s5_lance_"))
        tbl = db.create_table(
            "cards", data=[{"id": i, "vector": v[i].tolist()} for i in range(v.shape[0])],
            mode="overwrite")

        class _LanceIndex:
            name = "lancedb"

            def query(self, qvec, k=1):
                res = (tbl.search(np.asarray(qvec, dtype=np.float32).tolist())
                          .metric("cosine").limit(k).to_list())
                return [(int(r["id"]), 1.0 - float(r.get("_distance", 0.0))) for r in res]

        idx = _LanceIndex()
        idx.query(v[0], 1)  # self-test — any failure -> fall back
        return idx
    except Exception:
        return None


def _try_chroma(vectors: np.ndarray):
    try:
        import chromadb
        v = np.asarray(vectors, dtype=np.float32)
        client = chromadb.EphemeralClient()
        coll = client.create_collection(name="cards", metadata={"hnsw:space": "cosine"})
        coll.add(ids=[str(i) for i in range(v.shape[0])], embeddings=v.tolist())

        class _ChromaIndex:
            name = "chromadb"

            def query(self, qvec, k=1):
                res = coll.query(query_embeddings=[np.asarray(qvec, dtype=np.float32).tolist()],
                                 n_results=k)
                ids = res["ids"][0]
                dists = res.get("distances", [[0.0] * len(ids)])[0]
                return [(int(i), 1.0 - float(d)) for i, d in zip(ids, dists)]

        idx = _ChromaIndex()
        idx.query(v[0], 1)  # self-test
        return idx
    except Exception:
        return None


def make_index(vectors: np.ndarray, pref: str = "auto"):
    """Build a vector index. Prefers lancedb, then chromadb, else numpy. Never raises."""
    if pref in ("auto", "lance"):
        idx = _try_lance(vectors)
        if idx is not None:
            print(f"  index: {idx.name}")
            return idx
        if pref == "lance":
            print("  !! lancedb unavailable -> numpy brute-force")
    if pref in ("auto", "chroma"):
        idx = _try_chroma(vectors)
        if idx is not None:
            print(f"  index: {idx.name}")
            return idx
        if pref == "chroma":
            print("  !! chromadb unavailable -> numpy brute-force")
    idx = NumpyIndex(vectors)
    print(f"  index: {idx.name}")
    return idx


# ==============================================================================================
#  Eval loading + expected_value resolution (DuckDB does the arithmetic)
# ==============================================================================================
def load_eval() -> tuple[list[dict], dict]:
    data = json.loads(config.EVAL_SET.read_text())
    return data["items"], data.get("meta", {})


_BANNED_SQL = (" insert ", " update ", " delete ", " drop ", " alter ", " create ",
               " attach ", " copy ", " pragma ", " replace ", " truncate ", " grant ")


def guard_select(sql: str) -> bool:
    """SELECT-only allow-list. Try the shared s4_sql_guard if that stage exists; else fail-closed
    local check: a single SELECT/WITH statement, no chaining, no DDL/DML verbs."""
    try:
        from pipeline import s4_sql_guard  # sibling stage, owned elsewhere — may not exist yet
        for fn_name in ("assert_safe", "is_safe", "guard"):
            fn = getattr(s4_sql_guard, fn_name, None)
            if fn is None:
                continue
            try:
                res = fn(sql)
                return True if res is None else bool(res)  # assert_safe returns None on pass
            except Exception:
                return False
    except Exception:
        pass  # no shared guard yet -> local fallback below
    s = sql.strip().rstrip(";")
    if ";" in s:  # no statement chaining
        return False
    low = f" {s.lower()} "
    if not (low.lstrip().startswith("select") or low.lstrip().startswith("with")):
        return False
    return not any(b in low for b in _BANNED_SQL)


def duckdb_con():
    """In-memory DuckDB with a view per available raw Parquet. None if duckdb is unavailable."""
    if duckdb is None:
        return None
    con = duckdb.connect()
    datasets = {
        "game_logs": config.RAW_DIR / "game_logs.parquet",
        "player_season": config.RAW_DIR / "player_season.parquet",
        "players": config.RAW_DIR / "players.parquet",
        "bbref_advanced": config.RAW_DIR / "bbref_advanced.parquet",
        # player_crosswalk is produced by the resolver stage; if absent, cross-source items simply
        # fail to resolve (recorded as unresolved) rather than crash — refuse-rather-than-guess.
        "player_crosswalk": config.RAW_DIR / "player_crosswalk.parquet",
    }
    for name, path in datasets.items():
        if path.exists():
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{path.as_posix()}')")
    return con


def resolve_expected(con, item: dict):
    """Run canonical_sql (through the guard) and return the scalar answer, or None on any failure."""
    if con is None:
        return None
    sql = item["canonical_sql"]
    if not guard_select(sql):
        return None
    try:
        row = con.execute(sql).fetchone()
        return None if row is None else row[0]
    except Exception:
        return None


# ==============================================================================================
#  Answer extraction from a retrieved card + two-tier correctness
# ==============================================================================================
_PID_RE = re.compile(r"player_id\s*=\s*(\d+)")
_CARD_RE = {
    "pts": re.compile(r"([-\d.]+)\s*pts"),
    "reb": re.compile(r"([-\d.]+)\s*reb"),
    "ast": re.compile(r"([-\d.]+)\s*ast"),
    "net_rating": re.compile(r"net_rating\s*([-\d.]+)"),
    "usg": re.compile(r"usg\s*([-\d.]+)"),
}


def guess_metric(question: str) -> str | None:
    """Map a numeric question to the one card field it asks about (best-effort keyword map)."""
    q = question.lower()
    if "assist" in q:
        return "ast"
    if "rebound" in q:
        return "reb"
    if "net rating" in q or "net_rating" in q:
        return "net_rating"
    if "usage" in q or "usg" in q:
        return "usg"
    if "point" in q or "ppg" in q or "scoring" in q or "score" in q:
        return "pts"
    return None  # e.g. "how many games", "VORP" -> not representable in the card


def parse_stat(card: str, metric: str | None) -> float | None:
    if metric is None:
        return None
    rx = _CARD_RE.get(metric)
    if rx is None:
        return None
    m = rx.search(card)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def card_player(card: str) -> str:
    return card.split(",", 1)[0].strip()


def _to_str(v):
    """Stringify for the CSV so a column can't mix float (numeric items) and str (name items)."""
    return None if v is None else str(v)


def target_player_name(item: dict, id2name: dict) -> str | None:
    m = _PID_RE.search(item["canonical_sql"])
    if not m:
        return None
    return id2name.get(int(m.group(1)))


def _tokens(s: str) -> set:
    return set(re.findall(r"[a-z]+", (s or "").lower()))


def name_match(target: str | None, card_name: str) -> bool:
    if not target:
        return False
    t = _tokens(target)
    return bool(t) and t.issubset(_tokens(card_name))


def numeric_gate(got, expected, tol) -> bool:
    if got is None or expected is None:
        return False
    try:
        return abs(float(got) - float(expected)) <= (float(tol) if tol else 0.0)
    except (TypeError, ValueError):
        return False


def string_gate(got, expected) -> bool:
    if got is None or expected is None:
        return False
    return str(got).strip().lower() == str(expected).strip().lower()


def known_ok(item: dict, got, known_tol: float):
    """Informational soft check vs the hand-checked public anchor (rounded to 1 dp)."""
    k = item.get("known")
    if k is None or got is None:
        return None
    if item["answer_type"] == "numeric":
        try:
            return abs(float(got) - float(k)) <= known_tol
        except (TypeError, ValueError):
            return None
    return string_gate(got, k)


# ==============================================================================================
#  Experiment B — few-shot (question -> SQL) example bank (retrieval only, NEVER executed)
# ==============================================================================================
FEWSHOT_EXAMPLES = [
    {"id": "ex_oltp_pts", "workload": "OLTP",
     "question": "What did Kevin Durant average in points per game in the 2022-23 regular season?",
     "sql": "SELECT AVG(pts) FROM game_logs WHERE player_id = 201142 AND season = 2023 AND is_playoff = 0"},
    {"id": "ex_oltp_reb_playoff", "workload": "OLTP",
     "question": "How many rebounds per game did Giannis Antetokounmpo average in the 2023-24 playoffs?",
     "sql": "SELECT AVG(reb) FROM game_logs WHERE player_id = 203507 AND season = 2024 AND is_playoff = 1"},
    {"id": "ex_oltp_count", "workload": "OLTP",
     "question": "How many regular-season games did Stephen Curry play in 2024-25?",
     "sql": "SELECT COUNT(*) FROM game_logs WHERE player_id = 201939 AND season = 2025 AND is_playoff = 0"},
    {"id": "ex_olap_ast_leader", "workload": "OLAP",
     "question": "Who led the league in assists per game in 2024-25 among players with at least 58 games?",
     "sql": "SELECT player_name FROM player_season WHERE season = 2025 AND season_type = 'Regular Season' AND gp >= 58 ORDER BY ast DESC LIMIT 1"},
    {"id": "ex_olap_league_avg", "workload": "OLAP",
     "question": "Among qualified players, what was the average points per game in 2023-24?",
     "sql": "SELECT AVG(pts) FROM player_season WHERE season = 2024 AND season_type = 'Regular Season' AND gp >= 58"},
    {"id": "ex_olap_ts_leader", "workload": "OLAP",
     "question": "Which qualified player had the best true shooting percentage in 2024-25?",
     "sql": "SELECT player_name FROM player_season WHERE season = 2025 AND season_type = 'Regular Season' AND gp >= 58 ORDER BY ts_pct DESC LIMIT 1"},
]


# ==============================================================================================
#  Orchestration
# ==============================================================================================
def _load_id2name() -> dict:
    p = config.RAW_DIR / "players.parquet"
    if not p.exists():
        return {}
    df = pl.read_parquet(p)
    name_col = "full_name" if "full_name" in df.columns else "player_name"
    return {int(r["player_id"]): r[name_col] for r in df.select(["player_id", name_col]).iter_rows(named=True)}


def run_experiment_a(items, embedder, index, cards, metas, resolved, id2name, known_tol):
    """MISUSE-as-stat-store rows. Runs over ALL items so the min-games leaderboard hard-miss is
    captured (leaderboard items are answer_type='string')."""
    rows = []
    for it in items:
        q = it["question"]
        atype = it["answer_type"]
        expected = resolved.get(it["id"])
        with timer() as t:
            qv = embedder.embed([q])[0]
            hits = index.query(qv, k=1)
        latency_ms = t() * 1000.0
        if not hits:
            rows.append({"mode": "stat_lookup", "item": it["id"], "answer_type": atype,
                         "workload": it.get("workload"), "retrieved_ok": False, "correct": False,
                         "known_ok": None, "metric": None, "parsed_value": None,
                         "expected_value": _to_str(expected), "retrieved_player": None,
                         "target_player": None, "latency_ms": round(latency_ms, 3)})
            continue
        top_i, _score = hits[0]
        card = cards[top_i]
        rp = card_player(card)
        target = target_player_name(it, id2name)
        if atype == "numeric":
            metric = guess_metric(q)
            got = parse_stat(card, metric)
            correct = numeric_gate(got, expected, it.get("tolerance", 0))
        else:  # string leaderboard / name answer
            metric = None
            got = rp
            correct = string_gate(got, expected)
        # retrieved_ok = did we surface the right SUBJECT (when the item names one player)?
        retrieved_ok = True if target is None else name_match(target, rp)
        rows.append({
            "mode": "stat_lookup", "item": it["id"], "answer_type": atype,
            "workload": it.get("workload"), "retrieved_ok": bool(retrieved_ok),
            "correct": bool(correct), "known_ok": known_ok(it, got, known_tol),
            "metric": metric, "parsed_value": _to_str(got), "expected_value": _to_str(expected),
            "retrieved_player": rp, "target_player": target, "latency_ms": round(latency_ms, 3),
        })
    return rows


def run_experiment_b(items, embedder):
    """LEGIT few-shot retrieval rows: top-2 nearest examples, same-workload relevance + latency."""
    ex_vecs = embedder.embed([e["question"] for e in FEWSHOT_EXAMPLES])
    ex_index = make_index(ex_vecs, pref="numpy")  # tiny bank -> brute force is ideal
    rows = []
    for it in items:
        with timer() as t:
            qv = embedder.embed([it["question"]])[0]
            hits = ex_index.query(qv, k=2)
        latency_ms = t() * 1000.0
        picked = [FEWSHOT_EXAMPLES[i] for i, _ in hits]
        wl = it.get("workload")
        top1_match = bool(picked) and picked[0]["workload"] == wl
        top2_match = any(p["workload"] == wl for p in picked)
        rows.append({
            "mode": "fewshot", "item": it["id"], "workload": wl,
            "top1_workload_match": bool(top1_match), "top2_workload_match": bool(top2_match),
            "top1_example_id": picked[0]["id"] if picked else None,
            "top2_example_id": picked[1]["id"] if len(picked) > 1 else None,
            "latency_ms": round(latency_ms, 3),
        })
    return rows


def _rate(rows, key) -> float:
    vals = [bool(r[key]) for r in rows if r.get(key) is not None]
    return (sum(vals) / len(vals)) if vals else float("nan")


def write_findings(path, embedder, index, corpus_n, dim, a_rows, b_rows, search_stats, n_resolved):
    ra = _rate(a_rows, "retrieved_ok")
    ca = _rate(a_rows, "correct")
    b1 = _rate(b_rows, "top1_workload_match")
    b2 = _rate(b_rows, "top2_workload_match")
    b_lat = [r["latency_ms"] for r in b_rows]
    b_lat_mean = (sum(b_lat) / len(b_lat)) if b_lat else float("nan")
    lead = next((r for r in a_rows if r["item"] == "scoring_leader_2025_reg_minGP"), None)
    lead_line = ("(item not present)" if lead is None else
                 f"retrieved_player=`{lead['retrieved_player']}` expected=`{lead['expected_value']}` "
                 f"-> correct={lead['correct']}")
    ss = search_stats or {}
    md = f"""# S5 — Vector-store probe: findings

**Backend:** `{embedder.name}`  &nbsp;|&nbsp; **Index:** `{index.name}`  &nbsp;|&nbsp;
**Corpus:** {corpus_n:,} stat cards @ dim {dim}  &nbsp;|&nbsp; **expected_value resolved for** {n_resolved}/{len(a_rows)} items (DuckDB).

## TL;DR
A vector store is the **wrong** tool for returning an exact statistic and a **useful** tool for
retrieving semantically similar few-shot examples. Numbers below are from this run.

## Experiment A — misuse as a stat store (mode=`stat_lookup`)
- **Right subject retrieved:** {ra:.0%} of items (semantic search usually finds the correct player-season card).
- **Exact answer correct:** {ca:.0%} of items (two-tier gate vs the DuckDB-resolved `expected_value`).

Why accuracy collapses even when retrieval works:
1. **Rounding / different window.** A card shows a *rounded* full-season PerGame number
   (e.g. `24.4 pts`); the canonical answer is an exact rational `AVG(pts)` over the game-log
   window. Parsed value != exact value, so the `1e-7` gate fails.
2. **Not representable.** Counts (`how many games`) and cross-source metrics (`VORP`) are not in
   the card text at all — nothing to parse.
3. **No qualifier / ranking logic — the hard miss.** The "minimum 58 games" scoring-leader
   question cannot be answered by nearest-neighbor search: an ANN index has no `HAVING gp >= 58`
   and no `ORDER BY pts DESC LIMIT 1`. Result for that item: {lead_line}.

The vectors are a *fuzzy semantic address book*, not a calculator. This is exactly why the
architecture keeps every statistic in DuckDB.

## Experiment B — legitimate role: few-shot example retrieval (mode=`fewshot`)
Over a hand-written bank of {len(FEWSHOT_EXAMPLES)} (question -> SQL) examples (3 OLTP row-wise, 3 OLAP
column-wise), for each eval question we retrieve the top-2 nearest examples:
- **Top-1 example is the same workload:** {b1:.0%}
- **A same-workload example is in the top-2:** {b2:.0%}
- **Mean retrieval latency:** {b_lat_mean:.2f} ms per query.

Semantic similarity reliably surfaces an example of the *right shape* (OLTP point-lookup vs OLAP
leaderboard) to prime a text-to-SQL model. The example SQL is **never executed** here — it is
context for a downstream model, whose drafted SQL must still pass the SELECT-only guard and let
DuckDB do the arithmetic.

## Index search microbench (numpy cosine, top-1)
{("p50 " + format(ss.get('p50_ms', float('nan')), '.3f') + " ms, p95 " + format(ss.get('p95_ms', float('nan')), '.3f') + " ms over " + str(ss.get('reps', 0)) + " reps") if ss else "n/a"}

## Conclusion
Use vectors for **semantic retrieval** (finding relevant examples/rows), never as the **source of
truth for a number**. Exact stats stay in the database; the vector index feeds the LLM good
examples and leaves the math to DuckDB.
"""
    path.write_text(md)


def main():
    ap = argparse.ArgumentParser(description="S5 vector-store probe (stat-store misuse vs few-shot retrieval)")
    ap.add_argument("--backend", choices=["auto", "ollama", "st", "hash"], default="auto",
                    help="embedding backend (default auto: Ollama -> sentence-transformers -> hashing)")
    ap.add_argument("--index", choices=["auto", "lance", "chroma", "numpy"], default="auto",
                    help="vector index backend (default auto: lancedb -> chromadb -> numpy)")
    ap.add_argument("--limit-cards", type=int, default=None,
                    help="cap the stat-card corpus (smoke runs / slow embedders)")
    ap.add_argument("--reps", type=int, default=config.BENCH_REPS)
    ap.add_argument("--warmup", type=int, default=config.BENCH_WARMUP)
    args = ap.parse_args()

    print("=" * 78)
    print("S5 VECTOR PROBE — stat-store misuse (Exp A) vs few-shot retrieval (Exp B)")
    print("=" * 78)

    items, meta = load_eval()
    known_tol = float(meta.get("known_tolerance", config.__dict__.get("KNOWN_TOLERANCE", 0.1)))
    id2name = _load_id2name()

    # 1) Resolve expected_value from the canonical SQL — DuckDB does the arithmetic.
    con = duckdb_con()
    resolved = {it["id"]: resolve_expected(con, it) for it in items}
    n_resolved = sum(1 for v in resolved.values() if v is not None)
    print(f"resolved expected_value for {n_resolved}/{len(items)} items "
          f"({'DuckDB' if con is not None else 'duckdb unavailable — all None'})")

    # 2) Build the stat-card corpus.
    ps_path = config.RAW_DIR / "player_season.parquet"
    if not ps_path.exists():
        print("!! player_season.parquet missing — cannot build corpus; aborting cleanly")
        return
    ps = pl.read_parquet(ps_path)
    cards, metas = build_cards(ps, limit=args.limit_cards)
    print(f"built {len(cards):,} stat cards")

    # 3) Embed corpus + build index.
    embedder = get_embedder(args.backend)
    corpus_vecs = embedder.embed(cards)
    dim = int(corpus_vecs.shape[1]) if corpus_vecs.ndim == 2 else 0
    index = make_index(corpus_vecs, args.index)

    # 4) Experiments.
    print("Experiment A — misuse as a stat store ...")
    a_rows = run_experiment_a(items, embedder, index, cards, metas, resolved, id2name, known_tol)
    print("Experiment B — few-shot example retrieval ...")
    b_rows = run_experiment_b(items, embedder)

    # Index search microbench (search-only, reuses the shared bench()).
    search_stats = None
    if items:
        qv = embedder.embed([items[0]["question"]])[0]
        search_stats = bench(lambda: index.query(qv, 1), reps=args.reps, warmup=args.warmup,
                             label="index_search_top1")

    # 5) Persist. Diagonal concat unions the two modes' differing columns (s1 pattern).
    out_csv = config.RESULTS_DIR / "vector_probe.csv"
    pl.concat([pl.from_dicts(a_rows), pl.from_dicts(b_rows)], how="diagonal_relaxed").write_csv(out_csv)
    out_md = config.RESULTS_DIR / "vector_findings.md"
    write_findings(out_md, embedder, index, len(cards), dim, a_rows, b_rows, search_stats, n_resolved)

    # 6) Console summary.
    ra, ca = _rate(a_rows, "retrieved_ok"), _rate(a_rows, "correct")
    b1 = _rate(b_rows, "top1_workload_match")
    print("=" * 78)
    print(f"Exp A (stat_lookup): right-subject={ra:.0%}  exact-correct={ca:.0%}  (finding: vectors "
          f"can't return exact stats)")
    print(f"Exp B (fewshot):     top1 same-workload={b1:.0%}  (finding: vectors are great for "
          f"example retrieval)")
    if search_stats:
        print(f"index search top-1: p50={search_stats['p50_ms']}ms p95={search_stats['p95_ms']}ms")
    print(f"wrote -> {out_csv}")
    print(f"wrote -> {out_md}")


if __name__ == "__main__":
    main()
