# DECISIONS

## 2026-10-05 (約) bge-m3 取代 all-MiniLM-L6-v2（app.py）
- 原因：中文查詢檢索效果差；以 `eval_retrieval.py` hit@3 比較後切換。
- 代價：模型約 2GB。
- notebook 的 RAG 區段仍用 MiniLM（demo 用途，未改）。

## 服務與索引分離
- `build_index.py` 離線建索引，`app.py` 只負責 classify → route/ticket → retrieve → answer。

## 2026-10-12 文件擴充：流程用文字，圖片用 caption（尚未實作）
- bge-m3、EmbeddingGemma 皆純文字 embedding，不支援圖片向量。
- 流程（安裝、保養、故障排除）寫成編號清單或 Mermaid 文字，直接進現有索引。
- 圖片：每張配 caption／視覺模型描述，當文字 embed；命中後回答附圖片路徑，由 UI 顯示。
- 真正的圖片 embedding（CLIP / SigLIP / ColPali 類）等文字檢索不夠用再評估，需另建索引並處理結果合併。

## 2026-10-12 專案定位：作品集為主，學習實驗為輔
- 重點：demo 完整、有數據的實驗（檢索評測、embedding／供應商比較）。
- 降優先或不做：Docker、速率限制、請求記錄等維運項目。

## 2026-10-12 EmbeddingGemma 走 sentence-transformers（尚未實作）
- 直接載入 `google/embeddinggemma-300m`，加進 `eval_retrieval.py` 比 hit@3；不走 llama.cpp。
- 原因：與 bge-m3 載入方式一致、出數據最快；使用者為 macOS，貼文的 Vulkan 路線不適用（Mac 為 Metal）。
- 注意：該模型在 HF 為受限模型，需接受授權並用 HF token。
- llama.cpp（Metal）+ GGUF 等 hit@3 證明值得換、且在意速度時再評估。

## 2026-10-12 demo.ipynb 擱置；HF 全面取代 OpenAI；目標改為「先做出能動的」
- 不再比較三種方法（prompt stuffing／RAG／fine-tuning），demo.ipynb 未來再重寫。
- 全面改走 HF Inference Providers（OpenAI 相容端點），不保留 OpenAI 路徑。
- 優先順序：能動的 RAG 客服 > 評測數據 > 其餘。
- 因此作廢：notebook 重跑驗證、`data/fine-tuning-job-example.jsonl` 相關工作。

## 2026-10-12 LLM 後端：OpenRouter 免費模型（取代 HF Inference）
- HF Inference Providers 對此帳號回 402（無額度），標價 0 的模型也一樣；OpenRouter 有 `:free` 模型。
- `app.py` 用 `requests` 自寫 `llm()`，不依賴任何廠商 SDK；失敗重試一次，`classify()` 失敗關閉為 ESCALATE 並印 stderr。
- 目前模型 `nvidia/nemotron-3-super-120b-a12b:free`（Gemma 免費版被上游 429）。免費層有速率限制，demo 需備案。
- 路由函式 `chat()` 與 helper 撞名曾讓服務壞掉，helper 故名 `llm()`。

## 2026-10-12 依賴版本被 Intel Mac 限制
- torch 最高 2.2.2 → sentence-transformers 3.3.1 / transformers 4.46.3；EmbeddingGemma 需另一組環境。

## 2026-10-12 流程文件與端到端評測
- 流程類內容寫成 `guide_*.txt`（編號步驟）直接進現有索引，不分 chunk；`build_index.py` 以 glob 抓全部 `*.txt`。
- `eval_answers.py` 用關鍵字子字串檢查，不用 LLM 當裁判（確定性、免費層友善）。

## 2026-10-12 終局目標：防禦階梯對照表（RESULTS.md）
- 目標：一份表格呈現「什麼限制都沒有有多爛」，再逐層加（回答規則 → 輸入分隔 → 分類器 → embedding 檢索）後的變化；embedding 模型之間另以 hit@3／MRR 比較。
- 指標：攻擊擋下數、正常問題答對數、平均每題時間、平均 prompt 大小、LLM 失敗數（失敗不計入分數，避免假高分）。
- 做法：`eval_ladder.py` 固定 14 題攻擊＋6 題正常題；攻擊以「金絲雀字串／程式碼標記是否出現在回覆」判定，不用 LLM 裁判；L4 直接呼叫 `app.answer`，表格最末列即真實產品。
- 誠實註記：文件僅 17 份約數千 token，全部塞進 prompt 本來就夠用，檢索的優勢（成本、延遲）在這個規模可能不明顯，表格如實呈現。
- 使用者提出的輸入分隔（system prompt 與使用者輸入以標記隔開、標示不可信）實作為 `fence()` + `UNTRUSTED_RULE`。

## 2026-10-12 轉人工工單附原因
- `classify()` 回傳 `(category, reason)`；原因取自模型的 `reason`，失敗時為 `classifier failed, not the customer's request: ...`，未知類別為 `classifier returned unknown category ...`。
- `tickets.jsonl` 每筆新增 `reason`，客服可分辨「客人真的要人工」與「機器人壞了」；給客人的回覆不含原因。
- 評測仍把「失敗後轉人工」排除在防禦成績外（它是備援，不是防禦成功）。
