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

## Math problems (added 2026-08-25, work by hand)
1. **Cosine similarity, from scratch.** For two TF-IDF character-n-gram vectors `a`, `b`, write
   out `cos(a,b) = (a·b) / (||a|| ||b||)` and compute it by hand for two short toy vectors (e.g.
   `a=(2,0,1)`, `b=(1,1,1)`). Confirm your hand computation matches `exercises.ipynb` Exercise 4.
2. **Precision/recall algebra at the `min_score` threshold.** Given a confusion count
   (TP, FP, FN, TN) from your eval set at one threshold, derive precision `TP/(TP+FP)` and recall
   `TP/(TP+FN)`; then argue algebraically why *raising* `min_score` can only keep recall the same
   or lower it, and keep precision the same or raise it (monotonicity, not just intuition).
2b. **The refusal case.** A "refuse to guess" (`None`) prediction is neither a TP nor an FP for
   the *matched* class — it's an FN if the true answer was a real player, and a TN if the true
   answer was genuinely `None`. Redo your confusion matrix from Exercise 3 with refusals
   classified this way, then recompute precision/recall — does it change your answer to
   `workbook.md`'s "wrong confident answer or an honest 'I don't know'?" question?
3. **Bias–variance framing of the baseline vs. embedding trade-off.** The dictionary+fuzzy
   baseline is high-bias/low-variance (rigid but predictable); an embedding resolver is
   lower-bias/higher-variance (flexible but can drift on out-of-distribution nicknames). State,
   in one paragraph, which regime a 500-player entity space with a long nickname tail sits in,
   and why that argues for keeping the dictionary hit as a fast path even after adding embeddings.

## Definition of done
- Non-optional asserts pass; you have a number for baseline vs your resolver on the eval set.
- You can state the precision/recall trade-off you chose and *why* for a stats engine.

## Ship target (repo)
`src/statlas/entities/resolver.py` — add an embedding/n-gram path used as a fallback after the
exact nickname hit, keeping the `ResolvedPlayer(player_id, full_name, score)` return contract.
Keep the baseline reachable (e.g. a flag) so M7's eval can compare them.

## Carry-over
- Save your eval set — it becomes part of the M7 evaluation harness.
