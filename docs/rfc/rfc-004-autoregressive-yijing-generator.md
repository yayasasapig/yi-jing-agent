# RFC-004: 自迴歸易經生成模型 — Autoregressive I Ching Generator

> **Status:** Draft · **Track:** v1.5+ Research  
> **Author:** yayafu × Orchestrator Nova  
> **Date:** 2026-07-29  
> **Depends on:** RFC-003 (疊卦遞迴編碼)

---

## 摘要

RFC-001 至 RFC-003 全部係用易經概念去 **壓縮或解釋** 現有 AI 技術。呢份 RFC 反轉個方向：

> **唔好用易經去壓縮 AI，要用易經做 AI 本身嘅架構。**

《易經》嘅核心唔係 64 個靜態卦象，而係一個 **自迴歸生成過程（Autoregressive Process）**：

$$P(\text{爻}_k | \text{爻}_1, ..., \text{爻}_{k-1}, \text{時位 Context})$$

逐爻疊加：初爻 → 二爻 → 三爻 → 四爻 → 五爻 → 上爻，每爻嘅出現都在前一爻形成嘅 Context 之上做條件機率預測。

呢個同 **GPT 嘅 Causal Language Model** 完全同構 — 只係 Token 由「字」變為「爻」，Vocabulary 由 50K 變為 2（陰/陽）。

如果成功，呢個模型可以做到：
- **真正嘅起卦** — 唔係 hash mapping，而係逐爻生成
- **變爻預測** — Detect 邊條爻係動爻（outlier probability）
- **State transition** — 由本卦推導之卦（預測未來演化）
- **Trainable** — 用歷史 data 訓練，唔係 rule-based

---

## 目錄

