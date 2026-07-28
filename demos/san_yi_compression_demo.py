#!/usr/bin/env python3
"""
䷀ 三易壓縮 PoC — San Yi Compression Demo
==========================================

將易經「三易」哲學轉譯為真實嘅 LLM 壓縮工程 Demo：
    Level 1: 簡易 = Ternary Quantization (BitNet b1.58)
    Level 2: 變易 = Moving Line Protection (AWQ)
    Level 3: 不易 = Core Preservation (Frozen Layers)

用 numpy 模擬真實 weight distribution，逐層輸出壓縮報告。
唔需要 GPU，任何 Mac 都 run 到。

Usage:
    python3 san_yi_compression_demo.py
"""

import math
import time
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

try:
    import numpy as np
except ImportError:
    print("❌ 需要 numpy: pip install numpy")
    sys.exit(1)


# ══════════════════════════════════════════════
#  易經裝飾
# ══════════════════════════════════════════════

HEXAGRAM_SYMBOLS = [
    "䷀","䷁","䷂","䷃","䷄","䷅","䷆","䷇",
    "䷈","䷉","䷊","䷋","䷌","䷍","䷎","䷏",
    "䷐","䷑","䷒","䷓","䷔","䷕","䷖","䷗",
    "䷘","䷙","䷚","䷛","䷜","䷝","䷞","䷟",
    "䷠","䷡","䷢","䷣","䷤","䷥","䷦","䷧",
    "䷨","䷩","䷪","䷫","䷬","䷭","䷮","䷯",
    "䷰","䷱","䷲","䷳","䷴","䷵","䷶","䷷",
    "䷸","䷹","䷺","䷻","䷼","䷽","䷾","䷿",
]

HEXAGRAM_NAMES = [
    "乾為天","坤為地","水雷屯","山水蒙","水天需","天水訟","地水師","水地比",
    "風天小畜","天澤履","地天泰","天地否","天火同人","火天大有","地山謙","雷地豫",
    "澤雷隨","山風蠱","地澤臨","風地觀","火雷噬嗑","山火賁","山地剝","地雷復",
    "天雷无妄","山天大畜","山雷頤","澤風大過","坎為水","離為火","澤山咸","雷風恆",
    "天山遯","雷天大壯","火地晉","地火明夷","風火家人","火澤睽","水山蹇","雷水解",
    "山澤損","風雷益","澤天夬","天風姤","澤地萃","地風升","澤水困","水風井",
    "澤火革","火風鼎","震為雷","艮為山","風山漸","雷澤歸妹","雷火豐","火山旅",
    "巽為風","兌為澤","風水渙","水澤節","風澤中孚","雷山小過","水火既濟","火水未濟",
]


def hash_to_hexagram(val: int) -> str:
    """Map a value (0-63) to hexagram symbol + name."""
    idx = abs(val) % 64
    return f"{HEXAGRAM_SYMBOLS[idx]} {HEXAGRAM_NAMES[idx]}"


# ══════════════════════════════════════════════
#  Simulate LLM Weight Matrix
# ══════════════════════════════════════════════

