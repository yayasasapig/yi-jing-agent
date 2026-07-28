"""Tests for YiJingAgentExecutor — the async lifecycle executor.

Tests cover:
- ABC invariant (YiJingAgentExecutor cannot be instantiated directly)
- HermesYiJingExecutor initialization and lifecycle
- Each yao stage (failure modes, safety gate, fallback, memory)
- Hexagram history recording
- HermesYiJingExecutor LLM-powered methods
"""

import asyncio
import pytest
from datetime import datetime

from yi_jing_agent.executor import YiJingAgentExecutor, HermesYiJingExecutor
from yi_jing_agent.agent_state import (
    YiJingAgentState, YaoPosition, SafetyReport, FeasibilityReport, TaskGraph,
)


# ════════════════════════════════════════════════════════════════
#  ABC Invariant Tests
# ════════════════════════════════════════════════════════════════

class TestYiJingAgentExecutorIsABC:
    """YiJingAgentExecutor must be an ABC — cannot be instantiated directly."""

    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            YiJingAgentExecutor()

    def test_has_abstract_methods(self):
        """Ensure the six required abstract methods exist on the class."""
        abstract_methods = {
            name
            for name, method in YiJingAgentExecutor.__dict__.items()
            if getattr(method, "__isabstractmethod__", False)
        }
        expected = {
            "_parse_intent",
            "_sandbox_prototype",
            "_reflexion_gate",
            "_request_authorization",
            "_execute_master",
            "_memory_compression",
        }
        assert abstract_methods == expected, (
            f"Expected {expected}, got {abstract_methods}"
        )

    def test_non_abstract_methods_exist(self):
        """Non-abstract methods should have concrete implementations."""
        methods = {
            "_run_3d_reflection",
            "_revise_plan",
            "_fallback_execution",
            "execute",
        }
        for name in methods:
            assert hasattr(YiJingAgentExecutor, name), f"Missing method: {name}"
            method = getattr(YiJingAgentExecutor, name)
            assert not getattr(method, "__isabstractmethod__", False), (
                f"{name} should not be abstract"
            )

    def test_hermes_executor_is_concrete(self):
        """HermesYiJingExecutor should be instantiable."""
        executor = HermesYiJingExecutor()
        assert isinstance(executor, YiJingAgentExecutor)


# ════════════════════════════════════════════════════════════════
#  HermesYiJingExecutor — Initialization
# ════════════════════════════════════════════════════════════════

class TestInitialization:
    """Executor initialization."""

    def test_session_id_generated(self):
        executor = HermesYiJingExecutor()
        assert executor.state.session_id != ""
        assert executor.state.session_id.startswith("S-")

    def test_session_id_custom(self):
        executor = HermesYiJingExecutor(session_id="CUSTOM-001")
        assert executor.state.session_id == "CUSTOM-001"

    def test_state_is_yijing_agent_state(self):
        executor = HermesYiJingExecutor()
        assert isinstance(executor.state, YiJingAgentState)

    def test_default_max_retries(self):
        executor = HermesYiJingExecutor()
        assert executor.max_retries == 3

    def test_state_initial_yao(self):
        executor = HermesYiJingExecutor()
        assert executor.state.current_yao == YaoPosition.FIRST_HIDDEN

    def test_state_initial_code(self):
        executor = HermesYiJingExecutor()
        assert executor.state.hexagram_code == "111111"

    def test_llm_call_default_none(self):
        executor = HermesYiJingExecutor()
        assert executor._llm_call is None

    def test_llm_call_custom(self):
        async def fake_llm(prompt: str) -> str:
            return '{"output": "test", "status": "completed"}'
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        assert executor._llm_call is fake_llm

    def test_default_execution_timeout(self):
        executor = HermesYiJingExecutor()
        assert executor._execution_timeout == 30.0


# ════════════════════════════════════════════════════════════════
#  Execute — Full Lifecycle (Happy Path)
# ════════════════════════════════════════════════════════════════

