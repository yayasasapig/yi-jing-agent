"""䷀ Integration Tests — HermesYiJingExecutor End-to-End Lifecycle

Tests the full lifecycle flow with HermesYiJingExecutor + fake LLM callback.
These are heavier than unit tests — they exercise the complete 6-stage pipeline.
"""
import pytest
from yi_jing_agent.executor import HermesYiJingExecutor
from yi_jing_agent.agent_state import (
    YiJingAgentState, YaoPosition, LifecycleMode,
    TaskGraph, FeasibilityReport, SafetyReport,
)


class TestFullLifecycleWithFakeLLM:
    """Full 6-stage lifecycle with a fake LLM callback."""

    @pytest.fixture
    def fake_llm_response(self):
        """Return a fake LLM that always succeeds."""
        async def fake_llm(prompt: str) -> str:
            if "Parse" in prompt:
                return (
                    '{"constraints": ["read-only"], '
                    '"success_criteria": ["output generated"], '
                    '"forbidden_actions": ["delete"], '
                    '"estimated_complexity": "easy"}'
                )
            if "Analyze" in prompt or "feasibility" in prompt.lower():
                return (
                    '{"key_apis": ["filesystem"], '
                    '"estimated_tokens": 500, '
                    '"known_risks": [], '
                    '"fallback_plans": ["use cache"]}'
                )
            if "safety" in prompt.lower() or "review" in prompt.lower():
                return (
                    '{"passed": true, '
                    '"issues": [], '
                    '"recommendations": [], '
                    '"requires_human": false}'
                )
            if "memory" in prompt.lower() or "compress" in prompt.lower():
                return (
                    '{"key_patterns": ["test pattern"], '
                    '"failure_modes": [], '
                    '"recommendations": ["add more tests"]}'
                )
            return '{"output": "task complete", "status": "completed"}'

        return fake_llm

    @pytest.mark.asyncio
    async def test_full_lifecycle_success(self, fake_llm_response):
        """Full lifecycle completes all 6 stages successfully."""
        executor = HermesYiJingExecutor(llm_call=fake_llm_response)
        result = await executor.execute("Build a data pipeline")

        assert result["status"] == "success"
        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET
        assert executor.state.hexagram_code == "111111"  # No moving yao
        assert len(executor.state.long_term_memory) == 1

    @pytest.mark.asyncio
    async def test_full_lifecycle_hexagram_path(self, fake_llm_response):
        """Hexagram path is in the result."""
        executor = HermesYiJingExecutor(llm_call=fake_llm_response)
        result = await executor.execute("Analyze data")

        assert "hexagram_path" in result
        assert "䷀" in result["hexagram_path"]

    @pytest.mark.asyncio
    async def test_full_lifecycle_execution_log(self, fake_llm_response):
        """Execution log has entries for all stages."""
        executor = HermesYiJingExecutor(llm_call=fake_llm_response)
        await executor.execute("Process files")

        assert len(executor.state.execution_log) >= 6  # At least 6 stage entries

    @pytest.mark.asyncio
    async def test_full_lifecycle_session_id(self, fake_llm_response):
        """Session ID is consistent."""
        executor = HermesYiJingExecutor(llm_call=fake_llm_response)
        result = await executor.execute("Run analysis")
        assert result["session_id"] == executor.state.session_id

    @pytest.mark.asyncio
    async def test_full_lifecycle_stores_reports(self, fake_llm_response):
        """All stage reports are stored in state."""
        executor = HermesYiJingExecutor(llm_call=fake_llm_response)
        await executor.execute("Complex task")
        assert executor.state.task_graph is not None
        assert executor.state.feasibility_report is not None
        assert executor.state.safety_report is not None


class TestLifecycleModes:
    """Integration tests for EXPRESS / STANDARD / FULL modes."""

    @pytest.mark.asyncio
    async def test_express_mode_skips_middle_stages(self):
        """EXPRESS: skips 二爻, 三爻, 四爻, goes directly to 五爻."""
        executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.EXPRESS)
        await executor.execute("Quick task")

        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET
        # In express mode, feasibility report should not be set
        # (二爻 is skipped, no sandbox_prototype call)
        assert len(executor.state.execution_log) > 0

    @pytest.mark.asyncio
    async def test_express_mode_still_writes_ltm(self):
        """EXPRESS: still writes memory at 上爻."""
        executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.EXPRESS)
        await executor.execute("Quick task")
        assert len(executor.state.long_term_memory) == 1

    @pytest.mark.asyncio
    async def test_result_contains_lifecycle_info(self):
        """Result includes lifecycle mode and skipped yao info."""
        executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.STANDARD)
        result = await executor.execute("Normal task")
        assert "lifecycle_mode" in result
        assert "skipped_yaos" in result

    @pytest.mark.asyncio
    async def test_standard_skips_fourth_yao_only(self):
        """STANDARD: skips only 四爻 (authorization), runs 二爻 + 三爻."""
        executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.STANDARD)
        await executor.execute("Standard task")
        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET

    @pytest.mark.asyncio
    async def test_full_mode_no_skips(self):
        """FULL: all 6 stages execute."""
        executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.FULL)
        await executor.execute("Full task")
        assert executor.state.current_yao == YaoPosition.SIXTH_REGRET


class TestErrorHandlingIntegration:
    """Error handling in full lifecycle."""

    @pytest.mark.asyncio
    async def test_fifth_yao_error_triggers_fallback(self):
        """Error at 五爻 triggers moving yao + fallback."""
        executor = HermesYiJingExecutor()

        async def failing_master(report):
            raise RuntimeError("API timeout")

        executor._execute_master = failing_master
        result = await executor.execute("Do something")

        assert result["status"] == "success"  # Fallback succeeds
        assert "hexagram_history" in result
        assert len(result["hexagram_history"]) == 1

    @pytest.mark.asyncio
    async def test_safety_failure_human_intervention(self):
        """Safety failure at 三爻 returns requires_human."""
        executor = HermesYiJingExecutor()

        async def failing_safety(task, report):
            return SafetyReport(passed=False, requires_human=True,
                                issues=["dangerous operation"])

        executor._reflexion_gate = failing_safety
        result = await executor.execute("Risky operation")

        assert result["status"] == "requires_human"
        assert "hexagram_transition" in result
