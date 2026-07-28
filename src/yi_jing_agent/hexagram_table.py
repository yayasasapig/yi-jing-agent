"""䷀ 64 卦名稱與策略對應表 — Complete Hexagram Names & Strategy Mapping

Bitwise Engine (v2):
- 6-bit integer representation (0-63)
- popcount / hamming distance helpers
- Error taxonomy masks for all 6 yao positions
- Backward compatible with string-based lookups
"""
from typing import Union, Tuple, Optional

# ════════════════════════════════════════════════════════════════
#  Bit Positions (MSB = 初爻, for visual string compatibility)
#  Bit 5 (MSB) = 初爻 → Intent Parsing
#  Bit 4        = 二爻 → Task Planning
#  Bit 3        = 三爻 → Tool Execution
#  Bit 2        = 四爻 → Validation
#  Bit 1        = 五爻 → Goal Alignment
#  Bit 0 (LSB)  = 上爻 → Memory Archival
# ════════════════════════════════════════════════════════════════

YAO_BIT_MASK = {
    1: 0b100000,  # 初爻 (bit 5)
    2: 0b010000,  # 二爻 (bit 4)
    3: 0b001000,  # 三爻 (bit 3)
    4: 0b000100,  # 四爻 (bit 2)
    5: 0b000010,  # 五爻 (bit 1)
    6: 0b000001,  # 上爻 (bit 0)
}

YAO_NAMES = {
    1: "初爻",
    2: "二爻",
    3: "三爻",
    4: "四爻",
    5: "五爻",
    6: "上爻",
}

# ── Error Taxonomy: each error type maps to exactly one bit ──
ERROR_MASK = {
    "INTENT_AMBIGUOUS":      0b100000,  # 初爻: intent parsing failed
    "PLANNING_FAILED":       0b010000,  # 二爻: task plan generation failed
    "TOOL_EXECUTION_ERROR":  0b001000,  # 三爻: tool/API call exception
    "VALIDATION_FAILED":     0b000100,  # 四爻: output failed schema/logic check
    "GOAL_DRIFT_DETECTED":   0b000010,  # 五爻: target drift from goal state
    "MEMORY_ARCHIVAL_FAIL":  0b000001,  # 上爻: memory persistence failed
}

# ── Goal state: ䷀ 乾 (all bits 1) ──
GOAL_STATE = 0b111111  # 63 — perfect health
NULL_STATE = 0b000000  # 0 — complete failure


# ════════════════════════════════════════════════════════════════
#  Bitwise Helpers
# ════════════════════════════════════════════════════════════════


def popcount(x: int) -> int:
    """Count set bits (number of healthy yao positions)."""
    return x.bit_count()


def hamming_distance(a: int, b: int) -> int:
    """Hamming distance between two hexagram states.
    
    d_H = 0 → identical
    d_H >= 3 → severe drift, needs human intervention
    """
    return (a ^ b).bit_count()


def drift_score(current: int, target: int = GOAL_STATE) -> float:
    """Normalized Hamming distance from target.
    
    Returns 0.0 (perfect alignment) to 1.0 (complete drift).
    """
    return hamming_distance(current, target) / 6.0


def check_yao(state: int, yao_index: int) -> bool:
    """Check if a specific yao position is healthy (bit = 1).
    
    Args:
        state: 6-bit hexagram integer (0-63).
        yao_index: 1-based (1=初爻, ..., 6=上爻).
    
    Returns:
        True if the bit is 1 (healthy), False if 0 (fault).
    """
    return bool(state & YAO_BIT_MASK[yao_index])


def get_faulty_yaos(state: int) -> list[int]:
    """Return list of yao indices where bit = 0 (faulty)."""
    return [i for i in range(1, 7) if not check_yao(state, i)]


def int_to_str(code: int) -> str:
    """Convert 6-bit integer to 6-char binary string."""
    return f"{code:06b}"


def str_to_int(code: str) -> int:
    """Convert 6-char binary string to 6-bit integer."""
    return int(code, 2)


# ════════════════════════════════════════════════════════════════
#  64 Hexagram Names (keyed by binary string, backward compat)
# ════════════════════════════════════════════════════════════════

