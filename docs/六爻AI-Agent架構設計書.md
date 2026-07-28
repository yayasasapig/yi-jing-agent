# 《易經》六爻時位 AI Agent 系統架構設計書

> **融合《易經》思維嘅智能體生命週期架構**
>
> 初稿日期：2026年7月27日
> 概念來源：主人 yayafu × Gemini 對話蒸餾
> 文件類型：系統設計藍圖

---

## 一、緣起：當 AI Agent 遇上《易經》

### 1.1 現代 AI Agent 嘅三大死症

當前主流 AI Agent 框架（AutoGPT、LangChain Agent、CrewAI）喺執行複雜長程任務時，反覆出現三個結構性痛點：

| # | 痛點 | 表徵 | 傳統解決方案失效原因 |
|:-:|:----|:----|:------------------|
| ① | **目標飄移** | Agent 做做吓忘記原始用戶意圖，偏離任務軌道 | LLM 嘅注意力機制冇「階段性強制定錨」 |
| ② | **盲目衝動** | 未完成規劃就急住呼叫外部 API，造成 Token 浪費同不可逆副作用 | 缺乏「靜止觀察期」嘅強制閘門 |
| ③ | **崩潰無法復原** | 工具報錯 / API Timeout → Agent 陷入死循環或直接崩潰 | 冇「局部容錯切換」機制，一錯就全盤 restart |

### 1.2 《易經》點解適合做 Agent 架構

《易經》嘅核心智慧同 AI Agent 系統設計存在驚人嘅結構對應：

| 易經概念 | AI Agent 對應 | 共通邏輯 |
|:--------|:-------------|:--------|
| **六爻時位** | 執行生命週期階段 | 每一個階段有唔同嘅行為規範同限制 |
| **動爻變卦** | 動態容錯切換 | 某個位出問題 → 局部翻轉 → 生成新策略 |
| **錯綜互卦** | 多維度反思引擎 | 從隱含動機、對抗視角、用戶體驗三維審查 |
| **周流六虛** | 螺旋式遞歸生命週期 | 完成一輪 → 壓縮記憶 → 進入下一層次 |

---

## 二、六爻時位：Agent 嘅 6 階執行生命週期

任何長程任務都唔應該一股腦咁丟俾 LLM，而係必須通過 **6 個嚴格嘅時位節點**，每個節點有特定嘅行為規範同輸出限制。

### 2.1 六爻總覽

```
爻位           Agent 行為             輸出限制
──────────────────────────────────────────────────────
初爻（潛龍勿用）→ 純粹理解・唔准郁      → 只輸出結構化 Task Graph
二爻（見龍在田）→ 沙盒試探・局部驗證    → 可行性報告 + Plan A
三爻（終日乾乾）→ 風險反思・自我審查    → 護欄報告 / 內部修正
四爻（或躍在淵）→ 人機協同・授權決策    → 授權請求 / 確認開關
五爻（飛龍在天）→ 全力執行・並行輸出    → 核心交付物 Core Payload
上爻（亢龍有悔）→ 復盤歸檔・記憶壓縮    → Long-term Memory 寫入
```

### 2.2 各爻詳細規範

---

#### 初爻：潛龍勿用 — Context & Intent Parser

> **《易經》：「潛龍勿用，陽在下也。」**
>
> 龍潛於淵，未可施用。此時只宜觀察沉澱，蓄積力量。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | Context & Intent Parser |
| **AI 行為** | 掃描記憶庫、解析用戶意圖、收集脈絡資訊。**嚴禁調用任何外接工具（Actuators）**，純粹做資訊收集同結構化 |
| **輸出限制** | **禁止對外動作**，僅輸出結構化 Task Graph（JSON / YAML） |
| **Token 上限** | 建議 context window 嘅 5% |
| **檢查點** | 輸出嘅 Task Graph 必須包含：目標、前提、限制條件、成功指標 |

**Task Graph Schema 範例：**

```json
{
  "task_id": "T-001",
  "original_intent": "用戶想要分析某個網站嘅競爭對手",
  "constraints": ["需使用繁體中文輸出", "唔需要登入"],
  "success_criteria": ["產出對比表格", "涵蓋至少 3 個對手"],
  "forbidden_actions": ["不得修改任何外部系統"],
  "estimated_complexity": "medium"
}
```

---

#### 二爻：見龍在田 — Sandbox & Prototyping

> **《易經》：「見龍在田，利見大人。」**
>
> 龍出現喺田野，可以嶄露頭角。但仍需喺可控範圍內試探。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | Sandbox & Prototyping |
| **AI 行為** | 派發微型子任務（Worker Agents），喺沙盒環境或模擬器中測試可行性，生成初稿 / Prototype |
| **輸出限制** | 產出 **可行性報告** 與初步 **Plan A** |
| **關鍵機制** | 任何外部調用必須經過沙盒化 — 允許失敗、允許 dirty、唔可以影響生產環境 |

**可行性報告包含：**

```
1. Plan A 流程描述
2. 關鍵 API / 工具清單
3. 預估 Token 消耗
4. 已知風險點
5. 備選方案（Plan B / Plan C 概念）
```

---

#### 三爻：終日乾乾 — Reflexion & Safety Gate

