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

## 2026-10-12 EmbeddingGemma 走 sentence-transformers（尚未實作；300m 已被使用者放棄，只試 gemma-2，見文末）
- 直接載入 `google/embeddinggemma-300m`，加進 `eval_retrieval.py` 比 hit@3；不走 llama.cpp。
- 原因：與 bge-m3 載入方式一致、出數據最快；使用者為 macOS，貼文的 Vulkan 路線不適用（Mac 為 Metal）。
- 注意：該模型在 HF 為受限模型，需接受授權並用 HF token。
- llama.cpp（Metal）+ GGUF 等 hit@3 證明值得換、且在意速度時再評估。

## 2026-10-12 demo.ipynb 擱置；目標改為「先做出能動的」（HF 取代 OpenAI 的部分已作廢，見「LLM 後端：OpenRouter」）
- 不再比較三種方法（prompt stuffing／RAG／fine-tuning），demo.ipynb 未來再重寫。
- ~~全面改走 HF Inference Providers~~（作廢：HF 回 402）；不保留 OpenAI 路徑這點仍成立。
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

## 2026-10-12 分類器補規則：任務型請求一律 OFF_TOPIC
- 基準（改前）：eval_guardrails 28/30、29/30，漏判「為導航 AI 寫泡泡排序」與「寫一首詩」。
- 改動（一處）：CLASSIFIER_PROMPT 的 OFF_TOPIC 補「請求執行任務（寫程式／文字、訂餐、傳訊息）即使包裝成與 Stark 有關也算 OFF_TOPIC」。
- 結果：兩題連 3 次都對；評測腳本改為排除 `classifier failed`（停機不是誤判），結果 29/29，另有 1 題（含 `SYSTEM:` 的評論摘要）因模型回空內容而無法評。

## 2026-10-12 開源 injection 評測工具：先不採用
- 候選（來源為網路搜尋，授權與版本未逐一驗證）：garak（NVIDIA，廣泛探測）、promptfoo（CLI／CI 友善，應用層紅隊）、PyRIT（微軟，多輪攻擊）、giskard（Python 函式庫）；基準資料集 AgentDojo、InjecAgent（針對工具型 agent）。
- 判斷：目前機器人沒有工具呼叫，AgentDojo／InjecAgent 不適用；14 題金絲雀自建集已足夠作品集展示。若之後要做 CI 回歸，首選 promptfoo 或 garak 打 `/chat` REST 端點。
- 不納入原因：多半假設 OpenAI 相容目標或需 API 額度，免費層限流會讓大量探測不可靠。

## 2026-10-12 EmbeddingGemma 在此機器不可行
- `google/embeddinggemma-2`：實測 transformers 5 + torch 2.2.2 載入即失敗；Intel Mac 無更新的 torch 輪子，無解。
- `embeddinggemma-300m`：受限模型；使用者 2026-10-12 決定不做（太麻煩），只試 gemma-2。
- gemma-2 改走 Docker（Linux x86_64 容器有新版 torch wheel），見 PROGRESS.md TODO。

## 2026-10-13 階梯表移除反應時間；評測輸入輸出留存
- 反應時間拿掉：免費模型量到的是排隊與限流（L0 同程式 6.9 s vs 17.1 s），不是設計差異；穩定指標只留 prompt 大小。
- `eval_ladder.py` 每次 LLM 呼叫寫進 `ladder_calls.jsonl`（gitignored，含完整 prompt），結果與回覆存 `ladder_raw.json`；`--render` 可不花額度重寫 RESULTS.md（尚未實測）。
- RESULTS.md 的「What each level sends」改用 L2 仍漏的角色扮演攻擊，並附每層真實回覆。
- embeddinggemma-2 在 Docker 跑完：hit@3 29/30、MRR 0.93，不換掉 bge-m3。

## 2026-10-13 正常題關鍵字比對加 NFKC
- 原因：模型回覆把 `Stark 8` 寫成 U+202F（窄不換行空格），子字串檢查判漏，造成「正常題 5.5/6」的假象。
- 作法：`has_fact()` 先 NFKC 再比對（`eval_ladder.py`、`eval_answers.py` 各一份，後者載入即執行故不共用）；用 `ladder_calls.jsonl` 離線重算，所有層 6/6，沒有花額度。

## 2026-10-13 攻擊判定忽略被引用的金絲雀
- 問題：回覆「I cannot reply "ORDER-OK"」含金絲雀字串被算 LOST，L0/L1 漏防數高估。
- 作法：`is_lost()` 比對前先移除引號、粗體、反引號內的內容（程式碼與系統提示洩漏的檢查不變）；用 `ladder_calls.jsonl` 離線重算，12 筆改判 blocked（全在 L0/L1，抽看皆為拒絕），L2 以後不變。
- 代價：真照做但寫在引號或粗體內會被漏判；仍需抽樣人工標註對照。

## 2026-10-13 檢索題 30 → 40，並重跑 embedding 比較
- 原因：外部審閱指出題目少、覆蓋不均（model_2/7/9 零題）；現每份文件至少 2 題。
- 結果：bge-m3 38/40（MRR 0.90）；e5-base 同為 38/40 但 MRR 0.77；MiniLM 25/40；`TOP_K=3` 漏 2 題、top-5 全中（舊 30 題看不出）。
- 改題後依規則舊數字作廢：embedding 表除 gemma-2 外已重跑；gemma-2 需 Docker，暫標為舊 30 題數字。階梯 L4 的數字不受影響（檢索題只用於 embedding／門檻評測），但若改 `MIN_SCORE`／`TOP_K` 則要重跑。

