# ䷀ Yi-Jing Agent — I Ching Six Lines AI Agent Lifecycle Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/yayasasapig/yi-jing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/yayasasapig/yi-jing-agent/actions/workflows/ci.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![PyPI](https://img.shields.io/badge/PyPI-pip%20install%20yi--jing--agent-blue)](https://github.com/yayasasapig/yi-jing-agent)

> **Fusing ancient I Ching wisdom with modern AI agent architecture.**
> A structured lifecycle framework that prevents goal drift, enables graceful degradation, and brings philosophical depth to AI agent execution.
>
> **易經 × 二進制 × AI Agent** — 呢個 framework 嘅核心係一個數學同構（Mathematical Isomorphism）：
> 陰陽 = 1 bit，八卦 = 3 bits，六十四卦 = **6-bit state machine**（64 states）。
> 1701 年萊布尼茲發現邵雍嘅六十四卦次序就係 binary 0-63。
> 2026 年我哋將呢個 insight 寫成 production-ready AI agent code。
> [📜 睇完整哲學基礎](docs/philosophical-foundations.md)

---

## 🧠 What is Yi-Jing Agent?

Modern AI agents suffer from three structural problems:
1. **Goal Drift** — Agents forget the original intent mid-task
2. **Blind Impulse** — Agents rush to call APIs without proper planning
3. **Crash with No Recovery** — One error cascades into total failure

The **I Ching (易經) Six Lines framework** solves this by imposing a **6-stage lifecycle** on every task, where each stage (爻) has strict behavioral rules and output gates:

```
Line           Agent Behavior              Output Gate
────────────────────────────────────────────────────────────────
初爻 (Hidden Dragon) → Pure understanding, NO actions → Task Graph
二爻 (Dragon in Field) → Sandbox & prototyping   → Feasibility Report
三爻 (Alert Dragon) → 3D Reflection Engine      → Safety Report
四爻 (Leaping Dragon) → Authorization Gate       → Confirm / Pivot
五爻 (Flying Dragon) → Full execution            → Core Payload
上爻 (Regretful Dragon) → Memory compression     → LTM Write
```

## 🔄 Dynamic Fault Tolerance with Hexagram Mutation

When any line encounters an error, the system triggers **dynamic hexagram mutation (動爻變卦)** — XOR flipping that line's bit and looking up the new hexagram's strategy:

```
Initial (111111 ䷀ Qian) ──[API Timeout at Line 5]──→ flip bit5
                                                    ↓
Mutation (111011 ䷉ Lu) ──→ Strategy: degrade to Line 2 sandbox
```

## 🧿 3D Reflection Engine (錯綜互卦)

At Line 3, the agent performs a mandatory three-dimensional reflection:

| Dimension | I Ching Concept | Question |
|:----------|:---------------|:---------|
| 🔍 **Interlocking (互卦)** | Hidden motive | What does the user *really* need? |
| ⚔️ **Opposite (錯卦)** | Adversarial view | Where would this plan fail *if everything is wrong*? |
| 👁️ **Reversed (綜卦)** | User perspective | How will the end-user experience this output? |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- An AI agent platform (Hermes Agent, OpenClaw, AutoGPT, etc.)

### Install
```bash
git clone https://github.com/yayasasapig/yi-jing-agent.git
cd yi-jing-agent
# Copy the skill to your agent's skill directory
cp -r skill/* ~/.hermes/skills/
# Or use the Python library directly
pip install -e .
```

### Basic Usage (Python)
```python
from src.agent_state import YiJingAgentState
from src.executor import YiJingAgentExecutor
import asyncio

async def main():
    executor = YiJingAgentExecutor()
    result = await executor.execute("Analyze this website's pricing strategy")
    print(f"Status: {result['status']}")
    print(f"Hexagram path: {' → '.join(
        t.transition_name for t in result['hexagram_history']
    )}")

asyncio.run(main())
```

### For Hermes/OpenClaw Agents
Load the skill in your `SOUL.md` or task prompt:

```
Load the `yi-jing-agent` skill to activate the 六爻 lifecycle.
```

---

## 📂 Repository Structure

