"""䷀ Integration: 多 Agent 同步 × Executor 整合測試

展示 Option B 嘅完整 workflow：
1. 多個 Agent 各自執行任務
2. 透過 Registry 追蹤狀態
3. 透過 Protocol 互相同步
4. 透過 ConsensusEngine 達成團隊共識
"""

import pytest
from yi_jing_agent.sync import (
    AgentRegistry,
    SyncProtocol,
    ConsensusEngine,
    ConsensusStrategy,
    SyncAction,
)


class TestMultiAgentSyncWorkflow:
    """完整多 Agent 同步場景"""

    @pytest.fixture
    def system(self):
        """建立一個有 3 個 Agent 嘅同步系統"""
        registry = AgentRegistry(stale_timeout=300)
        protocol = SyncProtocol(registry)
        engine = ConsensusEngine(registry)

        # Register 3 agents
        registry.register("researcher", hexagram_int=0b111111, metadata={"role": "research"})
        registry.register("coder", hexagram_int=0b111111, metadata={"role": "coding"})
        registry.register("reviewer", hexagram_int=0b111111, metadata={"role": "review"})

        return registry, protocol, engine

    def test_multi_agent_push_and_consensus(self, system):
        """多 Agent 推送狀態後，majority vote 正確反映團隊共識"""
        registry, protocol, engine = system

        # Simulate scenarios:
        # - Researcher encounters an error (TOOL_EXECUTION_ERROR → flip bit 3)
        protocol.push("researcher", hexagram_int=0b110111, task_type="research")
        info = registry.get("researcher")
        assert info.hexagram_int == 0b110111
        assert "夬" in info.hexagram_name

        # - Coder is still healthy
        protocol.push("coder", hexagram_int=0b111111, task_type="coding")

        # - Reviewer detects goal drift (flip bit 1)
        protocol.push("reviewer", hexagram_int=0b111101, task_type="review")

        # Now compute consensus — majority is still ䷀?
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)
        # 110111, 111111, 111101 → all unique!
        assert result.participant_count == 3
        # With 3 unique states, majority vote picks the first most_common
        # Each has count=1, so any could win — but confidence should be low
        assert result.confidence == pytest.approx(1 / 3, abs=0.001)  # Only 1 agent has the winning state

        # Drift report should reflect divergence
        report = engine.drift_report()
        assert report["unique_hexagram_count"] == 3

    def test_protocol_inbox_delivery(self, system):
        """Agent 之間嘅 push 訊息互相送達 inbox"""
        registry, protocol, engine = system

        # Researcher pushes state — coder and reviewer should get it
        protocol.push("researcher", hexagram_int=0b100111)

        coder_msgs = protocol.poll_updates("coder")
        reviewer_msgs = protocol.poll_updates("reviewer")

        assert len(coder_msgs) >= 1
        assert len(reviewer_msgs) >= 1
        assert coder_msgs[0].source_agent == "researcher"
        assert reviewer_msgs[0].source_agent == "researcher"

    def test_system_health_tracking(self, system):
        """registry.get_system_health() 隨 Agent 狀態變化"""
        registry, protocol, engine = system

        # Initially all healthy
        health = registry.get_system_health()
        assert health["healthy_count"] == 3
        assert health["critical_count"] == 0

        # One agent goes critical
        protocol.push("coder", hexagram_int=0b000000)  # ䷁ — all bits off

        health = registry.get_system_health()
        assert health["critical_count"] == 1
        assert health["healthy_count"] == 2
        assert health["status"] == "degraded"

    def test_pull_another_agent(self, system):
        """Agent 可以 pull 另一個 Agent 嘅狀態"""
        registry, protocol, engine = system

        # Reviewer pulls researcher's state
        msg = protocol.pull("reviewer", "researcher")
        assert msg is not None
        assert msg.source_agent == "researcher"
        assert msg.target_agent == "reviewer"

    def test_broadcast_warning(self, system):
        """Agent broadcast 警示訊息俾全體"""
        registry, protocol, engine = system

        # Coder broadcasts a warning
        protocol.broadcast(
            "coder",
            hexagram_int=0b001000,  # ䷖ — critical剝落
            warning="Context window overflow imminent",
        )

        # Everyone should have it
        for agent_id in ["researcher", "coder", "reviewer"]:
            msgs = protocol.poll_updates(agent_id)
            assert len(msgs) >= 1
            if agent_id != "coder":
                assert msgs[0].source_agent == "coder"

    def test_alert_propagation(self, system):
        """alert 機制：critical Agent 觸發全局警報"""
        registry, protocol, engine = system

        # Researcher sends alert
        protocol.alert("researcher", severity="critical", message="LLM API timeout")

        # Reviewer gets alert
        msgs = protocol.poll_updates("reviewer")
        alerts = [m for m in msgs if m.action == SyncAction.ALERT]
        assert len(alerts) >= 1
        assert alerts[0].payload["alert_message"] == "LLM API timeout"

    def test_register_from_state_object(self):
        """模擬用 state object register Agent"""
        registry = AgentRegistry()
        # Simulate what an executor would do
        info = registry.register(
            "agent-alpha",
            hexagram_int=0b111111,
            lifecycle_mode="FULL",
            current_yao="初爻",
            task_type="research",
            metadata={"session_id": "sess-001"},
        )

        assert info.agent_id == "agent-alpha"
        assert info.lifecycle_mode == "FULL"

        # Update with new state
        updated = registry.update(
            "agent-alpha",
            hexagram_int=0b011111,  # ䷈ — minor fault
        )
        assert updated.hexagram_int == 0b011111

    def test_edge_case_empty_registry(self):
        """空 registry 嘅邊界情況"""
        registry = AgentRegistry()
        protocol = SyncProtocol(registry)
        engine = ConsensusEngine(registry)

        assert registry.count() == 0
        assert registry.get_system_health()["status"] == "idle"

        # Consensus on empty registry
        result = engine.compute_consensus()
        assert result.participant_count == 0
        assert result.confidence == 0.0

        # Protocol push with no other agents
        registry.register("solo", hexagram_int=0b111111)
        protocol.push("solo", hexagram_int=0b000000)
        # No crash, no delivery to others (none exist)
        msgs = protocol.poll_updates("solo")
        assert len(msgs) == 0  # push doesn't go to self

    def test_rapid_state_transitions(self, system):
        """快速狀態變更 — 確保 sync 跟得上"""
        registry, protocol, engine = system

        # Simulate rapid state changes
        transitions = [
            (0b111111, "happy"),
            (0b111110, "minor_warning"),
            (0b111100, "two_faults"),
            (0b111000, "three_faults"),
            (0b110000, "four_faults"),
            (0b100000, "five_faults"),
            (0b000000, "total_failure"),
        ]

        for hex_int, label in transitions:
            protocol.push("researcher", hexagram_int=hex_int, state_label=label)

        # Latest state should be the final one
        info = registry.get("researcher")
        assert info.hexagram_int == 0b000000
        assert info.drift_score == 1.0

    def test_consensus_strategies_match(self, system):
        """5 種 consensus strategy 都應傳回有效嘅 hexagram int"""
        registry, protocol, engine = system

        # Give agents different states
        registry.update("researcher", hexagram_int=0b111111)
        registry.update("coder", hexagram_int=0b000111)
        registry.update("reviewer", hexagram_int=0b000000)

        for strategy in ConsensusStrategy:
            result = engine.compute_consensus(strategy)
            assert 0 <= result.consensus_hexagram_int <= 63, f"{strategy} out of bounds"
            assert result.strategy_used == strategy
            assert result.participant_count == 3
