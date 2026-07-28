# RFC-001: Yi-Jing Neural Network (YNN) — Hyperdimensional Computing × 易經

> **Status:** Draft · **Track:** v2.0+ Research  
> **Author:** yayasasapig · **Date:** 2026-07-28  
> **License:** MIT (this document)

## Abstract

This RFC explores the theoretical foundation for a **Yi-Jing Neural Network (YNN)** —
a computational framework that maps the 64 hexagrams of the I Ching (易經) onto
**Hyperdimensional Computing (HDC)** / **Vector Symbolic Architecture (VSA)**.

The core insight: the I Ching's binary system (6-bit hexagrams, 2^6 = 64) is
mathematically isomorphic to a **6-dimensional binary hyperdimensional space**.
Each hexagram can be represented as a hypervector, and I Ching operations
(XOR flip for moving lines, trigram composition, opposite/reversal) map directly
to HDC operations (XOR, Bind, Bundle).

If proven, this could enable:
- Neural-symbolic integration of I Ching reasoning into embedding spaces
- Differentiable hexagram mutation for gradient-based optimization
- Hyperdimensional memory with built-in 64-strategy recall

---

## 1. Mathematical Foundation

### 1.1 The 6-Bit Hexagram Space

Each hexagram is a 6-bit binary vector:

```
䷀ 乾 = [1, 1, 1, 1, 1, 1]
䷁ 坤 = [0, 0, 0, 0, 0, 0]
䷂ 屯 = [0, 1, 0, 1, 0, 0]  (水雷屯)
...
```

This forms a **6-dimensional binary space** with exactly 2^6 = 64 unique states —
a complete, closed space with no "unknown" or "invalid" states.

### 1.2 Hyperdimensional Computing Primer

Hyperdimensional Computing (HDC), also known as Vector Symbolic Architecture (VSA),
operates on high-dimensional vectors (typically D = 1,000–10,000) with three core operations:

| Operation | Symbol | Description | I Ching Analog |
|:----------|:------:|:------------|:---------------|
| **Binding** | ⊕ (XOR) | Associates two symbols | 動爻變卦 (Moving Line XOR flip) |
| **Bundling** | + (sum) | Builds sets of symbols | 卦象組合 (Trigram composition) |
| **Permutation** | ρ(·) | Encodes sequence/order | 爻位順序 (Line position encoding) |
| **Similarity** | cos(·,·) | Measures semantic closeness | 錯綜互卦關係 (Hexagram relations) |

### 1.3 The Mapping

```
HDC Concept              I Ching Concept        Yi-Jing Agent Code
─────────────────────────────────────────────────────────────────────
D-dimensional vector      6-bit hexagram code    hexagram_code: str
XOR binding (⊕)           Moving line mutation   trigger_moving_yao()
Bundle (+)                Hexagram composition   HEXAGRAM_NAMES dict
Permutation (ρ)           Yao position           6-line ordered structure
Cosine similarity         Hexagram relationships  STRATEGIES proximity
Prototype vector          "Pure" trigram          Trigram (3-bit atoms)
```

### 1.4 Dimensionality Considerations

Current hexagram space: **D = 6** (64 states)

For HDC to work properly, D should be much larger than 6:
- Minimum meaningful HDC dimension: D ≈ 1,000
- For robust symbol operations: D ≈ 2,000–10,000
- For embedding integration: D = model hidden size (e.g., 768, 1024, 4096)

**Key question:** Can we project 6-bit hexagrams into a higher-dimensional space
while preserving the I Ching algebraic structure?

Answer: **Yes, via random projection / fractional coding.**

Each 6-bit hexagram `h ∈ {0,1}⁶` can be mapped to a D-dimensional hypervector
`H ∈ {+1,-1}ᴰ` via:

```
H = ϕ(h) = sign(R · h)
```

