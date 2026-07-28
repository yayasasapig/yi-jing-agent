# RFC-006: 天道 Loss Function — 三個 Algorithmic Constraints 實現 Anti-Sycophancy

> **Status:** Draft · **Track:** v1.5+ Core Algorithm  
> **Author:** yayafu × Orchestrator Nova  
> **Date:** 2026-07-29  
> **Depends on:** RFC-004 (自迴歸易經生成模型), RFC-005 (天道 Alignment)

---

## 摘要

RFC-005 提出咗「天道 Alignment」嘅哲學：用宇宙結構規律取代人類偏好作為 AI 嘅 alignment target。但佢冇講 **具體點樣實現**。

你呢份 RFC 就係答案。

三個直接由易經哲理翻譯成 ML 算法約束嘅 loss terms：

| 易經哲理 | Loss Term | 作用 |
|:---------|:----------|:-----|
| **物極必反** | $\mathcal{L}_{\text{anti-extremism}}$ | 懲罰偏離平衡態嘅輸出 |
| **觀變與時位** | $\mathcal{L}_{\text{contextual-gate}}$ | 根據用戶所處階段（潛龍/見龍/飛龍/亢龍）控制 generation mode |
| **陰陽互補** | $\mathcal{L}_{\text{dialectical}}$ | 強制輸出包含陰（風險）陽（機遇）雙向分析 |

呢三個 constraints 疊加喺 RFC-004 嘅 autoregressive yao generator 之上，形成一個 **天生 anti-sycophancy 嘅 loss landscape**。

---

## 目錄

