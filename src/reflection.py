"""⚔️ 三維反思引擎 — 3D Reflection Engine (錯綜互卦)

三爻（終日乾乾）時強制啟動，從三個維度審視任務計畫。
"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class Reflection3DResult:
    """三維反思結果"""
    # 互卦：隱含動機分析
    hidden_motive: str = ""
    deeper_goal: str = ""
    
    # 錯卦：對抗視角
    worst_case: str = ""
    failure_points: List[str] = field(default_factory=list)
    
    # 綜卦：用戶視角
    user_experience: str = ""
    accessibility_issues: List[str] = field(default_factory=list)
    
    # 結果
    requires_changes: bool = False
    changes: List[str] = field(default_factory=list)


class ThreeDimensionalReflection:
    """
    🧿 三維反思引擎
    
    基於《易經》錯綜互卦概念：
    - 互卦 (Interlocking) = 2-3-4 + 3-4-5 爻 → 隱含動機
    - 錯卦 (Opposite) = 每爻徹底反轉 → 對抗思維
    - 綜卦 (Reversed) = 卦象倒轉 180° → 用戶視角
    """

    def __init__(self, hexagram_code: str = "111111"):
        self.hexagram_code = hexagram_code

    def analyze_interlocking(self, task_description: str) -> dict:
        """
        互卦分析：深挖用戶隱含動機
        
        易經：互卦由 2-3-4（內互卦）+ 3-4-5 爻（外互卦）組成
        AI: 分析表面 request 背後嘅真正需要
        """
        bits = list(self.hexagram_code)
        inner_trigram = "".join(bits[1:4])   # 2-3-4 爻
        outer_trigram = "".join(bits[2:5])   # 3-4-5 爻
        
        return {
            "inner_trigram": inner_trigram,
            "outer_trigram": outer_trigram,
            "surface_task": task_description,
            "reflection_prompt": (
                "互卦反思：用戶表面 request 係「{task}」，"
                "但 deeper goal 可能係咩？有冇未講出口嘅真正需求？"
            ).format(task=task_description),
        }

    def analyze_opposite(self, plan: str) -> dict:
        """
        錯卦分析：Red Teaming / 對抗視角
        
        易經：錯卦 = 每個爻位徹底反轉（陰↔陽）
        AI: 假設所有 Plan 都錯，邊度會死？
        """
        opposite_code = "".join(
            "0" if bit == "1" else "1"
            for bit in self.hexagram_code
        )
        
        return {
            "original_code": self.hexagram_code,
            "opposite_code": opposite_code,
            "plan": plan,
            "reflection_prompt": (
                "錯卦反思：假設當前的假設全部都係錯嘅，"
                "呢個計劃會喺邊度徹底潰敗？"
            ),
        }

    def analyze_reversed(self, output_format: str) -> dict:
        """
        綜卦分析：User Perspective / 換位思考
        
        易經：綜卦 = 將卦象倒轉 180°
        AI: 企喺終端用戶角度審視呢個輸出
        """
        reversed_code = self.hexagram_code[::-1]
        
        return {
            "original_code": self.hexagram_code,
            "reversed_code": reversed_code,
            "output_format": output_format,
            "reflection_prompt": (
                "綜卦反思：終端使用者接到呢個輸出時，"
                "體驗係咪順暢？格式啱唔啱佢地閱讀？"
            ),
        }

    def run_full_reflection(
        self,
        task_description: str = "",
        plan: str = "",
        output_format: str = ""
    ) -> Reflection3DResult:
        """
        執行完整三維反思，返回結構化結果。
        
        每個 Agent 可以 override 呢個方法注入自己嘅 LLM call。
        """
        interlocking = self.analyze_interlocking(task_description)
        opposite = self.analyze_opposite(plan)
        reversed_view = self.analyze_reversed(output_format)
        
        return Reflection3DResult(
            hidden_motive=interlocking["reflection_prompt"],
            worst_case=opposite["reflection_prompt"],
            user_experience=reversed_view["reflection_prompt"],
        )