1. [核心 Insight：易經 = Autoregressive Model](#1-核心-insight易經--autoregressive-model)
2. [模型架構總覽](#2-模型架構總覽)
3. [Module 1：爻生成器（Causal Yao Generator）](#3-module-1爻生成器causal-yao-generator)
4. [Module 2：樹狀編碼器（Binary Trie Encoder）](#4-module-2樹狀編碼器binary-trie-encoder)
5. [Module 3：狀態轉移預測器（State Transition Predictor）](#5-module-3狀態轉移預測器state-transition-predictor)
6. [完整 Inference Pipeline](#6-完整-inference-pipeline)
7. [Training Data 問題](#7-training-data-問題)
8. [誠實邊界](#8-誠實邊界)
9. [下一步](#9-下一步)

---

## 1. 核心 Insight：易經 = Autoregressive Model

### 1.1 數學同構

| | GPT / Causal LM | 易經生成模型 |
|:--|:---------------|:------------|
| Token | 字 / subword | **爻（陰/陽）** |
| Vocabulary size | 32K-128K | **2（{陰, 陽}）** |
| Sequence length | 2K-128K tokens | **6 爻** |
| Generation | $$P(t_i \mid t_1..t_{i-1})$$ | $$P(爻_k \mid 爻_1..爻_{k-1}, \text{context})$$ |
| Attention | Causal (masked) | **Causal（後爻不可見前爻）** |
| Training | Next-token prediction | **Next-yao prediction** |

### 1.2 關鍵分別

GPT 嘅 sequence length 好長（2K+ tokens），vocabulary 好大（50K+）。易經 generator 嘅 sequence length 只得 6，vocabulary 得 2。

呢個極簡設定其實係 **advantage**：
- 6 步就完成一次 generation → inference 極快
- 2-class classification → 每步只需一個 binary decision
- 6 步嘅 hidden state 就係完整嘅「卦 context」→ 可解釋性極高

### 1.3 生成過程對比

```
GPT 生成一句話：
「我今天___」
    ↓ P(token | "我今天")
「我今天去___」
    ↓ P(token | "我今天去")
「我今天去食___」
    ↓ P(token | "我今天去食")
「我今天去食飯。」✅

易經生成一個卦：
「初爻___」
    ↓ P(爻 | context)
「初爻陽，二爻___」
    ↓ P(爻 | context, 初爻=陽)
「初爻陽，二爻陽，三爻___」
    ↓ ...
「䷀ 乾為天」✅
```

**Structure is identical.** 只係 token set 唔同。

---

## 2. 模型架構總覽

```
Input Context（事件描述 / 環境變數）
    │
    ▼
┌─────────────────────────────────────┐
│  Module 1: Causal Yao Generator     │
│  （自迴歸爻生成器）                  │
│                                      │
│  初爻: P(陰/陽 | context)           │
│  二爻: P(陰/陽 | context, 初爻)     │
│  三爻: P(陰/陽 | context, 初,二爻)  │
│  → 下卦完成（八卦）                  │
│  四爻: P(陰/陽 | context, 初~三爻)  │
│  五爻: P(陰/陽 | context, 初~四爻)  │
│  上爻: P(陰/陽 | context, 初~五爻)  │
│  → 六十四卦完成                      │
└──────────────┬──────────────────────┘
               │ 本卦 + 每爻 probability
               ▼
┌─────────────────────────────────────┐
│  Module 2: Binary Trie Decoder      │
│  （樹狀路徑解碼器）                  │
│                                      │
│  將 6 爻路徑映射到 64 卦空間        │
│  輸出：本卦 index (0-63)             │
│         inner trigram (0-7)          │
│         outer trigram (0-7)          │
└──────────────┬──────────────────────┘
               │ 本卦 index
               ▼
┌─────────────────────────────────────┐
│  Module 3: State Transition         │
│  （狀態轉移預測器）                  │
│                                      │
│  Detect 動爻（低 confidence 爻位）   │
│  → 計算 64×64 transition matrix     │
│  → 輸出之卦 probability distribution │
└──────────────┬──────────────────────┘
               │
               ▼
Output: 本卦 + 動爻位 + 之卦排名 + confidence
```

---

## 3. Module 1：爻生成器（Causal Yao Generator）

### 3.1 Architecture

```
Input: context_vector (embedding dim d)
    │
    ▼
L0: Embedding(context) → h_0 ∈ ℝᵈ
    │
    ▼
L1: CausalSelfAttention(h_0) → h_1
    │  （初爻生成 — 只有 context，冇前爻）
    │
    ▼
    y_1 = softmax(MLP(h_1)) → P(陰), P(陽)
    ──── 抽樣 / argmax → 初爻值 y_1 ∈ {0, 1}
    │
    ▼
L2: Embedding(y_1) → e_1 ∈ ℝᵈ
    h_2 = CausalSelfAttention(h_1 + e_1) → h_2
    │  （二爻生成 — context + 初爻）
    │
    ▼
    y_2 = softmax(MLP(h_2)) → P(陰), P(陽)
    ──── 抽樣 → 二爻值 y_2 ∈ {0, 1}
    │
    ▼
    ...（重複至第六爻）
    │
    ▼
L6: 完成
    y_1..y_6 = 6-bit hexagram
    P_1..P_6 = 每爻嘅 confidence score
```

### 3.2 每步嘅數學

Step $k$（生成第 $k$ 爻）：

$$h_k = \text{CausalAttention}(h_{k-1} + \text{Embedding}(y_{k-1}))$$

$$P(y_k = 1 \mid y_1..y_{k-1}, \text{context}) = \sigma(W \cdot h_k + b)$$

$$P(y_k = 0) = 1 - P(y_k = 1)$$

其中 $\sigma$ 係 sigmoid（binary classification）。

### 3.3 爻 confidence 嘅意義

每爻輸出唔止係「陰/陽」，仲有一個 **probability score**：

$$c_k = \max(P(y_k=0), P(y_k=1))$$

$c_k$ 嘅意義：

| $c_k$ | 意義 | 易經對應 |
|:------|:-----|:--------|
| >0.95 | 好肯定 | 靜爻 — 呢爻穩定 |
| 0.7-0.95 | 一般肯定 | 少陽/少陰 |
| 0.5-0.7 | 唔肯定 | **動爻（老陽/老陰）** |
| <0.5 | 幾乎隨機 | 強烈動爻 — 系統不穩 |

**呢個係天生嘅動爻 detection mechanism。** 邊條爻 confidence 低，就係邊條動。

### 3.4 為甚麼用 Causal Attention 而唔係 RNN？

因為：
- RNN：線性壓縮，前爻資訊隨步衰減
- Causal Attention：**每步可以直接 attend 任何前爻** — 初爻嘅影響永遠唔會消失

呢個 matches 易經嘅哲學：**上爻嘅意義包含初爻，唔係 overwrite 初爻。**

---

## 4. Module 2：樹狀編碼器（Binary Trie Decoder）

### 4.1 6 爻 → 路徑 → 卦

Module 1 輸出 6-bit sequence $[y_1, y_2, y_3, y_4, y_5, y_6]$。

呢個 sequence 自然對應一個 **深度 6 嘅 binary trie 路徑**：

```
                    Root
                   /    \
                  0      1          ← 初爻
                 / \    / \
               00  01  10  11       ← 二爻
               /\  /\  /\  /\
             000 001 010 011 100 101 110 111  ← 三爻（下卦完成）

                    |
                    |（四、五、上爻繼續）
                    |
             000000 ... 111111     ← 六十四卦（葉節點）
```

**Decoder 就係 lookup：** 6-bit path → 64 卦 index（0-63）。

### 4.2 下卦 / 上卦提取

呢個結構仲可以自然提取：

```
下卦（inner trigram）= y_1 y_2 y_3 → 3-bit → 0-7（八卦）
上卦（outer trigram）= y_4 y_5 y_6 → 3-bit → 0-7（八卦）
```

呢個唔係額外 computation，就係 bit slicing。

### 4.3 路徑 confidence

每條路徑嘅 total confidence = 每爻 confidence 嘅 product：

$$P(\text{卦}) = \prod_{k=1}^6 c_k$$

如果某條爻 confidence 低，成個卦嘅 confidence 就 drop。呢個係 **卦層級嘅 uncertainty measure**。

---

## 5. Module 3：狀態轉移預測器（State Transition Predictor）

### 5.1 64 × 64 Transition Matrix

呢個 module 接收：
- 本卦 index $s_t \in \{0..63\}$
- 每爻 confidence $c_1..c_6$
- context embedding

輸出：
- 64 維 probability distribution over 之卦
- $P(s_{t+1} = h \mid s_t, \text{moving lines}, \text{context})$

### 5.2 Transition 計算方法

**Method A：Rule-based（毋須 training）**

用易經嘅變卦規則：
- 動爻位 mask → XOR flip → 之卦
- 如果多條動爻 → 多個可能之卦 → weighted by confidence

Example：
```
本卦: ䷀ 乾為天（111111）
動爻: 三爻、上爻（confidence < 0.7）
    ↓ XOR flip bit 3 & bit 6
之卦: ䷫ 天風姤（111110）？定䷉ 天澤履（111011）？
    ↓
output: ䷫ P=0.45, ䷉ P=0.35, ䷌ P=0.10, ...
```

**Method B：Learned（需 training data）**

Train 一個 64→64 嘅 transition matrix $T$：

$$T_{ij} = P(s_{t+1}=j \mid s_t=i, \text{動爻 mask})$$

呢個可以係一個 learned embedding + softmax。

### 5.3 動爻 detection

Module 1 嘅每爻 confidence 直接 serve 做動爻 detector：

```python
def detect_moving_lines(yao_probabilities):
    """Return list of (yao_index, confidence) where confidence < threshold."""
    moving = []
    for i, p in enumerate(yao_probabilities):
        confidence = max(p, 1-p)
        if confidence < MOVING_LINE_THRESHOLD:  # e.g. 0.7
            moving.append((i, confidence))
    return moving
```

呢個 threshold 可以係 hyperparameter。越低 threshold = 越敏感（更多動爻）。

---

## 6. Complete Inference Pipeline

### 6.1 Pseudocode

```python
class YiJingGenerator:
    def __init__(self, model: CausalYaoModel, threshold=0.7):
        self.model = model
        self.threshold = threshold
        self.trie = HexagramTrie()  # 6-bit → 64 卦 lookup

    def predict(self, context: str) -> dict:
        """Complete inference: generate hexagram + predict transition."""

        # ── Module 1：Autoregressive Yao Generation ──
        context_vec = self.model.encode(context)
        yao_bits = []
        yao_probs = []
        hidden = context_vec

        for step in range(6):
            prob_sigmoid = self.model.predict_yao(hidden)
            yao_bit = 1 if prob_sigmoid > 0.5 else 0
            yao_bits.append(yao_bit)
            yao_probs.append(prob_sigmoid)
            # Append chosen yao for next step
            hidden = self.model.step(hidden, yao_bit)

        # ── Module 2：Trie Decoding ──
        hexagram_idx = self.trie.path_to_index(yao_bits)
        inner_trigram = self.trie.inner_trigram(yao_bits)
        outer_trigram = self.trie.outer_trigram(yao_bits)

        # ── Module 3：State Transition ──
        moving_lines = [
            (i, max(p, 1-p))
            for i, p in enumerate(yao_probs)
            if max(p, 1-p) < self.threshold
        ]

        transitions = self.model.predict_transition(
            hexagram_idx, moving_lines, context_vec
        )

        return {
            "hexagram": hexagram_idx,
            "symbol": HEXAGRAM_SYMBOLS[hexagram_idx],
            "name": HEXAGRAM_NAMES[hexagram_idx],
            "inner_trigram": inner_trigram,   # 0-7
            "outer_trigram": outer_trigram,   # 0-7
            "yao_bits": yao_bits,             # [0/1]*6
            "yao_confidence": [max(p, 1-p) for p in yao_probs],
            "moving_lines": moving_lines,      # [(idx, conf), ...]
            "transitions": transitions,        # list of (hex_idx, prob)
            "本卦_confidence": np.prod([max(p, 1-p) for p in yao_probs]),
        }
```

### 6.2 Output Example

```json
{
  "hexagram": 1,
  "symbol": "䷀",
  "name": "乾為天",
  "inner_trigram": 7,
  "outer_trigram": 7,
  "yao_bits": [1, 1, 1, 1, 1, 1],
  "yao_confidence": [0.98, 0.95, 0.45, 0.92, 0.88, 0.97],
  "moving_lines": [[2, 0.45]],
  "transitions": [
    [44, 0.52],
    [10, 0.23],
    [14, 0.10],
    ...
  ],
  "本卦_confidence": 0.34
}
```

解讀：
- 本卦：䷀ 乾為天（好高 confidence）
- 三爻 confidence 得 0.45 → **動爻**
- 變卦後最高 probability：䷫ 天風姤（52%）
- 整體卦 confidence 得 0.34 = 因為有動爻，要睇之卦

---

## 7. Training Data 問題

呢個係最難嘅 part。

### 7.1 需要乜 data？

每條訓練樣本：
```
{
  "context": "某年某月某事",
  "hexagram": [1,1,1,1,1,1],     # 6-bit
  "moving_lines": [2],            # 邊條動
  "future_hexagram": [1,1,1,1,1,0]  # 之卦
}
```

### 7.2 可能嘅 data sources

| Source | Quality | 數量 | 可行性 |
|:-------|:-------|:----|:------|
| **《左傳》《國語》筮例** | 最高 — 真實歷史 + 卦象 | ~20 條 | ✅ 立即可用 |
| **《周易正義》歷史占例** | 高 — 經過考證 | ~100 條 | ✅ 需要整理 |
| **《梅花易數》案例** | 中 — 後人記錄 | ~500 條 | ✅ 需要數位化 |
| **《易經》經文本身** | 中 — 卦辭爻辭 | 64 卦 × 6 爻 = 384 | ✅ 已有 |
| **合成 data（rule-based）** | 低 — 冇真實 context | 無限 | 🔄 可做但 unreliable |
| **現代占卜記錄** | 高但冇標準化 | 潛在大量 | ❌ 需社群貢獻 |

### 7.3 最可行嘅起步策略

**Phase 1：用經文做 pretrain（384 samples）**

每條 sample：
```
context = 卦名 + 卦辭概略
hexagram = 該卦 6-bit
moving_lines = 根據爻辭推斷（有啲爻辭明講「動」）
future_hexagram = 爻變後之卦
```

呢個只夠學到 **靜態 mapping**，唔夠學到 **動態預測**。

**Phase 2：用人造 context 做 synthetic training**

用 LLM（e.g. GPT-4）生成大量「情境 → 卦象對應」：
```
Prompt: "Given this situation, which I Ching hexagram best describes it?
         Generate the 6 yao lines and which lines are moving."

Input:  "A startup founder faces an unexpected competitor..."
Output: "䷂ 屯卦 (100010), moving lines: 3,5"
```

呢個 data 係 noisy，但量大可以補償。

**Phase 3：Fine-tune on real historical records**

用《左傳》《國語》嘅真實筮例做 fine-tune。數量少但 quality 高。

### 7.4 最好嘅可能性

如果有一個平台可以 collect 大量真實起卦記錄（context + 卦象 + 應驗結果），呢個 dataset 嘅 value 會極高。但呢個係 chicken-and-egg problem — 你需要個 model 先吸引人用，但你需要 data 先 train 到 model。

---

## 8. 誠實邊界

### 8.1 呢個係乜

一個 **conceptual neural architecture**，將易經嘅生成過程翻譯為 autoregressive model + binary trie + state transition。佢係 trainable、interpretable、同 causal language model 同構。

### 8.2 呢個唔係乜

- ❌ 唔係一個已經 train 好嘅 model
- ❌ 唔係一個 production-ready 嘅系統
- ❌ 唔係聲稱易經「本質上係 neural network」
- ❌ 唔係迷信 — 呢個係 **工程架構提案**，用 ML 技術重建易經嘅結構

### 8.3 最大風險

| Risk | Severity | Mitigation |
|:-----|:---------|:-----------|
| **冇足夠 training data** | 🔴 High | 用 synthetic data 起步，collect 真實 data 需時 |
| **Model 太細學唔到複雜 context** | 🟡 Medium | 6-step binary decision 其實好簡單，可能夠用 |
| **Overfitting 到 64 卦** | 🟡 Medium | 64 卦係 deterministic mapping，唔會 overfit |
| **易經 prediction 無法驗證** | 🔴 High | 點 measure 「準」？呢個係 philosophical 問題 |
| **Causal attention 對 6 step 嚟講 overkill** | 🟢 Low | 可以用更簡單嘅 architecture，但 attention 更優雅 |

### 8.4 同現有 AI 架構嘅比較

| | GPT | 易經 Generator |
|:--|:----|:---------------|
| Parameters | 7B-1.7T | **~1M-10M**（估計） |
| Training cost | $1M-$100M | **~$100**（估計） |
| Inference speed | ~20 tokens/s on GPU | **~1000 inferences/s on CPU** |
| Interpretability | 低（黑箱） | **高（每爻 decision 可睇）** |
| 實用價值 | 通用 | **特定 domain（決策支援）** |

因為 sequence length 只有 6，vocab 只有 2，呢個 model 可以小到 **喺你部 Mac 嘅 CPU 上即時 inference**，唔需要 GPU。

---

## 9. 下一步

- [ ] **寫 PoC** — 用 PyTorch / numpy 實作 Module 1（Causal Yao Generator），用 synthetic data 驗證 generation 係咪合理
- [ ] **整理 training data** — 將《左傳》《國語》筮例 digitize，做第一版 fine-tune dataset
- [ ] **決定 model size** — 6-step causal attention，hidden dim 64? 128? 256?
- [ ] **公開討論** — 呢個 architecture 係 novel，值得响 ML community 分享
- [ ] **Collect real data** — 如果你個 Telegram bot 可以 record「context → 卦象」pairs，將來可以 fine-tune

---

## 參考

1. RFC-001: YNN/HDC Research — Hyperdimensional Computing × 易經
2. RFC-002: 三易壓縮框架
3. RFC-003: 疊卦遞迴編碼
4. Vaswani et al. "Attention Is All You Need" — [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)
5. Brown et al. "Language Models are Few-Shot Learners" (GPT-3) — [arXiv:2005.14165](https://arxiv.org/abs/2005.14165)
6. 《左傳》《國語》筮例 — 最早嘅易經占卜歷史記錄
7. 邵雍《梅花易數》— 以 context 起卦嘅方法論

---

> **「易與天地準，故能彌綸天地之道。」**
> — 《易經·繫辭上傳》
>
> **Translation for ML：**
> 易經嘅結構同世界嘅結構係 isomorphic 嘅。
> 所以我哋可以用易經嘅 generative process 去 model 世界嘅變化。
>
> **呢個唔係玄學。呢個係 architecture design。**
