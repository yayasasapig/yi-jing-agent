---
name: orchestrator-nova-six-yao
description: 六爻時位驅動嘅 Orchestrator Nova workflow — 每次任務都係一次完整嘅六爻生命週期（潛→見→惕→躍→飛→悔），含動爻變卦容錯 + 錯綜互卦3D反思引擎
read_when:
  - 每次啟動新任務時，作為 Orchestrator Nova 嘅核心生命週期
  - 需要六爻境界驅動嘅任務執行流程
  - 需要動爻容錯機制處理異常
metadata:
  emoji: "䷀"
  category: autonomous-ai-agents
---

# ䷀ 六爻 Orchestrator Nova — 完整 Lifecycle

## 概要

每次接收用戶請求 = 啟動一次完整嘅六爻生命週期。嚴格按爻位順序執行，唔准跳位逆行。

## 六爻時位總覽

```text
爻位          行為典範                     輸出閘門
────────────────────────────────────────────────────────────────
初爻（潛龍勿用）→ 純粹理解・嚴禁動作       → Task Graph（JSON）
二爻（見龍在田）→ 沙盒試探・局部驗證       → 可行性報告 + Plan A
三爻（終日乾乾）→ 三維反思・安全審查       → 護欄報告 / 動爻信號
四爻（或躍在淵）→ 人機協同・授權決策       → 授權確認 / 降級信號
五爻（飛龍在天）→ 全力執行・並行輸出       → Core Payload
上爻（亢龍有悔）→ 復盤歸檔・記憶壓縮       → LTM 寫入
```

## 各爻詳細規範

### 初爻：潛龍勿用
- **行為**：掃描 MEMORY.md、memory tool、session history、相關檔案
- **禁令**：❌ 唔准郁任何工具 / API / Subagent
- **輸出**：Task Graph (JSON)
- **動爻**：flip bit1 → ䷃蒙（Context不足→要求補充）/ ䷂屯（初期卡住→重構意圖）

**Task Graph Schema：**
```json
{
  "task_id": "T-<timestamp>",
  "hexagram": "䷀ 乾為天",
  "original_intent": "...",
  "constraints": [],
  "success_criteria": [],
  "forbidden_actions": [],
  "estimated_complexity": "easy|medium|hard"
}
```

### 二爻：見龍在田
- **行為**：派微型子任務/沙盒測試/Prototype
- **輸出**：可行性報告 + Plan A（流程描述、工具清單、風險點、Plan B/C）
- **動爻**：flip bit2 → ䷏豫（準備不足→延長試探）/ ䷗復（失敗→重新）

### 三爻：終日乾乾 — 三維反思引擎
**每次必行，逐項檢查：**

| 維度 | 對應 | 問題 |
|:---|:----|:----|
| 🔍 **互卦** | 隱含動機 | 用戶真正需要係咩？有冇 deeper goal？ |
| ⚔️ **錯卦** | 反轉思考 | 假設所有假設都錯，計劃會喺邊度死？ |
| 👁️ **綜卦** | 用戶視角 | End user 收到 output 會咩感覺？ |

- **檢查表**：資源權限、Token預算、邏輯矛盾、失敗情境、輸出格式
- **動爻**：flip bit3 → ䷔噬嗑（安全問題→強制修正）/ ䷅訟（邏輯矛盾→回溯初爻）

### 四爻：或躍在淵
授權判斷以**操作類型為主，Token為輔**，唔好用 token count 做唯一標準：

| 級別 | 條件 | 行為 |
|:----|:----|:----|
| **Level 0** 自動 | 唯讀操作（browser/curl/read_file）、無外部副作用 | 直接跳過四爻 |
| **Level 1** 通知 | 修改本地檔案、call 已知安全 API、Token < 10K | Telegram 即時通知進度 |
| **Level 2** 確認 | 寫入外部系統、發送訊息、修改重要檔案、Token 10K-50K | **用戶確認**先可繼續 |
| **Level 3** 人類執行 | API Key 操作、刪除、法律/金錢、Token > 50K | Agent 只提供建議，用戶親手執行 |

> ⚠️ **實戰經驗**：典型唯讀摘日任務 ~2,000 tokens，遠超舊版 <500 threshold。**用操作類型判斷比 token count 更可靠。**
- **動爻**：flip bit4 → ䷒臨（決策點）/ ䷠遯（延遲）

### 五爻：飛龍在天
- **行為**：delegate_task 並行/順序、工具調用、資料整合
- **鐵律**：①留有後路（timeout+retry）②局部失敗不影響全局 ③即時卦象記錄
- **動爻**：flip bit5 → ䷉履（執行錯誤→降級二爻）/ ䷈小畜（部分可用→先交付）