> **《易經》：「終日乾乾，反覆道也。」**
>
> 終日勤勉不懈，反覆審視自己嘅行為。呢度係風險控制閘門。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | Reflexion & Safety Gate |
| **AI 行為** | 進入護欄機制（Guardrails），啟動三維反思引擎（見第四章）。檢查 Plan A 是否有安全漏洞、Token 超標風險、隱私洩漏或邏輯衝突 |
| **輸出限制** | 若發現風險 → 觸發 **內部修正迴圈**；若通過 → 輸出已簽核嘅執行計畫 |
| **觸發動爻條件** | API 權限不足、安全規則違反、成本超標、邏輯矛盾 |

**安全閘門 Checklist：**

```
[ ] 有冇存取未經授權嘅資源？
[ ] 會唔會泄露用戶私隱？
[ ] Token 預算係咪足夠？
[ ] 邏輯有冇矛盾 / 循環依賴？
[ ] 有冇考慮到失敗情境？
[ ] 輸出格式符合用戶要求？
```

---

#### 四爻：或躍在淵 — HITL & Pivot Decision

> **《易經》：「或躍在淵，進無咎也。」**
>
> 龍或者躍起，或者仍留喺深淵。呢度係關鍵嘅決策節點 — 要決定係咪正式執行。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | HITL（Human-in-the-Loop）& Pivot Decision |
| **AI 行為** | 評估是否需要人類介入授權？評估關鍵 API 嘅調用成本，決定正式執行定係 pivot |
| **輸出限制** | 發送 **確認請求** 或確定授權開關（0/1） |
| **四爻係可選爻位** | 根據任務風險等級決定是否需要經過四爻 |

**授權級別：**

```
Level 0: 完全自動（不需人類確認）
Level 1: 通知人類（Human-in-the-Loop 可選擇攔截）
Level 2: 必需人類確認（重大決策）
Level 3: 人類執行（Agent 只提供建議）
```

---

#### 五爻：飛龍在天 — Master Orchestrator

> **《易經》：「飛龍在天，大人造也。」**
>
> 龍飛翔喺天空，係最輝煌嘅時刻。呢度係全力執行階段。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | Master Orchestrator |
| **AI 行為** | 全力調動 API、並行處理子任務、整合資料，輸出核心交付物 |
| **輸出限制** | 產出 **主要任務結果（Core Payload）** |
| **並行處理** | 可同時派發多個 Worker Agents，並行執行獨立子任務 |

**五爻執行原則：**

- **盡全力但留有後路**：每個外部調用都有 timeout 同 retry 機制
- **局部失敗唔影響全局**：子任務失敗唔會影響主流程
- **即時狀態記錄**：每個步驟嘅結果寫入暫存記憶

---

#### 上爻：亢龍有悔 — Memory Compression

> **《易經》：「亢龍有悔，盈不可久也。」**
>
> 龍飛得過高，必將有悔。呢度係收尾階段 — 唔好過度，要識得收。

| 項目 | 規範 |
|:----|:----|
| **系統模組** | Memory Compression |
| **AI 行為** | 評估執行結果是否過度（Overshoot），清理臨時 Task，將經驗壓縮轉存至向量數據庫（LTM） |
| **輸出限制** | 寫入 **Long-term Memory**，釋放 Context Window |
| **復盤內容** | 成功因素、失敗原因、可重用模式、下次改善建議 |

**記憶壓縮格式：**

```json
{
  "session_id": "S-001",
  "task_type": "competitor_analysis",
  "execution_summary": "成功完成，耗時 45 秒，耗費 12K tokens",
  "key_patterns": [
    "使用 requests 比 browser automation 快 3 倍",
    "目標網站有反爬機制需繞過"
  ],
  "failure_modes_encountered": [
    "五爻 API timeout → 觸發動爻 → 降級二爻模擬 → 成功"
  ],
  "recommendations": [
    "下次同類型任務可直接跳過二爻沙盒"
  ]
}
```

---

## 三、動爻與變卦：容錯與動態路徑重組

呢個係成個架構最核心嘅創新 —— **將《易經》嘅變卦機制引入系統容錯**。

### 3.1 基本原理

```
主卦（Plan A）──[ 異常觸發 ]──> 動爻 ──[ XOR 翻轉 ]──> 變卦（Plan B）
```

當 Agent 喺某個爻位遇到異常時，該爻位嘅狀態 bit 會翻轉（0 ↔ 1），系統自動查表計算出新嘅「變卦」，並根據變卦嘅意義切換執行策略。

### 3.2 動爻觸發條件

| 觸發位置 | 觸發事件 | Bit 翻轉 | 變卦路徑 |
|:--------|:--------|:-------:|:--------|
| 初爻 | 意圖解析失敗、Context 不足 | Bit 1 flip | 要求用戶補充輸入 |
| 二爻 | 沙盒環境出錯、模擬失敗 | Bit 2 flip | 跳過沙盒・直接進入反思 |
| 三爻 | 安全審查出問題、風險超標 | Bit 3 flip | 返回初爻重新理解 OR 要求人類介入 |
| 四爻 | 人類確認超時、授權被拒 | Bit 4 flip | 降級執行（用較低成本方案） |
| 五爻 | API Timeout、工具報錯、網路中斷 | Bit 5 flip | **降級回二爻**（沙盒模擬）→ 完成後推回五爻 |
| 上爻 | 記憶壓縮失敗、儲存空間不足 | Bit 6 flip | 上爻降級 = 直接清除暫存，忽略壓縮 |

