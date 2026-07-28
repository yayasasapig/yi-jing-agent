"""䷀ Tests: AgentRegistry — 多 Agent 註冊表"""

import pytest
from yi_jing_agent.sync import AgentRegistry


class TestAgentRegistry:
    """測試 AgentRegistry 核心功能"""

    def test_register_and_get(self):
        """註冊 Agent 然後查詢"""
        registry = AgentRegistry()
        info = registry.register("agent-a", hexagram_int=0b111111)
        assert info.agent_id == "agent-a"
        assert info.hexagram_int == 0b111111
        assert info.hexagram_str == "111111"
        assert "乾" in info.hexagram_name
        assert info.is_healthy is True

        # Get back
        got = registry.get("agent-a")
        assert got is not None
        assert got.agent_id == "agent-a"

    def test_register_unknown_agent_returns_none(self):
        """未註冊嘅 Agent 回傳 None"""
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_unregister(self):
        """取消註冊應移除 Agent"""
        registry = AgentRegistry()
        registry.register("agent-a")
        assert registry.count() == 1

        result = registry.unregister("agent-a")
        assert result is True
        assert registry.count() == 0
        assert registry.get("agent-a") is None

    def test_unregister_nonexistent(self):
        """取消註冊不存在的 Agent 回傳 False"""
        registry = AgentRegistry()
        assert registry.unregister("no-such-agent") is False

    def test_update_state(self):
        """更新 Agent 狀態應反映新 hexagram_int"""
        registry = AgentRegistry()
        registry.register("agent-a", hexagram_int=0b111111)

        updated = registry.update("agent-a", hexagram_int=0b000111)
        assert updated.hexagram_int == 0b000111
        assert "泰" in updated.hexagram_name

        got = registry.get("agent-a")
        assert got.hexagram_int == 0b000111

    def test_update_auto_register(self):
        """如果 Agent 未註冊，update 應該自動註冊"""
        registry = AgentRegistry()
        info = registry.update("new-agent", hexagram_int=0b101010)
        assert info is not None
        assert info.agent_id == "new-agent"
        assert registry.count() == 1

    def test_list_agents(self):
        """list_agents 返回所有非過期 Agent"""
        registry = AgentRegistry(stale_timeout=300)
        registry.register("a", hexagram_int=0b111111)
        registry.register("b", hexagram_int=0b000111)
        registry.register("c", hexagram_int=0b000000)

        agents = registry.list_agents()
        assert len(agents) == 3
        ids = [a.agent_id for a in agents]
        assert "a" in ids
        assert "b" in ids
        assert "c" in ids

    def test_healthy_threshold(self):
        """is_healthy: drift ≤ 2 (= healthy), drift ≥ 3 (= critical)"""
        registry = AgentRegistry()

        # Perfect: ䷀
        perfect = registry.register("perfect", hexagram_int=0b111111)
        assert perfect.is_healthy is True
        assert perfect.is_critical is False

        # 1 faulty bit → healthy (hamming=1)
        minor1 = registry.register("minor1", hexagram_int=0b111110)  # ䷉
        assert minor1.is_healthy is True
        assert minor1.is_critical is False
        assert minor1.hamming_to_goal == 1

        # 2 faulty bits → still healthy (hamming=2)
        minor2 = registry.register("minor2", hexagram_int=0b111100)  # ䷘
        assert minor2.is_healthy is True
        assert minor2.is_critical is False
        assert minor2.hamming_to_goal == 2
        # 0b000111 → hamming = (0b000111 ^ 0b111111).bit_count() = 3 → >=3 → critical

    def test_critical_threshold(self):
        """is_critical: hamming ≥ 3"""
        registry = AgentRegistry()
        info = registry.register("bad", hexagram_int=0b000111)
        # 000111 ^ 111111 = 111000 → bit_count = 3
        assert info.hamming_to_goal == 3
        assert info.is_critical is True
        assert info.drift_score == 0.5

    def test_prune_stale(self):
        """prune_stale 清除過期 Agent"""
        registry = AgentRegistry(stale_timeout=0)  # instant stale
        registry.register("a")
        registry.register("b")

        # With stale_timeout=0, they're immediately stale
        pruned = registry.prune_stale()
        assert pruned == 2
        assert registry.count() == 0

    def test_count(self):
        """count 返回正確嘅活躍 Agent 數量"""
        registry = AgentRegistry()
        assert registry.count() == 0
        registry.register("a")
        assert registry.count() == 1
        registry.register("b")
        assert registry.count() == 2
        registry.unregister("a")
        assert registry.count() == 1

    def test_get_system_health_idle(self):
        """無 Agent 時 system health 回報 idle"""
        registry = AgentRegistry()
        health = registry.get_system_health()
        assert health["status"] == "idle"
        assert health["agent_count"] == 0

    def test_get_system_health_healthy(self):
        """所有 Agent 健康時 status = healthy"""
        registry = AgentRegistry()
        registry.register("a", hexagram_int=0b111111)
        registry.register("b", hexagram_int=0b111111)

        health = registry.get_system_health()
        assert health["status"] == "healthy"
        assert health["agent_count"] == 2
        assert health["healthy_count"] == 2
        assert health["critical_count"] == 0
        assert health["avg_drift"] == 0.0

    def test_get_system_health_degraded(self):
        """部分 Agent critical 時 status = degraded"""
        registry = AgentRegistry()
        registry.register("healthy", hexagram_int=0b111111)
        registry.register("critical", hexagram_int=0b000000)

        health = registry.get_system_health()
        assert health["status"] == "degraded"
        assert health["healthy_count"] == 1
        assert health["critical_count"] == 1

    def test_get_system_health_critical(self):
        """全部 Agent critical 時 status = critical"""
        registry = AgentRegistry()
        registry.register("a", hexagram_int=0b000000)
        registry.register("b", hexagram_int=0b000000)

        health = registry.get_system_health()
        assert health["status"] == "critical"
        assert health["critical_count"] == 2

    def test_find_by_state(self):
        """find_by_state 返回所有匹配卦象嘅 Agent"""
        registry = AgentRegistry()
        registry.register("a", hexagram_int=0b111111)
        registry.register("b", hexagram_int=0b111111)
        registry.register("c", hexagram_int=0b000000)

        matches = registry.find_by_state(0b111111)
        assert len(matches) == 2
        assert [m.agent_id for m in matches] == ["a", "b"]

    def test_find_by_role(self):
        """find_by_role 透過 metadata 篩選"""
        registry = AgentRegistry()
        registry.register("researcher", hexagram_int=0b111111, metadata={"role": "researcher"})
        registry.register("coder", hexagram_int=0b111111, metadata={"role": "coder"})
        registry.register("another-researcher", hexagram_int=0b111111, metadata={"role": "researcher"})

        researchers = registry.find_by_role("researcher")
        assert len(researchers) == 2

    def test_agent_age_seconds(self):
        """age_seconds 係正數"""
        registry = AgentRegistry()
        info = registry.register("a")
        assert info.age_seconds >= 0

    def test_stale_agent_not_returned(self):
        """stale_timeout 過左就唔應該 return"""
        registry = AgentRegistry(stale_timeout=0)
        registry.register("a")
        got = registry.get("a")
        assert got is None  # immediately stale
