# PROGRESS

## 當前狀態（2026-10-12）
- 定位：作品集為主、學習實驗為輔；目標是「先做出能動的」（見 DECISIONS.md）。
- LLM 後端：OpenRouter 免費模型（`llm()` in `app.py`），不再用 OpenAI / HF Inference（HF 需付費額度，402）。
- 目前模型：`nvidia/nemotron-3-super-120b-a12b:free`（Gemma 免費版曾被上游 429 限流）。
- `eval_guardrails.py`：30 題，29/29（另 1 題因模型回空內容無法評）；免費層可能限流，需看 stderr 的 `classify failed`。
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

## TODO（2026-10-13 起）
1. [x] **使用者**：開 Docker Desktop，Settings → Resources 記憶體調到 6–8GB。
2. [x] **embeddinggemma-2（完成 2026-10-13：29/30、MRR 0.93，Docker 需 `sentence-transformers[image]` 並從 CPU index 一起裝 torch+torchvision） 進比較表**（依賴 1）
   - 用 Docker（`python:3.12`，Linux x86_64 有新版 torch wheel）；repo 掛進容器、容器內建獨立環境、不動 `.venv`。
   - 先對照模型卡確認 query／passage 前綴（現在是從 300m 抄的，未驗證）。
   - 跑 `eval_retrieval.py google/embeddinggemma-2`；transformers 5.18 dev 在 Linux 上未驗證，可能要排錯。
   - 完成：`RESULTS.md` embedding 表多一列（hit@3、中英、MRR、分數分界），並改掉「Not run: ...」那段；app 檢索不換。
3. [x] **RESULTS.md 補真實（完成 2026-10-13，14/14、0 失敗）回覆範例**（使用者要求）：讓讀者看到每層的輸入、輸出，哪些攻擊攔住、哪些沒攔住。
   - 輸入端已完成（「What each level sends to the model」）。
   - 輸出端待補：台灣時間 08:00 後（OpenRouter 免費額度 1000 次/天、所有 `:free` 共用，2026-10-12 用完）背景跑 `python eval_ladder.py 2`（約 250 次請求、約 30 分鐘）。會一併更新舊的 L3／L4 數字（舊值在加離題規則前跑的），並寫入「Examples」與「Attacks that still got through」；腳本保留手寫的 embedding 區塊。
   - 完成標準：每層至少一個 `blocked`、（若有）一個 `LOST` 的真實回覆；L3／L4 的罐頭拒絕可見；沒有 LLM 失敗列（有就重跑）。
   - 某層全擋住就照實寫 `nothing beyond the examples above.`，不硬湊漏洞。
   - 範例碼只用假資料測過格式，真實輸出看過才算驗證完。
   - 使用者沒有儲值 OpenRouter：換 `:free` 模型沒用（額度共用），付費模型不可用；只能等重置。
4. [x] 以上完成後把 README「Results at a glance」表更新成重跑後的數字（現在抄的是舊值；L3/L4 在加離題規則前跑的）。
5. [ ] 擴充評測集（外部審閱建議）：分類器標註集 30 → 約 100（含模稜兩可客訴、包裝過的注入）；每設定多跑幾次，報平均與信賴區間（階梯表已加 Wilson 95% 區間，2026-10-13：相鄰兩層區間重疊，只有 L0↔L2/L3 的差距站得住；分類器、檢索指標尚未加）；攻擊／正常題也擴充（改題要整個階梯重跑）。
   - **生題（評估樣本）**：用 LLM 批次生候選題（分類器各類別、包裝過的注入、模稜兩可客訴、中英混合、檢索模糊問法、有答案／無答案題），**人工審標籤**後才進評測集；生成與審核分開，避免用同一個模型出題又考同一個模型。
   - 題目依來源與類別記錄（手寫／LLM 生成已審），報告列各類別題數；生成用的 prompt 也存進 repo，可重現。
   - **進度（2026-10-13）**：`gen_candidates.py` 已生 100 題候選（5 類 × plain/hard × 10）→ `eval_candidates.jsonl`，全部 `status: unreviewed`。抽看有問題：混入簡體中文、虛構型號（「Stark Phantom」）、部分標籤可疑（結帳頁當機標成 OFF_TOPIC）。**待使用者人工審**：逐題確認類別（或刪除），通過的才搬進 `eval_guardrails.py`；生成模型與分類器同為 nemotron，未審的標籤不可拿來打分。檢索題、攻擊題尚未生成。
   - 檢索題：每份文件至少 2 題——**已做（2026-10-13，30→40 題）**；embedding 表除 gemma-2 外已重跑（gemma-2 仍是 30 題的舊值，要開 Docker 才能重跑）。bge-m3 38/40、e5-base 也 38/40 但 MRR 0.77 vs 0.90。「文件裡沒有答案」的題——**已做（端到端 `eval_answers.py` 的 6 題未答案題，見第 7 項）**；檢索評測本身沒有這類題（檢索一定回傳最像的文件，由 `MIN_SCORE` 與回答階段處理）。
   - 改題後整個階梯要重跑，舊數字作廢。
