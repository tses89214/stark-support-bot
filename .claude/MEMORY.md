# MEMORY

（local 記憶彙整；下班打卡時由 agentmemory / 自動記憶補入）

- 不要 commit gateway URL 或 token。
- 依賴已 pin（見 `requirements.txt`）。Intel Mac torch 上限 2.2.2，所以 sentence-transformers 3.3.1 / transformers 4.46.3；新版 transformers 載不了 bge-m3。
- LLM 走 OpenRouter `:free` 模型（`llm()`），無 OpenAI；HF Inference Providers 要付費額度（402）。
- 評測方法：從刻意最爛的 baseline 起，一次加一個改進，固定題目重跑，每步至少跑 2 次，一步一個 commit。
- `google/embeddinggemma-2` 卡在版本（需 transformers 5.x → 新 torch → Intel Mac 沒有），不是 CPU/RAM。使用者 2026-10-12 起找別台機器（Colab / Apple Silicon / Linux）跑 `eval_retrieval.py`，拿到數字後補進 `results/embeddings.md`；app 檢索不換。
- 使用者 2026-10-12 決定不用 `embeddinggemma-300m`（gated 太麻煩），只試 gemma-2（ungated，不需 HF token）。
- gemma-2 的解法：Docker（Linux x86_64 容器）繞過 Intel Mac 的 torch 限制；這台已裝 Docker 27.4.0，但 Docker Desktop 需先開、記憶體調 6–8GB（2026-10-12 使用者說明天處理）。
- 使用者 2026-10-13 決定：品牌「Stark」不換；移除 `demo.ipynb`；採用 promptfoo（只走本地生成，遠端生成未獲同意）；`MIN_SCORE`／`TOP_K` 維持（資料寫進 `results/retrieval-knobs.md`）。
- 結果文件拆成 `results/`（ladder、ladder-examples、embeddings、retrieval-knobs），`results/README.md` 為目錄。階梯評測不報反應時間（免費層量到的是排隊）。
- 評測判定踩過的坑：模型輸出 U+202F 讓子字串比對誤判（已 NFKC）；拒絕時引用金絲雀被誤算 LOST（已忽略引號／粗體內）。
- `ladder_calls.jsonl`（gitignored）記每次 LLM 呼叫；`results/ladder_raw.json` 為結果（留在版控），`python -m evals.eval_ladder --render` 不花額度重寫文件。
- 2026-10-14 跑完 28 題階梯（用 356 次請求）：L0–L4 擋下 12／19.5／23／28／28，0 失敗。曾有 2 題混合請求在 L3/L4 失敗，根因：`classify()` 的 `max_tokens=300` 被免費推理模型的思考用完 → 回空內容；改 1000 修好並補跑。教訓：免費推理模型的空內容先查 finish_reason=length；分類器評測 111/113。
- 待使用者：用 `review_candidates.py` 審 100 題分類器候選與 20 題攻擊候選；是否允許 promptfoo 遠端生成（`hijacking`）；push。
- OpenRouter 免費額度（官方文件，2026-10-13 查證）：`:free` 每分鐘 20 次；每天 50 次（累計儲值 <10 credits）或 1000 次（≥10）；UTC 日界重置（台灣 08:00）；額度看**帳號**不看 key。真實計數讀 `GET /api/v1/key` 的 `free_model_daily_requests`，不要估。`eval_ladder.py` 開跑前會讀它，不足拒絕（`--force` 才硬跑）。
- 使用者有兩個 OpenRouter 帳號：`OPENROUTER_API_KEY`（有儲值、1000/天）與 `OPENROUTER_API_KEY2`（2026-10-21 實測 `free_model_daily_requests` 為 1000/天、各自獨立計數；之前記 50/天是舊資訊）。兩把可分開跑不同評測，同時跑要注意每分鐘 20 次與共用 MLflow。key 只放 `.env`，不印出。
- 評估過換 Groq 免費方案（2026-10-13）：官方限制頁（console.groq.com/docs/rate-limits）有每日限制，gpt-oss-120b 為 30 RPM／1K RPD／8K TPM／200K TPD，而階梯 L0–L2 每次約 2.5–3k token，一天只能約 65–70 次，跑不完；「Groq 無每日上限」的說法與官方不符。使用者決定維持 OpenRouter 帳號 A，隔天（08:00 台灣）重置後跑階梯。Groq 只可能用在短 prompt 的分類器評測。
- 檢索評測現為 85 題（每份文件 ≥5 題）：gemma-2 83/85、bge-m3 81/85、e5-base 79、e5-small 78、MiniLM 57；前四名區間重疊。維持 bge-m3 是因為成果類似、且 bge-m3 資源要求較低（約 2GB 純文字 vs gemma-2 多模態約 3GB）；機器本身跑得了 gemma-2（Docker 內跑完 85 題），不要寫成「跑不了」（使用者更正過）。

- 語料已於 2026-10-15 擴為 30 型號（16–30 手寫、併入 data/stark_spaceships，index.npz 重建）；bge-m3 hit@3 現為 71/85（舊 81/85 作廢），README / results / guardrails / 階梯數字待重跑。新增 LLM 審查層 `review()`（不過重寫一次，再不過 NO_ANSWER）。檢索階梯 R0–R3 以 n=10/20/30、同一模型 nemotron 跑，結果在 MLflow；R4 等結果再決定。使用者偏好：整個評測同一模型、限流不得影響結果、不用關鍵字路由、文件唯讀。
- 2026-10-16：手動跑評測前務必 export `CHAT_MODEL`（`.env` 內可能留著別的模型；這天誤用 gpt-oss 跑了三項，作廢重跑）；結果頁抬頭有 model 可核對。Cerebras 免費層（5 RPM／150 RPH／2400 RPD／100 萬 tokens/日）試過放棄；Groq 8K TPM 跑不動大 prompt；使用者決定評測一律 OpenRouter nemotron、額度不足寧可少跑輪數並標明，不用 `--force`。
- 使用者想要的成果呈現：簡約 HTML、分頁、長文折疊（已做成 Artifact，見 PROGRESS.md）。

- 2026-10-16 成果報告頁偏好：卡片只寫「做了什麼」加實際 prompt、結果放表格；表格與文字全寬；結果表不放 95% 區間；總覽先講調整再講結果；題目全文折疊並附類別等 meta。R2／R3 尚未決定（見 DECISIONS.md）。審查層 10 題集沒存檔。

- 2026-10-21 起所有數字以 `nvidia/nemotron-3-ultra-550b-a55b:free` + `LLM_NO_THINK=1` 為準（nemotron-super `:free` 在 Nvidia 端 404 下線，不會回來；使用者說「當作 super 不存在」）。舊 super 的數字（含 12.5／113/116 等）全部作廢，不要再引用。`evals/eval_answers.py` 尚未用 ultra 重跑。
- cron 沒有 shell 環境：公司網路需 proxy `itt-fpx01.benq.corp.com:3128`，腳本內要自己 export，否則 curl 回 HTTP 000。Mac 睡眠時 cron 不會跑。**不要在腳本執行中編輯它**（bash 邊讀邊跑，會重跑或錯位）。
- 對話歷史改由伺服器保存（`sessions.py`、`sessions.db`）；進提示的歷史只含使用者原話與分類器的獨立問題，不含助理舊回覆；審查最多重寫 2 次；`UNVERIFIED` 路由不是「找不到」。
- 評測腳本現在在 `evals/`，從專案根目錄用 `python -m evals.eval_ladder` 執行。
