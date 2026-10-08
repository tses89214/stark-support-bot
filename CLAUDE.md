# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Customer-service chatbot (`chatbot.py`, RAG over `data/stark_spaceships/`) plus `demo.ipynb`, a hands-on demo comparing three ways to give an LLM domain knowledge, using fake product data for "Stark Spaceships" (models 1–10). No build system, tests, or linter — the project is `chatbot.py`, `demo.ipynb` and data.

## Running

- `python chatbot.py` starts the CLI chat loop (same deps/env as below). Set `OPENAI_BASE_URL` and `CHAT_MODEL` to use another OpenAI-compatible endpoint (e.g. a LiteLLM gateway serving Claude). Never commit gateway URLs or tokens.
- Run `demo.ipynb` from the repo root (data paths are relative: `data/stark_spaceships/...`).
- Needs `OPENAI_API_KEY` in env. Python deps (not pinned anywhere): `openai`, `sentence-transformers`, `numpy`.
- Notebook calls paid OpenAI APIs (`gpt-4o` for chat, `gpt-4o-mini-2024-07-18` for fine-tuning). The fine-tuning cell uploads a file, starts a job and polls every 30s.

## Structure

`demo.ipynb` has three independent methods, each followed by a markdown pros/cons cell:

1. **Prompt stuffing** — concatenates all `data/stark_spaceships/model_{1..10}.txt` into the system prompt.
2. **RAG** — embeds docs with `sentence-transformers/all-MiniLM-L6-v2`, retrieves top-N by cosine similarity, passes hits to GPT.
3. **Fine-tuning** — trains on `data/fine-tuning-job-example.jsonl` (OpenAI chat format; polite replies to customer complaints, prefixed `Question:` / `Answer:`).

Data: one markdown-ish `.txt` per model (description, size, weight, capacity, color, price, accessories, notes). Notebook cells are English prose; keep that style when editing.