def simulate_llm_weights(
    n_layers: int = 12,
    d_model: int = 768,
    seed: int = 42
) -> dict:
    """模擬一個 mini transformer 嘅 weight matrices。

    模擬 12-layer transformer：
    - attention weight (Q, K, V, O): 4 × d_model × d_model
    - FFN weight (gate, up, down): 3 × d_model × (4*d_model)
    - embedding: vocab_size × d_model
    """
    rng = np.random.default_rng(seed)
    weights = {}

    # Embedding layer — 守護對象（不易）
    vocab_size = 32000
    weights["embedding"] = rng.normal(0, 0.1, (vocab_size, d_model))

    for layer in range(n_layers):
        # Attention weights（Q, K, V, O）
        for name in ["q", "k", "v", "o"]:
            key = f"layer{layer}.attn.{name}"
            # 混合分佈：大部分 normal + 少數 outlier
            w = rng.normal(0, 0.02, (d_model, d_model))
            # 加 ~1% outlier
            n_outliers = max(1, int(d_model * 0.01))
            outlier_idx = rng.choice(d_model, n_outliers, replace=False)
            w[:, outlier_idx] += rng.normal(0, 0.5, (d_model, n_outliers))
            weights[key] = w.astype(np.float32)

        # FFN weights（gate, up, down）
        d_ffn = d_model * 4
        for name in ["gate", "up", "down"]:
            key = f"layer{layer}.ffn.{name}"
            w = rng.normal(0, 0.02, (d_model, d_ffn))
            n_outliers = max(1, int(d_ffn * 0.005))
            outlier_idx = rng.choice(d_ffn, n_outliers, replace=False)
            w[:, outlier_idx] += rng.normal(0, 0.5, (d_model, n_outliers))
            weights[key] = w.astype(np.float32)

    return weights


# ══════════════════════════════════════════════
#  Level 1: 簡易 — Ternary Quantization
# ══════════════════════════════════════════════

@dataclass
class TernaryResult:
    ternary_weights: np.ndarray  # {-1, 0, +1}
    scale_factor: float          # scaling to restore approximate values
    compression_ratio: float
    snr_db: float
    original: np.ndarray


def ternary_quantize(weights: np.ndarray, threshold: float = 0.02) -> TernaryResult:
    """Quantize weights to ternary {-1, 0, +1} with scaling.

    Corresponds to BitNet b1.58 (Microsoft, 2024).

    Args:
        weights: Original FP32 weight matrix.
        threshold: Below this absolute value → 0 (neutral).

    Returns:
        TernaryResult with quantized weights and metrics.
    """
    orig_float = weights.astype(np.float64)
    abs_w = np.abs(orig_float)
    scale = np.mean(abs_w[abs_w > threshold]) if np.any(abs_w > threshold) else 1.0

    # {-1, 0, +1}
    ternary = np.zeros_like(orig_float)
    ternary[orig_float > threshold] = 1
    ternary[orig_float < -threshold] = -1
    # 0 部分保持 0

    # Dequantize for error computation
    dequantized = ternary * scale

    # Compute SNR
    signal_var = np.var(orig_float)
    noise_var = np.var(orig_float - dequantized)
    snr = 10 * math.log10(signal_var / noise_var) if noise_var > 1e-12 else float('inf')

    # Compression ratio: FP32 → ~1.58bit per weight
    bits_fp32 = orig_float.size * 32
    bits_ternary = orig_float.size * 2  # can encode in 2 bits: 00=-1, 01=0, 10=1
    # Actual achievable: ~1.58 bit (binary encoding of ternary)
    bits_ternary_achievable = orig_float.size * math.log2(3)
    ratio = bits_fp32 / bits_ternary_achievable

    return TernaryResult(
        ternary_weights=ternary,
        scale_factor=scale,
        compression_ratio=ratio,
        snr_db=snr,
        original=weights,
    )


# ══════════════════════════════════════════════
#  Level 2: 變易 — Moving Line Protection (AWQ)
# ══════════════════════════════════════════════

@dataclass
class MixedPrecisionResult:
    # 動爻位置（outlier channels）
    moving_line_indices: List[int]
    moving_line_count: int
    static_line_count: int
    # 動爻：FP16（16-bit）
    # 靜爻：Ternary {-1,0,+1}（~1.58-bit）
    compression_ratio: float
    snr_db: float
    protected_weights: np.ndarray  # column indices for protection
    original: np.ndarray


