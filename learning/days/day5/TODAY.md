# ✅ TODAY — Day 5 (2026-06-13) · Foundations, Stage 3: Transformers & Attention

Your entry point (MS-DS → Stages 1–2 are revision, skipped). Work top to bottom. Check the box
when done. Open this file in VS Code with **Cmd+Shift+V** so the links are clickable.

---

### Step 1 — Watch (~27 min)
- [x] **3Blue1Brown — "Attention in transformers, visually explained"** (Ch. 6 of the NN series).
      The best visual intuition for Q/K/V and attention.
      https://www.youtube.com/watch?v=eMlx5fFNoYc

*(Optional warm-up if you want the GPT framing first, ~27 min: 3B1B "But what is a GPT?"
https://www.youtube.com/watch?v=wjZofJX0v4M — skip if short on time.)*

### Step 2 — Read (~40 min)
- [x] **Jay Alammar — "The Illustrated Transformer."** Read slowly, all the way through the
      self-attention + multi-head sections. https://jalammar.github.io/illustrated-transformer/

### Step 3 — Read the source (~30 min)
- [x] **"Attention Is All You Need," §3.1–3.2** (the attention + multi-head math), with the
      Illustrated Transformer open beside it for reference. https://arxiv.org/abs/1706.03762

### Step 4 — Code it (~60–90 min)  ← the hands-on part
- [x] Open **`learning/days/day5/exercises/attention_from_scratch.ipynb`** in VS Code.
- [x] Complete the 3 TODOs: `softmax`, `scaled_dot_product_attention`, `causal_mask`.
- [x] Run every cell — keep fixing until **all the ✅ test cells pass.**

### Step 5 — Log it
- [x] Tell the coach (this chat) what you finished, e.g. "did steps 1–4, all tests pass." I'll
      update `progress.md` + your day summary and tee up Stage 5 (prompting & function calling).

---

> **✅ DONE — 2026-06-13.** All 5 steps complete. Notebook executes top-to-bottom with all three
> ✅ test cells passing (`softmax`, `scaled_dot_product_attention`, `causal_mask`). Stage 3 (transformers
> & attention) is the first foundations stage finished. **Next: roadmap Stage 4 (LLMs) → Stage 5 (prompting
> & function calling).**

---

**Today's goal in one line:** *understand attention well enough to implement scaled dot-product
attention + a causal mask from scratch.* That's the core mechanism behind every LLM you'll use
for text-to-SQL.

> Not building Statlas today — this is pure foundation on toy tensors. No NBA data involved.