Where `R ∈ ℝᴰˣ⁶` is a fixed random projection matrix. This preserves:
- XOR structure: `ϕ(h₁ ⊕ h₂) ≈ ϕ(h₁) ⊕ ϕ(h₂)` (binding homomorphism)
- Similarity structure: `h₁ · h₂ ≈ ⟨ϕ(h₁), ϕ(h₂)⟩` (inner product preservation)

---

## 2. Proposed Architecture

### 2.1 YNN Layer: Hexagram Embedding

```
Input: 6-bit hexagram code (string "111111")
        ↓
Projection: R · one_hot(code)  [random projection matrix]
        ↓
D-dimensional hypervector H ∈ {+1,-1}ᴰ
        ↓
Optional: Bundle with context vectors (task type, error signal, stage)
        ↓
Output: Context-aware hexagram embedding
```

### 2.2 Differentiable Hexagram Mutation

Current XOR flip is **discrete and deterministic**:

```python
code_list[yao_index] = "0" if code_list[yao_index] == "1" else "1"
```

YNN would make this **differentiable**:

```
Mutation probability: p_yao = σ(W · context)
                     ↓
Expected hexagram:   E[h] = Σ_{i=1}^{6} p_i · flip_i(h)
                     ↓
Gradient:            ∂E/∂W  backpropagatable through mutation
```

### 2.3 Hyperdimensional Memory

64 hexagram strategies = 64 prototype hypervectors in a **content-addressable memory**:

```
Memory:        M = {H_䷀, H_䷁, ..., H_䷿}   (64 × D)
Query:         q = current hexagram embedding
Retrieval:     h_retrieved = argmax_{i} cos(q, M_i)
Strategy:      STRATEGIES[h_retrieved]
```

This enables:
- **Noisy input tolerance**: Nearby hexagrams retrieve semantically similar strategies
- **Interpolation**: Mixed states retrieve blended strategies
- **Learning**: Strategy vectors can be updated via gradient descent

---

## 3. Relationship to Existing Codebase

### 3.1 What Already Exists

| Component | File | YNN Relevance |
|:----------|:-----|:--------------|
| 64 hexagram codes | `hexagram_table.py` | Foundation vectors |
| XOR flip logic | `agent_state.py:trigger_moving_yao()` | Binding operation primitive |
| Opposite hexagram | `reflection.py:analyze_opposite()` | Bitwise NOT = record-level negation |
| Reversed hexagram | `reflection.py:analyze_reversed()` | Order permutation |
| Strategy lookup | `hexagram_table.py:get_strategy_for_hexagram()` | Memory retrieval target |
| 6-line state machine | `agent_state.py` | Sequential permutation structure |

### 3.2 What Needs to Be Built (v2.0+)

| Module | Effort | Priority |
|:-------|:------:|:---------|
| `ynn/random_projection.py` | ~3 days | High |
| `ynn/hexagram_embedding.py` | ~5 days | High |
| `ynn/differentiable_mutation.py` | ~7 days | Medium |
| `ynn/hyperdimensional_memory.py` | ~5 days | Medium |
| `ynn/layers.py` (nn.Module) | ~7 days | Low |
| `tests/test_ynn.py` | ~3 days | High |

### 3.3 Integration Points

```
┌──────────────────┐     ┌─────────────────────┐
│  YiJingAgentState│────→│  YNN Embedding Layer  │
│  (6-bit state)   │     │  (D-dim hypervector)  │
└──────────────────┘     └───────────────────────┘
         │                         │
         │ XOR flip                │ Differentiable mutation
         ↓                         ↓
┌──────────────────┐     ┌─────────────────────┐
│  64-Strategy Table│←────│  Hyperdimensional    │
│  (deterministic)  │     │  Memory (learnable)  │
└──────────────────┘     └───────────────────────┘
```

---

## 4. Open Questions & Risks

### 4.1 Theoretical Questions

1. **Dimensionality gap**: Can 6-bit → D-dim random projection preserve enough
   I Ching algebraic structure for meaningful neural integration?

2. **Gradient signal**: Will differentiable hexagram mutation provide useful
   gradients, or is the binary space too sparse for gradient-based learning?