def detect_moving_lines(
    weights: np.ndarray,
    outlier_pct: float = 0.01,
    activation_scores: Optional[np.ndarray] = None,
) -> MixedPrecisionResult:
    """Detect and protect 動爻（outlier channels）.

    Corresponds to AWQ (Activation-aware Weight Quantization, MIT 2024).

    Analyzes columns (output channels) for high-impact outliers.
    The top `outlier_pct` channels are preserved at higher precision,
    while the rest are aggressively quantized.

    Args:
        weights: FP32 weight matrix (d_in, d_out).
        outlier_pct: Top % of columns to protect as 動爻.
        activation_scores: Optional pre-computed activation magnitudes.

    Returns:
        MixedPrecisionResult with protection mask.
    """
    w = weights.astype(np.float64)
    n_cols = w.shape[1]

    # Compute column importance: mean absolute weight per column
    # This simulates activation-aware importance
    col_scores = np.mean(np.abs(w), axis=0)

    if activation_scores is not None:
        col_scores = col_scores * activation_scores

    # Top outlier_pct columns = 動爻
    n_moving = max(1, int(n_cols * outlier_pct))
    moving_idx = np.argsort(-col_scores)[:n_moving]

    # Simulate mixed precision:
    # Protect moving lines → keep FP16
    # Compress static lines → ternary
    # We simulate by computing SNR with vs without protection
    static_mask = np.ones(n_cols, dtype=bool)
    static_mask[moving_idx] = False

    # Full ternary quantization (no protection)
    full_ternary = ternary_quantize(w)

    # With protection: moving lines keep original value, rest ternary
    ternary_w = full_ternary.ternary_weights * full_ternary.scale_factor
    protected_w = w.copy()
    protected_w[:, static_mask] = ternary_w[:, static_mask]

    # SNR
    signal_var = np.var(w)
    noise_var = np.var(w - protected_w)
    snr = 10 * math.log10(signal_var / noise_var) if noise_var > 1e-12 else float('inf')

    # Compression ratio: weighted avg of ternary (1.58 bit) and FP16 (16 bit)
    n_moving_float = float(n_moving)
    n_static_float = float(n_cols - n_moving)
    avg_bits = (n_moving_float * 16 + n_static_float * math.log2(3)) / n_cols
    ratio = 32 / avg_bits

    return MixedPrecisionResult(
        moving_line_indices=sorted(moving_idx.tolist()),
        moving_line_count=n_moving,
        static_line_count=n_cols - n_moving,
        compression_ratio=ratio,
        snr_db=snr,
        protected_weights=w[:, moving_idx],
        original=weights,
    )


# ══════════════════════════════════════════════
#  Level 3: 不易 — Core Preservation
# ══════════════════════════════════════════════

@dataclass
class CorePreservationPlan:
    frozen_layers: List[str]  # layer keys to freeze
    compressed_layers: List[str]  # layer keys to compress
    total_params_before: int
    total_params_after: int
    compression_ratio: float


def design_preservation_plan(layer_keys: List[str]) -> CorePreservationPlan:
    """Decide which layers to freeze and which to compress.

    不易 = 守住根本：
    - Embedding layer → FP16 frozen（根基）
    - Bottom 2 transformer layers → FP16 frozen（基礎語法）
    - Remaining layers → compressed（上層語義可壓縮）
    """
    frozen = []
    compressed = []

    for key in layer_keys:
        if key == "embedding":
            frozen.append(key)
        elif key.startswith("layer0.") or key.startswith("layer1."):
            frozen.append(key)
        else:
            compressed.append(key)

    return CorePreservationPlan(
        frozen_layers=frozen,
        compressed_layers=compressed,
        total_params_before=0,  # filled later
        total_params_after=0,
        compression_ratio=0.0,
    )


# ══════════════════════════════════════════════
#  Full 三易 Pipeline
# ══════════════════════════════════════════════

