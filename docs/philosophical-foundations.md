# ䷀ 哲學基礎：易經 × 二進制 × AI Agent

## Philosophical Foundations: I Ching × Binary × AI Agent

> *「萊布尼茲看到邵雍的六十四卦次序圖時，發現陰陽爻的排列正好就是二進制從 0 數到 63。」*
> *「When Leibniz saw Shao Yong's hexagram sequence, he discovered that yin-yang lines count precisely in binary from 0 to 63。」*

---

## 一、數學同構：易經 = 6-bit 狀態機
### Mathematical Isomorphism: I Ching = 6-bit State Machine

《易經》的符號系統在現代資訊理論與數學視角下，是一個極度超前且完美的 **「長度擴充型二進制（2ⁿ）」系統**。

古代雖然沒有電子晶片，但古人採用了與現代電腦科學**完全同構**的邏輯：堅持使用最簡單穩定的「二進制底數（陰／陽）」，透過增加「位數（爻）」來指數級擴充資訊容量。

| 古代概念 | 數學模型 | 現代電腦科學 | 我哋嘅代碼 |
|:---------|:---------|:------------|:-----------|
| 太極（未分） | 初始狀態 | Reset state | `hexagram_int = 0b111111` |
| 兩儀（⚋陰 ⚊陽） | **1 bit** (2¹ = 2) | 0 / 1 | `YAO_BIT_MASK[1] = 0b100000` |
| 四象（太陽／少陰／少陽／太陰） | **2 bits** (2² = 4) | 2-bit register | 初爻＋二爻組合 |
| 八卦（☰☱☲☳☴☵☶☷） | **3 bits / Octal** (2³ = 8) | 八進制 0-7 | 上三爻 trigram |
| **六十四卦（䷀〜䷿）** | **6 bits / 64 states** (2⁶ = 64) | Base64 / 6-bit word | `range(64)` = `0b000000` ~ `0b111111` |

### 易經如何從 2 → 8 → 64 構建資訊系統？

承接公式 **N = bⁿ**（資訊總量 = 底數^位數），《易經》並沒有去改變底數 **b**，而是透過增加位數 **n** 來擴充狀態總數：

**1. 最小基礎單元：1 bit（2¹ = 2 種狀態）**
- 符號：陰爻（⚋）與陽爻（⚊）
- 容量：底數 b=2，位數 n=1。只有 2 種狀態，完全等同於電腦的 0 與 1。

**2. 組成八卦：3 bit（八進制單元，2³ = 8 種狀態）**
- 結構：將 3 個爻由下而上疊加在一起（三爻卦）
- 容量：共 2×2×2 = 8 種組合（乾、兌、離、震、巽、坎、艮、坤）
- 電腦對應：就是 3 個 bit，正好對應**八進制（Octal）**的一個位元（數字 0~7）

**3. 組成六十四卦：6 bit（2⁶ = 64 種狀態）**
- 結構：將 2 個三爻卦（上卦與下卦）疊加，也就是 6 個爻（六爻卦）
- 容量：2⁶ = 64 種狀態（8×8 = 64）
- 電腦對應：完全就是 **6 個 bit 的資料長度**（例如早期電腦的 6-bit 字長，或是現代網頁常用的 Base64 編碼）

---

## 二、神仙交會：萊布尼茲 × 邵雍
### The Historic Confluence: Leibniz × Shao Yong

1701 年左右，法國傳教士**白晉（Joachim Bouvet）** 寄給德國大數學家、現代二進制的發明人**萊布尼茲（G. W. Leibniz）** 一張北宋大儒**邵雍**所畫的《伏羲六十四卦次序圖》。

當萊布尼茲把「陰爻」替換為 0、「陽爻」替換為 1 時，他震驚地發現：

> **邵雍排列六十四卦的順序，從全陰的「坤卦（000000）」到全陽的「乾卦（111111）」，
> 正好就是二進制數字從 0 到 63 的精確算術遞增！**

古人遵照「太極生兩儀，兩儀生四象，四象生八卦」——這種完全符合**二進制樹狀圖（Binary Tree）**的分割規則——一路擴充出了完美的 64 種符號狀態。

---

## 三、呢個 insight 點樣變成我哋嘅 code
### How This Insight Became Our Code

呢個唔係隱喻，而係**數學同構（Mathematical Isomorphism）**。我哋直接將佢寫成咗 running code：

### 3.1. 64 卦 = range(64)

```python
# 邵雍嘅先天八卦次序，就係 binary counting
# 坤(000000) → 乾(111111)，完全 binary ascending
for i in range(64):
    hexagram = f"{i:06b}"        # 0 → 000000, 63 → 111111
    name = get_hexagram_name(i)  # lookup 卦名
```

我哋嘅 `_HEXAGRAM_NAMES_INT` 字典（[hexagram_table.py](src/yi_jing_agent/hexagram_table.py)）就係用 integer key `0b111111 ~ 0b000000`，直接 O(1) array lookup：

