"""䷀ LangGraph Integration — Yi-Jing Agent as LangGraph Nodes

Provides two integration levels:

Level 1 — YiJingNode (Single Node)
    One LangGraph node = full 6-stage Yi-Jing lifecycle.
    Simplest integration: just add one node to your graph.

Level 2 — create_yi_jing_graph() (Multi-Node Graph)
    Pre-built StateGraph with 6 individual lifecycle stages
    + hexagram-based conditional routing.

Usage:
    # Level 1: Single node
    from yi_jing_agent.integrations.langgraph import YiJingNode
    graph.add_node("yi_jing", YiJingNode(executor=...))

    # Level 2: Full graph
    from yi_jing_agent.integrations.langgraph import create_yi_jing_graph
    app = create_yi_jing_graph(llm_call=my_llm)
    result = app.invoke({"user_input": "Analyze this"})
"""
from typing import Any, Dict, List, Optional, TypedDict, Callable, Awaitable, Union, Literal

from yi_jing_agent.agent_state import LifecycleMode, YaoPosition
from yi_jing_agent.executor import HermesYiJingExecutor, YiJingAgentExecutor, LLMCallable
from yi_jing_agent.hexagram_table import get_hexagram_name, get_strategy_for_hexagram


# ════════════════════════════════════════════════════════════════
#  State Schema
# ════════════════════════════════════════════════════════════════


class YiJingState(TypedDict):
    """State schema for LangGraph Yi-Jing integration.

    Flows through the lifecycle graph carrying task context
    and execution results.
    """
    user_input: str
    """Original user input (required)."""

    lifecycle_mode: str
    """One of 'FULL', 'STANDARD', 'EXPRESS'."""

    hexagram_code: str
    """Current 6-bit hexagram state code (e.g. '111111')."""

    hexagram_path: str
    """Human-readable hexagram transition path."""

    task_graph: Optional[Dict[str, Any]]
    """Structured task decomposition (初爻 output)."""

    feasibility_report: Optional[Dict[str, Any]]
    """Feasibility analysis (二爻 output)."""

    safety_report: Optional[Dict[str, Any]]
    """Safety review result (三爻 output)."""

    output: Optional[Dict[str, Any]]
    """Core execution payload (五爻 output)."""

    error: Optional[str]
    """Error message if any stage failed."""

    skipped_yaos: List[str]
    """List of skipped yao position names."""

    hexagram_history: List[Dict[str, Any]]
    """History of hexagram transitions (moving yao events)."""


# ════════════════════════════════════════════════════════════════
#  Default State Factory
# ════════════════════════════════════════════════════════════════


def default_state(user_input: str, mode: str = "FULL") -> YiJingState:
    """Create a default YiJingState with initial values.

    Args:
        user_input: The user's task request.
        mode: Lifecycle mode ('FULL', 'STANDARD', or 'EXPRESS').

    Returns:
        YiJingState with defaults.
    """
    return {
        "user_input": user_input,
        "lifecycle_mode": mode,
        "hexagram_code": "111111",
        "hexagram_path": "",
        "task_graph": None,
        "feasibility_report": None,
        "safety_report": None,
        "output": None,
        "error": None,
        "skipped_yaos": [],
        "hexagram_history": [],
    }


# ════════════════════════════════════════════════════════════════
#  Hexagram Router — Conditional Edge Logic
# ════════════════════════════════════════════════════════════════