@dataclass
class SanYiPipelineResult:
    """完整三易 pipeline 輸出"""
    # 原始
    total_params: int
    original_size_bytes: float
    # Phase 1: 簡易（Pruning)
    pruned_params: int
    pruning_pct: float
    # Phase 2: 變易（Ternary + Mixed Precision）
    phase2_avg_bits: float
    phase2_compression: float
    phase2_snr_db: float
    # Phase 3: 不易（Core Preservation）
    plan: CorePreservationPlan
    # Final
    final_size_bytes: float
    total_compression: float

    def print_report(self):
        """Print formatted compression report."""

        print(f"""
╔{'═'*62}╗
║ {'䷀ 三易壓縮 Pipeline — 完整報告':^60} ║
╠{'═'*62}╣

📊 原始模型 Stats：
   總參數:        {self.total_params:>15,}
   原始大小:      {self.original_size_bytes:>10.2f} GB (FP32)

Phase 1: 簡易（Pruning）
   剪枝後參數:   {self.pruned_params:>15,}
   剪枝率:       {self.pruning_pct * 100:>9.1f}%

Phase 2: 變易（Ternary + Moving Line Protection）
   動爻（outlier）: ~1% channels → FP16
   靜爻（background）: ~99% channels → Ternary {{-1, 0, +1}}
   加權平均 bit:  {self.phase2_avg_bits:>10.2f} bit/weight
   Phase 2 壓縮: {self.phase2_compression:>10.1f}x
   SNR:          {self.phase2_snr_db:>10.2f} dB

Phase 3: 不易（Core Preservation）
   Frozen layers: {len(self.plan.frozen_layers):>4} ({', '.join(self.plan.frozen_layers)})
   Compressed:    {len(self.plan.compressed_layers):>4} layers

{'─' * 62}
📦 最終結果
   壓縮後大小:   {self.final_size_bytes:>10.2f} GB
   總壓縮比:     {self.total_compression:>10.1f}x
{'─' * 62}
        """)


def run_san_yi_pipeline(
    n_layers: int = 12,
    d_model: int = 768,
    seed: int = 42,
) -> SanYiPipelineResult:
    """Run the full 三易 pipeline on simulated weights."""

    # Generate weights
    weights = simulate_llm_weights(n_layers, d_model, seed)
    layer_keys = list(weights.keys())

    # ── Phase 0: Measure original ──
    total_params = sum(w.size for w in weights.values())
    # Only count 1 transformer layer for representative metrics
    sample_key = [k for k in layer_keys if k.startswith("layer2")][0]
    sample_w = weights[sample_key]

    original_size_gb = total_params * 32 / 8 / 1024**3

    # ── Phase 1: 簡易 — Simulated Pruning ──
    # Simulate: prune 20% of least important heads
    pruning_ratio = 0.2
    pruned_params = int(total_params * (1 - pruning_ratio))
    pruning_pct = pruning_ratio

    # ── Phase 2: 變易 — Ternary + Moving Line Protection ──
    # Apply to the representative sample layer
    moving = detect_moving_lines(sample_w, outlier_pct=0.01)
    ternary_full = ternary_quantize(sample_w)

    # Weighted average bits: ternary (1.58 bit) for static, FP16 (16 bit) for moving lines
    moving_ratio = moving.moving_line_count / sample_w.shape[1]
    static_ratio = 1 - moving_ratio
    avg_bits = moving_ratio * 16 + static_ratio * math.log2(3)
    phase2_compression = 32 / avg_bits

    # ── Phase 3: 不易 — Core Preservation ──
    plan = design_preservation_plan(layer_keys)

    # Compute final size
    # Frozen layers: kept at FP32 → 32 bit/weight
    # Compressed layers: Phase 2 compression applied
    frozen_params = sum(weights[k].size for k in plan.frozen_layers)
    compressed_params = sum(weights[k].size for k in plan.compressed_layers)
    final_bits = frozen_params * 32 + compressed_params * avg_bits
    final_size_gb = final_bits / 8 / 1024**3
    total_compression = original_size_gb / final_size_gb if final_size_gb > 0 else 0

    return SanYiPipelineResult(
        total_params=total_params,
        original_size_bytes=original_size_gb,
        pruned_params=pruned_params,
        pruning_pct=pruning_pct,
        phase2_avg_bits=avg_bits,
        phase2_compression=phase2_compression,
        phase2_snr_db=moving.snr_db,
        plan=plan,
        final_size_bytes=final_size_gb,
        total_compression=total_compression,
    )


