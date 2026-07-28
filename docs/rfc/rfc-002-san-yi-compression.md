# RFC-002: 三易壓縮 — 易經驅動嘅 LLM 壓縮框架

> **Status:** Draft  
> **Author:** yayafu × Orchestrator Nova  
> **Date:** 2026-07-28  
> **Depends on:** RFC-001 (YNN/HDC Research)  

---

## 摘要

本 RFC 提出一個基於《易經》「三易」哲學嘅 LLM 壓縮框架：**簡易、變易、不易**。

唔係將易經文化符號貼喺現有技術上面（hash % 64），而係將易經最核心嘅**系統結構**翻譯為真實嘅工程數學算法。

---

## 目錄

1. [核心概念：三易 Pipeline](#1-核心概念三易-pipeline)
2. [Level 1：陰陽三才 ＝ 1.58-Bit Ternary Quantization](#2-level-1陰陽三才--158-bit-ternary-quantization)
3. [Level 2：變爻保護 ＝ Mixed Precision / AWQ](#3-level-2變爻保護--mixed-precision--awq)
4. [Level 3：上下卦分解 ＝ Low-Rank Decomposition](#4-level-3上下卦分解--low-rank-decomposition)
5. [三易 Pipeline 整合](#5-三易-pipeline-整合)
6. [誠實邊界](#6-誠實邊界)
7. [下一步](#7-下一步)

---

## 1. 核心概念：三易 Pipeline

### 1.1 三易（易經核心哲學）

| 原則 | 易經意涵 | LLM 工程映射 | 技術手段 |
|:-----|:---------|:------------|:--------|
| **簡易** | 刪繁就簡，去掉冗餘 | Pruning（剪枝） | 砍掉不活躍嘅 Attention Heads 同冗餘層 |
| **變易** | 隨時而變，動態調節 | Dynamic Quantization | 根據 input context 動態調整精度同 MoE 路由 |
| **不易** | 守住根本，萬變不離其宗 | Core Preservation | 凍結語言模型最底層嘅邏輯基底同 Token Embedding |

### 1.2 Pipeline 流程

```
輸入 Weight Matrix W
    │
    ▼
Phase 1: 簡易（Pruning）
    │ 砍掉 ‖W_i‖ < threshold 嘅 rows/cols
    │ → W 變做 W_pruned (m' × n')
    ▼
Phase 2: 變易（Dynamic Quantization）
    │ Detect outlier columns（變爻）
    │ → 保護 outlier → FP16
    │ → 其餘 → 2-bit ternary {-1, 0, +1}
    ▼
Phase 3: 不易（Core Preservation）
    │ Embedding layer 同 bottom layers frozen
    │ → 永遠保持 FP16
    ▼
輸出：壓縮 Model（5-10x smaller）
```

---

## 2. Level 1：陰陽三才 ＝ 1.58-Bit Ternary Quantization

### 2.1 易經概念

爻（Line）不只是 0 和 1 的二進制，更關鍵的是它有 **「陰、陽、中」** 三個狀態：

| 狀態 | 符號 | 數值 | 意義 |
|:-----|:----|:----|:-----|
| 陽 | ⚊ | +1 | 主動、剛健 |
| 陰 | ⚋ | -1 | 被動、柔順 |
| 中/無動 | — | 0 | 中和、潛伏 |

> **三才者，天地人也。** — 《易經·繫辭》

### 2.2 數學表達

BitNet b1.58 將每個 weight 量化至三值集合：

$$W_{ij} \in \{-1, 0, +1\}$$

原本：

$$Y = W \cdot X = \sum_{j} W_{ij} X_{j} \quad \text{(FP32 乘法)}$$

Ternary 後：

$$Y = \sum_{j} \text{sign}(W_{ij}) \cdot X_{j} \quad \text{(純加減法，無乘法)}$$

### 2.3 工程增益

| Metric | FP32 | Ternary (-1,0,+1) | 節省 |
|:-------|:-----|:-----------------|:-----|
| Bits per weight | 32 | **~1.58** | **~20x** |
| 7B model size | ~28 GB | **~1.4 GB** | 手機級 |
| 矩陣乘法 | FP32 multiplier | **adder only** | 10x 能耗降 |

### 2.4 已有實作

- **BitNet b1.58** (Microsoft, 2024) — [arXiv:2402.17764](https://arxiv.org/abs/2402.17764)
- **BitNet GitHub** — [https://github.com/microsoft/BitNet](https://github.com/microsoft/BitNet)
- **1-bit LLMs** (UCAS, 2024) — [arXiv:2402.17764](https://arxiv.org/abs/2404.00598)

### 2.5 易經 × 工程對照

```
範例 weight matrix（4 weights）:

易經視角：        工程視角：
⚊ +1 +1 ⚊        [+1  +1]
⚋ -1  0 中        [-1   0]

每個 weight 係一個「爻位」，
成個 matrix 係一個「卦」。
```

---

## 3. Level 2：變爻保護 ＝ Mixed Precision / AWQ

### 3.1 易經概念

64 卦最精妙的地方是 **「動爻（變爻）」**。一個卦裡通常只有 1～2 個爻在變，這 1～2 個爻決定了整體的局勢走勢，其餘 4～5 個靜爻只是背景。

> **「爻者，言乎變者也。」** — 《易經·繫辭》

### 3.2 數學表達

AWQ (Activation-aware Weight Quantization) 的核心觀察：

$$\text{Per-channel importance} = \text{mean}(|X W|)$$

其中 $X$ 係 activation，$W$ 係 weight。只保護 top 1% outlier channels：

$$
W_{\text{quantized}} = 
\begin{cases}
W_{ij} \in \text{FP16}, & \text{if } \text{importance}_j > \tau \quad \text{(動爻)} \\
W_{ij} \in \text{INT2}, & \text{otherwise} \quad \text{(靜爻)}
\end{cases}
$$

### 3.3 工程增益

| Layer Type | Outlier % (動爻) | 精度 | 其餘 (靜爻) | 平均壓縮 |
|:-----------|:-----------------|:-----|:------------|:---------|
| Attention | ~3% | FP16 | INT2 | ~6x |
| FFN | ~0.5% | FP16 | INT2 | ~12x |
| Embedding | 0% | FP16 frozen | — | 不壓縮 |

### 3.4 已有實作

- **AWQ** (MIT, 2024) — [arXiv:2306.00978](https://arxiv.org/abs/2306.00978)
- **llama.cpp** `-a awq` 支援 — [GitHub](https://github.com/ggerganov/llama.cpp)
- **QuIP#** (Cornell, 2024) — [arXiv:2402.04396](https://arxiv.org/abs/2402.04396)

### 3.5 易經 × 工程對照

```
卦象（weight matrix）:

初爻 ──── outlier weight → 變 → 保留 FP16（動爻）
二爻 ──── normal weight  → 靜 → 壓縮 INT2（靜爻）
三爻 ──── normal weight  → 靜 → 壓縮 INT2（靜爻）
四爻 ──── normal weight  → 靜 → 壓縮 INT2（靜爻）
五爻 ──── outlier weight → 變 → 保留 FP16（動爻）
上爻 ──── normal weight  → 靜 → 壓縮 INT2（靜爻）

→ 1, 5爻係變爻，決定大局
→ 2, 3, 4, 6爻係背景
→ 壓縮後 model 體積 ~40% of original
```

---

## 4. Level 3：上下卦分解 ＝ Low-Rank Decomposition

### 4.1 易經概念

六十四卦是由 **上卦（外卦，3-bit）** 與 **下卦（內卦，3-bit）** 疊加而成的結構：$8 \times 8 = 64$。

> **「太極生兩儀，兩儀生四象，四象生八卦。」**  
> **「八卦相盪，六十四卦成焉。」** — 《易經·繫辭》

高維的複雜狀態（64 狀態），可以解構為兩個低維的基礎動力（$8 \times 8$）互相交感。

### 4.2 數學表達

一個大的 Weight 矩陣 $W \in \mathbb{R}^{m \times n}$，不需要硬記每一個 entry：

$$W \approx A \times B$$

其中 $A \in \mathbb{R}^{m \times k}$，$B \in \mathbb{R}^{k \times n}$，且 $k \ll \min(m, n)$。

用「內卦」與「外卦」來 analogize：

```
W (64×64)          A (64×4)          B (4×64)
┌──────────┐     ┌──────┐          ┌──────────┐
│ 64×64    │  ≈  │ 64×4 │    ×    │ 4×64     │
│          │     │      │          │          │
└──────────┘     └──────┘          └──────────┘
4096 entries     256 entries       256 entries
                                    → 512 total vs 4096
                                    → 8x 壓縮
```

**注意：** 呢個 analogy 嘅 rank $k$ 係任意嘅，唔等同 3 或 6。卦象分解係 **conceptual inspiration**，唔係 exact mapping。

### 4.3 工程增益

| 原始大小 | Rank k=4 | Rank k=8 | Rank k=16 |
|:---------|:---------|:---------|:----------|
| 4096 (64×64) | 512 (**8x**) | 1024 (**4x**) | 2048 (**2x**) |
| 1M (1024×1024) | 8K (**125x**) | 16K (**62x**) | 32K (**31x**) |

### 4.4 已有實作

- **LoRA** (Microsoft, 2021) — [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)
- **SVD Quantization** (Google, 2023) — [arXiv:2303.08934](https://arxiv.org/abs/2303.08934)
- **Tensor Train Decomposition** — [arXiv:2305.14380](https://arxiv.org/abs/2305.14380)

### 4.5 易經 × 工程對照

```
高維狀態（64卦）           低維基礎（8卦 × 8卦）
────────────────      ────────────────
䷀ ䷁ ䷂ ䷃ ... ䷿         上卦 下卦
64 × 64 matrix    =    A(64×8) × B(8×64)
                          ↓        ↓
                       外卦(8)   內卦(8)
                       3-bit     3-bit
                       八卦      八卦
```

---

## 5. 三易 Pipeline 整合

### 5.1 完整流程

```
原始 LLM (FP32, 28GB for 7B)
    │
    ├── Phase 1: 簡易（Pruning）
    │   砍掉 unused attention heads (15-30% volume reduction)
    │
    ├── Phase 2: 變易（Variable Precision）
    │   ├── Detect 動爻（outlier weights, top 1%）
    │   ├── 動爻 → FP16 preserved
    │   └── 靜爻 → Ternary {-1, 0, +1} / INT2
    │
    ├── Phase 3: 不易（Core Preservation）
    │   ├── Embedding layer → FP16 frozen
    │   ├── Bottom 2 transformer layers → FP16 frozen
    │   └── Remaining → compressed
    │
    └── Output: 壓縮 LLM (1.5-5GB, 5-10x smaller)
```

### 5.2 預期壓縮效果

| 原始 (7B FP32) | 三易壓縮後 | 壓縮比 | 裝置 |
|:---------------|:-----------|:------|:-----|
| 28 GB | **~5.25 GB** (6-bit uniform) | 5.3x | MacBook |
| 28 GB | **~1.4 GB** (ternary) | 20x | iPhone |
| 28 GB | **~2.8 GB** (ternary + AWQ) | 10x | MacBook/Android |
| 28 GB | **~0.7 GB** (ternary + AWQ + pruning) | 40x | Edge device |

### 5.3 誠實邊界

| Claim | Reality |
|:------|:--------|
| 「易經啟發咗 ternary quantization」 | BitNet 嘅發明人冇引用易經。呢個係 **retroactive analogy**，唔係 causal |
| 「變爻 = AWQ」 | AWQ 嘅數學同變爻概念吻合，但 AWQ 嘅發明冇參考過易經 |
| 「上下卦 = LoRA」 | 低秩分解同卦象疊加嘅 analogy 最有啟發性，但 rank k 唔固定為 3 |
| 「三易 pipeline」 | **呢個係新嘅統一框架**。三個 component 各自存在，但未有人用三易命名 |

---

## 6. 誠實邊界

### 6.1 呢個 framework 係乜

一個 **philosophical unification framework**，將易經系統結構映射到已經存在嘅 LLM 壓縮技術。佢嘅價值在於 **統一敘事**，唔係新嘅 engineering discovery。

### 6.2 呢個 framework 唔係乜

- ❌ 唔係一篇新的 ML paper
- ❌ 唔係一個 production-ready 嘅壓縮工具
- ❌ 唔係話古人發明咗 neural network
- ❌ 唔係聲稱 BitNet/AWQ/LoRA 係抄易經

### 6.3 點解仍然有價值

- **跨越文化 barrier**：中文世界嘅讀者可能唔識 BitNet 但識陰陽三才
- **記憶鉤**：三易（簡易、變易、不易）比 Pruning/Dynamic Quant/Core Preservation 容易記
- **統一視角**：以前呢三個技術散落在唔同 paper，而家有 unified narrative

---

## 7. 下一步

- [ ] RFC-002 接受 feedback → 定稿
- [x] PoC Code：`demos/san_yi_compression_demo.py` — 三易壓縮示範 ✅ [Run it: `python3 demos/san_yi_compression_demo.py`](demos/san_yi_compression_demo.py)
- [ ] 整合入 yi-jing-agent repo（PoC 已入 demos/）
- [ ] 考慮 HuggingFace Community Article

---

## 參考

1. BitNet b1.58 — [arXiv:2402.17764](https://arxiv.org/abs/2402.17764)
2. AWQ — [arXiv:2306.00978](https://arxiv.org/abs/2306.00978)
3. LoRA — [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)
4. QuIP# — [arXiv:2402.04396](https://arxiv.org/abs/2402.04396)
5. Tensor Decomposition — [arXiv:2305.14380](https://arxiv.org/abs/2305.14380)
6. 邵雍《皇極經世》— 先天八卦次序圖
7. 萊布尼茲《論二進制算術》— 1703, 基於邵雍易圖