def hexagram_router(state: YiJingState) -> str:
    """Route to the next node based on the current hexagram strategy.

    Maps hexagram strategies to LangGraph edge destinations:
    - Happy Path / Coordination → 'execute' (五爻)
    - Reflection / Correction → 'reflect' (三爻回溯)
    - Failure / Human Takeover → 'human_intervention'
    - Fallback → 'fallback'

    Args:
        state: Current YiJingState with hexagram_code.

    Returns:
        str: Name of the next node to route to.
    """
    code = state.get("hexagram_code", "111111")
    strategy = get_strategy_for_hexagram(code)

    # Degradation / fallback (check BEFORE coordination since strategies like
    # "資源耗盡，等待降級" contain "等待" which also appears in coordination)
    fallback_keywords = ["降級", "回溯", "重構", "暫停", "延遲", "初期卡住", "初生艱難",
                         "耗盡"]
    if any(kw in strategy for kw in fallback_keywords):
        return "fallback"

    # Happy Path strategies
    happy_keywords = ["Happy Path", "推進", "交泰", "加速", "豐盛", "成功", "超額", "順利"]
    if any(kw in strategy for kw in happy_keywords):
        return "execute"

    # Coordination strategies — still proceed to execution
    coord_keywords = ["協同", "協作", "分配", "整合", "合併", "跟隨", "等待外部",
                      "累積", "充足", "滿意"]
    if any(kw in strategy for kw in coord_keywords):
        return "execute"

    # Reflection / correction needed
    reflect_keywords = ["反思", "審查", "修正", "觀察", "調整", "優化", "重新理解",
                        "補充", "維護", "暫停"]
    if any(kw in strategy for kw in reflect_keywords):
        return "reflect"

    # Degradation / fallback
    fallback_keywords = ["降級", "回溯", "重構", "暫停", "延遲", "等待", "初期卡住", "初生艱難"]
    if any(kw in strategy for kw in fallback_keywords):
        return "fallback"

    # Resource issues
    resource_keywords = ["資源", "Token", "Budget", "成本", "限制", "Rate Limit", "耗盡"]
    if any(kw in strategy for kw in resource_keywords):
        return "fallback"

    # Failure / human takeover
    failure_keywords = ["崩潰", "接管", "失敗", "意外", "剝落", "緊急", "人類接管"]
    if any(kw in strategy for kw in failure_keywords):
        return "human_intervention"

    # Default: continue
    return "execute"


# ════════════════════════════════════════════════════════════════
#  Level 1: YiJingNode — Single Node Wrapper
# ════════════════════════════════════════════════════════════════


class YiJingNode:
    """LangGraph node that runs the full Yi-Jing 6-stage lifecycle.

    Wraps a HermesYiJingExecutor and runs the complete lifecycle
    (初爻→上爻) as a single LangGraph node. Best for users who want
    the full lifecycle without managing individual stages.

    Example:
        >>> from langgraph.graph import StateGraph
        >>> from yi_jing_agent.integrations.langgraph import YiJingNode, YiJingState
        >>>
        >>> graph = StateGraph(YiJingState)
        >>> graph.add_node("yi_jing", YiJingNode())
        >>> graph.set_entry_point("yi_jing")
        >>> graph.set_finish_point("yi_jing")
        >>> app = graph.compile()
        >>> result = app.invoke({"user_input": "Analyze data", "lifecycle_mode": "FULL"})
    """

    def __init__(
        self,
        llm_call: Optional[LLMCallable] = None,
        lifecycle_mode: Union[LifecycleMode, str] = LifecycleMode.FULL,
        executor: Optional[HermesYiJingExecutor] = None,
    ):
        """Initialize YiJingNode.

        Args:
            llm_call: Optional async LLM callable for LLM-powered stages.
            lifecycle_mode: Default lifecycle mode (FULL, STANDARD, or EXPRESS).
            executor: Pre-configured HermesYiJingExecutor (optional).
                      If not provided, one is created from llm_call + lifecycle_mode.
        """
        self._llm_call = llm_call
        if isinstance(lifecycle_mode, str):
            lifecycle_mode = getattr(LifecycleMode, lifecycle_mode.upper(), LifecycleMode.FULL)
        self._lifecycle_mode = lifecycle_mode
        self._executor = executor

    def _get_executor(self) -> HermesYiJingExecutor:
        """Get or create the executor for this node."""
        if self._executor is not None:
            return self._executor
        return HermesYiJingExecutor(
            llm_call=self._llm_call,
            lifecycle_mode=self._lifecycle_mode,
        )

    async def __call__(self, state: YiJingState) -> YiJingState:
        """Run one full Yi-Jing lifecycle iteration.

        Args:
            state: Current YiJingState (must contain 'user_input').

        Returns:
            Updated YiJingState with lifecycle results.
        """
        user_input = state.get("user_input", "")
        if not user_input:
            return {**state, "error": "No user_input provided"}

        # Determine mode from state or default
        mode_str = state.get("lifecycle_mode", self._lifecycle_mode.name)
        if isinstance(mode_str, str):
            mode = getattr(LifecycleMode, mode_str.upper(), self._lifecycle_mode)
        else:
            mode = self._lifecycle_mode

        executor = self._get_executor()

        try:
            result = await executor.execute(user_input)
            return {
                **state,
                "hexagram_code": executor.state.hexagram_code,
                "hexagram_path": executor.state.get_hexagram_path(),
                "hexagram_history": result.get("hexagram_history", []),
                "task_graph": (
                    {
                        "original_intent": executor.state.task_graph.original_intent,
                        "constraints": executor.state.task_graph.constraints,
                        "success_criteria": executor.state.task_graph.success_criteria,
                        "estimated_complexity": executor.state.task_graph.estimated_complexity,
                    }
                    if executor.state.task_graph
                    else None
                ),
                "feasibility_report": (
                    {
                        "plan_a_description": executor.state.feasibility_report.plan_a_description,
                        "estimated_tokens": executor.state.feasibility_report.estimated_tokens,
                        "known_risks": executor.state.feasibility_report.known_risks,
                    }
                    if executor.state.feasibility_report
                    else None
                ),
                "safety_report": (
                    {
                        "passed": executor.state.safety_report.passed,
                        "issues": executor.state.safety_report.issues,
                    }
                    if executor.state.safety_report
                    else None
                ),
                "output": result.get("result"),
                "error": None,
                "lifecycle_mode": mode.name,
                "skipped_yaos": [y.chinese_name for y in executor.state.skipped_yaos],
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
            }