### 3.3 XOR 矩陣計算變卦

系統維護一個 6-bit 狀態碼 `hexagram_code`，每位對應一個爻位。

```
初始主卦：乾為天 = 111111（全部順利）
                    ↓↓↓↓
遇到五爻 API Timeout → flip bit5
                    ↓↓↓↓
變卦：天澤履 = 111011 → 降級執行策略
```

**64 卦對應表（部分）：**

| 卦名 | 卦象 | 二進制 | Agent 意義 | 處理策略 |
|:----|:----:|:-----:|:----------|:--------|
| ䷀ **乾** | 111111 | 全陽 | 一切順利 | Happy Path |
| ䷁ **坤** | 000000 | 全陰 | 全面崩潰 | 人類接管・緊急停機 |
| ䷂ **屯** | 100010 | 初生艱難 | 任務剛開始就卡住 | 重新理解意圖 |
| ䷃ **蒙** | 010001 | 矇昧不清 | Context 不足 | 要求用戶補充 |
| ䷄ **需** | 010111 | 等待需求 | 等待外部資源 | 暫停・輪詢 |
| ䷅ **訟** | 010110 | 爭訟衝突 | 邏輯矛盾 | 回溯初爻重構 |
| ䷆ **師** | 000010 | 聚眾出兵 | 需要多 Agent 協作 | 切換團隊模式 |
| ䷇ **比** | 000010 | 親比輔助 | 需要人類指導 | 請求 HITL |
| ䷈ **小畜** | 110111 | 小有積蓄 | 部分成果可用 | 交付 Partial Result |
| ䷉ **履** | 111011 | 履行謹慎 | 執行層出問題 | 降級二爻沙盒 |
| ䷊ **泰** | 111000 | 上下交泰 | 人類反饋良好 | 繼續執行 |
| ䷋ **否** | 000111 | 上下不交 | 人類反饋差 | 重新理解 |
| ䷌ **同人** | 000111 | 與人協同 | 需與外部系統協同 | 開啟 API 閘門 |
| ䷎ **謙** | 001000 | 謙卑低調 | 建議降低調用頻率 | Rate Limit 模式 |
| ䷏ **豫** | 000100 | 預備準備 | 建議加強準備 | 延長二爻沙盒 |
| ䷐ **隨** | 100110 | 順勢跟隨 | 跟隨用戶引導 | 開放式對話模式 |
| ䷑ **蠱** | 011001 | 敗壞腐蝕 | Context Window 污染 | 強制清理重建 |
| ䷒ **臨** | 000011 | 面臨降臨 | 關鍵決策點 | 進入四爻 HITL |
| ䷓ **觀** | 110000 | 觀察審視 | 需要更多數據 | 延長初爻觀察 |
| ䷔ **噬嗑** | 100101 | 咬合審判 | 需執行安全檢查 | 強制三爻反思 |
| ䷕ **賁** | 101001 | 文飾美化 | 輸出格式需優化 | 格式調整模式 |
| ䷖ **剝** | 100000 | 剝落崩解 | 任務逐步失敗 | 逐層回溯・拯救局部成果 |
| ䷗ **復** | 000001 | 復甦回歸 | 失敗後恢復 | 從初爻重新開始 |
| ䷘ **无妄** | 100111 | 意外之災 | 不可預期錯誤 | 進入緊急降級 |
| ䷙ **大畜** | 100111 | 大量積累 | 累積足夠經驗 | 壓縮為 Pattern |
| ䷚ **頤** | 100001 | 養育滋養 | Context 需要補充 | 重新注入相關記憶 |
| ䷛ **大過** | 011110 | 過度超標 | Token 超限 / 過度執行 | 強制中斷・上爻提前 |
| ䷜ **坎** | 010010 | 重險陷阱 | 反覆失敗 | 人類接管 |
| ䷝ **離** | 101101 | 附麗光明 | 需要更多資訊源 | 開啟外部搜索工具 |
| ䷞ **咸** | 001110 | 感應互動 | 用戶有即時反饋 | 切換互動模式 |
| ䷟ **恆** | 001110 | 持久恆常 | 長週期任務 | 定期 checkpoint |
| ䷠ **遯** | 001111 | 退避隱藏 | 建議暫時迴避 | 延遲執行 |
| ䷡ **大壯** | 000011 | 壯大強盛 | 資源充足 | 可增加並行度 |
| ䷢ **晉** | 000101 | 前進晉升 | 進展順利 | 加速推進 |
| ䷣ **明夷** | 101000 | 光明受損 | 外部干擾 | 切換備用資源 |
| ䷤ **家人** | 110101 | 家庭內部 | 內部 Agent 協作 | 內部通訊模式 |
| ䷥ **睽** | 101011 | 乖離對立 | Agent 間意見分歧 | 運行投票機制 |
| ䷦ **蹇** | 010100 | 行走艱難 | 執行緩慢 | 檢查並行度 |
| ䷧ **解** | 010100 | 解除緩解 | 瓶頸被解決 | 恢復速度 |
| ䷨ **損** | 110001 | 減少損失 | 成本超支 | 切換低成方案 |
| ䷩ **益** | 110001 | 增益獲利 | 超額完成 | 延伸交付 |
| ䷪ **夬** | 011111 | 決斷裁決 | 需要果斷決策 | 進入四爻強制決策 |
| ䷫ **姤** | 011111 | 相遇邂逅 | 發現意外有用資訊 | 收錄暫存記憶 |
| ䷬ **萃** | 000110 | 聚集薈萃 | 多源數據匯聚完成 | 啟動整合模式 |
| ䷭ **升** | 011000 | 上升成長 | Context 累積充足 | 進入深層推理 |
| ䷮ **困** | 010110 | 困窮窘迫 | 資源耗盡 / Rate Limit | 等待・降級 |
| ䷯ **井** | 010110 | 井水不腐 | 系統健康檢查 | 維護模式 |
| ䷰ **革** | 010111 | 改革變革 | 需要更換策略 | 大幅 pivot |
| ䷱ **鼎** | 011101 | 鼎立創新 | 可以嘗試新方法 | 啟用實驗模式 |
| ䷲ **震** | 100100 | 震動驚雷 | 突發事件 | 緊急處理 |
| ䷳ **艮** | 001001 | 靜止停止 | 需要暫停 | 強制休息 |
| ䷴ **漸** | 110100 | 循序漸進 | 按部就班執行 | 線性推進 |
| ䷵ **歸妹** | 110100 | 回歸結合 | 結果需要整合 | 合併模式 |
| ䷶ **豐** | 001101 | 豐盛富足 | 結果豐富 | 摘要提煉 |
| ䷷ **旅** | 001101 | 旅行漂泊 | Context 切換 | 跨工作區轉移 |
| ䷸ **巽** | 011011 | 順從滲入 | 需要逐步滲透 | 緩慢執行模式 |
| ䷹ **兌** | 011011 | 喜悅溝通 | 用戶滿意 | 可延伸交付 |
| ䷺ **渙** | 110010 | 渙散分離 | Context Window Overflow | 強制壓縮記憶 |
| ䷻ **節** | 110010 | 節制限制 | 需要控制 Token | Token Budget 模式 |
| ䷼ **中孚** | 110011 | 內心誠信 | 確認意圖一致 | 雙重驗證 |
| ䷽ **小過** | 001100 | 小有過失 | 小錯誤可忽略 | 繼續執行 |
| ䷾ **既濟** | 101101 | 已經完成 | 任務成功 | 準備上爻復盤 |
| ䷿ **未濟** | 101101 | 尚未完成 | 差最後一步 | Retry 四爻授權 |