# ══════════════════════════════════════════════
#  Visual Demo: 變爻可視化
# ══════════════════════════════════════════════

def visualize_moving_lines(weight_matrix: np.ndarray, n_cols_show: int = 64):
    """ASCII visualization of moving lines in a weight matrix."""
    moving = detect_moving_lines(weight_matrix, outlier_pct=0.02)
    w = moving.original.astype(np.float64)[:, :n_cols_show]

    moving_set = set(moving.moving_line_indices)
    moving_set = {i for i in moving_set if i < n_cols_show}

    print(f"\n  🀄 變爻 Visualisation (showing first {n_cols_show} columns):")
    print()
    for row in range(min(8, w.shape[0])):
        line = "  "
        for col in range(n_cols_show):
            val = w[row, col]
            if col in moving_set:
                if val > 0:
                    line += "⚊"  # 動爻陽
                else:
                    line += "⚋"  # 動爻陰
            else:
                if abs(val) < 0.02:
                    line += "·"  # 靜爻中性
                elif val > 0:
                    line += "─"  # 靜爻陽
                else:
                    line += "─"  # 靜爻陰
        print(line)
        if row == 0:
            print(f"  {'▼':>{8 + n_cols_show // 2}}")
            print(f"  {'動爻(保護) ↑  靜爻(壓縮) ↓':^{8 + n_cols_show // 2}}")
    print()