# Build from integer keys for accuracy
_HEXAGRAM_NAMES_INT: dict[int, Tuple[str, str]] = {
    0b111111: ("䷀", "乾為天"),      # 1
    0b000000: ("䷁", "坤為地"),      # 2
    0b010100: ("䷂", "水雷屯"),      # 3
    0b001010: ("䷃", "山水蒙"),      # 4
    0b010111: ("䷄", "水天需"),      # 5
    0b111010: ("䷅", "天水訟"),      # 6
    0b000010: ("䷆", "地水師"),      # 7
    0b010000: ("䷇", "水地比"),      # 8
    0b011111: ("䷈", "風天小畜"),    # 9
    0b111110: ("䷉", "天澤履"),      # 10
    0b000111: ("䷊", "地天泰"),      # 11
    0b111000: ("䷋", "天地否"),      # 12
    0b111101: ("䷌", "天火同人"),    # 13
    0b101111: ("䷍", "火天大有"),    # 14
    0b000001: ("䷎", "地山謙"),      # 15
    0b100000: ("䷏", "雷地豫"),      # 16
    0b110100: ("䷐", "澤雷隨"),      # 17
    0b001011: ("䷑", "山風蠱"),      # 18
    0b000110: ("䷒", "地澤臨"),      # 19
    0b011000: ("䷓", "風地觀"),      # 20
    0b101100: ("䷔", "火雷噬嗑"),    # 21
    0b001101: ("䷕", "山火賁"),      # 22
    0b001000: ("䷖", "山地剝"),      # 23
    0b000100: ("䷗", "地雷復"),      # 24
    0b111100: ("䷘", "天雷无妄"),    # 25
    0b001111: ("䷙", "山天大畜"),    # 26
    0b001100: ("䷚", "山雷頤"),      # 27
    0b110011: ("䷛", "澤風大過"),    # 28
    0b010010: ("䷜", "坎為水"),      # 29
    0b101101: ("䷝", "離為火"),      # 30
    0b110001: ("䷞", "澤山咸"),      # 31
    0b100011: ("䷟", "雷風恆"),      # 32
    0b111001: ("䷠", "天山遯"),      # 33
    0b100111: ("䷡", "雷天大壯"),    # 34
    0b101000: ("䷢", "火地晉"),      # 35
    0b000101: ("䷣", "地火明夷"),    # 36
    0b011101: ("䷤", "風火家人"),    # 37
    0b101110: ("䷥", "火澤睽"),      # 38
    0b010001: ("䷦", "水山蹇"),      # 39
    0b100010: ("䷧", "雷水解"),      # 40
    0b001110: ("䷨", "山澤損"),      # 41
    0b011100: ("䷩", "風雷益"),      # 42
    0b110111: ("䷪", "澤天夬"),      # 43
    0b111011: ("䷫", "天風姤"),      # 44
    0b110000: ("䷬", "澤地萃"),      # 45
    0b000011: ("䷭", "地風升"),      # 46
    0b110010: ("䷮", "澤水困"),      # 47
    0b010011: ("䷯", "水風井"),      # 48
    0b110101: ("䷰", "澤火革"),      # 49
    0b101011: ("䷱", "火風鼎"),      # 50
    0b100100: ("䷲", "震為雷"),      # 51
    0b001001: ("䷳", "艮為山"),      # 52
    0b011001: ("䷴", "風山漸"),      # 53
    0b100110: ("䷵", "雷澤歸妹"),    # 54
    0b100101: ("䷶", "雷火豐"),      # 55
    0b101001: ("䷷", "火山旅"),      # 56
    0b011011: ("䷸", "巽為風"),      # 57
    0b110110: ("䷹", "兌為澤"),      # 58
    0b011010: ("䷺", "風水渙"),      # 59
    0b010110: ("䷻", "水澤節"),      # 60
    0b011110: ("䷼", "風澤中孚"),    # 61
    0b100001: ("䷽", "雷山小過"),    # 62
    0b010101: ("䷾", "水火既濟"),    # 63
    0b101010: ("䷿", "火水未濟"),    # 64
}

# Backward compat: string-keyed dict
HEXAGRAM_NAMES: dict[str, Tuple[str, str]] = {
    int_to_str(k): v for k, v in _HEXAGRAM_NAMES_INT.items()
}

# Verify all 64 are present
assert len(_HEXAGRAM_NAMES_INT) == 64, f"Expected 64, got {len(_HEXAGRAM_NAMES_INT)}"


# ════════════════════════════════════════════════════════════════
#  64 Hexagram Strategies (array-indexed by int for O(1) lookup)
# ════════════════════════════════════════════════════════════════

# Pre-allocate array of 64
_HEXAGRAM_STRATEGIES: list[str] = [""] * 64