# ════════════════════════════════════════════════════════════════
#  Level 2: Individual Stage Nodes
# ════════════════════════════════════════════════════════════════


class IntentNode:
    """初爻 node: Parse user intent into structured TaskGraph."""

    def __init__(self, executor: YiJingAgentExecutor):
        self._executor = executor

    async def __call__(self, state: YiJingState) -> YiJingState:
        task_graph = await self._executor._parse_intent(state["user_input"])
        self._executor.state.task_graph = task_graph
        return {
            **state,
            "task_graph": {
                "original_intent": task_graph.original_intent,
                "constraints": task_graph.constraints,
                "success_criteria": task_graph.success_criteria,
                "estimated_complexity": task_graph.estimated_complexity,
            },
        }


class FeasibilityNode:
    """二爻 node: Run sandbox feasibility analysis."""

    def __init__(self, executor: YiJingAgentExecutor):
        self._executor = executor

    async def __call__(self, state: YiJingState) -> YiJingState:
        if not self._executor.state.task_graph:
            return {**state, "error": "No task graph from 初爻"}
        report = await self._executor._sandbox_prototype(
            self._executor.state.task_graph
        )
        self._executor.state.feasibility_report = report
        return {
            **state,
            "feasibility_report": {
                "plan_a_description": report.plan_a_description,
                "estimated_tokens": report.estimated_tokens,
                "known_risks": report.known_risks,
            },
        }


class SafetyNode:
    """三爻 node: Run safety review + 3D reflection."""

    def __init__(self, executor: YiJingAgentExecutor):
        self._executor = executor

    async def __call__(self, state: YiJingState) -> YiJingState:
        if not self._executor.state.task_graph or not self._executor.state.feasibility_report:
            return {**state, "error": "Missing task graph or feasibility report"}
        safety = await self._executor._reflexion_gate(
            self._executor.state.task_graph,
            self._executor.state.feasibility_report,
        )
        self._executor.state.safety_report = safety
        return {
            **state,
            "safety_report": {
                "passed": safety.passed,
                "issues": safety.issues,
                "requires_human": safety.requires_human,
            },
        }


class ExecutionNode:
    """五爻 node: Full power execution."""

    def __init__(self, executor: YiJingAgentExecutor):
        self._executor = executor

    async def __call__(self, state: YiJingState) -> YiJingState:
        if not self._executor.state.feasibility_report:
            return {**state, "error": "No feasibility report"}
        try:
            result = await self._executor._execute_master(
                self._executor.state.feasibility_report
            )
            return {**state, "output": result, "error": None}
        except Exception as e:
            # Trigger moving yao for fault tolerance
            transition = self._executor.state.trigger_moving_yao(5)
            fallback = await self._executor._fallback_execution(
                transition, self._executor.state.feasibility_report, str(e)
            )
            return {
                **state,
                "output": fallback,
                "hexagram_code": self._executor.state.hexagram_code,
                "error": None,
            }


