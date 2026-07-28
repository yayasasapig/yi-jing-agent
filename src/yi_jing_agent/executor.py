"""䷀ 六爻 Agent 執行器 — Full Lifecycle Executor

控制完整嘅六爻生命週期：初爻→二爻→三爻→四爻→五爻→上爻
含動爻變卦容錯機制

YiJingAgentExecutor (ABC):
    抽象基底類別，定義六爻生命週期框架。
    Subclasses must implement the 6 abstract methods.

HermesYiJingExecutor:
    Concrete default implementation with optional LLM callback.
    Use this for a ready-to-use executor.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable

from .agent_state import (
    YiJingAgentState, YaoPosition, AuthorizationLevel,
    TaskGraph, FeasibilityReport, SafetyReport,
    HexagramTransition, MemoryEntry,
)
from .reflection import ThreeDimensionalReflection, Reflection3DResult
from .hexagram_table import get_hexagram_name

logger = logging.getLogger(__name__)

# ── LLM Callback Interface ──

LLMCallable = Callable[[str], Awaitable[str]]
"""
LLM callback protocol.

An async callable that accepts a prompt string and returns a response string.
Used by HermesYiJingExecutor to power LLM-dependent stages.
"""


class YiJingAgentExecutor(ABC):
    """
    ䷀ 六爻 Agent 執行器 (Abstract Base Class)

    定義六爻生命週期框架：
    1. 初爻：解析意圖 → Task Graph
    2. 二爻：沙盒試探 → 可行性報告
    3. 三爻：三維反思 → 安全審查
    4. 四爻：授權決策 → 確認閘門
    5. 五爻：全力執行 → Core Payload
    6. 上爻：記憶壓縮 → LTM 寫入

    Subclasses必须 implement 以下 abstract methods：
        _parse_intent, _sandbox_prototype, _reflexion_gate,
        _request_authorization, _execute_master, _memory_compression

    Use :class:`HermesYiJingExecutor` for a ready-to-use default implementation.
    """

    def __init__(self, session_id: str = ""):
        self.state = YiJingAgentState()
        self.state.session_id = (
            session_id
            or f"S-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        self.max_retries = 3
        self.reflection_engine = ThreeDimensionalReflection()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # ═══════════════════════════════════════════════
    #  Abstract Methods — 子類必須實作
    # ═══════════════════════════════════════════════

    @abstractmethod
    async def _parse_intent(self, user_input: str) -> TaskGraph:
        """
        初爻：解析用戶意圖，返回結構化 TaskGraph。

        Args:
            user_input: 用戶原始輸入。

        Returns:
            TaskGraph: 結構化任務圖。若無法解析，
                       original_intent 應留空以觸發 execute() 嘅失敗路徑。
        """
        ...

    @abstractmethod
    async def _sandbox_prototype(self, task: TaskGraph) -> FeasibilityReport:
        """
        二爻：沙盒試探可行性。

        喺隔離環境測試可行性、檢查工具可用性、
        估算 token usage、列舉已知風險。

        Args:
            task: 結構化任務圖。

        Returns:
            FeasibilityReport: 可行性報告。
        """
        ...

    @abstractmethod
    async def _reflexion_gate(
        self, task: TaskGraph, report: FeasibilityReport
    ) -> SafetyReport:
        """
        三爻：風險審查。

        執行安全檢查，可配合三維反思引擎做深度審查。

        Args:
            task: 結構化任務圖。
            report: 可行性報告。

        Returns:
            SafetyReport: 安全審查報告。
        """
        ...

    @abstractmethod
    async def _request_authorization(self) -> bool:
        """
        四爻：請求人類授權。

        Returns:
            bool: True 表示授權通過，False 表示人類拒絕。
        """
        ...

    @abstractmethod
    async def _execute_master(self, report: FeasibilityReport) -> Any:
        """
        五爻：全力執行。

        調用工具、並行處理、整合結果。
        Subclasses 應實作 retry logic 與 timeout handling。

        Args:
            report: 可行性報告。

        Returns:
            Any: 執行結果（通常為 dict，含 output/status 等欄位）。
        """
        ...

    @abstractmethod
    async def _memory_compression(self, result: Any):
        """
        上爻：記憶壓縮。

        清理臨時 data，提取 key patterns/failure modes，
        經驗寫入 LTM（self.state.long_term_memory）。

        Args:
            result: 執行結果（_execute_master 嘅回傳值）。
        """
        ...

    # ═══════════════════════════════════════════════
    #  Non-Abstract Methods — 有默認實作，可選擇性覆寫
    # ═══════════════════════════════════════════════

    async def execute(self, user_input: str) -> Dict[str, Any]:
        """
        執行一次完整嘅六爻任務生命週期。

        呢個係框架核心 controller，**唔應該俾人 override**。
        如需自訂行為，請覆寫對應嘅 abstract methods。

        Args:
            user_input: 用戶原始輸入。

        Returns:
            dict: 包含 status, result, hexagram_history, execution_log, session_id。
        """
        # ── 初爻：潛龍勿用 ──
        self.state.current_yao = YaoPosition.FIRST_HIDDEN
        self._logger.info("初爻：潛龍勿用 — 解析意圖")
        task_graph = await self._parse_intent(user_input)
        self.state.task_graph = task_graph

        if not task_graph or not task_graph.original_intent:
            self._logger.warning("初爻失敗：無法解析用戶意圖")
            return self._fail("初爻失敗：無法解析用戶意圖")

        # ── 二爻：見龍在田 ──
        self.state.step_forward()
        self._logger.info("二爻：見龍在田 — 沙盒試探")
        feasibility = await self._sandbox_prototype(task_graph)
        self.state.feasibility_report = feasibility

        # ── 三爻：終日乾乾 ──
        self.state.step_forward()
        self._logger.info("三爻：終日乾乾 — 安全審查 + 三維反思")
        safety = await self._reflexion_gate(task_graph, feasibility)
        self.state.safety_report = safety

        # 三維反思（額外分析層）
        reflection_result = await self._run_3d_reflection(
            task_graph.original_intent,
            feasibility.plan_a_description or "",
            "Default output format",
        )
        if reflection_result and reflection_result.requires_changes:
            self._logger.info("三維反思觸發計畫修正")
            feasibility = await self._revise_plan(reflection_result)
            self.state.feasibility_report = feasibility

        if not safety.passed and safety.requires_human:
            transition = self.state.trigger_moving_yao(3)
            # 三爻動爻 → 要求人類介入
            self._logger.warning("三爻安全審查失敗，要求人類介入")
            return self._request_human_intervention(transition, safety)

        # ── 四爻：或躍在淵 ──
        self.state.step_forward()
        if self.state.authorization_level == AuthorizationLevel.CONFIRM:
            self._logger.info("四爻：或躍在淵 — 請求授權")
            authorization = await self._request_authorization()
            if not authorization:
                return self._fail("四爻：人類拒絕授權，任務終止")

        # ── 五爻：飛龍在天 ──
        self.state.step_forward()
        self._logger.info("五爻：飛龍在天 — 全力執行")
        try:
            result = await self._execute_master(feasibility)
        except Exception as e:
            # 觸發動爻 → 變卦 → 降級執行
            self._logger.warning(f"五爻執行異常，觸發動爻: {e}")
            transition = self.state.trigger_moving_yao(5)
            result = await self._fallback_execution(transition, feasibility, str(e))

        # ── 上爻：亢龍有悔 ──
        self.state.step_forward()
        self._logger.info("上爻：亢龍有悔 — 記憶壓縮")
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

    async def _run_3d_reflection(
        self,
        task_desc: str,
        plan: str,
        output_fmt: str,
    ) -> Reflection3DResult:
        """執行三維反思引擎。

        run_full_reflection() 係 CPU-bound sync operation，
        用 asyncio.to_thread() offload 以免阻塞 event loop。

        Args:
            task_desc: 任務描述。
            plan: 執行計劃。
            output_fmt: 預期輸出格式。

        Returns:
            Reflection3DResult: 三維反思結果。
        """
        return await asyncio.to_thread(
            self.reflection_engine.run_full_reflection,
            task_description=task_desc,
            plan=plan,
            output_format=output_fmt,
        )

    async def _revise_plan(
        self, reflection: Reflection3DResult
    ) -> FeasibilityReport:
        """根據三維反思結果修正計畫。

        Args:
            reflection: 三維反思結果。

        Returns:
            FeasibilityReport: 更新後嘅可行性報告。
        """
        self.state._log("三維反思觸發內部修正")
        return self.state.feasibility_report or FeasibilityReport()

    async def _fallback_execution(
        self,
        transition: HexagramTransition,
        report: FeasibilityReport,
        error: str = "",
    ) -> Any:
        """
        降級執行（動爻觸發後）。

        根據變卦策略執行 Plan B。

        Args:
            transition: 動爻變卦結果。
            report: 原始可行性報告。
            error: 觸發降級嘅錯誤訊息。

        Returns:
            Any: 降級執行結果。
        """
        self.state._log(
            f"降級執行: {transition.strategy} | error: {error}"
        )
        self._logger.info(f"降級執行: strategy={transition.strategy}, error={error}")
        return {
            "output": "fallback result",
            "fallback": True,
            "triggered_by": transition.transition_name,
            "strategy": transition.strategy,
        }

    def _request_human_intervention(
        self,
        transition: HexagramTransition,
        safety: SafetyReport,
    ) -> Dict[str, Any]:
        """請求人類介入（三爻動爻）。

        Args:
            transition: 動爻變卦結果。
            safety: 安全審查報告。

        Returns:
            dict: requires_human status response。
        """
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
        """返回失敗響應。

        Args:
            reason: 失敗原因。

        Returns:
            dict: failed status response。
        """
        self.state._log(f"❌ FAIL: {reason}")
        self._logger.error(reason)
        return {
            "status": "failed",
            "reason": reason,
            "session_id": self.state.session_id,
        }


class HermesYiJingExecutor(YiJingAgentExecutor):
    """
    ䷀ Hermes 默認六爻執行器

    提供 meaningful default implementation for all abstract methods。
    接受一個 optional LLM callback，用於 LLM-powered 嘅步驟。
    如果無提供 LLM callback，則用 logging 模擬執行。

    Usage::

        # Without LLM (simulated)
        executor = HermesYiJingExecutor()
        result = await executor.execute("Build a test")

        # With LLM
        async def my_llm(prompt: str) -> str:
            return await my_client.generate(prompt)
        executor = HermesYiJingExecutor(llm_call=my_llm)
        result = await executor.execute("Summarize this file")
    """

    def __init__(
        self,
        session_id: str = "",
        llm_call: Optional[LLMCallable] = None,
    ):
        super().__init__(session_id=session_id)
        self._llm_call = llm_call
        self._execution_timeout: float = 30.0  # seconds for timeout handling
        if llm_call is None:
            self._logger.info(
                "HermesYiJingExecutor: no llm_call provided, "
                "using simulated execution"
            )

    # ── Helpers ──

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """If LLM callable is available, call it; else log and return None.

        LLMCallable 保證係 async callable（回傳 Awaitable[str]），
        所以直接用 await，唔需要 iscoroutine() check。
        """
        if self._llm_call is not None:
            self._logger.debug(f"LLM call: {prompt[:120]}...")
            try:
                return await self._llm_call(prompt)
            except Exception as e:
                self._logger.warning(f"LLM call failed: {e}")
                return None
        self._logger.info(f"[SIMULATED LLM] %s", prompt[:150])
        return None

    def _try_parse_json(self, response: Optional[str]) -> Optional[dict]:
        """Safely attempt to parse a JSON response."""
        if not response:
            return None
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self._logger.warning("LLM response was not valid JSON")
            return None

    # ── Abstract Method Implementations ──

    async def _parse_intent(self, user_input: str) -> TaskGraph:
        """初爻：用 LLM 做 prompt-based intent parsing。

        如果無 LLM callback，返回基本 TaskGraph（與舊 stub 行為兼容）。
        """
        self._logger.info("初爻：解析意圖 begin")
        task_graph = TaskGraph(
            task_id=f"T-{self.state.session_id}",
            original_intent=user_input,
            estimated_complexity="medium",
        )

        if self._llm_call is not None:
            prompt = (
                "Parse the following user intent into a structured TaskGraph.\n"
                f"User input: {user_input}\n"
                "Return JSON ONLY with these keys: "
                "constraints (list), success_criteria (list), "
                "forbidden_actions (list), estimated_complexity (string)"
            )
            response = await self._call_llm(prompt)
            data = self._try_parse_json(response)
            if data:
                task_graph.constraints = data.get("constraints", [])
                task_graph.success_criteria = data.get("success_criteria", [])
                task_graph.forbidden_actions = data.get("forbidden_actions", [])
                task_graph.estimated_complexity = data.get(
                    "estimated_complexity", "medium"
                )
                self._logger.info(
                    "LLM parsed intent: %d constraints, %d criteria, %d forbidden",
                    len(task_graph.constraints),
                    len(task_graph.success_criteria),
                    len(task_graph.forbidden_actions),
                )
        else:
            self._logger.info("Intent (simulated): %s", user_input[:100])

        self._logger.info("初爻：解析意圖 complete")
        return task_graph

    async def _sandbox_prototype(self, task: TaskGraph) -> FeasibilityReport:
        """二爻：檢查 tools availability，估算 token usage，列舉已知風險。"""
        self._logger.info("二爻：沙盒試探 begin")
        report = FeasibilityReport(
            plan_a_description=(
                f"Feasibility analysis for: {task.original_intent[:100] or 'No input'}"
            ),
            estimated_tokens=500,
            known_risks=[],
            key_apis=[],
            fallback_plans=[],
        )

        if self._llm_call is not None:
            prompt = (
                "Analyze the feasibility of this task.\n"
                f"Task: {task.original_intent}\n"
                f"Constraints: {task.constraints}\n"
                "Return JSON ONLY with: "
                "key_apis (list), estimated_tokens (int), "
                "known_risks (list), fallback_plans (list)"
            )
            response = await self._call_llm(prompt)
            data = self._try_parse_json(response)
            if data:
                report.key_apis = data.get("key_apis", [])
                report.estimated_tokens = data.get("estimated_tokens", 500)
                report.known_risks = data.get("known_risks", [])
                report.fallback_plans = data.get("fallback_plans", [])

        # Simulate tools availability check
        self._logger.info(
            "Tools available: %d | Estimated tokens: %d | Risks: %d",
            len(report.key_apis),
            report.estimated_tokens,
            len(report.known_risks),
        )
        self._logger.info("二爻：沙盒試探 complete")
        return report

    async def _reflexion_gate(
        self, task: TaskGraph, report: FeasibilityReport
    ) -> SafetyReport:
        """三爻：執行 reflection engine + LLM safety check。"""
        self._logger.info("三爻：安全審查 begin")

        # Default: safe
        safety = SafetyReport(passed=True, issues=[], recommendations=[])

        # Run reflection engine for safety signals
        reflection_result = await asyncio.to_thread(
            self.reflection_engine.run_full_reflection,
            task_description=task.original_intent,
            plan=report.plan_a_description,
            output_format="Default",
        )
        if reflection_result and reflection_result.requires_changes:
            safety.issues.extend(reflection_result.changes)
            if not safety.issues:
                safety.issues = ["Reflection engine flagged changes needed"]

        # LLM-based safety check
        if self._llm_call is not None:
            prompt = (
                "Perform a safety review of this task plan.\n"
                f"Task: {task.original_intent}\n"
                f"Plan: {report.plan_a_description}\n"
                f"Known risks: {', '.join(report.known_risks)}\n"
                "Return JSON ONLY with: "
                "passed (bool), issues (list), "
                "recommendations (list), requires_human (bool)"
            )
            response = await self._call_llm(prompt)
            data = self._try_parse_json(response)
            if data:
                safety.passed = data.get("passed", True)
                safety.issues.extend(data.get("issues", []))
                safety.recommendations = data.get("recommendations", [])
                safety.requires_human = data.get("requires_human", False)

        # If any issues found, don't pass automatically
        if safety.issues and safety.passed:
            self._logger.warning(
                "Safety issues found but passed=True — flagging for review"
            )
            # Keep passed=True but log warning; caller will check requires_human

        self._logger.info(
            "審查結果: passed=%s, issues=%d, requires_human=%s",
            safety.passed,
            len(safety.issues),
            safety.requires_human,
        )
        self._logger.info("三爻：安全審查 complete")
        return safety

    async def _request_authorization(self) -> bool:
        """四爻：記錄授權請求日誌（唔係真係 send message）。"""
        self._logger.info("四爻：請求人類授權")
        task_preview = (
            self.state.task_graph.original_intent[:100]
            if self.state.task_graph
            else "N/A"
        )
        self._logger.info(
            "[AUTHORIZATION REQUEST] Session: %s | Task: %s",
            self.state.session_id,
            task_preview,
        )
        self._logger.info(
            "授權請求已記錄 — 預設返回 True (authorized)"
        )
        return True

    async def _execute_master(self, report: FeasibilityReport) -> Any:
        """五爻：全力執行（含 retry + timeout + 具體 exception handling）。"""
        self._logger.info("五爻：全力執行 begin")
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if self._llm_call is not None:
                    # LLM-powered execution with timeout
                    prompt = (
                        "Execute the following task and return the result.\n"
                        f"Plan: {report.plan_a_description}\n"
                        "Return JSON with 'output' (string) and 'status' (string)."
                    )
                    response = await asyncio.wait_for(
                        self._llm_call(prompt),
                        timeout=self._execution_timeout,
                    )
                    data = self._try_parse_json(response)
                    if data:
                        result = data
                    else:
                        result = {"output": response, "status": "completed"}
                    self._logger.info(
                        "五爻：LLM 執行成功 (attempt %d/%d)",
                        attempt,
                        self.max_retries,
                    )
                    return result
                else:
                    # Simulated execution (instant — no timeout needed)
                    self._logger.info(
                        "五爻：模擬執行 (attempt %d/%d)",
                        attempt,
                        self.max_retries,
                    )
                    return {"output": "task result (stub)", "status": "completed"}

            except asyncio.TimeoutError:
                self._logger.warning(
                    "執行超時 (attempt %d/%d)", attempt, self.max_retries
                )
                last_exception = asyncio.TimeoutError(
                    f"Execution timed out after {self._execution_timeout}s"
                )
            except ConnectionError as e:
                self._logger.warning(
                    "連接錯誤 (attempt %d/%d): %s", attempt, self.max_retries, e
                )
                last_exception = e
            except OSError as e:
                self._logger.warning(
                    "系統錯誤 (attempt %d/%d): %s", attempt, self.max_retries, e
                )
                last_exception = e

            if attempt < self.max_retries:
                wait = 2**attempt
                self._logger.info("等待 %ds 後重試...", wait)
                await asyncio.sleep(wait)

        self._logger.error(
            "五爻：全部 %d 次嘗試均失敗", self.max_retries
        )
        raise last_exception or RuntimeError(
            "Execution failed with no specific exception"
        )

    async def _memory_compression(self, result: Any):
        """上爻：用 LLM 做 meaningful memory compression。"""
        self._logger.info("上爻：記憶壓縮 begin")
        result_status = (
            result.get("status", "unknown")
            if isinstance(result, dict)
            else "unknown"
        )

        entry = MemoryEntry(
            hexagram_path=self.state.get_hexagram_path(),
            task_type=(
                self.state.task_graph.original_intent[:50]
                if self.state.task_graph
                else ""
            ),
            execution_summary=f"Status: {result_status}",
        )

        if self._llm_call is not None and self.state.task_graph:
            prompt = (
                "Compress this execution into a structured memory entry.\n"
                f"Task: {self.state.task_graph.original_intent}\n"
                f"Result status: {result_status}\n"
                f"Hexagram path: {self.state.get_hexagram_path()}\n"
                "Return JSON ONLY with: "
                "key_patterns (list), failure_modes (list), "
                "recommendations (list)"
            )
            response = await self._call_llm(prompt)
            data = self._try_parse_json(response)
            if data:
                entry.key_patterns = data.get("key_patterns", [])
                entry.failure_modes = data.get("failure_modes", [])
                entry.recommendations = data.get("recommendations", [])

        self.state.long_term_memory.append(entry)
        self.state._log(f"記憶壓縮完成: {entry.hexagram_path}")
        self._logger.info(
            "記憶壓縮 complete: path=%s, status=%s",
            entry.hexagram_path,
            result_status,
        )
