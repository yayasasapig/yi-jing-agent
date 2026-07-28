"""䷀ 六爻 Agent 狀態機 — Core Agent State Machine"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .yao_positions import YaoPosition, AuthorizationLevel


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
    ䷀ 核心 Agent 狀態機
    
    維護六爻生命週期嘅完整狀態，包括：
    - 當前爻位追踪
    - 6-bit 卦象狀態碼
    - 動爻變卦歷史
    - 各爻輸出快取
    - 執行日誌
    """

    def __init__(self):
        # 當前狀態
        self.current_yao: YaoPosition = YaoPosition.FIRST_HIDDEN

        # 卦象狀態
        self.hexagram_code: str = "111111"  # 初始䷀ 乾為天
        self.active_moving_yaos: List[int] = []
        self.hexagram_history: List[HexagramTransition] = []

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
        
        Args:
            yao_index: 1-based 爻位（1=初爻, ..., 6=上爻）
            
        Returns:
            HexagramTransition: 變卦結果
        """
        if yao_index < 1 or yao_index > 6:
            raise ValueError(f"Invalid yao_index: {yao_index}. Must be 1-6.")

        old_code = self.hexagram_code
        code_list = list(self.hexagram_code)

        # XOR 翻轉：0 ↔ 1
        code_list[yao_index - 1] = "0" if code_list[yao_index - 1] == "1" else "1"
        new_code = "".join(code_list)

        from .hexagram_table import get_hexagram_name, get_strategy_for_hexagram

        transition = HexagramTransition(
            original_code=old_code,
            new_code=new_code,
            moving_yaos=[yao_index],
            transition_name=get_hexagram_name(new_code),
            strategy=get_strategy_for_hexagram(new_code),
        )

        self.hexagram_code = new_code
        self.active_moving_yaos.append(yao_index)
        self.hexagram_history.append(transition)
        self._log(
            f"⚡ moving_yao bit{yao_index}: "
            f"{old_code} → {new_code} ({transition.transition_name})"
        )

        return transition

    def get_hexagram_path(self) -> str:
        """返回卦象變遷路徑（用於交付報告）"""
        if not self.hexagram_history:
            return f"䷀ (初始) → ䷀ (當前)"
        
        path_parts = ["䷀ (初始)"]
        for t in self.hexagram_history:
            symbol = t.transition_name.split(" ")[0] if " " in t.transition_name else "䷀"
            path_parts.append(f"{symbol} ({t.transition_name})")
        
        # Add current
        from .hexagram_table import get_hexagram_name
        current = get_hexagram_name(self.hexagram_code)
        symbol = current.split(" ")[0] if " " in current else "䷀"
        path_parts.append(f"{symbol} (當前)")
        
        return " → ".join(path_parts)

    def _log(self, message: str):
        """記錄執行日誌"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "yao": self.current_yao.chinese_name,
            "hexagram": self.hexagram_code,
            "message": message,
        })