# Populate from integer keys
_STRATEGIES_INT: dict[int, str] = {
    0b111111: "Happy Path，一切順利，繼續執行",
    0b000111: "上下交泰，人類反饋良好，推進",
    0b100111: "資源充足，可增加並行度",
    0b101000: "進展順利，加速推進",
    0b001111: "經驗累積充足，壓縮為 Pattern",
    0b100101: "結果豐富，摘要提煉",
    0b010101: "任務成功，準備上爻復盤",
    0b011100: "超額完成，可延伸交付",
    # ── 中上：Coordination ──
    0b110011: "過度執行風險，檢查 Token 預算",
    0b111101: "與人協同，開啟 API 閘門",
    0b101111: "成果豐盛，考慮多 Agent 分配",
    0b000110: "關鍵決策點，進入四爻 HITL",
    0b110101: "需要更換策略，大幅 pivot",
    0b101011: "可以嘗試新方法，啟用實驗模式",
    0b110110: "用戶滿意，可延伸交付",
    0b110001: "用戶有即時反饋，切換互動模式",
    0b100011: "長週期任務，定期 checkpoint",
    0b011101: "內部 Agent 協作，內部通訊模式",
    0b101110: "Agent 間意見分歧，運行投票機制",
    0b110000: "多源數據匯聚完成，啟動整合模式",
    0b000011: "Context 累積充足，進入深層推理",
    0b100110: "結果需要整合，合併模式",
    0b011110: "確認意圖一致，雙重驗證",
    0b010111: "等待需求/外部資源，暫停輪詢",
    0b110100: "用戶中途改變方向，順勢跟隨",
    # ── 中中：觀察／調整 ──
    0b011111: "小有積蓄，部分成果可用，先交付再修復",
    0b111110: "履行謹慎，執行層出問題，降級二爻沙盒",
    0b110010: "資源耗盡/Rate Limit，等待降級",
    0b010011: "系統健康檢查，維護模式",
    0b010010: "重險陷阱，反覆失敗，人類接管",
    0b101101: "需要更多資訊源，開啟搜索工具",
    0b100010: "瓶頸被解決，恢復速度",
    0b100100: "突發事件，緊急處理",
    0b001001: "需要暫停，強制休息",
    0b011011: "需要逐步滲透，緩慢執行模式",
    0b001100: "Context 需要補充，重新注入相關記憶",
    0b010110: "Token 超標，Token Budget 模式",
    0b011010: "Context Overflow，強制壓縮記憶",
    0b100001: "小錯誤可忽略，繼續執行",
    0b000101: "外部干擾，切換備用資源",
    0b011001: "按部就班執行，線性推進",
    0b101001: "Context 切換，跨工作區轉移",
    0b101100: "審判咬合，需執行安全檢查",
    0b001101: "輸出格式需優化，格式調整模式",
    # ── 中下：反思／修正 ──
    0b000001: "謙卑低調，建議降低調用頻率，Rate Limit 模式",
    0b100000: "預備準備，建議加強準備，延長二爻沙盒",
    0b010100: "初生艱難，任務剛開始就卡住，重新理解意圖",
    0b111010: "爭訟衝突，邏輯矛盾，回溯初爻重構",
    0b010000: "親比輔助，需要人類指導，請求 HITL",
    0b000010: "聚眾出兵，需要多 Agent 協作，切換團隊模式",
    0b010001: "行走艱難，執行緩慢，檢查並行度",
    0b111001: "退避隱藏，建議暫時迴避，延遲執行",
    0b001010: "矇昧不清，Context 不足，要求用戶補充",
    0b111011: "相遇邂逅，發現意外有用資訊，收錄暫存記憶",
    0b110111: "決斷裁決，需要果斷決策，進入四爻強制決策",
    0b011000: "觀察審視，需要更多數據，延長初爻觀察",
    0b001110: "減少損失，成本超支，切換低成本方案",
    0b001011: "敗壞腐蝕，Context Window 污染，強制清理重建",
    0b101010: "尚未完成，差最後一步，Retry 四爻授權",
    # ── 下下：失敗／接管 ──
    0b111000: "上下不交，人類反饋差，重新理解",
    0b111100: "意外之災，不可預期錯誤，進入緊急降級",
    0b001000: "剝落崩解，任務逐步失敗，逐層回溯拯救局部",
    0b000100: "復甦回歸，失敗後恢復，從初爻重新開始",
    0b000000: "全面崩潰，人類接管，緊急停機",
}