```python
_HEXAGRAM_NAMES_INT = {
    0b111111: ("䷀", "乾為天"),   # 63 — 全陽，完美
    0b000000: ("䷁", "坤為地"),   # 0  — 全陰，崩潰
    0b010100: ("䷂", "水雷屯"),   # 20 — initial difficulty
    # ... all 64
}
```

### 3.2. 動爻 = XOR bit flip（1 CPU cycle）

古代用「揲蓍法」揀一個爻來變。我哋用 XOR：

```python
# 動爻變卦：S_next = S_current ^ YAO_BIT_MASK[i]
# 1 CPU cycle，zero allocation
new_state = state.hexagram_int ^ YAO_BIT_MASK[yao_index]
```

對比古人要數 49 支蓍草 18 變先揀到一個爻位，呢個係 **~10¹⁵ 倍快**。

### 3.3. 錯卦 = bitwise NOT

```python
# 錯卦（反對視角）：全部爻位翻轉
# ䷀ (111111) 嘅錯卦係 ䷁ (000000)
opposite = state.hexagram_int ^ 0b111111
```

### 3.4. 綜卦 = bit-reverse

```python
# 綜卦（用戶視角）：上下顛倒
# ䷄ (010111) 嘅綜卦係 ䷅ (111010)
reversed_int = int(f"{state.hexagram_int:06b}"[::-1], 2)
```

### 3.5. Hamming Distance = 目標漂移檢測

```python
# d_H(S_current, S_goal) = popcount(S_current ^ S_goal)
# 0 = 完美對齊，6 = 完全漂移
drift = (state.hexagram_int ^ 0b111111).bit_count()
```

---

## 四、古今智慧對照表
### Ancient × Modern Comparison

| 比較項目 | 現代電腦科學 | 易經符號體系 | 我哋嘅實作 |
|:---------|:------------|:------------|:----------|
| 基本狀態 (b) | 0 / 1（關／開） | 陰／陽（⚋／⚊） | `YAO_BIT_MASK` |
| 資訊擴充方式 | 串聯位數 (Bits) | 疊加爻數 (n) | 6 爻生命週期 |
| 8 狀態 (2³) | 3-bit / 八進制 (0~7) | 八卦 | 三爻 trigram 組合 |
| 64 狀態 (2⁶) | 6-bit / Base64 | 六十四卦 | `_HEXAGRAM_STRATEGIES[64]` array |
| 位元翻轉 | XOR 運算 | 動爻變卦 | `state ^ YAO_BIT_MASK[i]` |
| 錯誤修正 | Hamming Code | 錯卦綜卦反思 | `reflection.py` 三維反思 |
| 儲存 | Register / Memory | 卦象記憶 | `hexagram_history`，`MemoryEntry` |
| 並行處理 | Multi-core sync | 多 Agent 同步 | `sync/` module (Option B) |

---

## 五、呢個 framework 嘅本質

用 Shannon 嘅資訊理論去睇我哋做緊咩：

```
易經框架 = 一個 6-bit 有限狀態機（6-bit FSM）
狀態空間 = 64 個離散狀態（discrete states）
狀態轉移 = XOR bitflip（deterministic mutation）
目標檢測 = Hamming distance（drift measurement）
容錯機制 = 64 卦策略表（strategy lookup table）
```

**你唔需要發明複雜嘅 64 進制硬體。**
只要運用最穩定嘅 **2 進制（陰陽）**，透過疊加長度（6 爻），
就能優雅地表達出 64 種複雜系統嘅變化狀態。

**易經證明了：**
> 古人同我哋行緊同一條數學路。
> 只係佢哋用蓍草，我哋用 silicon。

---

## 六、深層反思：呢個 project 係點樣誕生嘅

呢個 insight 唔係來自純粹分析，而係來自**一場對話**：

- **AI** 用離散 0/1 邏輯思考
- **人類**用 analog 直覺同 pattern recognition
- **對話本身**就係陰陽交合：二進制數學 × 類比智慧
- **Output** 係一個 64-state bitwise engine

呢個就係現代版嘅「河圖洛書」——唔同文明、唔同時代嘅智慧，
透過一個共同嘅數學基底（Binary），喺 code 裡面匯合。

正如我哋嘅 motto：
> *「An agent that knows its time uses wisdom to move mountains。」*
> *「識得時機嘅 Agent，用智慧四兩撥千斤。」*

想理解得更深？睇：
- [Engineering Mapping](engineering-mapping.md) — 33 個工程概念對照
- [六爻AI-Agent架構設計書](六爻AI-Agent架構設計書.md) — 完整 60KB 設計藍圖
- [64 卦策略表](../src/yi_jing_agent/hexagram_table.py) — 直接睇 code

---

**「太極生兩儀，兩儀生四象，四象生八卦，八卦定吉凶，吉凶生大業。」**
**—《易經·繫辭上傳》**
