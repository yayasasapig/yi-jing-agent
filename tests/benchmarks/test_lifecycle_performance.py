"""䷀ Lifecycle Performance Benchmarks

Benchmarks measure core operation speed:
- State machine transitions
- Hexagram lookups
- Full lifecycle execution
- Moving yao mutations
- 3D reflection engine

Run with: python -m pytest tests/benchmarks/ --benchmark-only -v
"""
import asyncio
import pytest
from datetime import datetime

from yi_jing_agent.agent_state import (
    YiJingAgentState, YaoPosition, TaskGraph,
)
from yi_jing_agent.executor import HermesYiJingExecutor
from yi_jing_agent.hexagram_table import (
    get_hexagram_name, get_strategy_for_hexagram, HEXAGRAM_NAMES,
)
from yi_jing_agent.reflection import ThreeDimensionalReflection


class TestStateTransitionBenchmarks:
    """Speed of step_forward() operations."""

    def test_step_forward_10k(self, benchmark):
        """10,000 sequential step_forward() calls."""
        state = YiJingAgentState()

        def run():
            for _ in range(10000):
                state.step_forward()
                if state.current_yao == YaoPosition.SIXTH_REGRET:
                    state.current_yao = YaoPosition.FIRST_HIDDEN

        benchmark(run)

    def test_trigger_moving_yao_all_positions(self, benchmark):
        """Moving yao at all 6 positions, repeated."""
        state = YiJingAgentState()

        def run():
            for i in range(1, 7):
                state.trigger_moving_yao(i)

        benchmark(run)

    def test_hexagram_path_generation(self, benchmark):
        """get_hexagram_path() with full history."""
        state = YiJingAgentState()
        for i in range(1, 7):
            state.trigger_moving_yao(i)

        def run():
            for _ in range(1000):
                state.get_hexagram_path()

        benchmark(run)


class TestHexagramLookupBenchmarks:
    """Speed of hexagram table lookups."""

    def test_all_64_name_lookups(self, benchmark):
        """Look up all 64 hexagram names."""
        codes = list(HEXAGRAM_NAMES.keys())

        def run():
            for code in codes:
                get_hexagram_name(code)

        benchmark(run)

    def test_all_64_strategy_lookups(self, benchmark):
        """Look up all 64 strategies."""
        codes = list(HEXAGRAM_NAMES.keys())

        def run():
            for code in codes:
                get_strategy_for_hexagram(code)

        benchmark(run)

    def test_unknown_code_fallback(self, benchmark):
        """Fallback strategy for unknown codes."""
        unknown_codes = ["000001", "111110", "010101", "101010", "001100"]

        def run():
            for code in unknown_codes:
                get_hexagram_name(code)
                get_strategy_for_hexagram(code)

        benchmark(run)


class TestLifecycleBenchmarks:
    """Full lifecycle execution time."""

    def test_full_lifecycle_empty_input(self, benchmark):
        """Full lifecycle with empty input (fast-fail at 初爻)."""
        async def _run():
            executor = HermesYiJingExecutor()
            return await executor.execute("")

        benchmark(lambda: asyncio.run(_run()))

    def test_full_lifecycle_happy_path(self, benchmark):
        """Full lifecycle with normal input (all 6 stages)."""
        async def _run():
            executor = HermesYiJingExecutor()
            return await executor.execute("Build a test project")

        benchmark(lambda: asyncio.run(_run()))

    def test_full_lifecycle_with_llm(self, benchmark):
        """Full lifecycle with fake LLM callback."""
        async def fake_llm(prompt: str) -> str:
            return '{"output": "done", "status": "completed"}'

        async def _run():
            executor = HermesYiJingExecutor(llm_call=fake_llm)
            return await executor.execute("Run analysis")

        benchmark(lambda: asyncio.run(_run()))

    def test_express_mode_lifecycle(self, benchmark):
        """Express mode lifecycle (skip 3 stages)."""
        async def _run():
            from yi_jing_agent.agent_state import LifecycleMode
            executor = HermesYiJingExecutor(lifecycle_mode=LifecycleMode.EXPRESS)
            return await executor.execute("Quick task")

        benchmark(lambda: asyncio.run(_run()))


class TestReflectionBenchmarks:
    """3D reflection engine speed."""

    def test_full_reflection_all_codes(self, benchmark):
        """Run full 3D reflection across multiple hexagram codes."""
        codes = ["111111", "000000", "101010", "010101", "111000"]

        def run():
            for code in codes:
                engine = ThreeDimensionalReflection(hexagram_code=code)
                engine.run_full_reflection(
                    task_description="test task",
                    plan="test plan",
                    output_format="text",
                )

        benchmark(run)

    def test_interlocking_analysis(self, benchmark):
        """Interlocking (互卦) analysis speed."""
        engine = ThreeDimensionalReflection()

        def run():
            for _ in range(100):
                engine.analyze_interlocking("Analyze user request")

        benchmark(run)

    def test_opposite_analysis(self, benchmark):
        """Opposite (錯卦) analysis speed."""
        engine = ThreeDimensionalReflection()

        def run():
            for _ in range(100):
                engine.analyze_opposite("Original plan")

        benchmark(run)