# Populate the O(1) array
for code, strategy in _STRATEGIES_INT.items():
    _HEXAGRAM_STRATEGIES[code] = strategy

# Backward compat: string-keyed dict
STRATEGIES: dict[str, str] = {
    int_to_str(k): v for k, v in _STRATEGIES_INT.items()
}

# Verify all 64 have strategies
assert len(_STRATEGIES_INT) == 64, f"Expected 64 strategies, got {len(_STRATEGIES_INT)}"


# ════════════════════════════════════════════════════════════════
#  Hexagram Name Lookup (int + str)
# ════════════════════════════════════════════════════════════════


def get_hexagram_name(code: Union[int, str]) -> str:
    """根據 6-bit code 返回卦象名稱。
    
    Accepts both int (0-63) and str ("111111").
    """
    if isinstance(code, str):
        try:
            code = str_to_int(code)
        except (ValueError, KeyError):
            # Non-binary string: extract yang count from digits
            pass
    
    if isinstance(code, int) and 0 <= code <= 63:
        result = _HEXAGRAM_NAMES_INT.get(code)
        if result:
            symbol, name = result
            return f"{symbol} {name}"
    return "䷀ 未知"


def get_hexagram_symbol(code: Union[int, str]) -> str:
    """返回卦象符號 (e.g. '䷀')."""
    if isinstance(code, str):
        code = str_to_int(code)
    result = _HEXAGRAM_NAMES_INT.get(code)
    return result[0] if result else "䷀"


# ════════════════════════════════════════════════════════════════
#  Strategy Lookup (int + str, with intelligent fallback)
# ════════════════════════════════════════════════════════════════


def get_strategy_for_hexagram(code: Union[int, str]) -> str:
    """根據卦象返回對應執行策略。
    
    Accepts both int (0-63) and str ("111111").
    Returns format: "䷀ 乾為天 — Happy Path..."
    Fallback 有意義 — 根據卦象特徵推斷策略。
    """
    if isinstance(code, str):
        try:
            code = str_to_int(code)
        except (ValueError, KeyError):
            # Non-binary string: keep as str for backward-compat fallback
            pass
    
    # Prefix hexagram name
    name_prefix = get_hexagram_name(code)
    
    # O(1) array lookup (int only)
    if isinstance(code, int) and 0 <= code < 64 and _HEXAGRAM_STRATEGIES[code]:
        return f"{name_prefix} — {_HEXAGRAM_STRATEGIES[code]}"
    
    # Fallback — 根據卦象特徵推斷
    if isinstance(code, str):
        # Backward compat: count '1' chars in non-binary string
        yang_count = sum(1 for c in code if c == '1')
    elif code >= 0:
        yang_count = popcount(code)
    else:
        yang_count = 0
    
    if yang_count >= 5:
        suffix = "通用 — 多陽爻，資源充足，可進取執行"
    elif yang_count <= 1:
        suffix = "通用 — 多陰爻，建議收斂觀察，降低預期"
    elif isinstance(code, int) and code & 0b001000:
        suffix = "通用 — 坎象出現，注意潛在風險，準備降級"
    elif isinstance(code, str) and "010" in code:
        suffix = "通用 — 坎象出現，注意潛在風險，準備降級"
    else:
        suffix = "通用降級 — 回到初爻重新規劃"
    
    return f"{name_prefix} — {suffix}"


# ════════════════════════════════════════════════════════════════
#  One-shot hexagram mutation (XOR flip)
# ════════════════════════════════════════════════════════════════


def flip_yao(state: int, yao_index: int) -> int:
    """XOR flip a specific yao position. Returns new state.
    
    Args:
        state: Current 6-bit hexagram integer.
        yao_index: 1-based (1=初爻, ..., 6=上爻).
    
    Returns:
        New hexagram integer after flip.
    """
    if yao_index < 1 or yao_index > 6:
        raise ValueError(f"Invalid yao_index: {yao_index}. Must be 1-6.")
    return state ^ YAO_BIT_MASK[yao_index]


def apply_error_mask(state: int, error_type: str) -> int:
    """Apply an error mask to the hexagram state.
    
    Args:
        state: Current 6-bit hexagram integer.
        error_type: Key from ERROR_MASK dict.
    
    Returns:
        New hexagram integer after flipping the error's bit.
    """
    mask = ERROR_MASK.get(error_type)
    if mask is None:
        raise ValueError(f"Unknown error type: {error_type}")
    return state ^ mask