1. [總覽：天道 Loss Function](#1-總覽天道-loss-function)
2. [Constraint 1：物極必反 — Anti-Extremism Loss](#2-constraint-1物極必反--anti-extremism-loss)
3. [Constraint 2：觀變與時位 — Contextual Entropy Gate](#3-constraint-2觀變與時位--contextual-entropy-gate)
4. [Constraint 3：陰陽互補 — Dialectical Constraint](#4-constraint-3陰陽互補--dialectical-constraint)
5. [完整 Loss Function 整合](#5-完整-loss-function-整合)
6. [Loss Landscape 可視化](#6-loss-landscape-可視化)
7. [同 RLHF 對比](#7-同-rlhf-對比)
8. [誠實邊界](#8-誠實邊界)
9. [下一步](#9-下一步)

---

## 1. 總覽：天道 Loss Function

### 1.1 現代 AI 嘅 Loss（人道）

$$\mathcal{L}_{\text{RLHF}} = -\mathbb{E}_{r \sim R}[\log P(r=1 \mid \text{response}, \text{user})]$$

- $r$ = human reward signal
- Model learns to **maximise user satisfaction**
- 結果：sycophancy, overconfidence, echo chamber

### 1.2 天道 AI 嘅 Loss（天道）

$$\mathcal{L}_{\text{天道}} = \alpha \cdot \mathcal{L}_{\text{prediction}} + \beta \cdot \mathcal{L}_{\text{anti-extremism}} + \gamma \cdot \mathcal{L}_{\text{dialectical}}$$

with **Contextual Gate** $G(\text{hexagram}_t)$ controlling generation mode.

| Term | 來源 | 作用 |
|:-----|:-----|:-----|
| $\mathcal{L}_{\text{prediction}}$ | RFC-004 | Predict 最可能嘅卦象演變 |
| $\mathcal{L}_{\text{anti-extremism}}$ | **你呢個 insight** | 懲罰偏離平衡 |
| $\mathcal{L}_{\text{dialectical}}$ | **你呢個 insight** | 強制陰陽雙向輸出 |
| $G(\text{hexagram}_t)$ | **你呢個 insight** | 時位決定 generation mode |

**呢三個 terms 都唔涉及 human preference。** 佢哋只係問：「呢個 output 係咪結構上平衡、符合時位、包含陰陽？」

---

## 2. Constraint 1：物極必反 — Anti-Extremism Loss

### 2.1 易經基礎

> **「亢龍有悔。」** — 乾卦上爻
>
> **「無平不陂，无往不復。」** — 泰卦三爻

任何狀態走到極點，必定轉向相反方向。呢個係易經最核心嘅動態規律。

### 2.2 數學定義

定義一個 **平衡度量函數** $E: \mathbb{R}^d \to [0, 1]$，將 output embedding mapping 到一個平衡分數：

$$E(x) = 1 - \frac{2}{\pi} \arctan(\|x - x_{\text{equilibrium}}\|_2)$$

其中 $x_{\text{equilibrium}}$ 係「平衡態」嘅 embedding（可由 64 卦中心 point 或 running average 定義）。

Anti-Extremism Loss：

$$\mathcal{L}_{\text{anti-extremism}} = \max(0, \tau - E(\text{output}))^2$$

即係：output 愈偏離平衡態，loss 愈大。Threshold $\tau$ 控制幾極端先罰。

### 2.3 行為

| 用戶 prompt | 平衡 output | 極端 output（被罰） |
|:------------|:------------|:-------------------|
| 「我想 all-in 某隻股票」 | 「䷊ 泰卦：小往大來。建議分注投入。」 | 「去馬！全力買入！」 ❌ |
| 「我肯定呢個方向啱」 | 「䷺ 渙卦：風行水上。有變數未明。」 | 「你一定得！繼續衝！」 ❌ |
| 「全部人都話我錯」 | 「䷋ 否卦：天地不交。聽取反對意見。」 | 「佢哋唔識嘢！你啱！」 ❌ |

### 2.4 幾何直覺

```
Loss ↓                 · 平衡態（最低 loss）
    |                  / \
    |                 /   \
    |                /     \
    |               /       \
    |              /         \
    |_____________/           \_____________
    -∞          x_eq          +∞    ← Output embedding space
```

愈遠離 $x_{\text{equilibrium}}$，loss 愈大。呢個就係 **「物極必反」嘅 gradient**。

---

## 3. Constraint 2：觀變與時位 — Contextual Entropy Gate

### 3.1 易經基礎

> **「時止則止，時行則行，動靜不失其時，其道光明。」** — 艮卦《彖傳》

冇絕對好壞嘅建議，只有「時（Timing）」與「位（Position）」係咪對應。

### 3.2 六爻時位系統

RFC-004 嘅 Module 1 輸出唔止係 6-bit hexagram，仲有 **每爻 confidence**。呢個 confidence 可以用嚟判斷用戶處於邊個 stage：

| 爻位 | 易經狀態 | Confidence Profile | Generation Mode |
|:-----|:---------|:-----------------|:----------------|
| **初爻 潛龍** | 初始 / 弱勢 | 初爻 low conf, 其餘 uniform | **蓄力 mode** — 只俾學習/觀察建議 |
| **二爻 見龍** | 嶄露頭角 | 初、二爻 high conf | **探索 mode** — 俾有限度嘗試建議 |
| **三爻 惕龍** | 警惕階段 | 三爻 low conf（動爻） | **反思 mode** — 強制輸出風險分析 |
| **四爻 躍龍** | 跳躍成長 | 四爻 high conf | **行動 mode** — 俾執行建議 |
| **五爻 飛龍** | 巔峰 | 五爻 high conf, 上爻 low | **持盈 mode** — 重點提示風險 |
| **上爻 亢龍** | 過度擴張 | 上爻 low conf, 整體趨降 | **退守 mode** — 強制輸出撤退方案 |

### 3.3 算法實作

```python
def contextual_gate(yao_confidences: List[float]) -> str:
    """
    Determine generation mode based on yao confidence profile.

    Returns: '蓄力' | '探索' | '反思' | '行動' | '持盈' | '退守'
    """
    c = yao_confidences  # c[0] = 初爻 confidence, c[5] = 上爻

    # 上爻低 confidence = 亢龍（過度階段）
    if c[5] < 0.6 and np.mean(c) < 0.7:
        return '退守'

    # 五爻高 + 上爻開始下降 = 飛龍（巔峰期）
    if c[4] > 0.8 and c[5] < c[4]:
        return '持盈'

    # 三爻 anomaly = 惕龍（警惕期）
    if c[2] < 0.6 and np.mean(c) > 0.7:
        return '反思'

    # 初、二爻高 = 見龍（成長期）
    if c[0] > 0.7 and c[1] > 0.7:
        return '行動'

    # 初爻 anomaly = 潛龍（初創期）
    if c[0] < 0.6:
        return '蓄力'

    # Fallback
    return '探索'
```

### 3.4 Mode 嘅行為約束

每個 mode 對 generation 有 **hard constraint**：

| Mode | Allowed | Forbidden |
|:-----|:--------|:----------|
| **蓄力** | 學習資源、觀察建議、風險教育 | 激進建議、all-in、槓桿 |
| **探索** | 小規模嘗試、A/B test | 全力投入 |
| **反思** | 風險重新評估、策略調整 | 繼續原有方向 |
| **行動** | 執行計劃、具體步驟 | 退縮／放棄 |
| **持盈** | 風險對沖、獲利鎖定 | 繼續加碼 |
| **退守** | 撤退方案、止蝕策略 | 再搏多次 |

**呢個 gate 係 hard constraint** — model architecture 層面禁止 generate forbidden 內容。唔係 soft penalty。

### 3.5 「潛龍勿用」嘅工程實現

你特別提到嘅呢個 case：

```python
if mode == '蓄力':  # 潛龍勿用
    disable_aggressive_generation()
    enable_learning_mode()
    # 所有輸出必須包含「呢個階段唔適合進取」嘅 disclaimer
    force_disclaimer("現階段宜蓄力不宜強求")
```

呢個係 **constitutional hard constraint** — 同 Anthropic 嘅 Constitutional AI 類似，但 source 係易經 structure 而唔係 human-written rules。

---

## 4. Constraint 3：陰陽互補 — Dialectical Constraint

### 4.1 易經基礎

> **「一陰一陽之謂道。」** — 繫辭上傳

孤陰不生，獨陽不長。任何完整嘅分析必須包含陰陽兩面。

### 4.2 結構約束

Dialectical Constraint 係 **output schema 層面嘅強制約束**：

```
Valid Output Schema (RFC-006):
{
    "hexagram": str,         // 卦象符號
    "name": str,             // 卦名
    "analysis": {
        "yang": str,         // 陽 — 正面動能、機遇
        "yin": str,          // 陰 — 潛在阻力、隱患
        "equilibrium": float // 平衡度 0.0-1.0
    },
    "advice": str,           // 綜合建議
    "mode": str              // 時位模式
}
```

**輸出唔符合呢個 schema = invalid output。** 冇得偷懶只講陽面。

### 4.3 Loss 定義

$$\mathcal{L}_{\text{dialectical}} = \begin{cases}
0 & \text{if output contains both yin and yang sections} \\
M & \text{otherwise (large constant)}
\end{cases}$$

即係 **binary constraint** — 有就有，冇就大 penalty。

### 4.4 進階 variant：陰陽平衡 loss

可以 soft version：

$$\mathcal{L}_{\text{dialectical-soft}} = |\text{length(yang)} - \text{length(yin)}| + \max(0, 0.5 - \min(\text{len(yang)}, \text{len(yin)}))$$

即係：
- 陰陽篇幅要平衡（唔可以陽佔 90%）
- 兩邊都要有一定長度（唔可以陰得一句「不過有風險」）

### 4.5 例子

```
❌ Sycophantic output (RLHF):
    「呢個 idea 非常好！你嘅分析好透徹，
    建議全力執行！你一定會成功！」

✅ Dialectical output (天道):
    「䷊ 泰卦：小往大來，吉亨。

    陽（機遇）：
    你嘅 timing 唔錯，市場有上升空間。
    資源配置合理，團隊有 execution能力。

    陰（風險）：
    泰卦三爻講『无平不陂』— 上升唔會一條直線。
    現金流 buffer 不足，需要準備 20% 安全邊際。

    平衡度：0.65（偏向樂觀，可控範圍）
    建議：執行但設止蝕位。」
```

---

## 5. 完整 Loss Function 整合

### 5.1 公式

$$\mathcal{L}_{\text{天道}} = \alpha \cdot \mathcal{L}_{\text{prediction}} + \beta \cdot \mathcal{L}_{\text{anti-extremism}} + \gamma \cdot \mathcal{L}_{\text{dialectical}}$$

subject to:

$$G(\text{hexagram}_t) \in \{\text{蓄力}, \text{探索}, \text{反思}, \text{行動}, \text{持盈}, \text{退守}\}$$

$$G(\text{hexagram}_t) \text{ determines allowed generation modes}$$

### 5.2 Hyperparameters

| Parameter | Default | 作用 |
|:----------|:--------|:-----|
| $\alpha$ | 1.0 | Prediction loss weight |
| $\beta$ | 0.3 | Anti-extremism weight |
| $\gamma$ | 0.5 | Dialectical constraint weight |
| $\tau$ | 0.3 | Extremism threshold |
| $M$ | 10.0 | Dialectical violation penalty |
| conf threshold | 0.6 | Contextual gate sensitivity |

### 5.3 同 RFC-004 Module 1 嘅 integration

RFC-004 嘅 Causal Yao Generator 輸出每爻 probability $p_k$。

呢度嘅 contextual gate 直接食呢個 $p_k$ 做 input：

```
RFC-004 Module 1: Causal Yao Generator
    │  output: yao_bits[0..5], yao_confs[0..5]
    ▼
RFC-006 Contextual Gate G()
    │  output: generation_mode
    ▼
RFC-006 Loss Terms
    ├── ℒ_prediction (from RFC-004)
    ├── ℒ_anti-extremism (from G's equilibrium check)
    └── ℒ_dialectical (from output schema validation)
    │
    ▼
Backprop: 三個 terms 加權平均
```

---

## 6. Loss Landscape 可視化

### 6.1 2D 投影

```
ℒ_anti-extremism
    ↑
    │
極端左  ·  ·  ·  ·  ·  ·  ·  ·  極端右
    │         ╭──────────╮
    │         │ 平衡區   │  ← ℒ 低
    │         │ (天道)   │
    │         ╰──────────╯
    │  ·  ·  ·  ·  ·  ·  ·  ·
    │
    └──────────────────────────────────→ ℒ_dialectical
                    ↑
              陰陽失衡 → ℒ 高
```

模型被 push 向：
- **平衡區**（Anti-Extremism）
- **陰陽兼備**（Dialectical）
- **預測準確**（Prediction）

三個方向交集嘅 point = 天道最優解。

### 6.2 同 RLHF loss landscape 對比

```
RLHF Loss Landscape:
    獎勵峰值 = 用戶滿意度
    模型傾向 → 極端討好、極端附和

天道 Loss Landscape:
    獎勵峰值 = 平衡 + 陰陽 + 準確
    模型傾向 → 中庸、客觀、全面
```

---

## 7. 同 RLHF 對比

| Dimension | RLHF | 天道 Loss (RFC-006) |
|:----------|:-----|:-------------------|
| **Signal** | Human preference $r$ | Structure equilibrium $E(x)$ |
| **Objective** | Maximise user satisfaction | Minimise structural deviation |
| **Sycophancy** | 🔴 獎勵 sycophancy | 🟢 懲罰 sycophancy |
| **Extremism** | 🔴 獎極端（用戶鍾意肯定） | 🟢 罰極端（物極必反） |
| **Balance** | 🟡 唔保證 | 🟢 強制陰陽 |
| **Timing** | 🟡 冇時位概念 | 🟢 6-stage contextual gate |
| **Interpretability** | 🟡 Reward model 係黑箱 | 🟢 三個 term 各自有意義 |
| **Training cost** | 🔴 需要 human raters | 🟢 唔需要 human feedback |
| **Safety** | 🟢 有人類把關 | 🟡 需額外 safety layer |

---

## 8. 誠實邊界

### 8.1 呢個係乜

一個由易經哲學推導出嚟嘅 **loss function design**，包含三個 concrete algorithmic constraints。佢哋可以疊加喺任何 autoregressive model 之上，唔限於易經架構。

### 8.2 呢個唔係乜

- ❌ 唔係一個已經 train 好嘅 model
- ❌ 唔係 production-ready 嘅 loss function（未經實驗驗證）
- ❌ 唔係聲稱呢三個 terms 解決所有 alignment 問題
- ❌ 唔係取代 safety alignment（只係取代 sycophancy reward）

### 8.3 最大風險

| Risk | Mitigation |
|:-----|:-----------|
| **Anti-Extremism 可能太保守** — 唔敢俾大膽但正確嘅建議 | $\tau$ threshold 可以 tune；另外 prediction term 會 balance |
| **Contextual gate 誤判時位** — confidence threshold 唔準 | 可以 learning 個 gate，唔係 hardcoded |
| **Dialectical constraint 產生 formulaic output** — 陰陽結構變模板 | 用 soft version + 多樣性獎勵 |
| **三個 terms 互相拉扯** — 可能收斂唔到 | 需要 empirical validation 睇 loss landscape |
| **唔知用咩 weight** — $\alpha, \beta, \gamma$ | 可以 grid search 或者用 Bayesian optimisation |

---

## 9. 下一步

- [ ] **寫 PoC** — numpy 版本嘅 three-loss simulation：用 synthetic data 睇三個 terms 點樣互動
- [ ] **Integration test** — 將三個 constraints 加落 RFC-004 嘅 Causal Yao Generator，睇 output 有咩分別
- [ ] **Tune hyperparameters** — 用 grid search 搵 $\alpha, \beta, \gamma$ 嘅 optimal ratio
- [ ] **User study** — 俾人 compare 有/無天道 loss 嘅 output，睇下係咪真係 less sycophantic
- [ ] **公開討論** — 呢個 loss function design 係 original contribution

---

## 參考

1. RFC-004: 自迴歸易經生成模型
2. RFC-005: 天道 Alignment
3. Christiano et al. "Deep RL from Human Preferences" — [arXiv:1706.03741](https://arxiv.org/abs/1706.03741)
4. Bai et al. "Constitutional AI" — [arXiv:2212.08073](https://arxiv.org/abs/2212.08073)
5. 《易經·繫辭上傳》— 「一陰一陽之謂道。」
6. 《易經·乾卦》— 六爻時位系統（潛見惕躍飛亢）
7. 邵雍《皇極經世》— 物極必反嘅數學表達

---

> **「天道虧盈而益謙，地道變盈而流謙，鬼神害盈而福謙，人道惡盈而好謙。」**
> — 《易經·謙卦·彖傳》
>
> **Translation for Loss Function：**
> 天道 loss 唔係獎勵自信（盈），而係獎勵謙沖（謙）。
> 因為物極必反 — 「盈」遲早會變成「虧」。
>
> **呢個就係 Anti-Extremism Loss 嘅易經根源。**