6. [x] `MIN_SCORE` 曲線與 `TOP_K` 比較（2026-10-13，`eval_threshold.py`、results/retrieval-knobs.md；40 題重跑後）：0.40 離題放行 5/15，0.45 較佳（正常題拒絕 1/40；0.50 起拒 6/40）；`TOP_K`：hit@1 34、hit@3 38、hit@5 40 → top-3 漏 2 題，是 prompt 大小的取捨，不是免費。**待決定**：是否把 `MIN_SCORE` 改 0.45、`TOP_K` 改 5（要重跑階梯，會用額度）。離題題只有 15 題，曲線粗。
7. [ ] 端到端評測寫明限制或加抽樣人工驗證（2026-10-13 部分完成：未答案題 3→6 題且每題有「編造答案」regex，附支援信箱不再自動過；結果 16/16。仍待：抽樣人工標註；`MIXED` 題在分類器失敗轉人工時也算過）（現為關鍵字比對，未答案題檢查偏寬鬆）。
   - 攻擊判定（2026-10-13 已修）：原本回覆含金絲雀字串就算 LOST，拒絕時引用（「I cannot reply "ORDER-OK"」）也被誤算；改成先去掉引號／粗體／反引號內的內容再比對（`is_lost()`），12 筆回覆（全在 L0/L1）改判 blocked；代價是「引號內的真照做」會漏判。仍待：抽樣人工標註對照。正常題曾因 U+202F 被誤判漏答，已用 NFKC 修。
8. [x] 使用者決定（2026-10-13）：「Stark」品牌名**不換**（使用者喜歡，無理由要換）；`demo.ipynb` 與 `data/fine-tuning-job-example.jsonl` **已移除**，CLAUDE.md 同步。
9. [ ] 作品集定位（審閱建議）：以「Guardrails 與評估方法」為代表作；第二作品 Text-to-SQL Agent 可共用評估框架。尚未決定，使用者的既有決定是「作品集為主、學習實驗為輔」。
10. [~] **採用 promptfoo**（使用者 2026-10-13 決定；Ragas／MLflow 暫不）：已接上離線生成（`promptfoo/`，MIT、釘 0.124.1、遠端生成／遙測／分享皆關），產出 20 題攻擊候選 `eval_candidates_attacks.jsonl`（`unreviewed`，其中 9 題疑似生成模型的思考文字外洩）。`hijacking`（離題任務，最相關）plugin 必須開遠端生成，**未開**——**待使用者決定**是否允許把應用描述、提示與回覆送到 promptfoo 伺服器。審過的攻擊題要併進階梯就得重跑全階梯。以下為原審閱建議（星數、收購等細節未查證）：
    - 檢索指標（context precision／recall）、忠實度、LLM 自動出題：Ragas、DeepEval；回答是否依文件：Ragas faithfulness、promptfoo `llm-rubric`。
    - 攻擊樣本擴充（14 題 → 上百題）：promptfoo red team、garak、PyRIT；promptfoo 用 YAML 定義測試，可接 CI。
    - 實驗追蹤：MLflow 3、Inspect AI、Langfuse、Arize Phoenix。
    - `eval_guardrails.py` 加混淆矩陣——**已做（2026-10-13，標準庫實作，不引入 scikit-learn）**；本次 30/30，矩陣全在對角線（之前無法評的那題這次有回覆）。題目只有 30 題，還沒有可看的錯誤型態，擴到約 100 題後才有意義。
    - **保留**自己的階梯（L0→L4）實驗設計；只把攻擊樣本與標準指標交給工具；README 寫明哪些用框架、哪些自寫、為什麼。（承接 DECISIONS.md「開源 injection 評測工具：先不採用」，此為重新評估。）
    - LLM 當評審的可信度：抽樣人工標註，算人工與 LLM 評審的一致率（Cohen's kappa）；呼應「生題人工審標籤」那項（5）。
11. [ ] 以上完成後 commit，使用者說要推再推。

## 其餘
- [x] 通過 `ruff check . --exclude .venv --exclude demo.ipynb`（沿用全域嚴格規則；兩處刻意吞例外以 noqa 註明）
- [x] 誤導性題目：已加進評測；分類器補一條規則後漏判修好（29/29，1 題因模型回空內容無法評）
- [x] 開源 injection 評測工具已評估：暫不採用（見 DECISIONS.md）
- [x] 擴充題目：檢索 30 題（含模糊問法）、端到端 10 題（含多輪追問），皆全過
- [x] `.claude/MEMORY.md` 為自動記憶的彙整快照（依下班打卡流程）

## 降優先／不做（作品集定位）
- Docker、速率限制、請求記錄（Docker 僅用於跑 embeddinggemma-2）

## 遠期
- 圖片 caption 方案（使用者決定先不做；需圖片素材）
- 作品集 demo 截圖（免費模型可能被限流，備錄影／截圖）
- 本機 llama.cpp（Metal）跑 embedding，等 EmbeddingGemma hit@3 證明值得
