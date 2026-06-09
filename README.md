# statlas

An all-in-one hub for sports analytics — a natural-language sports stats engine (a "better StatMuse").

Ask a sports question in plain English and get an **exact**, database-backed answer.

## The one idea

A Gen AI / LLM layer translates your question into a structured query; a SQL engine computes the exact number. **The LLM handles language, never arithmetic** — that's what keeps the answers accurate instead of hallucinated.

```
question  --LLM-->  structured query  --SQL engine-->  exact number  --LLM-->  answer
```

## Status

`main` is kept clean. Active development lives on the **`learning`** branch — a phased, study-plan-driven build (p0 scaffold and beyond).

```bash
git checkout learning
```
