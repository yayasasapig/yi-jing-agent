"""䷀ 六爻 Agent 執行器 — Full Lifecycle Executor

控制完整嘅六爻生命週期：初爻→二爻→三爻→四爻→五爻→上爻
含動爻變卦容錯機制
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .agent_state import (
    YiJingAgentState, YaoPosition, AuthorizationLevel,
    TaskGraph, FeasibilityReport, SafetyReport,
    HexagramTransition, MemoryEntry,
)
from .reflection import ThreeDimensionalReflection
from .hexagram_table import get_hexagram_name


class YiJingAgentExecutor:
    """
    ䷀ 六爻 Agent 執行器
    
    控制完整嘅生命週期：
    1. 初爻：解析意圖 → Task Graph
    2. 二爻：沙盒試探 → 可行性報告
    3. 三爻：三維反思 → 安全審查
    4. 四爻：授權決策 → 確認閘門
    5. 五爻：全力執行 → Core Payload
    6. 上爻：記憶壓縮 → LTM 寫入
    """

    def __init__(self, session_id: str = ""):
        self.state = YiJingAgentState()
        self.state.session_id = session_id or f"S-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.max_retries = 3
        self.reflection_engine = ThreeDimensionalReflection()

    async def execute(self, user_input: str) -> Dict[str, Any]:
        """
        執行一次完整嘅六爻任務生命週期
        
        Args:
            user_input: 用戶原始輸入
            
        Returns:
            dict: 包含 status, result, hexagram_history, execution_log
        """
        # ── 初爻：潛龍勿用 ──
        self.state.current_yao = YaoPosition.FIRST_HIDDEN
        task_graph = await self._parse_intent(user_input)
        self.state.task_graph = task_graph

        if not task_graph or not task_graph.original_intent:
            return self._fail("初爻失敗：無法解析用戶意圖")

        # ── 二爻：見龍在田 ──
        self.state.step_forward()
        feasibility = await self._sandbox_prototype(task_graph)
        self.state.feasibility_report = feasibility

        # ── 三爻：終日乾乾 ──
        self.state.step_forward()
        safety = await self._reflexion_gate(task_graph, feasibility)
        self.state.safety_report = safety

        # 三維反思
        reflection_result = await self._run_3d_reflection(
            task_graph.original_intent,
            feasibility.plan_a_description,
            "Default output format"
        )
        if reflection_result.requires_changes:
            feasibility = await self._revise_plan(reflection_result)
            self.state.feasibility_report = feasibility

        if not safety.passed and safety.requires_human:
            transition = self.state.trigger_moving_yao(3)
            # 三爻動爻 → 要求人類介入
            return self._request_human_intervention(transition, safety)

        # ── 四爻：或躍在淵 ──
        self.state.step_forward()
        if self.state.authorization_level == AuthorizationLevel.CONFIRM:
            authorization = await self._request_authorization()
            if not authorization:
                return self._fail("四爻：人類拒絕授權，任務終止")

        # ── 五爻：飛龍在天 ──
        self.state.step_forward()
        try:
            result = await self._execute_master(feasibility)
        except Exception as e:
            # 觸發動爻 → 變卦 → 降級執行
            transition = self.state.trigger_moving_yao(5)
            result = await self._fallback_execution(transition, feasibility, str(e))

        # ── 上爻：亢龍有悔 ──
        self.state.step_forward()
        await self._memory_compression(result)

        return {
            "status": "success",
            "result": result,
            "hexagram_path": self.state.get_hexagram_path(),
            "hexagram_history": [
                {
                    "original": t.original_code,
                    "new": t.new_code,
                    "name": t.transition_name,
                    "strategy": t.strategy,
                    "moving_yaos": t.moving_yaos,
                }
                for t in self.state.hexagram_history
            ],
            "execution_log": self.state.execution_log,
            "session_id": self.state.session_id,
        }

    async def _parse_intent(self, user_input: str) -> TaskGraph:
        """
        初爻：純理解，唔准郁
        
        Agent 應 override 呢個方法注入 LLM call。
        呢度只係示範用嘅 stub。
        """
        return TaskGraph(
            task_id=f"T-{self.state.session_id}",
            original_intent=user_input,
            estimated_complexity="medium",
        )

    async def _sandbox_prototype(self, task: TaskGraph) -> FeasibilityReport:
        """
        二爻：沙盒試探
        
        喺隔離環境測試可行性。
        Agent 應 override 呢個方法注入實際檢查邏輯。
        """
        return FeasibilityReport(
            plan_a_description="可行性分析完成（stub）",
            estimated_tokens=500,
        )

    async def _reflexion_gate(
        self, task: TaskGraph, report: FeasibilityReport
    ) -> SafetyReport:
        """
        三爻：風險審查
        
        執行安全檢查 + 三維反思。
        Agent 應 override 呢個方法注入實際審查邏輯。
        """
        return SafetyReport(passed=True)

    async def _run_3d_reflection(
        self, task_desc: str, plan: str, output_fmt: str
    ):
        """執行三維反思引擎"""
        return self.reflection_engine.run_full_reflection(
            task_description=task_desc,
            plan=plan,
            output_format=output_fmt,
        )

    async def _revise_plan(self, reflection) -> FeasibilityReport:
        """根據三維反思結果修正計畫"""
        self.state._log("三維反思觸發內部修正")
        return self.state.feasibility_report or FeasibilityReport()

    async def _request_authorization(self) -> bool:
        """
        四爻：請求人類授權。
        Agent 應 override 注入實際通知邏輯。
        """
        return True

    async def _execute_master(self, report: FeasibilityReport) -> Any:
        """
        五爻：全力執行
        
        調用工具、並行處理、整合結果。
        Agent 應 override 注入實際執行邏輯。
        """
        return {"output": "task result (stub)", "status": "completed"}

    async def _fallback_execution(
        self, transition: HexagramTransition,
        report: FeasibilityReport,
        error: str = ""
    ) -> Any:
        """
        降級執行（動爻觸發後）
        
        根據變卦策略執行 Plan B。
        """
        self.state._log(
            f"降級執行: {transition.strategy} | error: {error}"
        )
        return {
            "output": "fallback result",
            "fallback": True,
            "triggered_by": transition.transition_name,
            "strategy": transition.strategy,
        }

    async def _memory_compression(self, result: Any):
        """
        上爻：記憶壓縮
        
        清理臨時 data，經驗寫入 LTM。
        Agent 應 override 注入實際記憶寫入邏輯。
        """
        entry = MemoryEntry(
            hexagram_path=self.state.get_hexagram_path(),
            task_type=self.state.task_graph.original_intent[:50] if self.state.task_graph else "",
            execution_summary=f"Status: {result.get('status', 'unknown')}",
        )
        self.state.long_term_memory.append(entry)
        self.state._log(f"記憶壓縮完成: {entry.hexagram_path}")

    def _request_human_intervention(
        self, transition: HexagramTransition,
        safety: SafetyReport
    ) -> Dict[str, Any]:
        """請求人類介入（三爻動爻）"""
        return {
            "status": "requires_human",
            "reason": "三爻安全審查失敗",
            "hexagram_transition": {
                "from": transition.original_code,
                "to": transition.new_code,
                "name": transition.transition_name,
                "strategy": transition.strategy,
            },
            "safety_issues": safety.issues,
        }

    def _fail(self, reason: str) -> Dict[str, Any]:
        self.state._log(f"❌ FAIL: {reason}")
        return {
            "status": "failed",
            "reason": reason,
            "session_id": self.state.session_id,
        }
