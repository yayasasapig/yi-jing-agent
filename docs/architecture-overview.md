# Architecture Overview — Yi-Jing (I Ching) Six Lines AI Agent Framework

## Core Concept

The Yi-Jing Agent framework applies the ancient Chinese **I Ching (易經)** divination system as a **structured lifecycle and fault-tolerance framework** for modern AI agents.

### Why I Ching?

| I Ching Concept | AI Agent Counterpart | Common Logic |
|:----------------|:---------------------|:-------------|
| **Six Lines (六爻時位)** | Execution lifecycle stages | Each position has different behavioral norms |
| **Moving Line Mutation (動爻變卦)** | Dynamic fault tolerance | Local XOR flip → new global strategy |
| **3D Reflection (錯綜互卦)** | Multi-dimensional review | Hidden motive, adversarial, user perspective |
| **Cyclical Return (周流六虛)** | Spiral recursion | Complete cycle → compress → next level |

---

## The Six Lines Lifecycle

```
Line 1 (Hidden Dragon) ── Pure Understanding ──→ Task Graph
Line 2 (Field Dragon) ─── Sandbox Testing ────→ Feasibility Report
Line 3 (Alert Dragon) ─── 3D Reflection ──────→ Safety Gate
Line 4 (Leaping Dragon) ─ Authorization ──────→ Confirm/Pivot
Line 5 (Flying Dragon) ── Full Execution ─────→ Core Payload
Line 6 (Regretful Dragon) Memory Compression ─→ LTM Write
```

### Line 1: Hidden Dragon (潛龍勿用)
- **Pure understanding phase** — scan memory, parse intent, collect context
- **STRICT RULE**: NO external tool calls, NO API, NO subagents
- **Output**: Structured Task Graph (JSON/YAML)

### Line 2: Field Dragon (見龍在田)
- **Sandbox testing** — test feasibility in isolated environment
- Spawn mini-workers, generate prototypes
- **Output**: Feasibility Report + Plan A

### Line 3: Alert Dragon (終日乾乾)
- **Mandatory 3D Reflection** — the most innovative component
- Three dimensions:
  1. **Interlocking (互卦)** — deep user needs analysis
  2. **Opposite (錯卦)** — adversarial red-teaming
  3. **Reversed (綜卦)** — end-user perspective shift
- **Output**: Safety Report (pass/fail + issues)

### Line 4: Leaping Dragon (或躍在淵)
- **Authorization Gate** — risk-based human-in-the-loop
- 4 levels: Auto → Notify → Confirm → Human Execute
- **Output**: Authorization signal

### Line 5: Flying Dragon (飛龍在天)
- **Full power execution** — parallel subagents, API calls, data integration
- **Critical rule**: partial failure ≠ total failure
- **Output**: Core Payload

### Line 6: Regretful Dragon (亢龍有悔)
- **Memory compression** — evaluate, compress, persist to LTM
- Clean up temporary data
- **Output**: LTM write

---

## Dynamic Hexagram Mutation (動爻變卦)

When any line encounters an error, the system:

1. **Detects the fault** at specific line position
2. **XOR flips** that bit in the 6-bit state code
3. **Looks up** the new hexagram in the 64-hexagram table
4. **Executes** the corresponding strategy

```
Initial: ䷀ 111111 (Everything OK)
                ↓
Line 5 API timeout → flip bit 5
                ↓
Mutation: ䷉ 111011 (Tread Carefully)
                ↓
Strategy: Degrade to Line 2 sandbox simulation
```

## 3D Reflection Engine (錯綜互卦)

A mandatory three-dimensional review at Line 3:

| Dimension | I Ching | Method | Question |
|:----------|:--------|:-------|:---------|
| 🔍 **Interlocking** | 互卦 (2-3-4 + 3-4-5 lines) | Chain-of-thought | What does user *really* want? |
| ⚔️ **Opposite** | 錯卦 (bitwise NOT) | Red team | Where does this plan *definitely* fail? |
| 👁️ **Reversed** | 綜卦 (reverse order) | UX shift | How does the end-user experience this? |

---

## Project Structure

```
src/
├── agent_state.py      # Core state machine (YiJingAgentState)
├── executor.py         # Lifecycle executor
├── hexagram_table.py   # 64 hexagrams → name + strategy
├── reflection.py       # 3D reflection engine
└── yao_positions.py    # Line enums & definitions
```

The framework is **platform-agnostic** — works with Hermes Agent, OpenClaw, AutoGPT, LangChain, or any LLM-based agent system.
