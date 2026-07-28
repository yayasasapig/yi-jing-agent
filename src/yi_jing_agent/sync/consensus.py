"""䷀ ConsensusEngine — 多 Agent 狀態合併共識

當多個 Agent 各自維護不同嘅 hexagram state，
需要一個機制將佢哋合併成單一「團隊共識狀態」。

支援多種共識策略：
- MAJORITY_VOTE: 多數 Agent 嘅 hexagram_int 取 mode
- WEIGHTED: 按 Agent authority 加權平均
- PESSIMISTIC: 取最低（最差）hexagram_int
- OPTIMISTIC: 取最高（最好）hexagram_int
- HITL: 無法達成共識時請求人類介入
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter

if TYPE_CHECKING:
    from .registry import AgentRegistry


class ConsensusStrategy(Enum):
    """共識策略枚舉"""
    MAJORITY_VOTE = "majority_vote"  # 多數決：取最常見卦象
    WEIGHTED = "weighted"             # 加權平均：by agent authority
    PESSIMISTIC = "pessimistic"      # 悲觀：取最低 hexagram_int
    OPTIMISTIC = "optimistic"        # 樂觀：取最高 hexagram_int
    HITL = "hitl"                    # 人類介入


@dataclass
class ConsensusResult:
    """共識結果"""
    consensus_hexagram_int: int
    consensus_hexagram_name: str
    strategy_used: ConsensusStrategy
    confidence: float  # 0.0 - 1.0
    participant_count: int
    cluster_count: int
    disagreements: List[str]  # 分歧描述
    agent_states: List[dict] = field(default_factory=list)


class ConsensusEngine:
    """䷀ 多 Agent 狀態共識引擎

    將多個 AgentInfo（來自 AgentRegistry）合併為單一團隊共識。
    """

    def __init__(self, registry: "AgentRegistry"):
        """
        Args:
            registry: AgentRegistry 實例
        """
        from .registry import AgentRegistry
        self._registry = registry

    # ── Main API ──

    def compute_consensus(
        self,
        strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE,
        agent_ids: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> ConsensusResult:
        """計算多 Agent 共識狀態。

        Args:
            strategy: 共識策略
            agent_ids: 指定 Agent（None = 全部活躍）
            weights: Agent 權重（僅 WEIGHTED 策略使用）

        Returns:
            ConsensusResult
        """
        agents = self._get_agents(agent_ids)
        if not agents:
            return ConsensusResult(
                consensus_hexagram_int=0b111111,
                consensus_hexagram_name="䷀ 乾為天",
                strategy_used=strategy,
                confidence=0.0,
                participant_count=0,
                cluster_count=0,
                disagreements=["No agents available"],
            )

        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            return self._majority_vote(agents)
        elif strategy == ConsensusStrategy.WEIGHTED:
            return self._weighted(agents, weights or {})
        elif strategy == ConsensusStrategy.PESSIMISTIC:
            return self._extremum(agents, take_min=True)
        elif strategy == ConsensusStrategy.OPTIMISTIC:
            return self._extremum(agents, take_min=False)
        elif strategy == ConsensusStrategy.HITL:
            return self._hitl(agents)
        else:
            return self._majority_vote(agents)

    def detect_clusters(self, agent_ids: Optional[List[str]] = None) -> List[List[dict]]:
        """檢測 Agent 狀態集群。

        將 hexagram_int 相近嘅 Agent 分組
        （Hamming distance ≤ 2 = 同一集群）。

        Returns:
            List of clusters, each cluster is a list of agent dicts.
        """
        agents = self._get_agents(agent_ids)
        if not agents:
            return []

        # Simple greedy clustering
        remaining = list(agents)
        clusters: List[List[dict]] = []

        while remaining:
            seed = remaining.pop(0)
            cluster = [seed]
            seed_int = seed["hexagram_int"]

            still_remaining = []
            for a in remaining:
                dist = (a["hexagram_int"] ^ seed_int).bit_count()
                if dist <= 2:
                    cluster.append(a)
                else:
                    still_remaining.append(a)
            remaining = still_remaining
            clusters.append(cluster)

        return clusters

    def drift_report(self, agent_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """生成團隊漂移報告。

        分析多 Agent 之間嘅狀態差異程度。

        Returns:
            dict with drift analysis.
        """
        agents = self._get_agents(agent_ids)
        if not agents:
            return {"status": "no_agents", "max_drift": 0.0}

        hex_ints = [a["hexagram_int"] for a in agents]
        unique_hex = set(hex_ints)

        # Pairwise Hamming distances
        max_pairwise = 0
        high_pairs: List[Tuple[str, str, int]] = []
        for i in range(len(hex_ints)):
            for j in range(i + 1, len(hex_ints)):
                dist = (hex_ints[i] ^ hex_ints[j]).bit_count()
                if dist > max_pairwise:
                    max_pairwise = dist
                if dist >= 3:
                    high_pairs.append((
                        agents[i]["agent_id"],
                        agents[j]["agent_id"],
                        dist,
                    ))

        clusters = self.detect_clusters(agent_ids)

        from ..hexagram_table import get_hexagram_name

        return {
            "status": (
                "coherent" if len(unique_hex) == 1
                else "diverged" if len(unique_hex) > 3
                else "slightly_diverged"
            ),
            "agent_count": len(agents),
            "unique_hexagram_count": len(unique_hex),
            "max_pairwise_hamming": max_pairwise,
            "divergent_pairs": len(high_pairs),
            "high_divergence_pairs": [
                f"{a} ↔ {b} (d_H={d})" for a, b, d in high_pairs
            ],
            "cluster_count": len(clusters),
            "dominant_hexagram": get_hexagram_name(
                Counter(hex_ints).most_common(1)[0][0]
            ) if hex_ints else "䷀ 乾為天",
        }

    # ── Internal Consensus Methods ──

    def _get_agents(self, agent_ids: Optional[List[str]] = None) -> List[dict]:
        """獲取 Agent 列表（dict 格式方便計算）"""
        if agent_ids is not None:
            agents = []
            for aid in agent_ids:
                info = self._registry.get(aid)
                if info:
                    agents.append(self._info_to_dict(info))
            return agents
        return [self._info_to_dict(a) for a in self._registry.list_agents()]

    def _info_to_dict(self, info) -> dict:
        """Convert AgentInfo to dict for computation."""
        return {
            "agent_id": info.agent_id,
            "hexagram_int": info.hexagram_int,
            "drift_score": info.drift_score,
            "hamming_to_goal": info.hamming_to_goal,
            "error_count": info.error_count,
            "is_healthy": info.is_healthy,
        }

    def _majority_vote(self, agents: List[dict]) -> ConsensusResult:
        """多數決：取最常見卦象"""
        votes = Counter(a["hexagram_int"] for a in agents)
        winner_int = votes.most_common(1)[0][0]
        winner_count = votes.most_common(1)[0][1]
        total = len(agents)

        from ..hexagram_table import get_hexagram_name

        confidence = winner_count / total
        disagreements = []
        for a in agents:
            if a["hexagram_int"] != winner_int:
                disagreements.append(
                    f"{a['agent_id']}: {get_hexagram_name(a['hexagram_int'])} "
                    f"(d_H={(a['hexagram_int'] ^ winner_int).bit_count()})"
                )

        clusters = self.detect_clusters([a["agent_id"] for a in agents])

        return ConsensusResult(
            consensus_hexagram_int=winner_int,
            consensus_hexagram_name=get_hexagram_name(winner_int),
            strategy_used=ConsensusStrategy.MAJORITY_VOTE,
            confidence=round(confidence, 3),
            participant_count=total,
            cluster_count=len(clusters),
            disagreements=disagreements,
            agent_states=[{
                "agent_id": a["agent_id"],
                "hexagram_int": a["hexagram_int"],
                "hexagram_name": get_hexagram_name(a["hexagram_int"]),
                "drift_score": a["drift_score"],
            } for a in agents],
        )

    def _weighted(self, agents: List[dict], weights: Dict[str, float]) -> ConsensusResult:
        """加權平均：按 Agent authority/weight 計算 consensus hexagram"""
        from ..hexagram_table import get_hexagram_name, hamming_distance

        total_weight = 0
        weighted_sum = 0
        weight_map = {}

        for a in agents:
            w = weights.get(a["agent_id"], 1.0)
            weighted_sum += a["hexagram_int"] * w
            total_weight += w
            weight_map[a["agent_id"]] = w

        # Weighted average as nearest hexagram int
        avg_int = round(weighted_sum / total_weight) if total_weight > 0 else 0b111111
        avg_int = max(0, min(63, avg_int))  # clamp to [0, 63]

        # Confidence = how close all agents are to the weighted average
        distances = [hamming_distance(a["hexagram_int"], avg_int) for a in agents]
        avg_distance = sum(distances) / len(distances)
        confidence = 1.0 - (avg_distance / 6.0)

        disagreements = []
        for a in agents:
            dist = hamming_distance(a["hexagram_int"], avg_int)
            if dist >= 2:
                disagreements.append(
                    f"{a['agent_id']} (weight={weight_map[a['agent_id']]}): "
                    f"{get_hexagram_name(a['hexagram_int'])} (d_H={dist})"
                )

        return ConsensusResult(
            consensus_hexagram_int=avg_int,
            consensus_hexagram_name=get_hexagram_name(avg_int),
            strategy_used=ConsensusStrategy.WEIGHTED,
            confidence=round(confidence, 3),
            participant_count=len(agents),
            cluster_count=len(self.detect_clusters([a["agent_id"] for a in agents])),
            disagreements=disagreements,
            agent_states=[{
                "agent_id": a["agent_id"],
                "hexagram_int": a["hexagram_int"],
                "hexagram_name": get_hexagram_name(a["hexagram_int"]),
                "weight": weight_map[a["agent_id"]],
            } for a in agents],
        )

    def _extremum(self, agents: List[dict], take_min: bool = True) -> ConsensusResult:
        """極值策略：取最低（悲觀）或最高（樂觀）hexagram_int"""
        from ..hexagram_table import get_hexagram_name

        hex_ints = [a["hexagram_int"] for a in agents]
        ext_int = min(hex_ints) if take_min else max(hex_ints)

        # 判斷採取極值嘅 Agent 佔比
        ext_count = sum(1 for a in agents if a["hexagram_int"] == ext_int)
        confidence = ext_count / len(agents)

        disagreements = []
        for a in agents:
            if a["hexagram_int"] != ext_int:
                disagreements.append(
                    f"{a['agent_id']}: {get_hexagram_name(a['hexagram_int'])} → "
                    f"would drop to {get_hexagram_name(ext_int)}"
                )

        return ConsensusResult(
            consensus_hexagram_int=ext_int,
            consensus_hexagram_name=get_hexagram_name(ext_int),
            strategy_used=(
                ConsensusStrategy.PESSIMISTIC if take_min
                else ConsensusStrategy.OPTIMISTIC
            ),
            confidence=round(confidence, 3),
            participant_count=len(agents),
            cluster_count=len(self.detect_clusters([a["agent_id"] for a in agents])),
            disagreements=disagreements,
            agent_states=[{
                "agent_id": a["agent_id"],
                "hexagram_int": a["hexagram_int"],
                "hexagram_name": get_hexagram_name(a["hexagram_int"]),
            } for a in agents],
        )

    def _hitl(self, agents: List[dict]) -> ConsensusResult:
        """HITL：無法達成共識時標記為人類介入

        輸出一個包含所有分歧嘅報告，等真人決定。
        """
        from ..hexagram_table import get_hexagram_name

        # 先以 majority vote 建議（但 confidence 標低）
        votes = Counter(a["hexagram_int"] for a in agents)
        winner_int = votes.most_common(1)[0][0]

        disagreements = []
        for a in agents:
            disagreements.append(
                f"{a['agent_id']}: {get_hexagram_name(a['hexagram_int'])} "
                f"(drift={a['drift_score']:.2f})"
            )

        return ConsensusResult(
            consensus_hexagram_int=winner_int,
            consensus_hexagram_name=get_hexagram_name(winner_int),
            strategy_used=ConsensusStrategy.HITL,
            confidence=0.0,  # 無信心，等人類決定
            participant_count=len(agents),
            cluster_count=len(self.detect_clusters([a["agent_id"] for a in agents])),
            disagreements=disagreements,
            agent_states=[{
                "agent_id": a["agent_id"],
                "hexagram_int": a["hexagram_int"],
                "hexagram_name": get_hexagram_name(a["hexagram_int"]),
                "drift_score": a["drift_score"],
                "is_healthy": a["is_healthy"],
            } for a in agents],
        )
