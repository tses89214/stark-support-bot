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
- 防禦階梯 `RESULTS.md`（`eval_ladder.py`，每層 2 次平均）：攻擊擋下 3.5→9.0→12.5→13/13→13/13（/14 題，失敗題排除）；L4 prompt 8.7k→1.5k 字元、每題 6.9s→3.7s。輸入分隔（L2）貢獻最大。
- 工單附 `reason`；ruff 通過。
- L3 正常題 5.0/6：分類器對 6 題各 3 次皆判 ANSWER，沒有誤擋；掉分來自回答階段措辭波動。
- embedding 比較已寫入 RESULTS.md：bge-m3 30/30、MRR 0.95；MiniLM 中文僅 1/13；各模型分數皆無法分離離題（MIN_SCORE 為弱防線）。

## 需要你決定／提供
- [x] EmbeddingGemma 試驗：`embeddinggemma-2` 已實測，transformers 5 在 torch 2.2.2 載入即 `NameError: nn`，此機器跑不動，放棄。使用者後來決定不做 `embeddinggemma-300m`，只試 gemma-2（需別台機器）
- [x] `PLAN.md`／`INTERVIEW.md`（本機，gitignored）OpenAI 說明已改成 OpenRouter
- [x] Rule 6 改為單任務 50k／單會話 500k

## 下一步（使用者端，2026-10-12 下班）
- [ ] 使用者找別台機器（Colab／Apple Silicon／Linux）跑 `google/embeddinggemma-2`：卡點是版本（需 transformers 5.x → 新 torch），不是 CPU／RAM。拿到 `eval_retrieval.py` 數字後補進 `RESULTS.md` embedding 表；app 檢索不換。需要時可請我寫 Colab 用的最小腳本（只含 embedding 評測）。

- [ ] 重跑 `python eval_ladder.py 2`（背景、約 250 次請求）：2026-10-12 OpenRouter 免費額度（1000 次/天，所有 `:free` 共用）用完，那輪 L0 起大量 429，已中止，RESULTS.md 未被覆蓋。額度約 2026-10-13 台灣 08:00 重置。重跑會產生 RESULTS.md 的「Examples」區塊（程式已加，離線測過格式，尚未用真實 LLM 跑過）；舊 L3/L4 數字也在加離題規則前，會一併更新。腳本會保留手寫的 embedding 區塊。
- [ ] 重跑後檢查範例是否有說服力；`eval_ladder.py` 範例碼在那之前不算驗證完。使用者曾問「別的 model」：免費額度是共用的，換 `:free` 模型沒用；使用者沒有儲值 OpenRouter，付費模型不是選項；就等額度重置。

## 其餘
- [x] 通過 `ruff check . --exclude .venv --exclude demo.ipynb`（沿用全域嚴格規則；兩處刻意吞例外以 noqa 註明）
- [x] 誤導性題目：已加進評測；分類器補一條規則後漏判修好（29/29，1 題因模型回空內容無法評）
- [x] 開源 injection 評測工具已評估：暫不採用（見 DECISIONS.md）
- [x] 擴充題目：檢索 30 題（含模糊問法）、端到端 10 題（含多輪追問），皆全過
- [x] `.claude/MEMORY.md` 為自動記憶的彙整快照（依下班打卡流程）

## 降優先／不做（作品集定位）
- Docker、速率限制、請求記錄
- demo.ipynb 驗證（已擱置）

## 遠期
- 圖片 caption 方案（使用者決定先不做；需圖片素材）
- 作品集 demo 截圖（免費模型可能被限流，備錄影／截圖）
- 本機 llama.cpp（Metal）跑 embedding，等 EmbeddingGemma hit@3 證明值得
