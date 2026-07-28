"""䷀ Tests: ConsensusEngine — 多 Agent 狀態合併共識"""

import pytest
from yi_jing_agent.sync import AgentRegistry, ConsensusEngine, ConsensusStrategy


class TestConsensusEngine:
    """測試多種共識策略"""

    @pytest.fixture
    def setup(self):
        """3 個 Agent，2 個一致 1 個分歧"""
        registry = AgentRegistry()
        registry.register("alice", hexagram_int=0b111111)
        registry.register("bob", hexagram_int=0b111111)
        registry.register("charlie", hexagram_int=0b000000)
        engine = ConsensusEngine(registry)
        return registry, engine

    @pytest.fixture
    def setup_all_same(self):
        """全體一致"""
        registry = AgentRegistry()
        registry.register("a", hexagram_int=0b111111)
        registry.register("b", hexagram_int=0b111111)
        registry.register("c", hexagram_int=0b111111)
        engine = ConsensusEngine(registry)
        return registry, engine

    @pytest.fixture
    def setup_all_different(self):
        """全部不同卦象"""
        registry = AgentRegistry()
        registry.register("a", hexagram_int=0b111111)  # ䷀
        registry.register("b", hexagram_int=0b000000)  # ䷁
        registry.register("c", hexagram_int=0b010101)  # ䷾
        registry.register("d", hexagram_int=0b101010)  # ䷿
        engine = ConsensusEngine(registry)
        return registry, engine

    # ── Majority Vote ──

    def test_majority_vote_wins(self, setup):
        """Majority: 多數者嘅卦象勝出"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)

        assert result.consensus_hexagram_int == 0b111111  # 2/3
        assert result.strategy_used == ConsensusStrategy.MAJORITY_VOTE
        assert result.confidence == pytest.approx(2 / 3, rel=1e-3)
        assert result.participant_count == 3

    def test_majority_vote_all_same(self, setup_all_same):
        """全部一致時 confidence = 1.0"""
        registry, engine = setup_all_same
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)

        assert result.consensus_hexagram_int == 0b111111
        assert result.confidence == 1.0

    def test_majority_vote_disagreements(self, setup):
        """分歧者應列喺 disagreements 列表"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)

        assert len(result.disagreements) == 1
        assert "charlie" in result.disagreements[0]

    def test_majority_vote_no_agents(self):
        """無 Agent 時應回傳預設值"""
        registry = AgentRegistry()
        engine = ConsensusEngine(registry)
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)

        assert result.consensus_hexagram_int == 0b111111
        assert result.confidence == 0.0
        assert result.participant_count == 0

    def test_majority_vote_specific_agents(self, setup):
        """指定特定 Agent 參與投票"""
        registry, engine = setup
        result = engine.compute_consensus(
            ConsensusStrategy.MAJORITY_VOTE,
            agent_ids=["alice", "charlie"],
        )
        # alice=111111, charlie=000000 → tie
        # majority vote picks most common (tie → first in Counter order)
        assert result.participant_count == 2

    # ── Weighted ──

    def test_weighted_with_weights(self, setup):
        """WEIGHTED: higher weight = more influence"""
        registry, engine = setup
        # Give charlie (000000) higher weight to pull consensus down
        result = engine.compute_consensus(
            ConsensusStrategy.WEIGHTED,
            weights={"alice": 1.0, "bob": 1.0, "charlie": 5.0},
        )

        avg = (0b111111 * 1.0 + 0b111111 * 1.0 + 0b000000 * 5.0) / 7.0
        expected = round(avg)
        assert result.consensus_hexagram_int == expected

    def test_weighted_all_same(self, setup_all_same):
        """WEIGHTED: 全部一致時唔理權重都係同一結果"""
        registry, engine = setup_all_same
        result = engine.compute_consensus(ConsensusStrategy.WEIGHTED)

        assert result.consensus_hexagram_int == 0b111111

    def test_weighted_bounds(self, setup):
        """WEIGHTED: 結果 clamp 喺 [0, 63]"""
        registry, engine = setup
        result = engine.compute_consensus(
            ConsensusStrategy.WEIGHTED,
            weights={"alice": 1000.0},
            agent_ids=["alice"],
        )
        assert 0 <= result.consensus_hexagram_int <= 63

    # ── Pessimistic ──

    def test_pessimistic_takes_min(self, setup):
        """PESSIMISTIC: 取最低 hexagram_int"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.PESSIMISTIC)

        assert result.consensus_hexagram_int == 0b000000  # charlie's state
        assert "䷁" in result.consensus_hexagram_name  # 坤
        assert result.strategy_used == ConsensusStrategy.PESSIMISTIC

    def test_pessimistic_all_same(self, setup_all_same):
        """PESSIMISTIC: 全部一致時取唯一值"""
        registry, engine = setup_all_same
        result = engine.compute_consensus(ConsensusStrategy.PESSIMISTIC)

        assert result.consensus_hexagram_int == 0b111111

    # ── Optimistic ──

    def test_optimistic_takes_max(self, setup):
        """OPTIMISTIC: 取最高 hexagram_int"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.OPTIMISTIC)

        assert result.consensus_hexagram_int == 0b111111  # alice/bob's state
        assert "䷀" in result.consensus_hexagram_name
        assert result.strategy_used == ConsensusStrategy.OPTIMISTIC

    # ── HITL ──

    def test_hitl_all_disagreements_recorded(self, setup):
        """HITL: 所有分歧記錄喺 disagreements"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.HITL)

        assert result.confidence == 0.0
        assert len(result.disagreements) > 0
        assert result.strategy_used == ConsensusStrategy.HITL

    # ── Cluster Detection ──

    def test_detect_clusters(self, setup):
        """detect_clusters 分返相似嘅 Agent 一組"""
        registry, engine = setup

        # Register a 4th agent similar to charlie
        registry.register("dave", hexagram_int=0b000001)

        clusters = engine.detect_clusters()
        assert len(clusters) >= 2  # at least 2 clusters

        # 111111 and 000000 should be in different clusters (hamming=6 > 2)
        # But 000001 and 000000 have hamming=1 → same cluster

    def test_detect_clusters_empty(self):
        """無 Agent 時 cluster = []"""
        registry = AgentRegistry()
        engine = ConsensusEngine(registry)
        assert engine.detect_clusters() == []

    # ── Drift Report ──

    def test_drift_report_all_same(self, setup_all_same):
        """全部一致時 status = coherent"""
        registry, engine = setup_all_same
        report = engine.drift_report()

        assert report["status"] == "coherent"
        assert report["agent_count"] == 3
        assert report["unique_hexagram_count"] == 1
        assert report["max_pairwise_hamming"] == 0
        assert report["divergent_pairs"] == 0

    def test_drift_report_diverged(self, setup_all_different):
        """全部不同時 status = diverged"""
        registry, engine = setup_all_different
        report = engine.drift_report()

        assert report["status"] == "diverged"
        assert report["unique_hexagram_count"] == 4
        assert report["max_pairwise_hamming"] >= 3

    def test_drift_report_no_agents(self):
        """無 Agent 時 report status = no_agents"""
        registry = AgentRegistry()
        engine = ConsensusEngine(registry)
        report = engine.drift_report()

        assert report["status"] == "no_agents"

    def test_drift_report_divergent_pairs(self, setup):
        """drift_report 列出 high divergence pairs"""
        registry, engine = setup
        report = engine.drift_report()

        assert report["divergent_pairs"] >= 1
        assert len(report["high_divergence_pairs"]) >= 1

    # ── Agent States Consistency ──

    def test_result_includes_agent_states(self, setup):
        """ConsensusResult 包含每個 Agent 嘅快照"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.MAJORITY_VOTE)

        assert len(result.agent_states) == 3
        agent_ids = [a["agent_id"] for a in result.agent_states]
        assert "alice" in agent_ids
        assert "bob" in agent_ids
        assert "charlie" in agent_ids

    def test_result_hexagram_name_matches_int(self, setup):
        """consensus_hexagram_name 同 int 一致"""
        registry, engine = setup
        result = engine.compute_consensus(ConsensusStrategy.PESSIMISTIC)

        from yi_jing_agent.hexagram_table import get_hexagram_name
        expected = get_hexagram_name(result.consensus_hexagram_int)
        assert result.consensus_hexagram_name == expected
