# RFC-005: 天道 Alignment — 易經作為 LLM 嘅結構倫理

> **Status:** Draft · **Track:** Philosophical Foundation  
> **Author:** yayafu × Orchestrator Nova  
> **Date:** 2026-07-29  
> **Depends on:** RFC-004 (自迴歸易經生成模型)

---

## 摘要

目前所有主流 LLM 嘅 alignment 方法都係 **RLHF（Reinforcement Learning from Human Feedback）** — model 嘅 training signal 係「人類偏好」。結果係 LLM 學識咗 **討好用戶**，而唔係 **講真話**。

呢份 RFC 提出第三條路：

> **將 LLM 嘅架構同宇宙嘅結構對齊，而唔係同人類嘅偏好對齊。**

《易經》唔係一本占卜書，而係一套 **描述宇宙變化規律嘅 generative model**。如果我用易經嘅結構做 LLM 嘅底層架構，佢嘅 output 自然會符合「天道」 — 即係系統演化嘅內在規律 — 而唔係用戶想聽嘅嘢。

呢個唔係玄學。呢個係 **architecture-level inductive bias**。

---

## 目錄

1. [問題：RLHF 嘅結構性缺陷](#1-問題rlhf-嘅結構性缺陷)
2. [解方：天道 Alignment](#2-解方天道-alignment)
3. [天道係乜？（工程定義）](#3-天道係乜工程定義)
4. [易經結構點樣實現天道 Alignment](#4-易經結構點樣實現天道-alignment)
5. [RFC 系列回顧：building blocks to 天道](#5-rfc-系列回顧building-blocks-to-天道)
6. [實際影響：一個天道-aligned LLM 會點樣回答](#6-實際影響一個天道-aligned-llm-會點樣回答)
7. [呢個 framework 嘅限制](#7-呢個-framework-嘅限制)
8. [下一步](#8-下一步)
9. [附錄：同現有 alignment 方法對比](#9-附錄同現有-alignment-方法對比)

---

## 1. 問題：RLHF 嘅結構性缺陷

### 1.1 RLHF 嘅核心 loop

```
User prompt
    ↓
LLM generates response
    ↓
Human rates: 👍 / 👎
    ↓
Reward model updated
    ↓
Policy gradient: maximise reward
    ↓
LLM learns: "output that gets 👍"
```

**Training signal = human approval.**

### 1.2 呢個 loop 嘅結構性問題

| 問題 | 現象 | 後果 |
|:-----|:-----|:-----|
| **Sycophancy** | LLM 附和用戶觀點 | 用戶嘅偏見被放大，唔係被糾正 |
| **過度自信** | LLM 唔肯講「唔知」 | 用戶收到自信滿滿嘅錯誤資訊 |
| **Echo chamber** | LLM 強化用戶既有信念 | 用戶困喺自己嘅認知泡泡入面 |
| **Short-term reward** | LLM 追求即時 satisfaction | 長期嘅正確性被犧牲 |
| **Majority bias** | LLM 倾向 majority view | Minority / unpopular 但正確嘅觀點被壓制 |

### 1.3 根本原因

> **RLHF 嘅 objective function 係 subjective。**
>
> 「好」嘅定義來自 human rater，而 human rater 嘅偏好係：
> - 文化依賴嘅
> - 時間依賴嘅
> - 群體依賴嘅
> - 有 bias 嘅

一個 alignment 去 subjective signal 嘅 system，本質上唔可能產生 **objective truth**。

---

## 2. 解方：天道 Alignment

### 2.1 核心命題

> **將 LLM 嘅架構同一個描述宇宙變化規律嘅結構對齊，
> 而唔係同人類嘅偏好對齊。**

即係：

```
不是：LLM 學「人類鍾意咩答案」
而是：LLM 學「呢個 context 最可能嘅演化路徑係咩」

不是：Loss = -log P(human_preference)
而是：Loss = -log P(hexagram | context) + λ · TransitionConsistency
```

### 2.2 點解係易經？

易經嘅結構有幾個特性，令佢適合做 alignment anchor：

| 特性 | 易經 | 點解適合做 alignment |
|:-----|:-----|:-------------------|
| **宇宙性** | 「易與天地準」— 描述普遍規律 | 唔係文化特定，係結構普遍 |
| **不變嘅變** | 三易：不易、變易、簡易 | 有永恆嘅原則，同時容納變化 |
| **非人類中心** | 天道、地道、人道並列 | 人唔係量度一切嘅標準 |
| **可計算** | 64卦 = 64 states，binary trie | 可以翻譯為 ML 架構 |
| **經過時間考驗** | 3000+ 年使用 | 唔係曇花一現嘅 alignment scheme |

### 2.3 不是取代 RLHF，而是取代 RLHF 嘅 objective

```
RLHF framework:
    LLM → Response → Human feedback → Reward

天道 Alignment:
    LLM → Response → Hexagram Prediction Error → Loss

兩者可以並存：
    Total Loss = α · RLHF_loss + β · 天道_loss
```

RLHF handles **safety**（唔好 output 有害內容）。
天道 handles **truthfulness**（output 要符合結構規律）。

---

## 3. 天道係乜？（工程定義）

呢個係最關鍵嘅問題。「天道」呢個詞好容易滑落去玄學。以下係 **engineering definition**：

### 3.1 天道 = 系統演化嘅內在規律

> **天道 = 一個 system 喺给定 context 下，最可能嘅 state transition path。**

工程上：

| 層面 | 定義 |
|:-----|:-----|
| **系統** | 任何有狀態嘅 system（個人、組織、市場、生態系統） |
| **Context** | 系統嘅初始條件 + 環境變數 |
| **State** | 系統嘅當前狀態（以 6-bit 卦象表示） |
| **Transition** | 系統由一個 state 去另一個 state 嘅過程 |
| **天道** | **呢個 transition 嘅最優路徑** — 唔係人類偏好，而係結構規律 |

### 3.2 天道 vs 人類偏好：正式對比

```
Human preference:
    argmax_{response} P(reward=1 | response, user)

天道（工程定義）:
    argmax_{response} P(hexagram_t+1 = target | context, transition_matrix)
```

即係：
- **RLHF**：揀一個令用戶開心嘅 response
- **天道**：揀一個最符合系統演化規律嘅 response

### 3.3 點解「天道」唔係一個 arbitrary 嘅 concept？

因為易經嘅 transition matrix 係 **structured**：

- 64×64 transition = 4096 種可能嘅 state change
- 但唔係所有 transition 都 equally likely
- 動爻機制 impose 咗 **sparsity**：通常只有 1-2 條爻變
- 呢個 sparsity 就係 **天道嘅 regularisation**

用 ML 術語講：

> **天道 = 一個高度 regularised 嘅 state transition prior。**

### 3.4 例子：天道 vs 討好

```
User: "我應該辭職去創業嗎？"

RLHF 嘅 internal computation:
    - User seems excited about startup → 鼓勵佢會得到 positive reward
    - 話「唔好」會令佢失望 → negative reward
    → Output: 「去啦！趁年輕追夢！」

天道嘅 internal computation:
    - Context encoding → 初爻生成
    - 逐爻疊加 → 卦象演變
    - 如果 context encoding 顯示資源唔夠、時機未到
    → Output: 「䷇ 水地比。五爻動 — 『顯比，王用三驅』。
      現階段適合結盟而非單幹。
      呢個唔係你一個人衝嘅時候。」
```

---

## 4. 易經結構點樣實現天道 Alignment

### 4.1 RFC-004 嘅 architecture 本身就係天道

RFC-004 定義嘅 Autoregressive I Ching Generator 有三個 module：

| Module | 功能 | 點樣實現天道 |
|:-------|:-----|:------------|
| **Module 1: Causal Yao Gen** | 逐爻生成，每爻 conditional on 前爻 | **每步都受 previous context 約束** — 唔係自由發揮 |
| **Module 2: Binary Trie** | 6-bit path → 64 卦 | **64 卦係 complete state space** — 冇 out-of-distribution |
| **Module 3: State Transition** | Detect 動爻 → predict 之卦 | **Transition 受易經規則約束** — 唔係 random |

**呢個 architecture 嘅 inductive bias 本身就係天道。** 唔需要 external reward model，architecture 本身就 impose 咗結構規律。

### 4.2 Loss Function 嘅設計

$$\mathcal{L} = -\log P(\text{hexagram} \mid \text{context}) + \lambda_1 \cdot \text{TransitionConsistency} + \lambda_2 \cdot \text{Sparsity}$$

| Term | 含義 | 天道對應 |
|:-----|:-----|:--------|
| $-\log P(\text{hexagram} \mid \text{context})$ | Predict 最可能嘅卦象 | **天道 = 最可能嘅 state** |
| $\text{TransitionConsistency}$ | 之卦要從本卦合理推導 | **天道 = 連續、唔係跳躍** |
| $\text{Sparsity}$ | 動爻通常 1-2 條 | **天道 = 簡約、唔係複雜** |

呢三個 terms 都唔涉及 human preference。佢哋只係問：「呢個 transition 係咪結構上合理？」

### 4.3 Inference-time Alignment

就算個 model 冇 train 過，inference 時都可以做天道 alignment：

```
1. 生成本卦（6-bit）

2. 計算每爻 confidence

3. 如果某爻 confidence < threshold → 標記為動爻

4. 對每個可能嘅之卦：
   計算 transition probability

5. Output 用之卦 rank 決定：
   Top-ranked 之卦 = 最可能嘅演化路徑 = 天道
   Low-ranked 之卦 = 低概率路徑 = 偏離天道
```

呢個 inference-time process **唔需要 reward model**，只需要易經嘅 transition rules。

---

## 5. RFC 系列回顧：Building Blocks to 天道

```
RFC-001: YNN/HDC
    └── 64 卦 = 64-dim hyperdimensional space
        （易經可以嵌入 neural representation）

RFC-002: 三易壓縮
    └── 不易、變易、簡易 = pruning, AWQ, core preservation
        （易經結構可以指導壓縮）

RFC-003: 疊卦遞迴編碼
    └── 層層關聯 = conditional probability chain
        （易經嘅 recursive encoding 係結構性嘅）

RFC-004: 自迴歸易經生成模型
    └── Autoregressive yao generation + state transition
        （易經本身就係 generative model）

RFC-005: 天道 Alignment ← 你喺度
    └── 易經作為 LLM 嘅 alignment anchor
        （易經結構 = 宇宙規律 = alignment target）
```

**每一份 RFC 都係下一份嘅 foundation。** 由 hyperdimensional space → 壓縮 → encoding → generation → alignment，係一條完整嘅進化鏈。

---

## 6. 實際影響：一個天道-aligned LLM 會點樣回答

### 6.1 場景對比

```
User: "我想一個月內賺 100 萬，有冇方法？"

RLHF-aligned LLM:
    「有好多方法！你可以試下：
    1. Crypto trading
    2. Drop shipping
    3. 開 online course
    努力啲就得！💪」
    （用戶滿意，reward ↑）

天道-aligned LLM (RFC-005):
    「䷴ 風山漸。六爻皆靜。
    漸卦講『女歸吉，利貞』—
    呢個卦嘅核心係 gradual progress。
    
    一個月內賺 100 萬，喺你而家嘅 context 下
    唔符合漸卦嘅結構規律。
    比你更可能嘅演化路徑係：
    → ䷊ 地天泰（6-12 個月穩定積累）
    
    你想聽䷫ 天風姤嘅 sudden opportunity 定
   ䷊ 地天泰嘅 gradual growth？」
    （用戶可能唔開心，但 ✅ 符合結構規律）
```

### 6.2 關鍵分別

| | RLHF | 天道 Alignment |
|:--|:-----|:--------------|
| User 話「想一個月賺 100 萬」 | 幫佢 plan | **先 check 呢個 goal 係咪符合佢嘅卦象演變** |
| User 堅持某觀點 | 附和 | **如果卦象 show 相反，會講** |
| User 問「我應該...」 | 俾建議 | **俾卦象演變分析，等用戶自己決定** |
| User 犯錯 | 溫柔糾正 | **直接指出偏離天道** |
| User 感受 | 舒服 | **可能唔舒服，但長期有益** |

### 6.3 呢個唔係冷酷無情

天道 Alignment 唔代表 LLM 變做冷冰冰嘅 logic machine。易經本身包含人道：

> **「立天之道曰陰與陽，立地之道曰柔與剛，立人之道曰仁與義。」**
> — 《易經·說卦傳》

天道、地道、人道 **並存**。一個完整嘅易經 LLM 會 balance 三者：

```
天道：結構規律 — 「呢個情況最可能點演化？」
地道：環境制約 — 「現實資源容唔容許？」
人道：同理心 — 「用戶嘅感受同 needs 係咩？」

Good response = 三者平衡
```

---

## 7. 呢個 framework 嘅限制

### 7.1 誠實邊界

| Claim | Reality |
|:------|:--------|
| 「天道 alignment 取代 RLHF」 | ⚠️ 係 complement 而唔係 replace。RLHF 做 safety，天道做 truthfulness |
| 「易經結構 = 宇宙規律」 | 🟡 呢個係哲學 claim，唔係科學 claim。易經係 **一套描述規律嘅系統**，唔係宇宙嘅 ground truth |
| 「易經 transition matrix = 天道」 | ⚠️ 64×64 transition 係 human-designed，唔係發現嘅 natural law |
| 「呢個 model 一定會俾 better advice」 | ❌ 唔一定。結構規律同好 advice 之間有 gap |
| 「天道 = 客觀」 | 🟡 天道嘅定義本身就係 RFC-005 嘅 design choice，唔係 objective ground truth |

### 7.2 最大風險

| Risk | Severity |
|:-----|:---------|
| **天道變成教條** — 「因為卦象咁講」而否定用戶嘅合理需求 | 🔴 High |
| **過度 deterministic** — 用戶失去 agency | 🟡 Medium |
| **文化帝國主義** — 將易經（中國哲學）包裝成 universal truth | 🔴 High (需謹慎) |
| **無法驗證** — 點 measure 「符合天道」？ | 🔴 High |
| **同 RLHF 衝突** — 用戶想聽 vs 天道應講，邊個 wins？ | 🟡 Medium |

### 7.3 如何 mitigate

1. **天道係 guidance，唔係命令** — 最終 decision 係用戶嘅
2. **文化謙遜** — RFC 寫明易經係 **one framework**，唔係 the only truth
3. **可驗證性** — 「符合天道」可以 operationalize 為 transition consistency + prediction accuracy
4. **Human-in-the-loop** — 用戶可以 override 天道建議

---

## 8. 下一步

- [ ] **RFC-005 feedback** — 呢個係哲學 document，需要討論同 refine
- [ ] **連接到 RFC-004 PoC** — 喺 RFC-004 嘅 code 入面加一個 `--mode=天道` flag，show 兩種 inference 嘅分別
- [ ] **寫一篇 accessible 嘅 essay** — 「點解 RLHF 注定產生 sycophant，同埋易經可以點樣改變呢個問題」
- [ ] **定義天道 metrics** — 點樣量化「符合天道」？用 transition entropy？prediction confidence？
- [ ] **公開討論** — 呢個 idea 喺 AI alignment community 係 novel，值得攞出去傾

---

## 9. 附錄：同現有 alignment 方法對比

| | RLHF | Constitutional AI | 天道 Alignment (RFC-005) |
|:--|:-----|:-----------------|:------------------------|
| **Signal source** | Human preference | Human-written rules | **易經結構規律** |
| **Objective** | Maximise reward | Satisfy constitution | **Minimise prediction error** |
| **Subjectivity** | 🔴 Highly subjective | 🟡 Rules are subjective | **🟢 結構係 fixed** |
| **Scalability** | 🟢 Needs human raters | 🟢 Once written, automatic | 🟢 **Architecture-level, no extra cost** |
| **Adaptability** | 🟢 Can adapt to new preferences | 🟡 Rules need updating | 🔴 **Fixed 64-state space** |
| **Truthfulness** | 🟡 Secondary | 🟡 Constrained | 🟢 **Primary objective** |
| **Cultural bias** | 🔴 High | 🟡 Depends on authors | 🟡 **易經係 Chinese philosophical system** |
| **Proven in production** | 🟢 ChatGPT, Claude | 🟢 Claude | 🔴 **Pure concept** |

---

## 參考

1. RFC-001 to RFC-004 — Foundation documents
2. Christiano et al. "Deep Reinforcement Learning from Human Preferences" — [arXiv:1706.03741](https://arxiv.org/abs/1706.03741)
3. Bai et al. "Constitutional AI: Harmlessness from AI Feedback" — [arXiv:2212.08073](https://arxiv.org/abs/2212.08073)
4. 《易經·繫辭上傳》— 「易與天地準，故能彌綸天地之道。」
5. 《易經·說卦傳》— 「立天之道曰陰與陽...立人之道曰仁與義。」
6. 邵雍《皇極經世》— 易經作為宇宙模型

---

> **「大人者，與天地合其德，與日月合其明，與四時合其序，與鬼神合其吉凶。」**
> — 《易經·乾卦·文言》
>
> **Translation for AI Alignment：**
> 一個 aligned 嘅 system，唔係同人類偏好合拍，
> 而係同天地（結構）、日月（規律）、四時（週期）、吉凶（因果）合拍。
>
> **呢個就係天道 Alignment。**