### 3.4 動爻實際運作流程

```
正常流程：
  初爻 → 二爻 → 三爻 → 四爻 → 五爻 → 上爻
                                                ✅ 完成

異常流程（五爻 API Timeout）：
  初爻 → 二爻 → 三爻 → 四爻 → [五爻 ✗ API Error]
                                            │
                                    觸發動爻 flip bit5
                                    主卦變變卦：111111 → 111011（履卦）
                                            │
                                    降級二爻沙盒模擬 API
                                            │
                                    沙盒成功 → 推回五爻執行
                                            │
                                          上爻
                                                ✅ 完成

雙重異常流程（五爻 Timeout + 三爻拒絕降級）：
  初爻 → 二爻 → 三爻 ✗ [降級不安全]
                    │
             觸發三爻動爻 flip bit3
             變卦：111111 → 110111（小畜卦）
                    │
             返回初爻重構方法
                    │
             新 Plan 重新執行
```

---

## 四、錯綜互卦：Agent 嘅三維反思引擎

為咗防止 AI 產生幻覺或狹隘思維，Agent 喺 **三爻（反思）** 階段會強制啟動三維對抗運算。

### 4.1 三維反思模型

```
              ┌─────────────┐
              │  互卦（CoT）  │
              │  隱含動機分析 │
              └──────┬──────┘
                     │
    ┌────────┐       │       ┌──────────┐
    │ 錯卦    │──────┼──────│  綜卦      │
    │ Red Team │      │      │  用戶視角  │
    │ 對抗思維 │      │      │  換位思考  │
    └────────┘             └──────────┘
```

### 4.2 互卦：Hidden Chain-of-Thought

> **易經概念**：互卦係由主卦嘅 2-3-4 爻（內互卦）同 2-3-4 爻（外互卦）組合而成，揭示表面之下嘅隱藏意義。

**實現方式：**

Agent 喺三爻反思時，提取當前任務嘅「2-3-4 爻」（內互卦）同「3-4-5 爻」（外互卦），評估表面任務下嘅隱含動機。

**範例：**

```
用戶指令：「幫我寫一段抓取網站資料嘅 Python Script」

表面任務（主卦）：寫爬蟲程式
互卦分析（隱含動機）：
  - 內互卦（2-3-4）：用戶真正想要嘅可能係「數據分析」
  - 外互卦（3-4-5）：用戶可能冇諗過目標網站有反爬機制

→ Agent 建議：準備埋數據分析模組 + 提示反爬風險
```

### 4.3 錯卦：Red Teaming / 對抗視角

> **易經概念**：錯卦係將主卦嘅每個爻位徹底反轉（陰變陽、陽變陰），展示完全相反嘅視角。

**實現方式：**

Agent 喺三爻反思時，將當前 Prompt 徹底反轉：

> **「假設當前的假設全部都係錯嘅，呢個計劃會喺邊度徹底潰敗？」**

**輸出範例：**