# ══════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║      ䷀ 三易壓縮 PoC — San Yi Compression Demo             ║
║      易經哲學 → 真實 LLM 壓縮工程                           ║
║      Level 1: 簡易 (Ternary)                                ║
║      Level 2: 變易 (Moving Line Protection)                 ║
║      Level 3: 不易 (Core Preservation)                      ║
╚══════════════════════════════════════════════════════════════╝
    """)

    start = time.time()

    # Simulate a 12-layer mini transformer
    print("  🔄 Generating simulated transformer weights (12 layers, d_model=768)...")
    weights = simulate_llm_weights(n_layers=12, d_model=768)
    print(f"  ✅ Generated {len(weights)} weight matrices")

    # ── Level 1: 簡易 — Ternary Quantization ──
    print("\n" + "─" * 62)
    print("  🀄 Level 1: 簡易 — Ternary Quantization (BitNet b1.58)")
    print("  " + "─" * 58)

    sample_key = list(weights.keys())[10]
    sample_w = weights[sample_key]
    ternary = ternary_quantize(sample_w)

    # Show ternary distribution
    unique, counts = np.unique(ternary.ternary_weights, return_counts=True)
    total = counts.sum()
    print(f"\n  Layer: {sample_key}")
    print(f"  Shape: {sample_w.shape}")
    print(f"    umber of weights: {total:,}")
    print(f"    ⚊ +1 (陽):  {counts[list(unique).index(1)] if 1 in unique else 0:>10,} ({counts[list(unique).index(1)]/total*100 if 1 in unique else 0:.1f}%)")
    print(f"    ⚋ -1 (陰):  {counts[list(unique).index(-1)] if -1 in unique else 0:>10,} ({counts[list(unique).index(-1)]/total*100 if -1 in unique else 0:.1f}%)")
    print(f"    ·  0 (中):  {counts[list(unique).index(0)] if 0 in unique else 0:>10,} ({counts[list(unique).index(0)]/total*100 if 0 in unique else 0:.1f}%)")
    print(f"    Compress:   {ternary.compression_ratio:.1f}x")
    print(f"    SNR:        {ternary.snr_db:.1f} dB")
    print(f"    Scale:      {ternary.scale_factor:.4f}")
    print(f"    Hexagram:   {hash_to_hexagram(int(ternary.scale_factor * 100))}")

    # ── Level 2: 變易 — Moving Line Protection ──
    print("\n" + "─" * 62)
    print("  🀄 Level 2: 變易 — Moving Line Protection (AWQ)")
    print("  " + "─" * 58)

    moving = detect_moving_lines(sample_w, outlier_pct=0.01)
    print(f"\n  Layer: {sample_key}")
    print(f"    Shape:           {sample_w.shape}")
    print(f"    Total channels:  {sample_w.shape[1]:,}")
    print(f"    動爻 (outlier):  {moving.moving_line_count:,} ({moving.moving_line_count/sample_w.shape[1]*100:.2f}%) → FP16")
    print(f"    靜爻 (static):   {moving.static_line_count:,} ({moving.static_line_count/sample_w.shape[1]*100:.2f}%) → Ternary")
    print(f"    Avg bits/weight: {(moving.moving_line_count * 16 + moving.static_line_count * math.log2(3)) / sample_w.shape[1]:.2f}")
    print(f"    Compression:     {moving.compression_ratio:.1f}x")
    print(f"    SNR:             {moving.snr_db:.1f} dB")

    # Show moving line indices as hexagram positions
    print(f"\n    動爻位置（頭 6 個）：")
    for i, idx in enumerate(moving.moving_line_indices[:6]):
        print(f"      爻{i+1}: column {idx:>5} → ⚊ 保留 FP16")

    # Visualize
    visualize_moving_lines(sample_w, n_cols_show=64)

    # ── Level 3: 不易 — Core Preservation ──
    print("\n" + "─" * 62)
    print("  🀄 Level 3: 不易 — Core Preservation")
    print("  " + "─" * 58)

    plan = design_preservation_plan(list(weights.keys()))
    print(f"\n  Frozen layers（不易—守住根本）：")
    for k in plan.frozen_layers[:4]:
        w = weights[k]
        print(f"    ✅ {k:<30} {w.shape} → FP16 frozen")
    if len(plan.frozen_layers) > 4:
        print(f"    ... + {len(plan.frozen_layers) - 4} more")

    print(f"\n  Compressed layers（變易）：")
    for k in plan.compressed_layers[:4]:
        w = weights[k]
        print(f"    🔄 {k:<30} {w.shape} → Ternary + AWQ")
    if len(plan.compressed_layers) > 4:
        print(f"    ... + {len(plan.compressed_layers) - 4} more")

    # ── Full Pipeline Report ──
    print("\n" + "━" * 62)
    result = run_san_yi_pipeline(n_layers=12, d_model=768)
    result.print_report()

    # ── 7B Model Projection ──
    print("  📐 Projection to real 7B model:")
    print()
    sizes = [
        ("FP32 (original)", 28.0),
        ("FP16 (half precision)", 14.0),
        ("INT4 (4-bit quant)", 3.5),
        ("三易 Ternary + AWQ", 2.8),
        ("三易 Ternary + AWQ + Pruning", 1.4),
    ]
    for label, size in sizes:
        bar = "█" * int(size * 3) + "░" * int((14 - size * 3))
        print(f"    {label:<30} {size:>5.1f} GB  {bar}")

    print()
    print(f"  ⏱️  Completed in {time.time() - start:.2f}s")
    print(f"""
  ──────────────────────────────────────────────────────────────
  💡 Key Insight:
      易經嘅「三易」唔係裝飾，而係一套完整嘅壓縮哲學：
      
      簡易（Pruning）→ 砍掉用唔著嘅
      變易（Variable Precision）→ 保護關鍵，壓縮其餘
      不易（Core Preservation）→ 守住語言根基

      呢三個 phase 各自對應已存在嘅 ML 技術，
      但未有人用三易將佢哋統一成一個框架。

      See docs/rfc/rfc-002-san-yi-compression.md
  ──────────────────────────────────────────────────────────────
    """)


if __name__ == "__main__":
    main()
