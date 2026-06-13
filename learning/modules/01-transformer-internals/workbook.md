# Module 1 — Transformer Internals

**Track 1 · advanced · ~2–4 sessions**
Goal: be able to derive and *implement* a transformer block from memory, and explain every
tensor shape. Statmuse-grade NLU later (M3) rests on actually understanding what an LLM does
internally — not treating it as a black box.

## Objectives (you can do these without notes when done)
1. Derive scaled dot-product attention and explain **why** the `1/√d_k` scaling exists.
2. Implement multi-head self-attention from scratch in numpy; match PyTorch's output.
3. Explain the role of the causal mask, positional encodings, residual stream, and LayerNorm.
4. Train nanoGPT on tiny-shakespeare and read the loss curve critically.

## Read / watch (primary sources, in this order)
- **Paper:** Vaswani et al., *Attention Is All You Need* (2017) — arXiv 1706.03762. Read §3
  (architecture) closely; skim training details. https://arxiv.org/abs/1706.03762
- **Annotated:** *The Annotated Transformer* (Harvard NLP) — line-by-line implementation next
  to the paper. https://nlp.seas.harvard.edu/annotated-transformer/
- **Video:** Karpathy, *Let's build GPT: from scratch, in code, spelled out* (~2h).
  https://www.youtube.com/watch?v=kCc8FmEb1nY
- **Code:** nanoGPT repo. https://github.com/karpathy/nanoGPT
- *Optional depth:* Elhage et al., *A Mathematical Framework for Transformer Circuits*
  (residual-stream view). https://transformer-circuits.pub/2021/framework/

## Theory notes (fill in as you read)
- Why scale by `√d_k`: dot products grow with dimension → softmax saturates → vanishing
  gradients. Scaling keeps variance ~1. _(prove it to yourself: var of dot product of two
  unit-variance d_k-vectors is d_k.)_
- Q/K/V intuition: ___
- Causal mask: ___
- Why multi-head beats one big head: ___
- Positional encoding (sinusoidal vs learned vs RoPE): ___

## Exercises → `exercises.ipynb`
Pure-numpy core (offline, asserts grade you); torch & nanoGPT cells are marked optional.
1. **Softmax** — numerically stable, axis-correct.
2. **Scaled dot-product attention** — with optional causal mask.
3. **Multi-head attention** — split heads, attend, concat, project.
4. **Positional encoding** — sinusoidal; verify the wavelength geometry.
5. **Causal-mask check** — prove position *t* can't see *t+1* (perturbation test).
6. **(Optional, torch)** match `torch.nn.MultiheadAttention` to your numpy version.
7. **(Optional, nanoGPT)** train on tiny-shakespeare; record final val loss + a sample.

## Definition of done
- All non-optional asserts in the notebook pass.
- You filled the theory-notes blanks in your own words.
- You can answer: "Walk me through the shape of every tensor from token IDs to logits."

## Ship target (repo)
No `src/` change this module — it's foundational. **Deliverable:** a short
`learning/modules/01-transformer-internals/notes.md` (your filled-in theory notes) + the
nanoGPT val-loss number. This is the only "read-only" module; M2 onward all touch `src/statlas/`.

## Carry-over
- Note any concept you had to look up — that's a candidate for a fundamentals refresher.