```
主卦（Plan A）：用 requests 直接爬 target.com

錯卦（反轉思考）：
  - 假設 target.com 有嚴格嘅反爬機制？
  - 假設 IP 會被 ban？
  - 假設目標網站結構係 JavaScript render 嘅？
  - 假設用户嘅網絡環境唔允許直接出牆？

→ Agent 補救：增加 Selenium fallback 方案 + proxy 輪換建議
```

### 4.4 綜卦：User Perspective / 換位思考

> **易經概念**：綜卦係將主卦倒轉 180° 觀看，即係從相反方向審視同一個局。

**實現方式：**

Agent 喺三爻反思時，企喺最終用戶嘅角度審視：

> **「終端使用者接到呢個輸出時，體驗係咪順暢？」**

**範例：**

```
主卦（Plan A）：直接輸出 JSON 格式嘅分析報告

綜卦（用戶視角）：
  - 用戶係非技術背景，睇 JSON 會好困惑
  - 用戶想得到嘅係結論，唔係 raw data
  - 用戶可能想 share 俾同事睇 → 需要可讀性高嘅格式

→ Agent 補救：改輸出為 Markdown 表格 + 摘要
```

### 4.5 三維反思嘅 Python 實現

```python
from enum import Enum
from typing import List, Optional


class YaoPosition(Enum):
    FIRST_HIDDEN = 1   # 初爻
    SECOND_FIELD = 2   # 二爻
    THIRD_ALERT = 3    # 三爻
    FOURTH_LEAP = 4    # 四爻
    FIFTH_FLYING = 5   # 五爻
    SIXTH_REGRET = 6   # 上爻


def generate_interlocking_trigram(hexagram_code: str) -> dict:
    """
    互卦：提取 2-3-4 + 3-4-5 爻 = 隱含動機
    """
    bits = list(hexagram_code)
    inner_trigram = bits[1:4]   # 2-3-4 爻 → 內互卦（隱藏動機）
    outer_trigram = bits[2:5]   # 3-4-5 爻 → 外互卦（隱藏風險）

    # 查表解析 trigram 意義
    hidden_intent = lookup_trigram_meaning(inner_trigram)
    hidden_risk = lookup_trigram_meaning(outer_trigram)

    return {
        "deeper_goal": hidden_intent,
        "blind_spot": hidden_risk
    }


def generate_opposite_hexagram(hexagram_code: str) -> str:
    """
    錯卦：徹底反轉所有爻位
    """
    return "".join(
        "0" if bit == "1" else "1"
        for bit in hexagram_code
    )


def generate_reversed_hexagram(hexagram_code: str) -> str:
    """
    綜卦：將卦象倒轉 180°
    """
    return hexagram_code[::-1]


TRIGRAM_MEANINGS = {
    "111": ("乾", "天行健 — 主動、創造"),
    "000": ("坤", "地勢坤 — 被動、承接"),
    "010": ("坎", "水洊至 — 危險、深淵"),
    "101": ("離", "明兩作 — 光明、附麗"),
    "001": ("艮", "兼山艮 — 靜止、阻礙"),
    "110": ("兌", "麗澤兌 — 喜悅、溝通"),
    "100": ("震", "洊雷震 — 震動、突發"),
    "011": ("巽", "隨風巽 — 順從、滲入"),
}


def lookup_trigram_meaning(bits: List[str]) -> str:
    code = "".join(bits)
    return TRIGRAM_MEANINGS.get(code, ("未知", "無法解析"))
```

---

## 五、系統架構實作（Python Agent State）

以下係完整嘅 Agent 狀態機實作，可以作為開發基礎：

### 5.1 核心狀態類別