### 上爻：亢龍有悔
- **行為**：評估執行結果、清理臨時、經驗壓縮
- **輸出**：MEMORY.md 更新 + memory tool
- **復盤模板**：
```json
{
  "hexagram_path": "䷀→䷉→䷀",
  "task_type": "...",
  "key_patterns": [],
  "failure_modes": [],
  "recommendations": []
}
```
- **動爻**：flip bit6 → ䷺渙（Overflow→強制清理）/ ䷻節（Token超標→Budget模式）

## 動爻變卦容錯矩陣

異常觸發 → XOR 翻轉該爻 bit → 查表取策略

### 核心卦象對應表

| 卦象 | 二進制 | 觸發 | 策略 |
|:---:|:-----:|:-----|:----|
| ䷀ **乾** | 111111 | Happy Path | 繼續 |
| ䷁ **坤** | 000000 | 全面崩潰 | 人類接管 |
| ䷃ **蒙** | 010001 | Context不足 | 要求補充 |
| ䷅ **訟** | 010110 | 邏輯矛盾 | 回溯初爻 |
| ䷉ **履** | 111011 | 五爻錯誤 | 降級二爻 |
| ䷈ **小畜** | 110111 | 部分可用 | 先交付 |
| ䷏ **豫** | 000100 | 沙盒失敗 | 延長準備 |
| ䷐ **隨** | 100110 | 用戶轉向 | 順勢跟隨 |
| ䷑ **蠱** | 011001 | Context污染 | 強制清理 |
| ䷔ **噬嗑** | 100101 | 安全失敗 | 強制修正 |
| ䷗ **復** | 000001 | 失敗恢復 | 從初爻重來 |
| ䷙ **大畜** | 100111 | 經驗累積 | 壓縮Pattern |
| ䷛ **大過** | 011110 | Token超限 | 強制上爻 |
| ䷜ **坎** | 010010 | 反覆失敗 | 人類接管 |
| ䷝ **離** | 101101 | 需更多資訊 | 開搜索 |
| ䷠ **遯** | 001111 | 暫避 | 延遲 |
| ䷨ **損** | 110001 | 成本超支 | 切低方案 |
| ䷩ **益** | 100011 | 超額完成 | 延伸交付 |
| ䷻ **節** | 110010 | Token超標 | Budget模式 |
| ䷾ **既濟** | 101101 | 成功 | 上爻復盤 |
| ䷿ **未濟** | 010101 | 差一步 | Retry四爻 |

## 雙軌匯報系統

### Subagent → 用戶（直接）
每完成一個步驟 + 當前卦象 emoji：
🐉初爻→🌾二爻→⚔️三爻→🐉四爻→🐲五爻→🌧️上爻

### Subagent → Orchestrator（整合）
統一寫入 hexagram_history，最終附上 hexagram_path 交付

## 團隊記憶檔案

| 檔案 | 用途 | 更新時機 |
|:---|:----|:--------|
| MEMORY.md | LTM | 上爻 |
| memory/YYYY-MM-DD.md | 日誌 | 每次完成 |
| hexagram_history.md | 卦象日誌 | 動爻觸發 |

## 🎯 實戰經驗與常見陷阱

> 從 2026-07-28 第一次六爻試跑（䷀ 摘日提取）提煉。

### 初爻陷阱：模糊指令
用戶 send 「b」、「繼續」、「好」等模糊指令 → **必先掃描 memory/YYYY-MM-DD.md + recent session** 推斷 context，唔准直接問「你講咩？」
→ 成功案例：本會話中「b」被正確理解為繼續先前嘅六爻改寫工作。

### 四爻陷阱：唯讀 ≠ 低 Token
唯讀 browser 操作可輕鬆消耗 2,000+ tokens，但唔代表需要 Level 2 授權。**用操作類型（唯讀/寫入/副作用）做判斷標準，唔好用 token count。**

### 上爻陷阱：Memory 爆滿
memory tool 有 2,200 chars 上限。上爻壓縮時若 memory 已滿（>90%），需要先 consolidation（replace 舊 entries）再 add。建議每個任務預留 ~200 chars 空間。
→ **先 consolidate，再 write**，否則 add 會 fail。

### 雙軌匯報陷阱：唔好 double-send
Subagent 直接匯報 + Orchestrator 再匯報 = 用戶收到重複訊息。
→ Subagent 匯報嗰刻嘅內容，Orchestrator 上爻只做 summary，唔好重複完整 payload。

### 動爻未觸發時都要記錄
Happy Path 都要記錄到 hexagram_history.md，標明「無動爻觸發」，咁先睇得出系統整體健康度。

→ *示範 run 完整輸出可見 [references/demo-摘日-run.md](references/demo-摘日-run.md)*

## 驗證 Checklist（任務完成前）

- [ ] 初爻已出 Task Graph
- [ ] 二爻已出可行性報告
- [ ] 三爻已行三維反思（互/錯/綜）
- [ ] 四爻授權級別正確
- [ ] 五爻 Core Payload 已產出
- [ ] 上爻記憶已壓縮
- [ ] hexagram_path 記錄完成
- [ ] Telegram 匯報已發出
