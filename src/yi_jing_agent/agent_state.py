"""䷀ 六爻 Agent 狀態機 — Core Agent State Machine"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .yao_positions import YaoPosition, AuthorizationLevel


class LifecycleMode(Enum):
    """六爻執行模式 — 控制生命週期完整度"""
    EXPRESS = 0   # 快速：初爻→五爻→上爻（skip 二、三、四爻）
    STANDARD = 1  # 標準：初爻→二爻→三爻→五爻→上爻（skip 四爻）
    FULL = 2      # 完整：所有 6 爻


@dataclass
class TaskGraph:
    """初爻輸出：結構化任務圖"""
    task_id: str = ""
    original_intent: str = ""
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # easy | medium | hard


@dataclass
class FeasibilityReport:
    """二爻輸出：可行性報告"""
    plan_a_description: str = ""
    key_apis: List[str] = field(default_factory=list)
    estimated_tokens: int = 0
    known_risks: List[str] = field(default_factory=list)
    fallback_plans: List[str] = field(default_factory=list)


@dataclass
class SafetyReport:
    """三爻輸出：安全審查報告"""
    passed: bool = False
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requires_human: bool = False


@dataclass
class HexagramTransition:
    """動爻變卦結果"""
    original_code: str = "111111"
    new_code: str = "111111"
    moving_yaos: List[int] = field(default_factory=list)
    transition_name: str = "䷀ 乾為天"
    strategy: str = "Happy Path"


@dataclass
class Reflection3D:
    """三維反思輸出"""
    interlocking_hidden: str = ""   # 互卦：隱含動機
    opposite_risk: str = ""         # 錯卦：對抗視角
    reversed_user: str = ""         # 綜卦：用戶視角
    requires_changes: bool = False
    changes: List[str] = field(default_factory=list)


@dataclass
class MemoryEntry:
    """上爻記憶壓縮格式"""
    hexagram_path: str = ""
    task_type: str = ""
    execution_summary: str = ""
    key_patterns: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class YiJingAgentState:
    """
    ䷀ 核心 Agent 狀態機 — Bitwise v2
    
    維護六爻生命週期嘅完整狀態，包括：
    - 當前爻位追踪
    - 6-bit 整數卦象狀態碼 (0-63, MSB=初爻)
    - 位元遮罩動爻變卦
    - Error taxonomy 錯誤分類 (6 types → 6 bits)
    - Hamming distance 目標漂移檢測
    - 各爻輸出快取
    - 執行日誌
    """

    @property
    def hexagram_code(self) -> str:
        """Backward compat: 6-char binary string (e.g. '111111')."""
        return f"{self._hexagram_int:06b}"
    
    @hexagram_code.setter
    def hexagram_code(self, val: str):
        self._hexagram_int = int(val, 2)

    @property
    def hexagram_int(self) -> int:
        """Current 6-bit hexagram state (0-63)."""
        return self._hexagram_int
    
    @hexagram_int.setter
    def hexagram_int(self, val: int):
        if not (0 <= val <= 63):
            raise ValueError(f"Hexagram int must be 0-63, got {val}")
        self._hexagram_int = val

    def __init__(self):
        # 當前狀態
        self.current_yao: YaoPosition = YaoPosition.FIRST_HIDDEN

        # 卦象狀態（integer, property handles string backward compat）
        self._hexagram_int: int = 0b111111  # ䷀ 乾 — 初始完美態
        self.active_moving_yaos: List[int] = []
        self.hexagram_history: List[HexagramTransition] = []

        # 錯誤歷史（error taxonomy）
        self.error_history: List[Dict[str, Any]] = []
        self.drift_scores: List[float] = []

        # 任務上下文
        self.task_graph: Optional[TaskGraph] = None
        self.feasibility_report: Optional[FeasibilityReport] = None
        self.safety_report: Optional[SafetyReport] = None

        # 記憶
        self.short_term_memory: Dict[str, Any] = {}
        self.long_term_memory: List[MemoryEntry] = []

        # 授權
        self.authorization_level: AuthorizationLevel = AuthorizationLevel.NOTIFY
        self.human_confirmed: Optional[bool] = None

        # 元數據
        self.session_start: datetime = datetime.now()
        self.session_id: str = ""
        self.execution_log: List[Dict[str, Any]] = []

        # 生命週期模式
        self.lifecycle_mode: LifecycleMode = LifecycleMode.FULL
        self.skipped_yaos: List[YaoPosition] = []
        self.skipped_stages_log: List[str] = []

    def step_forward(self) -> "YiJingAgentState":
        """推進至下一爻時位"""
        if self.current_yao.value < 6:
            self.current_yao = YaoPosition(self.current_yao.value + 1)
        self._log(f"step_forward → {self.current_yao.chinese_name}")
        return self

    def step_backward(self, target: YaoPosition) -> "YiJingAgentState":
        """回溯至指定爻位（用於動爻降級）"""
        self.current_yao = target
        self._log(f"step_backward → {target.chinese_name}")
        return self

    def trigger_moving_yao(self, yao_index: int) -> HexagramTransition:
        """
        當某層發生異常，引發動爻，翻轉 bit 計算變卦。
        
        使用位元遮罩 XOR 翻轉（μs-level, zero alloc）：
            S_next = S_current ^ YAO_BIT_MASK[yao_index]
        
        Args:
            yao_index: 1-based 爻位（1=初爻, ..., 6=上爻）
            
        Returns:
            HexagramTransition: 變卦結果
        """
        from .hexagram_table import YAO_BIT_MASK, get_hexagram_name, get_strategy_for_hexagram

        if yao_index < 1 or yao_index > 6:
            raise ValueError(f"Invalid yao_index: {yao_index}. Must be 1-6.")

        old_int = self.hexagram_int
        new_int = old_int ^ YAO_BIT_MASK[yao_index]  # 1 CPU cycle!

        transition = HexagramTransition(
            original_code=f"{old_int:06b}",
            new_code=f"{new_int:06b}",
            moving_yaos=[yao_index],
            transition_name=get_hexagram_name(new_int),
            strategy=get_strategy_for_hexagram(new_int),
        )

        self.hexagram_int = new_int
        self.active_moving_yaos.append(yao_index)
        self.hexagram_history.append(transition)
        self._log(
            f"⚡ moving_yao bit{yao_index}: "
            f"{old_int:06b} → {new_int:06b} ({transition.transition_name})"
        )

        return transition

    def check_yao(self, yao_index: int) -> bool:
        """Check if a specific yao position is healthy (bit = 1).
        
        Args:
            yao_index: 1-based (1=初爻, ..., 6=上爻).
        
        Returns:
            True if bit = 1 (healthy), False if 0 (fault).
        """
        from .hexagram_table import YAO_BIT_MASK
        return bool(self.hexagram_int & YAO_BIT_MASK[yao_index])

    def get_faulty_yaos(self) -> list[int]:
        """Return list of yao indices where bit = 0 (faulty)."""
        return [i for i in range(1, 7) if not self.check_yao(i)]

    def hamming_to_goal(self) -> int:
        """Hamming distance from current state to ䷀ 乾 (perfect goal).
        
        Returns 0-6:
            0 = perfect alignment
            1-2 = minor drift (local retry)
            3+ = severe drift (reroute / HITL)
        """
        return (self.hexagram_int ^ 0b111111).bit_count()

    def drift_score(self) -> float:
        """Normalized drift score (0.0 = perfect, 1.0 = complete drift)."""
        return self.hamming_to_goal() / 6.0

    def record_error(self, error_type: str, details: str = ""):
        """Record an error and apply its bit mask to the hexagram state.
        
        Args:
            error_type: Key from ERROR_MASK (e.g. 'TOOL_EXECUTION_ERROR').
            details: Human-readable error description.
        """
        from .hexagram_table import ERROR_MASK, YAO_BIT_MASK, YAO_NAMES
        
        mask = ERROR_MASK.get(error_type)
        if mask is None:
            self._log(f"⚠️ Unknown error type: {error_type}")
            return
        
        # Find which yao position this error maps to
        for idx, m in YAO_BIT_MASK.items():
            if m == mask:
                yao_idx = idx
                break
        else:
            yao_idx = 0
        
        old_int = self.hexagram_int
        self.hexagram_int ^= mask
        
        self.error_history.append({
            "error_type": error_type,
            "yao_index": yao_idx,
            "yao_name": YAO_NAMES.get(yao_idx, ""),
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "old_state": old_int,
            "new_state": self.hexagram_int,
        })
        
        self._log(
            f"⚠️ error {error_type} → {YAO_NAMES.get(yao_idx, '?')} "
            f"({old_int:06b} → {self.hexagram_int:06b})"
        )

    def get_hexagram_path(self) -> str:
        """返回卦象變遷路徑（用於交付報告）"""
        if not self.hexagram_history:
            return f"䷀ (初始) → ䷀ (當前)"
        
        from .hexagram_table import get_hexagram_name
        
        path_parts = ["䷀ (初始)"]
        for t in self.hexagram_history:
            symbol = t.transition_name.split(" ")[0] if " " in t.transition_name else "䷀"
            path_parts.append(f"{symbol} ({t.transition_name})")
        
        # Add current
        current = get_hexagram_name(self.hexagram_int)
        symbol = current.split(" ")[0] if " " in current else "䷀"
        path_parts.append(f"{symbol} (當前)")
        
        return " → ".join(path_parts)

    def record_skip(self, yao: YaoPosition, reason: str = ""):
        """記錄被跳過嘅爻位"""
        self.skipped_yaos.append(yao)
        msg = f"⏭️ skip {yao.chinese_name}: {reason}"
        self.skipped_stages_log.append(msg)
        self._log(msg)

    def _log(self, message: str):
        """記錄執行日誌"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "yao": self.current_yao.chinese_name,
            "hexagram": f"{self.hexagram_int:06b}",
            "message": message,
        })