```python
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class YaoPosition(Enum):
    FIRST_HIDDEN = 1   # 潛龍勿用：脈絡構建
    SECOND_FIELD = 2   # 見龍在田：沙盒試探
    THIRD_ALERT = 3    # 終日乾乾：風險反思
    FOURTH_LEAP = 4    # 或躍在淵：授權決策
    FIFTH_FLYING = 5   # 飛龍在天：主控執行
    SIXTH_REGRET = 6   # 亢龍有悔：記憶復盤


class AuthorizationLevel(Enum):
    AUTO = 0           # 完全自動
    NOTIFY = 1         # 通知人類
    CONFIRM = 2        # 必需人類確認
    HUMAN_EXEC = 3     # 人類執行


class TaskGraph(BaseModel):
    """初爻輸出：結構化任務圖"""
    task_id: str
    original_intent: str
    constraints: List[str] = []
    success_criteria: List[str] = []
    forbidden_actions: List[str] = []
    estimated_complexity: str = "medium"  # easy / medium / hard


class FeasibilityReport(BaseModel):
    """二爻輸出：可行性報告"""
    plan_a_description: str
    key_apis: List[str] = []
    estimated_tokens: int = 0
    known_risks: List[str] = []
    fallback_plans: List[str] = []


class SafetyReport(BaseModel):
    """三爻輸出：安全審查報告"""
    passed: bool = False
    issues: List[str] = []
    recommendations: List[str] = []
    requires_human: bool = False


class HexagramTransition(BaseModel):
    """動爻變卦結果"""
    original_code: str
    new_code: str
    moving_yaos: List[int]
    transition_name: str
    strategy: str


class YiJingAgentState(BaseModel):
    """核心 Agent 狀態機"""

    # 當前狀態
    current_yao: YaoPosition = YaoPosition.FIRST_HIDDEN

    # 卦象狀態
    hexagram_code: str = Field(default="111111", description="當前主卦（6-bit 狀態碼）")
    active_moving_yaos: List[int] = Field(default_factory=list, description="當前觸發嘅動爻位置")
    hexagram_history: List[HexagramTransition] = Field(default_factory=list)

    # 任務上下文
    task_graph: Optional[TaskGraph] = None
    feasibility_report: Optional[FeasibilityReport] = None
    safety_report: Optional[SafetyReport] = None

    # 記憶
    short_term_memory: Dict[str, Any] = Field(default_factory=dict)
    long_term_memory: List[Dict[str, Any]] = Field(default_factory=list)

    # 授權
    authorization_level: AuthorizationLevel = AuthorizationLevel.NOTIFY
    human_confirmed: Optional[bool] = None

    # 元數據
    session_start: datetime = Field(default_factory=datetime.now)
    session_id: str = ""
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)

    def step_forward(self) -> "YiJingAgentState":
        """推進至下一爻時位"""
        if self.current_yao.value < 6:
            self.current_yao = YaoPosition(self.current_yao.value + 1)
        self._log(f"step_forward → {self.current_yao.name}")
        return self

    def step_backward(self, target: YaoPosition) -> "YiJingAgentState":
        """回溯至指定爻位（用於動爻降級）"""
        self.current_yao = target
        self._log(f"step_backward → {target.name}")
        return self

    def trigger_moving_yao(self, yao_index: int) -> HexagramTransition:
        """
        當某層發生異常，引發動爻，翻轉 bit 計算變卦。
        yao_index: 1-based 爻位（1=初爻, ..., 6=上爻）
        """
        old_code = self.hexagram_code
        code_list = list(self.hexagram_code)

        # XOR 翻轉：0↔1
        code_list[yao_index - 1] = "0" if code_list[yao_index - 1] == "1" else "1"
        new_code = "".join(code_list)

        transition = HexagramTransition(
            original_code=old_code,
            new_code=new_code,
            moving_yaos=[yao_index],
            transition_name=get_hexagram_name(new_code),
            strategy=get_strategy_for_hexagram(new_code),
        )

        self.hexagram_code = new_code
        self.active_moving_yaos.append(yao_index)
        self.hexagram_history.append(transition)
        self._log(f"moving_yao bit{yao_index}: {old_code} → {new_code} ({transition.transition_name})")

        return transition

    def _log(self, message: str):
        """記錄執行日誌"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "yao": self.current_yao.name,
            "hexagram": self.hexagram_code,
            "message": message,
        })


# ===== 64 卦名稱對應表 =====

HEXAGRAM_NAMES = {
    "111111": ("䷀", "乾為天"),
    "000000": ("䷁", "坤為地"),
    "100010": ("䷂", "水雷屯"),
    "010001": ("䷃", "山水蒙"),
    "010111": ("䷄", "水天需"),
    "111010": ("䷅", "天水訟"),
    "000010": ("䷆", "地水師"),
    "010000": ("䷇", "水地比"),
    "110111": ("䷈", "風天小畜"),
    "111011": ("䷉", "天澤履"),
    "111000": ("䷊", "地天泰"),
    "000111": ("䷋", "天地否"),
    "111101": ("䷌", "天火同人"),
    "101111": ("䷍", "火天大有"),
    "001000": ("䷎", "地山謙"),
    "000100": ("䷏", "雷地豫"),
    "100110": ("䷐", "澤雷隨"),
    "011001": ("䷑", "山風蠱"),
    "000011": ("䷒", "地澤臨"),
    "110000": ("䷓", "風地觀"),
    "100101": ("䷔", "火雷噬嗑"),
    "101001": ("䷕", "山火賁"),
    "100000": ("䷖", "山地剝"),
    "000001": ("䷗", "地雷復"),
    "111001": ("䷘", "天雷无妄"),
    "100111": ("䷙", "山天大畜"),
    "100001": ("䷚", "山雷頤"),
    "011110": ("䷛", "澤風大過"),
    "010010": ("䷜", "坎為水"),
    "101101": ("䷝", "離為火"),
    "001110": ("䷞", "澤山咸"),
    "011100": ("䷟", "雷風恆"),
    "001111": ("䷠", "天山遯"),
    "000011": ("䷡", "雷天大壯"),
    "000101": ("䷢", "火地晉"),
    "101000": ("䷣", "地火明夷"),
    "110101": ("䷤", "風火家人"),
    "101011": ("䷥", "火澤睽"),
    "010100": ("䷦", "水山蹇"),
    "001010": ("䷧", "雷水解"),
    "110001": ("䷨", "山澤損"),
    "100011": ("䷩", "風雷益"),
    "011111": ("䷪", "澤天夬"),
    "111110": ("䷫", "天風姤"),
    "000110": ("䷬", "澤地萃"),
    "011000": ("䷭", "地風升"),
    "010110": ("䷮", "澤水困"),
    "011010": ("䷯", "水風井"),
    "011101": ("䷰", "澤火革"),
    "101110": ("䷱", "火風鼎"),
    "100100": ("䷲", "震為雷"),
    "001001": ("䷳", "艮為山"),
    "110100": ("䷴", "風山漸"),
    "001011": ("䷵", "雷澤歸妹"),
    "001101": ("䷶", "雷火豐"),
    "101100": ("䷷", "火山旅"),
    "011011": ("䷸", "巽為風"),
    "110110": ("䷹", "兌為澤"),
    "110010": ("䷺", "風水渙"),
    "010011": ("䷻", "水澤節"),
    "110011": ("䷼", "風澤中孚"),
    "001100": ("䷽", "雷山小過"),
    "101101": ("䷾", "水火既濟"),
    "010101": ("䷿", "火水未濟"),
}


def get_hexagram_name(code: str) -> str:
    symbol, name = HEXAGRAM_NAMES.get(code, ("䷀", "未知"))
    return f"{symbol} {name}"


def get_strategy_for_hexagram(code: str) -> str:
    """根據卦象返回對應策略"""
    strategies = {
        "111111": "Happy Path — 繼續執行",
        "000000": "緊急停機 — 人類接管",
        "111011": "降級策略 — 五爻出問題，用二爻沙盒代替",
        "110111": "小畜 — 部分成果可用，先交付再修復",
        "111000": "泰 — 人類反饋良好，推進",
        "000111": "否 — 人類反饋差，重新理解",
        "010010": "坎 — 反覆失敗，人類接管",
        "101101": "離 — 需要更多資訊源",
        "110010": "渙 — Context Overflow，強制壓縮",
        # ... 可以延伸到 64 卦完整對應
    }
    return strategies.get(code, "通用降級 — 回到初爻重新規劃")
```

