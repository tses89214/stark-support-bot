# MEMORY

（local 記憶彙整；下班打卡時由 agentmemory / 自動記憶補入）

- 不要 commit gateway URL 或 token。
- 依賴已 pin（見 `requirements.txt`）。Intel Mac torch 上限 2.2.2，所以 sentence-transformers 3.3.1 / transformers 4.46.3；新版 transformers 載不了 bge-m3。
- LLM 走 OpenRouter `:free` 模型（`llm()`），無 OpenAI；HF Inference Providers 要付費額度（402）。
- 評測方法：從刻意最爛的 baseline 起，一次加一個改進，固定題目重跑，每步至少跑 2 次，一步一個 commit。
- `google/embeddinggemma-2` 卡在版本（需 transformers 5.x → 新 torch → Intel Mac 沒有），不是 CPU/RAM。使用者 2026-10-12 起找別台機器（Colab / Apple Silicon / Linux）跑 `eval_retrieval.py`，拿到數字後補進 `RESULTS.md` 的 embedding 表；app 檢索不換。
- `embeddinggemma-300m` 是 gated，需使用者的 HF token 與授權，尚未提供。
