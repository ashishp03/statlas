# Module 2 — NLU & Entity Resolution

**Track 1 · advanced · ~2–3 sessions**
Goal: turn `src/statlas/entities/resolver.py` from a nickname-dictionary + rapidfuzz baseline
into an **embedding-based** linker, and — critically — **measure** whether the upgrade actually
helps on a held-out eval set. Entity resolution is, in StatMuse's own framing, *half* of accuracy:
if "the Joker vs OKC" resolves to the wrong player, every downstream number is wrong but confident.

## Objectives
1. Frame entity linking as retrieval: mention → nearest canonical entity in embedding space.
2. Build a labeled eval set of hard references (nicknames, misspellings, partials, ambiguous).
3. Beat the rapidfuzz baseline on that eval set with a sentence-embedding resolver — or prove it
   doesn't help and say why (this is a real result either way).
4. Understand the precision/recall trade-off of the `min_score` "refuse to guess" threshold.

## Read (primary sources)
- **Paper:** Devlin et al., *BERT* (2019) — arXiv 1810.04805. §3 (pre-training/fine-tuning) for
  what contextual embeddings buy you. https://arxiv.org/abs/1810.04805
- **Paper:** Reimers & Gurevych, *Sentence-BERT* (2019) — arXiv 1908.10084. Why mean-pooled
  sentence embeddings + cosine beats raw BERT[CLS] for similarity. https://arxiv.org/abs/1908.10084
- **Survey (skim):** Sevgili et al., *Neural Entity Linking* (2022) — candidate generation vs
  ranking framing. https://arxiv.org/abs/2006.00575
- **Docs:** rapidfuzz scorers (`WRatio`, `token_sort_ratio`) — know your baseline.
  https://rapidfuzz.github.io/RapidFuzz/

## Theory notes (fill in)
- Why a good dictionary beats a model "at the head of the distribution": ___
- Where embeddings win (the tail): misspellings, paraphrases, unseen nicknames because ___
- Candidate generation vs ranking — which is your bottleneck on a 5-player DB vs a 500-player DB? ___
- Threshold tuning: raising `min_score` trades recall for precision. For a *stats* engine, which
  error is worse — a wrong confident answer or an honest "I don't know"? ___

## Exercises → `exercises.ipynb`
1. **Load the baseline** — import the repo's `resolve_player`; reproduce a few resolutions.
2. **Build the eval set** — ~20 `(mention, expected_full_name_or_None)` pairs covering nicknames,
   typos, partial names, and an out-of-DB name that *should* return `None`.
3. **Score the baseline** — accuracy + a small confusion log (what it gets wrong and why).
4. **Char-ngram resolver** (no deps) — TF-IDF over character n-grams + cosine; score it.
5. **(OPTIONAL) sentence-embedding resolver** — `sentence-transformers` MiniLM; score it.
6. **Threshold sweep** — plot accuracy / refusal-rate vs `min_score`; pick an operating point.
7. **Ship** — write the winning approach into `resolver.py` behind the *same* `resolve_player`
   signature so the rest of the pipeline is untouched.

## Definition of done
- Non-optional asserts pass; you have a number for baseline vs your resolver on the eval set.
- You can state the precision/recall trade-off you chose and *why* for a stats engine.

## Ship target (repo)
`src/statlas/entities/resolver.py` — add an embedding/n-gram path used as a fallback after the
exact nickname hit, keeping the `ResolvedPlayer(player_id, full_name, score)` return contract.
Keep the baseline reachable (e.g. a flag) so M7's eval can compare them.

## Carry-over
- Save your eval set — it becomes part of the M7 evaluation harness.