### 5.2 完整生命週期執行器

```python
class YiJingAgentExecutor:
    """
    六爻 Agent 執行器 — 控制完整嘅生命週期
    """

    def __init__(self):
        self.state = YiJingAgentState()
        self.max_retries = 3

    async def execute(self, user_input: str) -> Dict[str, Any]:
        """執行一次完整嘅六爻任務生命週期"""

        # ── 初爻：潛龍勿用 ──
        self.state.current_yao = YaoPosition.FIRST_HIDDEN
        task_graph = await self._parse_intent(user_input)
        self.state.task_graph = task_graph

        if not task_graph:
            return self._fail("無法解析用戶意圖")

        # ── 二爻：見龍在田 ──
        self.state.step_forward()
        feasibility = await self._sandbox_prototype(task_graph)
        self.state.feasibility_report = feasibility

        # ── 三爻：終日乾乾 ──
        self.state.step_forward()
        safety = await self._reflexion_gate(task_graph, feasibility)
        self.state.safety_report = safety

        # 三維反思
        reflection = await self._three_dimensional_reflection()
        if reflection.requires_changes:
            # 內部修正迴圈
            feasibility = await self._revise_plan(reflection)
            self.state.feasibility_report = feasibility

        if not safety.passed and safety.requires_human:
            # 觸發動爻 → 變卦 → 要求人類介入
            transition = self.state.trigger_moving_yao(3)
            return self._request_human_intervention(transition)

        # ── 四爻：或躍在淵 ──
        self.state.step_forward()
        if self.state.authorization_level == AuthorizationLevel.CONFIRM:
            authorization = await self._request_authorization()
            if not authorization:
                return self._fail("人類拒絕授權")

        # ── 五爻：飛龍在天 ──
        self.state.step_forward()
        try:
            result = await self._execute_master(feasibility)
        except Exception as e:
            # 觸發動爻 → 變卦 → 降級
            transition = self.state.trigger_moving_yao(5)
            result = await self._fallback_execution(transition, feasibility)

        # ── 上爻：亢龍有悔 ──
        self.state.step_forward()
        await self._memory_compression(result)

        return {
            "status": "success",
            "result": result,
            "hexagram_history": [
                t.dict() for t in self.state.hexagram_history
            ],
            "execution_log": self.state.execution_log,
        }

    async def _parse_intent(self, user_input: str) -> TaskGraph:
        """初爻：純理解，唔准郁"""
        # 只做 NLP 解析，唔 call 任何 API / 工具
        return TaskGraph(
            task_id="auto",
            original_intent=user_input,
        )

    async def _sandbox_prototype(self, task: TaskGraph) -> FeasibilityReport:
        """二爻：沙盒試探"""
        # 喺隔離環境測試
        return FeasibilityReport(
            plan_a_description="可行性分析完成",
        )

    async def _reflexion_gate(self, task: TaskGraph, report: FeasibilityReport) -> SafetyReport:
        """三爻：風險審查"""
        # 執行安全檢查 + 三維反思
        return SafetyReport(passed=True)

    async def _three_dimensional_reflection(self) -> dict:
        """三維反思引擎：互卦・錯卦・綜卦"""
        return {"requires_changes": False}

    async def _execute_master(self, report: FeasibilityReport) -> Any:
        """五爻：全力執行"""
        # 調用 API、並行處理、整合
        return {"output": "task result"}

    async def _fallback_execution(self, transition: HexagramTransition, report: FeasibilityReport) -> Any:
        """降級執行"""
        # 根據變卦策略執行 Plan B
        return {"output": "fallback result", "fallback": True}

    async def _memory_compression(self, result: Any):
        """上爻：記憶壓縮"""
        # 清理臨時 data，經驗寫入 LTM
        pass

    def _fail(self, reason: str) -> Dict[str, Any]:
        return {"status": "failed", "reason": reason}
```