class TestExecuteFullLifecycle:
    """Complete execute() flow — all stubs succeed."""

    @pytest.mark.asyncio
    async def test_execute_returns_dict(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("Build a test")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_status_success(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("Build a test")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_advances_to_sixth_yao(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET

    @pytest.mark.asyncio
    async def test_execute_hexagram_unchanged(self):
        """With no exceptions, hexagram_code stays as initial."""
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.hexagram_code == "111111"

    @pytest.mark.asyncio
    async def test_execute_no_hexagram_history(self):
        """With no moving yaos, history stays empty."""
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.hexagram_history == []

    @pytest.mark.asyncio
    async def test_execute_ltm_has_entry(self):
        """Memory compression runs and writes to LTM."""
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert len(executor.state.long_term_memory) == 1
        entry = executor.state.long_term_memory[0]
        assert "Build a test" in entry.task_type
        assert "completed" in entry.execution_summary

    @pytest.mark.asyncio
    async def test_execute_hexagram_path_in_result(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("Build a test")
        assert "hexagram_path" in result
        assert "䷀" in result["hexagram_path"]

    @pytest.mark.asyncio
    async def test_execute_session_id_in_result(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("Build a test")
        assert result["session_id"] == executor.state.session_id

    @pytest.mark.asyncio
    async def test_execute_stores_task_graph(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.task_graph is not None
        assert executor.state.task_graph.original_intent == "Build a test"

    @pytest.mark.asyncio
    async def test_execute_stores_feasibility_report(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.feasibility_report is not None

    @pytest.mark.asyncio
    async def test_execute_stores_safety_report(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert executor.state.safety_report is not None
        assert executor.state.safety_report.passed is True

    @pytest.mark.asyncio
    async def test_execution_log_has_entries(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Build a test")
        assert len(executor.state.execution_log) > 0


# ════════════════════════════════════════════════════════════════
#  Execute — First Yao Failure (Empty Input)
# ════════════════════════════════════════════════════════════════

class TestFirstYaoFailure:
    """When _parse_intent returns empty original_intent → status = failed."""

    @pytest.mark.asyncio
    async def test_empty_input_returns_failed_status(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("")
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_empty_input_has_reason(self):
        executor = HermesYiJingExecutor()
        result = await executor.execute("")
        assert "無法解析用戶意圖" in result["reason"]

    @pytest.mark.asyncio
    async def test_empty_input_stays_at_first_yao(self):
        """When parsing fails, the state machine does not advance."""
        executor = HermesYiJingExecutor()
        await executor.execute("")
        assert executor.state.current_yao == YaoPosition.FIRST_HIDDEN

    @pytest.mark.asyncio
    async def test_empty_input_no_ltm_entry(self):
        executor = HermesYiJingExecutor()
        await executor.execute("")
        assert executor.state.long_term_memory == []


# ════════════════════════════════════════════════════════════════
#  Execute — Third Yao Safety Failure
# ════════════════════════════════════════════════════════════════

class TestThirdYaoSafetyFailure:
    """When third yao safety fails + requires_human → status = requires_human."""

    @pytest.fixture
    def executor_with_failing_safety(self):
        """An executor whose _reflexion_gate returns a failing SafetyReport."""
        executor = HermesYiJingExecutor()

        async def failing_safety(task, report):
            return SafetyReport(passed=False, requires_human=True)

        executor._reflexion_gate = failing_safety
        return executor

    @pytest.mark.asyncio
    async def test_safety_failure_returns_requires_human(self, executor_with_failing_safety):
        result = await executor_with_failing_safety.execute("Do something risky")
        assert result["status"] == "requires_human"

    @pytest.mark.asyncio
    async def test_safety_failure_has_reason(self, executor_with_failing_safety):
        result = await executor_with_failing_safety.execute("Do something risky")
        assert "三爻安全審查失敗" in result["reason"]

    @pytest.mark.asyncio
    async def test_safety_failure_has_transition(self, executor_with_failing_safety):
        result = await executor_with_failing_safety.execute("Do something risky")
        assert "hexagram_transition" in result
        assert result["hexagram_transition"]["from"] == "111111"

    @pytest.mark.asyncio
    async def test_safety_failure_triggers_moving_yao(self, executor_with_failing_safety):
        await executor_with_failing_safety.execute("Do something risky")
        assert len(executor_with_failing_safety.state.hexagram_history) == 1
        transition = executor_with_failing_safety.state.hexagram_history[0]
        assert 3 in transition.moving_yaos  # third yao moving

    @pytest.mark.asyncio
    async def test_safety_failure_hexagram_changed(self, executor_with_failing_safety):
        await executor_with_failing_safety.execute("Do something risky")
        assert executor_with_failing_safety.state.hexagram_code != "111111"


# ════════════════════════════════════════════════════════════════
#  Execute — Fifth Yao Exception (Fallback)
# ════════════════════════════════════════════════════════════════

class TestFifthYaoException:
    """When fifth yao raises an exception → moving yao + fallback execution."""

    @pytest.fixture
    def executor_with_failing_master(self):
        executor = HermesYiJingExecutor()

        async def failing_master(report):
            raise RuntimeError("API call failed!")

        executor._execute_master = failing_master
        return executor

    @pytest.mark.asyncio
    async def test_exception_caught_status_success(self, executor_with_failing_master):
        """Exception triggers fallback, which succeeds."""
        result = await executor_with_failing_master.execute("Build something")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_exception_triggers_moving_yao(self, executor_with_failing_master):
        await executor_with_failing_master.execute("Build something")
        assert len(executor_with_failing_master.state.hexagram_history) == 1
        transition = executor_with_failing_master.state.hexagram_history[0]
        assert 5 in transition.moving_yaos  # fifth yao moving

    @pytest.mark.asyncio
    async def test_exception_hexagram_changed(self, executor_with_failing_master):
        await executor_with_failing_master.execute("Build something")
        # 111111 → flip bit 5 → 111101
        assert executor_with_failing_master.state.hexagram_code == "111101"

    @pytest.mark.asyncio
    async def test_exception_fallback_result_contains_fallback_flag(self, executor_with_failing_master):
        result = await executor_with_failing_master.execute("Build something")
        assert result["result"].get("fallback") is True

    @pytest.mark.asyncio
    async def test_exception_fallback_result_has_strategy(self, executor_with_failing_master):
        result = await executor_with_failing_master.execute("Build something")
        assert "strategy" in result["result"]

    @pytest.mark.asyncio
    async def test_exception_still_completes_full_lifecycle(self, executor_with_failing_master):
        await executor_with_failing_master.execute("Build something")
        assert executor_with_failing_master.state.current_yao == YaoPosition.SIXTH_REGRET

    @pytest.mark.asyncio
    async def test_exception_still_writes_ltm(self, executor_with_failing_master):
        await executor_with_failing_master.execute("Build something")
        assert len(executor_with_failing_master.state.long_term_memory) == 1


# ════════════════════════════════════════════════════════════════
#  Hexagram History
# ════════════════════════════════════════════════════════════════

class TestHexagramHistory:
    """Hexagram history recording."""

    @pytest.mark.asyncio
    async def test_history_empty_when_no_failure(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Normal flow")
        assert executor.state.hexagram_history == []

    @pytest.mark.asyncio
    async def test_history_has_entry_on_safety_failure(self):
        executor = HermesYiJingExecutor()

        async def failing_safety(task, report):
            return SafetyReport(passed=False, requires_human=True)

        executor._reflexion_gate = failing_safety
        await executor.execute("Risky")
        assert len(executor.state.hexagram_history) == 1

    @pytest.mark.asyncio
    async def test_history_entry_structure(self):
        executor = HermesYiJingExecutor()

        async def failing_safety(task, report):
            return SafetyReport(passed=False, requires_human=True)

        executor._reflexion_gate = failing_safety
        await executor.execute("Risky")
        transition = executor.state.hexagram_history[0]
        assert transition.original_code == "111111"
        assert transition.new_code == "110111"  # flip bit 3
        assert transition.moving_yaos == [3]
        assert transition.transition_name != ""

    @pytest.mark.asyncio
    async def test_result_contains_hexagram_history(self):
        executor = HermesYiJingExecutor()

        async def failing_master(report):
            raise ValueError("fail")

        executor._execute_master = failing_master
        result = await executor.execute("Test")
        assert "hexagram_history" in result
        assert len(result["hexagram_history"]) == 1
        assert result["hexagram_history"][0]["original"] == "111111"
        assert result["hexagram_history"][0]["new"] == "111101"


# ════════════════════════════════════════════════════════════════
#  Memory Compression
# ════════════════════════════════════════════════════════════════

class TestMemoryCompression:
    """Memory compression writes to LTM."""

    @pytest.mark.asyncio
    async def test_ltm_has_memory_entry(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Some task")
        assert len(executor.state.long_term_memory) == 1

    @pytest.mark.asyncio
    async def test_ltm_entry_has_hexagram_path(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Some task")
        entry = executor.state.long_term_memory[0]
        assert entry.hexagram_path != ""
        assert "䷀" in entry.hexagram_path

    @pytest.mark.asyncio
    async def test_ltm_entry_has_task_type(self):
        executor = HermesYiJingExecutor()
        await executor.execute("My important task")
        entry = executor.state.long_term_memory[0]
        assert "My important task" in entry.task_type

    @pytest.mark.asyncio
    async def test_ltm_entry_has_execution_summary(self):
        executor = HermesYiJingExecutor()
        await executor.execute("Some task")
        entry = executor.state.long_term_memory[0]
        assert "Status:" in entry.execution_summary

    @pytest.mark.asyncio
    async def test_ltm_on_failure_no_entry(self):
        executor = HermesYiJingExecutor()
        await executor.execute("")
        assert executor.state.long_term_memory == []


# ════════════════════════════════════════════════════════════════
#  HermesYiJingExecutor — LLM-powered Methods
# ════════════════════════════════════════════════════════════════

class TestHermesYiJingExecutor:
    """HermesYiJingExecutor-specific tests for LLM-powered methods."""

    @pytest.mark.asyncio
    async def test_parse_intent_with_llm(self):
        """With LLM callable, _parse_intent should parse JSON response."""
        async def fake_llm(prompt: str) -> str:
            return (
                '{"constraints": ["no deletion"], '
                '"success_criteria": ["output generated"], '
                '"forbidden_actions": ["delete"], '
                '"estimated_complexity": "easy"}'
            )
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        task_graph = await executor._parse_intent("Generate a report")
        assert task_graph.original_intent == "Generate a report"
        assert task_graph.constraints == ["no deletion"]
        assert task_graph.success_criteria == ["output generated"]
        assert task_graph.forbidden_actions == ["delete"]
        assert task_graph.estimated_complexity == "easy"

    @pytest.mark.asyncio
    async def test_sandbox_prototype_with_llm(self):
        """With LLM callable, _sandbox_prototype should use LLM response."""
        async def fake_llm(prompt: str) -> str:
            return (
                '{"key_apis": ["filesystem", "network"], '
                '"estimated_tokens": 1200, '
                '"known_risks": ["network may be slow"], '
                '"fallback_plans": ["use local cache"]}'
            )
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        task = TaskGraph(original_intent="fetch data")
        report = await executor._sandbox_prototype(task)
        assert report.key_apis == ["filesystem", "network"]
        assert report.estimated_tokens == 1200
        assert "network may be slow" in report.known_risks

    @pytest.mark.asyncio
    async def test_reflexion_gate_with_llm(self):
        """With LLM callable, _reflexion_gate should incorporate LLM safety."""
        async def fake_llm(prompt: str) -> str:
            return (
                '{"passed": false, '
                '"issues": ["task modifies system files"], '
                '"recommendations": ["require human approval"], '
                '"requires_human": true}'
            )
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        task_graph = TaskGraph(original_intent="modify config")
        report = FeasibilityReport(plan_a_description="Modify config file")
        safety = await executor._reflexion_gate(task_graph, report)
        assert safety.passed is False
        assert "task modifies system files" in safety.issues
        assert safety.requires_human is True

    @pytest.mark.asyncio
    async def test_execute_master_with_llm(self):
        """With LLM callable, _execute_master returns parsed JSON result."""
        async def fake_llm(prompt: str) -> str:
            return '{"output": "task done", "status": "completed"}'
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        report = FeasibilityReport(plan_a_description="Do the thing")
        result = await executor._execute_master(report)
        assert isinstance(result, dict)
        assert result["output"] == "task done"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_memory_compression_with_llm(self):
        """With LLM callable, _memory_compression should enrich MemoryEntry."""
        async def fake_llm(prompt: str) -> str:
            return (
                '{"key_patterns": ["file ops"], '
                '"failure_modes": ["timeout"], '
                '"recommendations": ["add retry"]}'
            )
        executor = HermesYiJingExecutor(llm_call=fake_llm)
        executor.state.task_graph = TaskGraph(original_intent="Process files")
        result = {"output": "done", "status": "completed"}
        await executor._memory_compression(result)
        assert len(executor.state.long_term_memory) == 1
        entry = executor.state.long_term_memory[0]
        assert "file ops" in entry.key_patterns
        assert "timeout" in entry.failure_modes
        assert "add retry" in entry.recommendations

    @pytest.mark.asyncio
    async def test_request_authorization_returns_true(self):
        executor = HermesYiJingExecutor()
        result = await executor._request_authorization()
        assert result is True

    @pytest.mark.asyncio
    async def test_llm_call_graceful_failure(self):
        """When LLM raises during execute(), executor should fall back gracefully."""
        async def broken_llm(prompt: str) -> str:
            raise RuntimeError("LLM unavailable")
        executor = HermesYiJingExecutor(llm_call=broken_llm)
        result = await executor.execute("Test graceful fallback")
        # The LLM call in _parse_intent fails but is logged — task_graph returned
        # Then _execute_master also hits the broken LLM and raises → fallback runs
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_master_retry_on_timeout(self):
        """_execute_master retries on asyncio.TimeoutError."""
        call_count = {"n": 0}

        async def flaky_llm(prompt: str) -> str:
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise asyncio.TimeoutError("simulated")
            return '{"output": "done", "status": "completed"}'

        executor = HermesYiJingExecutor(llm_call=flaky_llm)
        executor.max_retries = 3
        executor._execution_timeout = 30.0  # doesn't matter — flaky raises instantly

        # Monkey-patch sleep to avoid 2^attempt second delays in test
        _original_sleep = asyncio.sleep

        async def _fast_sleep(duration: float):
            await _original_sleep(0)  # yield control but don't block
        asyncio.sleep = _fast_sleep

        try:
            report = FeasibilityReport(plan_a_description="test retry")
            result = await executor._execute_master(report)
            assert result["output"] == "done"
            assert call_count["n"] == 3  # 2 failures + 1 success
        finally:
            asyncio.sleep = _original_sleep

    @pytest.mark.asyncio
    async def test_execute_master_all_retries_fail_then_fallback(self):
        """When all retries fail, execute() catches the exception and falls back."""
        async def always_fail(prompt: str) -> str:
            raise asyncio.TimeoutError("always timeout")

        executor = HermesYiJingExecutor(llm_call=always_fail)
        executor.max_retries = 2
        executor._execution_timeout = 30.0  # instant raise
        _original_sleep = asyncio.sleep

        async def _fast_sleep(duration: float):
            await asyncio.sleep(0)
        asyncio.sleep = _fast_sleep

        try:
            result = await executor.execute("Retry then fallback")
            assert result["status"] == "success"
            assert result["result"].get("fallback") is True
        finally:
            asyncio.sleep = _original_sleep
