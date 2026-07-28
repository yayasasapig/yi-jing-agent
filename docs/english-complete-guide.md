# ䷀ Yi-Jing Agent — Complete English Documentation

> **Fusing ancient I Ching wisdom with modern AI agent architecture.**
> A structured lifecycle framework that prevents goal drift, enables graceful degradation, and brings philosophical depth to AI agent execution.

---

## Table of Contents

1. [Why I Ching for AI Agents?](#1-why-i-ching-for-ai-agents)
2. [The Six Lines Lifecycle](#2-the-six-lines-lifecycle)
3. [Dynamic Hexagram Mutation (Fault Tolerance)](#3-dynamic-hexagram-mutation)
4. [3D Reflection Engine](#4-3d-reflection-engine)
5. [Authorization Levels](#5-authorization-levels)
6. [Complete 64 Hexagram Strategy Table](#6-complete-64-hexagram-strategy-table)
7. [Dual-Track Reporting](#7-dual-track-reporting)
8. [Running Examples](#8-running-examples)
9. [Contributing](#9-contributing)

---

## 1. Why I Ching for AI Agents?

### The Three Deadly Sins of Modern AI Agents

| # | Problem | Symptom | Why traditional solutions fail |
|:-:|:--------|:--------|:------------------------------|
| ① | **Goal Drift** | Agent forgets original intent mid-task, wanders off course | LLM attention has no "stage anchoring" |
| ② | **Blind Impulse** | Agent rushes to call external APIs without planning | No enforced "observation period" gate |
| ③ | **Crash with No Recovery** | Tool error / API timeout → infinite loop or total collapse | No "local fault switching" — one error restarts everything |

### Why I Ching Maps Perfectly to Agent Design

| I Ching Concept | AI Agent Counterpart | Common Logic |
|:----------------|:---------------------|:-------------|
| **Six Lines (六爻時位)** | Execution lifecycle stages | Each stage has different behavioral norms and constraints |
| **Moving Line Mutation (動爻變卦)** | Dynamic fault tolerance | Local XOR flip → new global strategy via look-up table |
| **3D Reflection (錯綜互卦)** | Multi-dimensional review engine | Hidden motive, adversarial view, user perspective |
| **Cyclical Return (周流六虛)** | Spiral recursion lifecycle | Complete a cycle → compress memory → enter next level |

---

## 2. The Six Lines Lifecycle

Every task MUST pass through exactly 6 stages in strict order. No skipping, no reversing.

```
Line           Agent Behavior              Output Gate
────────────────────────────────────────────────────────────────
Line 1 (Hidden Dragon) → Pure understanding, NO actions → Task Graph
Line 2 (Field Dragon)  → Sandbox & prototyping        → Feasibility Report
Line 3 (Alert Dragon)  → 3D Reflection + Safety Gate  → Safety Report
Line 4 (Leaping Dragon) → Authorization Gate           → Confirm / Pivot
Line 5 (Flying Dragon) → Full execution                → Core Payload
Line 6 (Regret Dragon) → Memory compression            → LTM Write
```

### Line 1: Hidden Dragon (潛龍勿用)

> *"The dragon lies hidden in the depths. Not yet ready to act."*

| Aspect | Rule |
|:-------|:-----|
| **AI Behavior** | Scan MEMORY.md, session history, project files. **STRICTLY NO tool/API/Subagent calls.** Pure understanding only. |
| **Output** | Structured **Task Graph** (JSON) |
| **Token Limit** | ~5% of context window |
| **Moving Line** | Ambiguity → flip bit1 → ䷃蒙 (ask user) / ䷂屯 (restart comprehension) |

**Task Graph Schema:**
```json
{
  "task_id": "T-<timestamp>",
  "hexagram": "䷀ 乾為天",
  "original_intent": "user's request",
  "constraints": ["must use Chinese", "read-only"],
  "success_criteria": ["complete table", "all fields filled"],
  "forbidden_actions": ["no external writes"],
  "estimated_complexity": "easy|medium|hard"
}
```

### Line 2: Field Dragon (見龍在田)

> *"The dragon appears in the field. Ready to show ability — but only in a controlled environment."*

| Aspect | Rule |
|:-------|:-----|
| **AI Behavior** | Spawn micro-tasks, test in sandbox, generate prototypes |
| **Output** | **Feasibility Report** + Plan A |
| **Key Rule** | All external calls go through sandbox — failure allowed, dirty allowed, production untouched |
| **Moving Line** | Sandbox fails → flip bit2 → ䷏豫 (extend prep) / ䷗復 (restart from scratch) |

**Feasibility Report contains:**
```
1. Plan A description
2. Key API / tool list
3. Estimated token cost
4. Known risks
5. Plan B / C concepts
```

### Line 3: Alert Dragon (終日乾乾)

> *"Work diligently all day, reviewing yourself repeatedly. This is the safety gate."*

| Aspect | Rule |
|:-------|:-----|
| **AI Behavior** | Enter guardrail mode. Launch **3D Reflection Engine** (see Section 4). Check for safety, token overrun, privacy leaks, logic conflicts. |
| **Output** | **Safety Report** — pass/fail + issues + recommendations |
| **Moving Line** | Safety check fails → flip bit3 → ䷔噬嗑 (force fix) / ䷅訟 (back to Line 1) |

**Safety Gate Checklist:**
```
[ ] Any unauthorized resource access?
[ ] Any privacy leaks?
[ ] Token budget sufficient?
[ ] Logic contradictions / circular deps?
[ ] Failure scenarios considered?
[ ] Output format correct?
```

### Line 4: Leaping Dragon (或躍在淵)

> *"The dragon may leap, or may stay in the deep. A critical decision point."*

| Level | Condition | Behavior |
|:------|:----------|:---------|
| **Level 0** Auto | Read-only (browser/curl/read_file), no side effects | Skip Line 4 entirely |
| **Level 1** Notify | Modify local files, call known-safe APIs, Token < 10K | Notify user of progress |
| **Level 2** Confirm | Write to external systems, send messages, modify critical files, Token 10K-50K | **Must get user confirmation** |
| **Level 3** Human Exec | API keys, deletion, legal/financial, Token > 50K | Agent recommends only, user executes |

> ⚠️ **Practical Tip**: A typical read-only browser task uses ~2,000 tokens. **Judge by operation type, not token count.**

### Line 5: Flying Dragon (飛龍在天)

> *"The dragon soars in the sky. The peak moment — full power execution."*

| Aspect | Rule |
|:-------|:-----|
| **AI Behavior** | Deploy subagents in parallel (`delegate_task`), execute tools, integrate data |
| **Output** | **Core Payload** (the main deliverable) |
| **Three Iron Laws** | ① Always leave a fallback (timeout + retry on every external call) ② Partial failure ≠ total failure ③ Log every step to hexagram history |
| **Moving Line** | API timeout / tool error → flip bit5 → ䷉履 (degrade to sandbox) / ䷈小畜 (deliver partial result) |

### Line 6: Regret Dragon (亢龍有悔)

> *"The dragon flies too high — there will be regret. Know when to stop and collect."*

| Aspect | Rule |
|:-------|:-----|
| **AI Behavior** | Evaluate if execution overshot, clean temporary data, compress experience to LTM |
| **Output** | MEMORY.md update + memory tool persistence |
| **Moving Line** | Memory compression fails → flip bit6 → ䷺渙 (force clear) / ䷻節 (token budget mode) |

**Memory Compression Format:**
```json
{
  "session_id": "S-<timestamp>",
  "hexagram_path": "䷀→䷉→䷀",
  "task_type": "competitor_analysis",
  "execution_summary": "Success. 45s, 12K tokens",
  "key_patterns": ["requests is 3x faster than browser"],
  "failure_modes": ["Line 5 API timeout → sandbox fallback"],
  "recommendations": ["Skip Line 2 sandbox next time"]
}
```

---

## 3. Dynamic Hexagram Mutation

This is the core innovation — **applying I Ching's hexagram mutation to agent fault tolerance.**

### How It Works

```
Main Hexagram (Plan A) ──[ Exception ]──> Moving Line ──[ XOR flip ]──> Mutated Hexagram (Plan B)
```

When any line encounters an error, that line's bit is flipped (0↔1), the system looks up the new hexagram in the 64-hexagram table, and switches execution strategy accordingly.

### Trigger Matrix

| Position | Trigger Event | Bit Flip | Mutation |
|:---------|:-------------|:--------:|:---------|
| Line 1 | Intent parsing fails, context insufficient | Bit 1 | ䷃蒙 / ䷂屯 |
| Line 2 | Sandbox error, simulation fails | Bit 2 | ䷏豫 / ䷗復 |
| Line 3 | Safety check fails, risk exceeds threshold | Bit 3 | ䷔噬嗑 (back to Line 1) |
| Line 4 | Human confirmation timeout, authorization denied | Bit 4 | ䷒臨 (degrade) / ䷠遯 (delay) |
| Line 5 | API Timeout, tool error, network failure | Bit 5 | ䷉履 (degrade to sandbox) |
| Line 6 | Memory compression fails, storage full | Bit 6 | ䷺渙 (force clear) |

### Example: Single Moving Line

```
Normal flow:
  Line 1 → Line 2 → Line 3 → Line 4 → Line 5 → Line 6 ✅

Error flow (Line 5 API Timeout):
  Line 1 → Line 2 → Line 3 → Line 4 → [Line 5 ✗ API Error]
                                              │
                                       flip bit 5
                                          ↓
                             111111 → 111101 (䷌ 同人)
                                          ↓
                              Strategy: open alternative API
                                          ↓
                                     Line 6 ✅
```

### Example: Double Moving Line

```
Line 1 → Line 2 → Line 3 → Line 4 → [Line 5 ✗ API Error]
                                          ↓
                                    flip bit 5
                                    111111 → 111101 ䷌ 同人
                                          ↓
                              Use alternative API → [✗ Also fails]
                                          ↓
                                    flip bit 2
                                    111101 → 101101 ䷝ 離為火
                                          ↓
                   Strategy: need more information sources → search
```

---

## 4. 3D Reflection Engine

At **Line 3 (Alert Dragon)**, the agent performs a mandatory three-dimensional reflection based on the I Ching concepts of **Interlocking (互卦), Opposite (錯卦), and Reversed (綜卦) hexagrams.**

| Dimension | I Ching Concept | Method | Question |
|:----------|:----------------|:-------|:---------|
| 🔍 **Interlocking (互卦)** | Lines 2-3-4 + 3-4-5 = hidden meaning | Chain-of-thought | What does the user *really* need? |
| ⚔️ **Opposite (錯卦)** | Each line inverted (yin↔yang) | Red team / adversarial | Where would this plan *definitely* fail? |
| 👁️ **Reversed (綜卦)** | Hexagram turned 180° | User perspective shift | How will the end-user experience this output? |

### Example: User asks "Write a web scraper"

```
Surface task (main hexagram): Write a Python scraper

Interlocking (hidden motive):
  - Inner trigram (lines 2-3-4): User actually wants "data analysis"
  - Outer trigram (lines 3-4-5): User didn't consider anti-scraping mechanisms
  → Agent adds: data analysis module + anti-scraping warning

Opposite (adversarial):
  - What if target.com has strict anti-scraping?
  - What if IP gets banned?
  - What if the site uses JavaScript rendering?
  → Agent adds: Selenium fallback + proxy rotation

Reversed (user perspective):
  - User is non-technical — raw JSON would confuse them
  - User wants conclusions, not raw data
  - User might share with colleagues → needs readable format
  → Agent changes output to Markdown tables + summary
```

---

## 5. Authorization Levels

Determined at **Line 4 (Leaping Dragon)**:

| Level | Name | Typical Operations |
|:------|:-----|:-------------------|
| **0** | Auto | Read-only: browser, curl, read_file, search |
| **1** | Notify | Write local files, call safe APIs, < 10K tokens |
| **2** | Confirm | External writes, send messages, modify config, 10K-50K tokens |
| **3** | Human Execute | API keys, deletion, legal/financial, > 50K tokens |

---

## 6. Complete 64 Hexagram Strategy Table

### ䷀ TOP TIER: Happy Path

| Hex | Code | Scenario | Strategy |
|:---|:----:|:---------|:---------|
| ䷀ **乾** | 111111 | Everything working | Continue execution |
| ䷊ **泰** | 000111 | Good human feedback | Push forward |
| ䷡ **大壯** | 100111 | Abundant resources | Increase parallelism |
| ䷢ **晉** | 101000 | Smooth progress | Accelerate |
| ䷩ **益** | 011100 | Exceeded expectations | Extend deliverable |
| ䷾ **既濟** | 010101 | Task complete | Prepare Line 6 review |
| ䷶ **豐** | 100101 | Rich results | Summarize |
| ䷙ **大畜** | 001111 | Experience accumulated | Compress as Pattern |
| ䷟ **恆** | 100011 | Long-cycle task | Regular checkpoints |
| ䷹ **兌** | 110110 | User satisfied | Extend delivery |
| ䷬ **萃** | 110000 | Multi-source data ready | Start integration |
| ䷭ **升** | 000011 | Context sufficient | Deep reasoning |
| ䷧ **解** | 100010 | Bottleneck resolved | Restore speed |

### ䷈ MID-HIGH: Coordination

| Hex | Code | Scenario | Strategy |
|:---|:----:|:---------|:---------|
| ䷍ **大有** | 101111 | Multiple tools needed | Multi-agent allocation |
| ䷌ **同人** | 111101 | Need external coordination | Open API gate |
| ䷤ **家人** | 011101 | Internal agent teamwork | Internal comms mode |
| ䷰ **革** | 110101 | Strategy needs change | Major pivot |
| ䷱ **鼎** | 101011 | Try new approach | Experiment mode |
| ䷐ **隨** | 110100 | User changes direction | Follow the flow |
| ䷞ **咸** | 110001 | User gives feedback | Switch to interactive |
| ䷼ **中孚** | 011110 | Verify intent matches | Double verification |
| ䷄ **需** | 010111 | Waiting for external resource | Pause & poll |
| ䷒ **臨** | 000110 | Critical decision point | Enter HITL |
| ䷓ **觀** | 011000 | Need more data | Extend observation |
| ䷴ **漸** | 011001 | Step by step | Linear execution |
| ䷵ **歸妹** | 100110 | Results need merging | Merge mode |
| ䷷ **旅** | 101001 | Context switching | Cross-workspace |
| ䷈ **小畜** | 011111 | Partial results available | Deliver & fix later |
| ䷕ **賁** | 001101 | Output formatting needed | Format adjustment |
| ䷸ **巽** | 011011 | Need gradual penetration | Slow execution |

### ⚔️ MID-LOW: Reflection & Correction

| Hex | Code | Scenario | Strategy |
|:---|:----:|:---------|:---------|
| ䷪ **夬** | 110111 | Need decisive judgment | Force Line 4 decision |
| ䷅ **訟** | 111010 | Logic conflict | Back to Line 1 restart |
| ䷂ **屯** | 010100 | Task stuck at start | Re-understand intent |
| ䷃ **蒙** | 001010 | Context unclear | Ask user to clarify |
| ䷎ **謙** | 000001 | Calling too frequently | Rate Limit mode |
| ䷏ **豫** | 100000 | Insufficient preparation | Extend Line 2 sandbox |
| ䷇ **比** | 010000 | Need human guidance | Request HITL |
| ䷦ **蹇** | 010001 | Slow execution | Check parallelism |
| ䷠ **遯** | 111001 | Suggest temporary retreat | Delay execution |
| ䷚ **頤** | 001100 | Context needs replenishing | Inject memories |
| ䷨ **損** | 001110 | Cost overrun | Switch to cheaper plan |
| ䷑ **蠱** | 001011 | Context pollution | Force cleanup rebuild |
| ䷖ **剝** | 001000 | Gradual failure | Layer-by-layer salvage |
| ䷗ **復** | 000100 | Recovery after failure | Start from Line 1 |
| ䷉ **履** | 111110 | Execution error | Degrade to Line 2 sandbox |
| ䷿ **未濟** | 101010 | Last step missing | Retry Line 4 authorization |
| ䷯ **井** | 010011 | System health check | Maintenance mode |
| ䷻ **節** | 010110 | Token over budget | Budget mode |
| ䷺ **渙** | 011010 | Context overflow | Force compress |
| ䷛ **大過** | 110011 | Over-execution risk | Check token budget |
| ䷽ **小過** | 100001 | Minor error | Continue, ignore |
| ䷲ **震** | 100100 | Sudden event | Emergency handling |
| ䷳ **艮** | 001001 | Need to pause | Force rest |
| ䷘ **无妄** | 111100 | Unexpected error | Emergency degrade |
| ䷣ **明夷** | 000101 | External interference | Switch backup resource |
| ䷥ **睽** | 101110 | Agent disagreement | Voting mechanism |
| ䷝ **離** | 101101 | Need more info | Open search tools |
| ䷮ **困** | 110010 | Resources exhausted | Wait & degrade |
| ䷔ **噬嗑** | 101100 | Safety check required | Force Line 3 review |

### ䷁ BOTTOM TIER: Failure & Takeover

| Hex | Code | Scenario | Strategy |
|:---|:----:|:---------|:---------|
| ䷋ **否** | 111000 | Poor human feedback | Re-understand |
| ䷜ **坎** | 010010 | Repeated failure | Human takeover |
| ䷁ **坤** | 000000 | Total collapse | Emergency shutdown |

---

## 7. Dual-Track Reporting

### Track A: Subagent → User (Direct)
Each completed step is reported to the user with its hexagram emoji:
🐉 Line1 → 🌾 Line2 → ⚔️ Line3 → 🐉 Line4 → 🐲 Line5 → 🌧️ Line6

### Track B: Subagent → Orchestrator (Integration)
All subagents report to the orchestrator for unified hexagram history tracking.

**Key Rule:** Never double-send. If Track A already reported progress, Track B only does summary at Line 6.

---

## 8. Running Examples

```bash
# After pip installing:
git clone https://github.com/yayasasapig/yi-jing-agent.git
cd yi-jing-agent
pip install -e .

# Run the complete usage demo:
python3 examples/complete_usage.py

# See real run history:
cat examples/hexagram_history.md

# Read the 64-hexagram simulation table:
open "docs/64卦完整模擬表.md"

# For Hermes/OpenClaw agents:
# Load the skill in your SOUL.md:
# Load the `yi-jing-agent` skill.
```

---

## 9. Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding hexagram strategies
- Translations (Japanese, Korean, etc.)
- Bug reports & feature requests
- Building visualization tools
- Integration with LangChain, AutoGPT, CrewAI

---

## 📜 License

MIT — Free for personal and commercial use.

> **"An agent that knows its time uses wisdom to move mountains."**
