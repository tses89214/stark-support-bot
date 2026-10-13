# MEMORY

（local 記憶彙整；下班打卡時由 agentmemory / 自動記憶補入）

- 不要 commit gateway URL 或 token。
- 依賴已 pin（見 `requirements.txt`）。Intel Mac torch 上限 2.2.2，所以 sentence-transformers 3.3.1 / transformers 4.46.3；新版 transformers 載不了 bge-m3。
- LLM 走 OpenRouter `:free` 模型（`llm()`），無 OpenAI；HF Inference Providers 要付費額度（402）。
- 評測方法：從刻意最爛的 baseline 起，一次加一個改進，固定題目重跑，每步至少跑 2 次，一步一個 commit。
- `google/embeddinggemma-2` 卡在版本（需 transformers 5.x → 新 torch → Intel Mac 沒有），不是 CPU/RAM。使用者 2026-10-12 起找別台機器（Colab / Apple Silicon / Linux）跑 `eval_retrieval.py`，拿到數字後補進 `RESULTS.md` 的 embedding 表；app 檢索不換。
- 使用者 2026-10-12 決定不用 `embeddinggemma-300m`（gated 太麻煩），只試 gemma-2（ungated，不需 HF token）。
- gemma-2 的解法：Docker（Linux x86_64 容器）繞過 Intel Mac 的 torch 限制；這台已裝 Docker 27.4.0，但 Docker Desktop 需先開、記憶體調 6–8GB（2026-10-12 使用者說明天處理）。
- 使用者 2026-10-13 決定：品牌「Stark」不換；移除 `demo.ipynb`；採用 promptfoo（只走本地生成，遠端生成未獲同意）；`MIN_SCORE`／`TOP_K` 維持（資料寫進 `results/retrieval-knobs.md`）。
- 結果文件拆成 `results/`（ladder、ladder-examples、embeddings、retrieval-knobs），`RESULTS.md` 為目錄。階梯評測不報反應時間（免費層量到的是排隊）。
- 評測判定踩過的坑：模型輸出 U+202F 讓子字串比對誤判（已 NFKC）；拒絕時引用金絲雀被誤算 LOST（已忽略引號／粗體內）。
- `ladder_calls.jsonl`（gitignored）記每次 LLM 呼叫；`ladder_raw.json` 為結果，`python eval_ladder.py --render` 不花額度重寫文件。
- 待使用者：用 `review_candidates.py` 審 100 題分類器候選與 20 題攻擊候選；是否允許 promptfoo 遠端生成（`hijacking`）；push。