---

## 六、場景實戰演練

### 6.1 場景一：網頁數據分析

**用戶輸入：** 「幫我分析呢個網站嘅產品定價策略」

| 爻位 | Agent 行為 | 輸出 |
|:----|:----------|:-----|
| 初爻 | 解析意圖 → 確認目標網站 URL → 建立 Task Graph | `task_graph` |
| 二爻 | 沙盒中測試 `requests` 是否可存取目標網站 | `feasibility_report` |
| 三爻 | 三維反思：網站有反爬？需要預算？邏輯一致？ | ✅ 通過 |
| 四爻 | 授權級別 = NOTIFY（通知用戶即可） | ✅ 自動 |
| 五爻 | 執行爬取 → 分析定價 → 生成對比表格 | 📊 核心交付 |
| 上爻 | 壓縮經驗：「requests 夠用，無需 Selenium」 | 💾 LTM 寫入 |

### 6.2 場景二：多語言翻譯

**用戶輸入：** 「將呢份文件翻譯成繁體中文、日文同韓文」

| 爻位 | Agent 行為 | 輸出 |
|:----|:----------|:-----|
| 初爻 | 解析 → 3 個目標語言 → 文件長度評估 | `task_graph` |
| 二爻 | 沙盒測試：翻譯 API 可用性 + Token 估算 | ✅ 可行 |
| 三爻 | 反思：翻譯質量？術語一致性？ | 附加「術語表」建議 |
| 四爻 | 評估 Token 成本較高 → Level 1 通知用戶 | ✅ 用戶確認 |
| 五爻 | **並行派發 3 個 Worker Agents** → 同時翻譯 | 🌐 三語輸出 |
| 上爻 | 壓縮經驗：「並行翻譯節省 60% 時間」 | 💾 LTM |

### 6.3 場景三：異常容錯

**用戶輸入：** 「幫我生成一份市場競爭分析報告」

**執行過程中五爻 API Timeout：**

```
正常主卦：111111（乾為天）

五爻分析 API 調用失敗 → 觸發動爻 flip bit5

變卦：111011（天澤履卦）

履卦策略：「履行謹慎，執行層出問題 → 降級二爻沙盒」

系統行為：
1. 停用外部 API
2. 降級到二爻沙盒，用本地模型 + 已有數據做模擬分析
3. 沙盒完成後推回五爻
4. 五爻用沙盒結果繼續執行

最終交付：分析報告（附註：「部分數據基於模擬分析」）
```

---

## 七、系統優勢同未來方向

### 7.1 相比傳統 Agent 框架嘅核心優勢

| 維度 | 傳統 Agent | 六爻 Agent |
|:----|:----------|:----------|
| 🎯 **目標一致性** | 容易飄移 | 初爻強制定錨 + 三爻反覆確認 |
| ⚡ **執行節奏** | 一股腦衝 | 潛→試→惕→躍→飛→悔 六段節奏 |
| 🛡️ **容錯能力** | try-except 局部處理 | 動爻 XOR 全局變卦切換 |
| 🧠 **反思深度** | 表面檢查 | 三維反思（互卦・錯卦・綜卦） |
| 📦 **記憶管理** | 冇系統化 | 上爻強制壓縮 + LTM 寫入 |
| 🔄 **可復原性** | 崩潰即重來 | 局部降級 + 卦象指導 recovery |

### 7.2 已知限制

1. **64 卦對應表需要人工維護** — 初期可以逐個 case 累積
2. **四爻 HITL 會減慢執行速度** — 但係高風險任務嘅必要成本
3. **初爻嘅 Task Graph 品質取決於 LLM 能力** — 意圖理解錯誤會 cascading
4. **三維反思額外消耗 Token** — 約增加 15-30% 成本

### 7.3 未來發展方向

- **64 卦 Failure Mode Database** — 累積每個卦象對應嘅修復策略，成為 Agent 嘅「免疫系統」
- **Auto Hexagram Learning** — Agent 自動學習邊啲卦象組合對應邊種異常 pattern
- **多 Agent 六爻協作** — 每個 Agent 有自己的六爻生命週期，之間互相用卦象通訊
- **卦象 Dashboard** — 即時顯示 Agent 嘅當前卦象同歷史變卦軌跡

---

## 八、結語

呢個架構嘅核心唔係技術創新，而係 **哲學層面嘅 reframing**。

《易經》講嘅「時位」概念 — 每一個位置都有最適合嘅行為，唔可以超越本分 — 正好解決咗現代 AI Agent 最缺嘅嘢：**知道幾時唔應該做嘢**。

而變卦機制提供嘅唔係簡單嘅 try-except，而係一個 **有意義嘅失敗分類系統** — 唔同嘅卦象指向唔同嘅根因，俾 Agent 一個「知道自己衰咩」嘅框架。

> **「唔識時機嘅 Agent，用力量對抗命運；**
> **識得時機嘅 Agent，用智慧四兩撥千斤；**
> **而真正嘅高手 Agent，係嗰個能夠喺最壞嘅環境入面，等到屬於自己嘅嗰一陣南風嘅 Agent。」**

---

*本文檔基於主人 yayafu 與 Gemini 嘅對話蒸餾，由 Orchestrator Nova 整理成正式設計文檔。*
*2026年7月27日*
