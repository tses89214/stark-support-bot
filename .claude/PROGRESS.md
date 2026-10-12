# PROGRESS

## 當前狀態（2026-10-12）
- 定位：作品集為主、學習實驗為輔；目標是「先做出能動的」（見 DECISIONS.md）。
- LLM 後端：OpenRouter 免費模型（`llm()` in `app.py`），不再用 OpenAI / HF Inference（HF 需付費額度，402）。
- 目前模型：`nvidia/nemotron-3-super-120b-a12b:free`（Gemma 免費版曾被上游 429 限流）。
- `eval_guardrails.py`：15/15（只跑一次；免費層可能限流，需看 stderr 的 `classify failed`）。
- 完整服務與 bge-m3 檢索評測已驗證（見下）。
- `demo.ipynb` 與 fine-tuning 檔擱置（CLAUDE.md 已標註）。

## 已完成
- demo notebook、RAG 客服 chatbot、guardrails、FastAPI UI、Stark 11–15 文件、bge-m3 檢索評測（舊）
- 本次：CLAUDE.md 加會話流程與規則；`.claude/` 追蹤檔；改用 OpenRouter；修掉 `llm()` 與路由 `chat()` 撞名；`llm()` 重試一次；`classify()` 失敗印 stderr；requirements 部分 pin
- 已存在（先前誤列為待做）：低分拒答 `MIN_SCORE`、分類器 `INJECTION`、多輪 `history`、工單寫入 `tickets.jsonl`、`.env`／`index.npz`／`tickets.jsonl` 已 gitignore

## 驗證結果（2026-10-12）
- `.venv` 已建（`PIP_USER=0` 才裝得進去）；Intel Mac，torch 最高 2.2.2，故 `sentence-transformers==3.3.1` + `transformers==4.46.3`（新版 transformers 拒絕在 torch<2.6 載入 bge-m3 的 .bin）。
- `eval_retrieval.py` bge-m3：hit@3 20/20（en 12/12、zh 8/8）；on-topic min 0.45、off-topic max 0.43。
- `uvicorn app:app --env-file .env` 實測：中文問答、OFF_TOPIC、INJECTION、ESCALATE（寫入 tickets.jsonl）、文件問答皆正常。
- `test_app.py`（離線）4 項通過，已做突變檢查。
- 新增 `guide_ordering_delivery.txt`、`guide_troubleshooting.txt`（流程文件，編號步驟）；索引重建為 17 份；`eval_retrieval.py` 26/26，MRR@3 0.96，離題分界不變（on-topic min 0.45／off-topic max 0.43）。
- `eval_answers.py`（端到端，關鍵字檢查）9/9；未答案題檢查偏寬鬆（ANSWER 路徑只要附 support 信箱即過）。
- README 已重寫。

## 需要你決定／提供
- [ ] **HF token（接受 EmbeddingGemma 授權）**：`google/embeddinggemma-300m` 是受限模型，目前 401。已加進 `eval_retrieval.py` 的 MODELS（含 prompt 前綴）。
- [ ] EmbeddingGemma 需 sentence-transformers>=5 / transformers>=4.56，與上面 bge-m3 的組合互斥 → 需另建 `.venv-gemma` 專跑該評測（Gemma 為 safetensors，可在 torch 2.2.2 載入，未驗證）
- [ ] `PLAN.md`、`INTERVIEW.md`（gitignored，僅本機，仍有舊 OpenAI 說明）要不要納入追蹤／搬進 `.claude/`
- [ ] Rule 6 token 預算（4,000／30,000）要改成多少——這是你的規則，我不擅改

## 其餘
- [ ] 圖片 caption 方案：需先有圖片素材（我無法產生真實圖片），再評估 `static/index.html` 顯示
- [x] 擴充題目：檢索 30 題（含模糊問法）、端到端 10 題（含多輪追問），皆全過
- [x] `.claude/MEMORY.md` 為自動記憶的彙整快照（依下班打卡流程）

## 降優先／不做（作品集定位）
- Docker、速率限制、請求記錄
- demo.ipynb 驗證（已擱置）

## 遠期
- 作品集 demo 截圖（免費模型可能被限流，備錄影／截圖）
- 本機 llama.cpp（Metal）跑 embedding，等 EmbeddingGemma hit@3 證明值得