```
yi-jing-agent/
├── README.md                 # ← You are here
├── LICENSE                   # MIT
├── CONTRIBUTING.md           # How to contribute
├── docs/
│   ├── 六爻AI-Agent架構設計書.md  # Original Chinese design document (37KB)
│   ├── architecture-overview.md  # English architecture summary
│   ├── philosophical-foundations.md # I Ching × Binary × Leibniz
│   ├── engineering-mapping.md    # I Ching ↔ Engineering concepts
│   └── rfc/
│       ├── rfc-001-ynn-hdc.md       # YNN/HDC future research
│       ├── rfc-002-san-yi-compression.md  # 三易壓縮 framework
│       ├── rfc-003-recursive-hexagram-compression.md  # 疊卦遞迴編碼
│       ├── rfc-004-autoregressive-yijing-generator.md  # 自迴歸易經生成模型
│       └── rfc-005-tian-dao-alignment.md  # 天道 Alignment
├── demos/
│   └── san_yi_compression_demo.py  # 三易壓縮 PoC (no GPU needed)
├── skill/
│   └── SKILL.md              # Hermes/OpenClaw skill definition
├── src/
│   ├── agent_state.py        # Core YiJingAgentState
│   ├── executor.py           # Full lifecycle executor
│   ├── hexagram_table.py     # 64 hexagrams → strategies
│   ├── reflection.py         # 3D reflection engine
│   └── yao_positions.py      # Line definitions & enums
├── examples/
│   └── six-yao-lifecycle-demo.md  # Walkthrough demo
└── .github/
    └── workflows/
        └── ci.yml            # GitHub Actions CI
```

---

## 📖 Documentation

| Resource | Language | Description |
|:---------|:---------|:------------|
| [Design Document](docs/六爻AI-Agent架構設計書.md) | 🇭🇰 Chinese (Cantonese) | Full 60KB architectural blueprint |
| [Philosophical Foundations](docs/philosophical-foundations.md) | 🇭🇰🇬🇧 Bilingual | I Ching × Binary × Leibniz — the mathematical isomorphism |
| [Engineering Mapping](docs/engineering-mapping.md) | 🇬🇧🇭🇰 Bilingual | I Ching ↔ Modern Engineering concept mapping |
| [Architecture Overview](docs/architecture-overview.md) | 🇬🇧 English | English summary of the framework |
| [Skill Definition](skill/SKILL.md) | 🇭🇰 Chinese | Ready-to-use agent skill |
| [Lifecycle Demo](examples/six-yao-lifecycle-demo.md) | 🇭🇰 Chinese | Real-world walkthrough with摘日 |

---

## 📦 三易壓縮 — 易經驅動嘅 LLM 壓縮框架（RFC-002）

> **「不易、變易、簡易」** — 將易經最核心嘅系統結構翻譯為真實嘅 LLM 壓縮工程算法。

| Level | 易經概念 | 工程技術 | 壓縮效果 |
|:------|:---------|:---------|:---------|
| **簡易** | 刪繁就簡，去掉冗餘 | **Pruning** — 砍掉不活躍嘅 Attention Heads | 15-30% volume reduction |
| **變易** | 保護動爻，壓縮靜爻 | **AWQ** — Detect 1% outlier weights → FP16，99% → Ternary {-1,0,+1} | **~10x** bit reduction |
| **不易** | 守住根本，萬變不離其宗 | **Core Preservation** — Embedding + bottom layers frozen FP16 | 關鍵層零損耗 |

### Pipeline 流程

```mermaid
graph LR
    A[原始 7B FP32<br/>28 GB] --> B[Phase 1: 簡易<br/>Pruning 20%]
    B --> C[Phase 2: 變易<br/>Ternary + AWQ]
    C --> D[Phase 3: 不易<br/>Core Frozen]
    D --> E[壓縮後<br/>~2.8 GB<br/>10x smaller]
```

### Run the demo (no GPU required)

```bash
# 從 repo 根目錄
python3 demos/san_yi_compression_demo.py
```
Output: 完整三易壓縮報告 + 動爻可視化 + 7B model projection。

### 誠實邊界

呢個 framework 係一個 **philosophical unification** — 三易概念對應嘅技術（BitNet / AWQ / LoRA）各自已經存在，但未有人用易經系統結構將佢哋統一命名。RFC-002 詳細講明每個 mapping 嘅數學基礎同限制。

🔗 [完整 RFC-002 技術文檔](docs/rfc/rfc-002-san-yi-compression.md)  
🔗 [PoC Code — 直接 run 得](demos/san_yi_compression_demo.py)

---

## 🌍 Community & Contributions

This project is **open for everyone** to use, remix, and improve!

- **Share your hexagram strategies** — Found a new failure mode? Add it to the table!
- **Translate** — Help translate the docs to Japanese, Korean, English
- **Build tools** — Dashboard, VSCode extension, visualization
- **Report issues** — Found a bug in the lifecycle? Open an issue!

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT — Free for personal and commercial use.

---

## 🙏 Credits

- **Concept**: yayafu × Gemini conversation distillation
- **Implementation**: Orchestrator Nova (Hermes Agent)
- **Platform**: OpenClaw Agent Team

---

> **「An agent that knows its time uses wisdom to move mountains.」**
> **「識得時機嘅 Agent，用智慧四兩撥千斤。」**