class MemoryNode:
    """上爻 node: Compress and store execution memory."""

    def __init__(self, executor: YiJingAgentExecutor):
        self._executor = executor

    async def __call__(self, state: YiJingState) -> YiJingState:
        await self._executor._memory_compression(
            state.get("output") or {}
        )
        return {
            **state,
            "hexagram_code": self._executor.state.hexagram_code,
            "hexagram_path": self._executor.state.get_hexagram_path(),
            "hexagram_history": [
                {
                    "original": t.original_code,
                    "new": t.new_code,
                    "name": t.transition_name,
                    "strategy": t.strategy,
                }
                for t in self._executor.state.hexagram_history
            ],
        }


# ════════════════════════════════════════════════════════════════
#  Level 2: Graph Builder
# ════════════════════════════════════════════════════════════════


def create_yi_jing_graph(
    llm_call: Optional[LLMCallable] = None,
    lifecycle_mode: Union[LifecycleMode, str, None] = None,
    executor: Optional[HermesYiJingExecutor] = None,
    include_reflection: bool = True,
    include_authorization: bool = False,
) -> Any:
    """Create a LangGraph StateGraph with Yi-Jing lifecycle stages.

    Builds a graph with 4-6 nodes depending on configuration:
    - intent (初爻) → feasibility (二爻) → [safety (三爻)] → execute (五爻) → memory (上爻)
    - Conditional routing via hexagram_router after execution.

    Args:
        llm_call: Optional async LLM callable.
        lifecycle_mode: Lifecycle mode (FULL, STANDARD, EXPRESS).
        executor: Pre-configured HermesYiJingExecutor (optional).
        include_reflection: If True, include the 三爻 safety/reflection node.
        include_authorization: If True, include the 四爻 authorization node.

    Returns:
        Compiled LangGraph StateGraph ready for invocation.

    Example:
        >>> from yi_jing_agent.integrations.langgraph import create_yi_jing_graph
        >>> app = create_yi_jing_graph()
        >>> result = app.invoke({"user_input": "Analyze trends", "lifecycle_mode": "STANDARD"})
    """
    from langgraph.graph import StateGraph, START, END

    # Resolve lifecycle mode
    if isinstance(lifecycle_mode, str):
        lifecycle_mode = getattr(LifecycleMode, lifecycle_mode.upper(), LifecycleMode.FULL)
    elif lifecycle_mode is None:
        lifecycle_mode = LifecycleMode.FULL

    # Create shared executor
    if executor is None:
        executor = HermesYiJingExecutor(
            llm_call=llm_call,
            lifecycle_mode=lifecycle_mode,
        )

    # Create graph
    graph = StateGraph(YiJingState)

    # Add nodes
    graph.add_node("intent", IntentNode(executor))
    graph.add_node("feasibility", FeasibilityNode(executor))
    if include_reflection:
        graph.add_node("safety", SafetyNode(executor))
    graph.add_node("execute", ExecutionNode(executor))
    graph.add_node("memory", MemoryNode(executor))

    # Define edges
    graph.add_edge(START, "intent")
    graph.add_edge("intent", "feasibility")

    if include_reflection:
        graph.add_edge("feasibility", "safety")
        graph.add_conditional_edges(
            "safety",
            lambda s: (
                "human_intervention"
                if (s.get("safety_report") or {}).get("requires_human")
                else "execute"
            ),
            {"execute": "execute", "human_intervention": END},
        )
    else:
        graph.add_edge("feasibility", "execute")

    # Hexagram-based conditional routing from execute
    graph.add_conditional_edges(
        "execute",
        hexagram_router,
        {
            "execute": "memory",
            "reflect": "safety" if include_reflection else "execute",
            "fallback": "memory",
            "human_intervention": END,
        },
    )

    graph.add_edge("memory", END)

    return graph.compile()