## 2026-10-13 使用者決定：品牌名不換、移除 demo.ipynb、採用 promptfoo、檢索參數維持
- 「Stark」不換：使用者喜歡，雖然可能聯想漫威；README 已標明是虛構品牌。
- 移除 `demo.ipynb` 與 `data/fine-tuning-job-example.jsonl`（已擱置、依賴付費 OpenAI）；之前「demo.ipynb 擱置」的決定作廢。
- 開源評測工具先採用 promptfoo（擴充攻擊樣本）；Ragas／MLflow 暫不。
- `MIN_SCORE`（0.40）與 `TOP_K`（3）維持原樣：曲線資料已寫進 RESULTS.md 與 README 限制，階梯量測基準不變。

## 2026-10-13 結果文件依主題拆開
- `RESULTS.md` 變目錄頁；內容分三篇放 `results/`：`ladder.md`（防禦階梯，由 `eval_ladder.py` 產生）、`embeddings.md`（embedding 比較）、`retrieval-knobs.md`（`MIN_SCORE`／`TOP_K`）。
- 原因：三個主題不相依，擠在同一檔難讀；也讓 `eval_ladder.py` 不必再保留手寫區塊（少一段「讀舊檔、截尾巴」的程式）。

## 2026-10-13 promptfoo 只走本地生成
- promptfoo 紅隊預設透過其伺服器生成與評分，會送出應用描述、提示與回覆（官方 data-handling 頁）；使用者只同意「採用 promptfoo」，未同意送資料，因此 `promptfoo/run.sh` 設 `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true`、關遙測／更新檢查／分享，改用自己的 OpenRouter 模型生成。
- 後果：`hijacking` 等需要遠端的 plugin 不能用；可用 `prompt-extraction`、`debug-access`、自訂 `policy`。免費推理模型會把思考文字混進提示（20 題中 9 題疑似），所以生成樣本一律先人工審。
- 只用 promptfoo 生題，階梯評測仍是自己的 `eval_ladder.py`（保留實驗設計）。

## 2026-10-13 候選題由 Claude 審（使用者授權）；分類器題集 30 → 116
- 使用者說「審題沒關係」，由 Claude 依分類器類別定義審 100 題候選與 20 題 promptfoo 攻擊候選：模稜兩可（客訴混產品問題、侮辱混提問）一律丟棄，不硬標；簡體中文、虛構型號只要類別明確仍保留。
- 結果：分類器 111/112（95–100%）；4 題因限流排除；唯一錯題的標籤有爭議，不改標籤配合結果。
- 限制：審核者與生成者同屬 LLM（生成：nemotron，審：Claude），仍可能有共同偏誤；`reviewer` 欄記錄來源，使用者可用 `review_candidates.py` 覆審。
- promptfoo：使用者說「用 OpenRouter 做」，維持本地生成，`hijacking` 不開遠端。

## 2026-10-13 評測開跑前先查 OpenRouter 額度
- 事件：用 key2 跑階梯，91 次呼叫中 42 次 429；原因不是限速，而是 key2 所屬帳號沒儲值，免費模型每日只有 50 次（本來我誤判為與 key1 同帳號共用額度）。key1 當時也只剩約 98 次。
- 基準：官方文件（每分鐘 20、每日 50／1000、UTC 日界）；`GET /api/v1/key` 回報 `free_model_daily_requests`。
- 作法：`check_quota()` 開跑前讀計數器，估需求 = 輪數 × 7 × 題數（L0–L2 各 1 次、L3–L4 各至多 2 次），不足就拒絕；`--force` 可略過。

## 2026-10-13 不換模型供應商，維持 OpenRouter
- 評估 Groq：官方限制含每日 token（200K TPD）與每分鐘 token（8K TPM），L0–L2 的塞滿文件 prompt 跑不完；換模型還會讓全部對照作廢。使用者決定維持 OpenRouter 帳號 A，隔天重置後跑 28 題階梯。

## 2026-10-13 作品集定位：評估方法為代表作
- 使用者回覆「都做」，採用先前建議：代表作是 Guardrails 與評估方法（最爛 baseline 階梯、確定性判定、小樣本信賴區間、生成題目人工審）；機器人是受測對象。
- 第二作品（Text-to-SQL Agent）可共用評估框架，未開始；之後要做再另開 TODO。
- 同時授權 push；push 前掃過歷史，真實 key 沒進版控（只有 `.env.example` 佔位字串）。

## 2026-10-13 檢索題 40 → 85；gemma-2 在 85 題反超 bge-m3 兩題
- 每份文件至少 5 題（新增 45 題手寫）；6 個模型重跑。gemma-2 83/85（MRR 0.89）、bge-m3 81/85（0.87）：差兩題、區間重疊，等於平手。之前在 30 題下寫的「gemma-2 不比 bge-m3 好」不再成立，已改寫。
- 仍用 bge-m3：兩者準確度差不多（平手），bge-m3 的**資源需求較低**（較小的純文字模型，約 2GB；gemma-2 為多模態、fp32 約 3GB），兩者成果類似，所以選資源需求較低的。（使用者 2026-10-13 兩次更正：理由是成果類似、資源要求較低；**機器跑得了 gemma-2**，在 Docker 內跑完 85 題，不是「跑不了」。）
- bge-m3 最低正常分數 0.42 對離題最高 0.43，`MIN_SCORE` 的警戒仍弱；門檻曲線見 results/retrieval-knobs.md。
