"""Tests for YiJingAgentExecutor — the async lifecycle executor."""
import pytest
from datetime import datetime

from yi_jing_agent.executor import YiJingAgentExecutor
from yi_jing_agent.agent_state import (
    YiJingAgentState, YaoPosition, SafetyReport, FeasibilityReport,
)


class TestInitialization:
    """Executor initialization."""

    def test_session_id_generated(self):
        executor = YiJingAgentExecutor()
        assert executor.state.session_id != ""
        assert executor.state.session_id.startswith("S-")

    def test_session_id_custom(self):
        executor = YiJingAgentExecutor(session_id="CUSTOM-001")
        assert executor.state.session_id == "CUSTOM-001"

    def test_state_is_yijing_agent_state(self):
        executor = YiJingAgentExecutor()
        assert isinstance(executor.state, YiJingAgentState)

    def test_default_max_retries(self):
        executor = YiJingAgentExecutor()
        assert executor.max_retries == 3

    def test_state_initial_yao(self):
        executor = YiJingAgentExecutor()
        assert executor.state.current_yao == YaoPosition.FIRST_HIDDEN

    def test_state_initial_code(self):
        executor = YiJingAgentExecutor()
        assert executor.state.hexagram_code == "111111"


class TestExecuteFullLifecycle:
    """Complete execute() flow — all stubs succeed."""

    @pytest.mark.asyncio
    async def test_execute_returns_dict(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("Build a test")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_status_success(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("Build a test")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_advances_to_sixth_yao(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET

    @pytest.mark.asyncio
    async def test_execute_hexagram_unchanged(self):
        """With no exceptions, hexagram_code stays as initial."""
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.hexagram_code == "111111"

    @pytest.mark.asyncio
    async def test_execute_no_hexagram_history(self):
        """With no moving yaos, history stays empty."""
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.hexagram_history == []

    @pytest.mark.asyncio
    async def test_execute_ltm_has_entry(self):
        """Memory compression runs and writes to LTM."""
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert len(executor.state.long_term_memory) == 1
        entry = executor.state.long_term_memory[0]
        assert "Build a test" in entry.task_type
        assert "completed" in entry.execution_summary

    @pytest.mark.asyncio
    async def test_execute_hexagram_path_in_result(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("Build a test")
        assert "hexagram_path" in result
        assert "䷀" in result["hexagram_path"]

    @pytest.mark.asyncio
    async def test_execute_session_id_in_result(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("Build a test")
        assert result["session_id"] == executor.state.session_id

    @pytest.mark.asyncio
    async def test_execute_stores_task_graph(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.task_graph is not None
        assert executor.state.task_graph.original_intent == "Build a test"

    @pytest.mark.asyncio
    async def test_execute_stores_feasibility_report(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.feasibility_report is not None

    @pytest.mark.asyncio
    async def test_execute_stores_safety_report(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert executor.state.safety_report is not None
        assert executor.state.safety_report.passed is True

    @pytest.mark.asyncio
    async def test_execution_log_has_entries(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Build a test")
        assert len(executor.state.execution_log) > 0


class TestFirstYaoFailure:
    """When _parse_intent returns empty original_intent → status = failed."""

    @pytest.mark.asyncio
    async def test_empty_input_returns_failed_status(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("")
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_empty_input_has_reason(self):
        executor = YiJingAgentExecutor()
        result = await executor.execute("")
        assert "無法解析用戶意圖" in result["reason"]

    @pytest.mark.asyncio
    async def test_empty_input_stays_at_first_yao(self):
        """When parsing fails, the state machine does not advance."""
        executor = YiJingAgentExecutor()
        await executor.execute("")
        assert executor.state.current_yao == YaoPosition.FIRST_HIDDEN

    @pytest.mark.asyncio
    async def test_empty_input_no_ltm_entry(self):
        executor = YiJingAgentExecutor()
        await executor.execute("")
        assert executor.state.long_term_memory == []


class TestThirdYaoSafetyFailure:
    """When third yao safety fails + requires_human → status = requires_human."""

    @pytest.fixture
    def executor_with_failing_safety(self):
        """An executor whose _reflexion_gate returns a failing SafetyReport."""
        executor = YiJingAgentExecutor()

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


class TestFifthYaoException:
    """When fifth yao raises an exception → moving yao + fallback execution."""

    @pytest.fixture
    def executor_with_failing_master(self):
        executor = YiJingAgentExecutor()

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


class TestHexagramHistory:
    """Hexagram history recording."""

    @pytest.mark.asyncio
    async def test_history_empty_when_no_failure(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Normal flow")
        assert executor.state.hexagram_history == []

    @pytest.mark.asyncio
    async def test_history_has_entry_on_safety_failure(self):
        executor = YiJingAgentExecutor()

        async def failing_safety(task, report):
            return SafetyReport(passed=False, requires_human=True)

        executor._reflexion_gate = failing_safety
        await executor.execute("Risky")
        assert len(executor.state.hexagram_history) == 1

    @pytest.mark.asyncio
    async def test_history_entry_structure(self):
        executor = YiJingAgentExecutor()

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
        executor = YiJingAgentExecutor()

        async def failing_master(report):
            raise ValueError("fail")

        executor._execute_master = failing_master
        result = await executor.execute("Test")
        assert "hexagram_history" in result
        assert len(result["hexagram_history"]) == 1
        assert result["hexagram_history"][0]["original"] == "111111"
        assert result["hexagram_history"][0]["new"] == "111101"


class TestMemoryCompression:
    """Memory compression writes to LTM."""

    @pytest.mark.asyncio
    async def test_ltm_has_memory_entry(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Some task")
        assert len(executor.state.long_term_memory) == 1

    @pytest.mark.asyncio
    async def test_ltm_entry_has_hexagram_path(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Some task")
        entry = executor.state.long_term_memory[0]
        assert entry.hexagram_path != ""
        assert "䷀" in entry.hexagram_path

    @pytest.mark.asyncio
    async def test_ltm_entry_has_task_type(self):
        executor = YiJingAgentExecutor()
        await executor.execute("My important task")
        entry = executor.state.long_term_memory[0]
        assert "My important task" in entry.task_type

    @pytest.mark.asyncio
    async def test_ltm_entry_has_execution_summary(self):
        executor = YiJingAgentExecutor()
        await executor.execute("Some task")
        entry = executor.state.long_term_memory[0]
        assert "Status:" in entry.execution_summary

    @pytest.mark.asyncio
    async def test_ltm_on_failure_no_entry(self):
        executor = YiJingAgentExecutor()
        await executor.execute("")
        assert executor.state.long_term_memory == []