3. **Interpretability**: Can hyperdimensional representations be decoded back
   to specific hexagrams, or do they lose discrete structure?

### 4.2 Engineering Risks

1. **Complexity overhead**: HDC operations (D=10,000) may be slower than the
   existing dict lookup (O(1) with 64 entries). Need careful benchmarking.

2. **Tuning difficulty**: HDC performance depends on hyperparameters
   (D, projection matrix distribution, similarity threshold) with limited
   theoretical guidance.

3. **Community adoption**: YNN is a significant departure from the current
   lightweight, zero-dependency design philosophy.

### 4.3 When NOT to Use YNN

YNN is NOT needed when:
- The agent lifecycle is working well with the current deterministic system
- Performance (speed, memory) is more important than neural integration
- The 64 discrete strategies are sufficient for the use case
- The deployment environment cannot support ML dependencies

---

## 5. Research Roadmap

### Phase 1: Feasibility (v2.0, ~2 months)
- [ ] Literature review: HDC/VSA for symbolic reasoning
- [ ] Random projection prototype (D=100–1,000)
- [ ] Empirical test: structure preservation under projection
- [ ] RFC update with findings

### Phase 2: Differentiable Core (v2.1, ~3 months)
- [ ] YNN embedding layer in PyTorch/JAX
- [ ] Differentiable hexagram mutation
- [ ] Hyperdimensional memory prototype
- [ ] Integration tests with HermesYiJingExecutor

### Phase 3: Production (v2.2, ~3 months)
- [ ] Performance optimization
- [ ] Optional dependency packaging (`pip install yi-jing-agent[ynn]`)
- [ ] Documentation + tutorials
- [ ] A/B benchmark vs. deterministic system

---

## 6. References

1. Kanerva, P. (2009). *Hyperdimensional Computing: An Introduction to Computing in Distributed Representation with High-Dimensional Random Vectors.* Cognitive Computation.
2. Plate, T. A. (2003). *Holographic Reduced Representation: Distributed Representation for Cognitive Structures.* CSLI Publications.
3. Gayler, R. W. (2003). *Vector Symbolic Architectures Answer Jackendoff's Challenges for Cognitive Neuroscience.*
4. Kleyko, D., et al. (2022). *A Survey on Hyperdimensional Computing aka Vector Symbolic Architecture.* ACM Computing Surveys.
5. I Ching / 易經: *The hexagram system as a 6-bit binary coding scheme predates modern binary by ~3,000 years.*

---

## Appendix A: Conceptual Python Prototype

```python
"""Conceptual YNN prototype — NOT for production use."""
import numpy as np

class HexagramHypervector:
    """Map 64 hexagrams to D-dimensional hypervectors."""

    def __init__(self, dim: int = 1000):
        self.dim = dim
        # 64 hexagram codes from hexagram_table
        self.hexagrams = {
            "111111": "䷀", "000000": "䷁", "010100": "䷂", ...
        }
        # Random projection matrix (fixed seed for reproducibility)
        rng = np.random.RandomState(42)
        self.R = rng.randn(dim, 6)  # D × 6

    def embed(self, code: str) -> np.ndarray:
        """Project 6-bit hexagram to D-dim hypervector."""
        bits = np.array([int(b) for b in code], dtype=np.float32)
        return np.sign(self.R @ bits)

    def mutate(self, h: np.ndarray, yao_idx: int) -> np.ndarray:
        """Binary XOR flip in HDC space."""
        return h * (-1)  # Flip all signs (equivalent to XOR in bipolar)

    def similarity(self, h1: np.ndarray, h2: np.ndarray) -> float:
        """Cosine similarity in HDC space."""
        return np.dot(h1, h2) / (np.linalg.norm(h1) * np.linalg.norm(h2))
```

---

*This RFC is a research exploration document. No implementation in the
current v0.1.x codebase is planned. Contributions and discussion welcome
via GitHub Issues.*
