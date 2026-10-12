# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Customer-service chatbot (`app.py`, RAG over `data/stark_spaceships/`) plus `demo.ipynb`, a hands-on demo comparing three ways to give an LLM domain knowledge, using fake product data for "Stark Spaceships" (models 1–15). No build system. Offline tests are in `test_app.py`, evals are `eval_*.py`, lint is `ruff check . --exclude .venv --exclude demo.ipynb`; results are in `RESULTS.md`.

## Running

- `python build_index.py` then `uvicorn app:app` (web chat at :8000); `python eval_guardrails.py` checks the input classifier (live LLM calls); `python eval_retrieval.py` compares embedding models by hit@3 (no LLM calls). `app.py` embeds with bge-m3 (`build_index.py`), which is ~2GB. `app.py` is the whole serving path: classify -> route/ticket -> retrieve -> answer; `static/index.html` is the UI. LLM calls go to OpenRouter (`llm()` in `app.py`, free `:free` models; HF Inference Providers needs paid credits); copy `.env.example` to `.env` and run `uvicorn app:app --env-file .env`. Never commit tokens.
- Run `demo.ipynb` from the repo root (data paths are relative: `data/stark_spaceships/...`).
- Needs `OPENROUTER_API_KEY` and `CHAT_MODEL` in env. Python deps are pinned in `requirements.txt` (Intel Mac: torch tops out at 2.2.2, so sentence-transformers 3.3.1 / transformers 4.46.3); use `.venv` and `PIP_USER=0` when installing.
- `demo.ipynb` (shelved) calls paid OpenAI APIs (`gpt-4o` for chat, `gpt-4o-mini-2024-07-18` for fine-tuning). The fine-tuning cell uploads a file, starts a job and polls every 30s.

## Structure

> **Status: shelved.** `demo.ipynb` and `data/fine-tuning-job-example.jsonl` are kept for reference only; the notebook will be rewritten later. Current focus is `app.py`.

`demo.ipynb` has three independent methods, each followed by a markdown pros/cons cell:

1. **Prompt stuffing** — concatenates all `data/stark_spaceships/model_{1..10}.txt` into the system prompt.
2. **RAG** — embeds docs with `sentence-transformers/all-MiniLM-L6-v2`, retrieves top-N by cosine similarity, passes hits to GPT.
3. **Fine-tuning** — trains on `data/fine-tuning-job-example.jsonl` (OpenAI chat format; polite replies to customer complaints, prefixed `Question:` / `Answer:`).

Data: one markdown-ish `.txt` per model (description, size, weight, capacity, color, price, accessories, notes). Notebook cells are English prose; keep that style when editing.

## 每次會話流程

### 上班打卡（會話開始時）
1. 讀 `.claude/PROGRESS.md` 了解當前狀態與下一步
2. 讀 `.claude/DECISIONS.md` 了解重要設計決策

### 下班打卡（會話結束或任務完成時）
1. 更新 `.claude/PROGRESS.md`（當前狀態、已完成、下一步）
2. 若有新的重要設計決策，補記到 `.claude/DECISIONS.md`
3. 把儲存在 local 的記憶捕進去 `.claude/MEMORY.md`
4. Commit 所有已完成工作

判斷標準：短任務（單次會話可完成）可不更新進度檔。跨會話任務或有重要決策時必須更新。

## Development Rules

These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

### Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

### Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

### Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

### Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

### Rule 5 — Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

### Rule 6 — Token budgets are not advisory
Per-task: 50,000 tokens. Per-session: 500,000 tokens.
If approaching budget, summarize and start fresh.
Surface the breach. Do not silently overrun.

### Rule 7 — Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

### Rule 8 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

### Rule 9 — Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

### Rule 10 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

### Rule 11 — Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

### Rule 12 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.
