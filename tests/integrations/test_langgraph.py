"""䷀ LangGraph Integration Tests

Tests for the LangGraph adapter at both levels:
- Level 1: YiJingNode (single node)
- Level 2: create_yi_jing_graph() (multi-node graph)
"""
import pytest
from yi_jing_agent.agent_state import LifecycleMode
from yi_jing_agent.integrations.langgraph import (
    YiJingState, YiJingNode, default_state, hexagram_router,
    create_yi_jing_graph,
)


class TestYiJingState:
    """YiJingState schema and defaults."""

    def test_default_state_has_required_fields(self):
        state = default_state("test input")
        assert state["user_input"] == "test input"
        assert state["lifecycle_mode"] == "FULL"
        assert state["hexagram_code"] == "111111"
        assert state["hexagram_path"] == ""
        assert state["task_graph"] is None
        assert state["output"] is None
        assert state["skipped_yaos"] == []

    def test_default_state_custom_mode(self):
        state = default_state("input", mode="STANDARD")
        assert state["lifecycle_mode"] == "STANDARD"


class TestHexagramRouter:
    """Hexagram-based conditional routing logic."""

    def test_happy_path_routes_to_execute(self):
        state = default_state("test", mode="FULL")
        state["hexagram_code"] = "111111"  # ䷀ Happy Path
        assert hexagram_router(state) == "execute"

    def test_failure_routes_to_human_intervention(self):
        state = default_state("test")
        state["hexagram_code"] = "000000"  # ䷁ 全面崩潰
        assert hexagram_router(state) == "human_intervention"

    def test_reflection_needed_routes_to_reflect(self):
        state = default_state("test")
        state["hexagram_code"] = "111000"  # ䷋ 天地否（上下不交）
        assert hexagram_router(state) == "reflect"

    def test_fallback_routes_to_fallback(self):
        state = default_state("test")
        state["hexagram_code"] = "110010"  # ䷮ 澤水困（資源耗盡，等待降級）
        assert hexagram_router(state) == "fallback"

    def test_resource_issue_routes_to_fallback(self):
        state = default_state("test")
        state["hexagram_code"] = "010010"  # ䷜ 坎為水（重險陷阱，反覆失敗，人類接管）
        assert hexagram_router(state) == "human_intervention"

    def test_unknown_code_defaults_to_execute(self):
        state = default_state("test")
        state["hexagram_code"] = "101010"  # ䷿ 火水未濟（差最後一步）
        assert hexagram_router(state) == "execute"


class TestYiJingNode:
    """Level 1: Single-node integration."""

    @pytest.mark.asyncio
    async def test_node_requires_user_input(self):
        node = YiJingNode()
        result = await node({"user_input": ""})
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_node_happy_path(self):
        node = YiJingNode(lifecycle_mode=LifecycleMode.STANDARD)
        state = default_state("Build a test", mode="STANDARD")
        result = await node(state)
        assert result["error"] is None
        assert result["hexagram_code"] == "111111"
        assert "hexagram_path" in result

    @pytest.mark.asyncio
    async def test_node_output_has_task_graph(self):
        node = YiJingNode()
        result = await node(default_state("Analyze data"))
        assert "task_graph" in result
        if result["task_graph"]:
            assert "original_intent" in result["task_graph"]

    @pytest.mark.asyncio
    async def test_node_with_llm_callback(self):
        async def fake_llm(prompt: str) -> str:
            return '{"output": "done", "status": "completed"}'

        node = YiJingNode(llm_call=fake_llm, lifecycle_mode=LifecycleMode.FULL)
        result = await node(default_state("Process files"))
        assert result["error"] is None
        assert "output" in result

    @pytest.mark.asyncio
    async def test_node_with_string_mode(self):
        node = YiJingNode(lifecycle_mode="express")
        result = await node(default_state("Quick task", mode="EXPRESS"))
        assert result["error"] is None


class TestYiJingGraph:
    """Level 2: Multi-node graph integration."""

    def test_create_graph_returns_compiled_app(self):
        app = create_yi_jing_graph()
        assert app is not None
        # CompiledStateGraph has an invoke method
        assert hasattr(app, "invoke")
        assert hasattr(app, "ainvoke")

    @pytest.mark.asyncio
    async def test_graph_invoke_happy_path(self):
        app = create_yi_jing_graph()
        result = await app.ainvoke(default_state("Build a data pipeline"))
        assert result is not None
        assert "hexagram_code" in result
        assert result["hexagram_code"] == "111111"

    @pytest.mark.asyncio
    async def test_graph_with_reflection_included(self):
        app = create_yi_jing_graph(include_reflection=True)
        result = await app.ainvoke(default_state("Analyze trends"))
        assert result is not None
        assert result["hexagram_code"] == "111111"

    @pytest.mark.asyncio
    async def test_graph_with_standard_mode(self):
        """Graph invocation with STANDARD mode."""
        state = default_state("Test task", mode="STANDARD")
        app = create_yi_jing_graph()
        result = await app.ainvoke(state)
        assert result is not None
        assert "output" in result or "error" in result

    @pytest.mark.asyncio
    async def test_graph_express_mode(self):
        """Graph with EXPRESS mode via create parameter."""
        app = create_yi_jing_graph(lifecycle_mode=LifecycleMode.EXPRESS)
        state = default_state("Quick check", mode="EXPRESS")
        result = await app.ainvoke(state)
        assert result is not None
