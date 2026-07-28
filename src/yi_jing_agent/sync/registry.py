"""䷀ AgentRegistry — 多 Agent 中央註冊表

追蹤所有活躍 Agent 嘅 6-bit hexagram state，
提供系統健康度聚合視圖。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading

if TYPE_CHECKING:
    from ..agent_state import YiJingAgentState


@dataclass
class AgentInfo:
    """單一 Agent 嘅註冊資訊快照"""

    agent_id: str
    hexagram_int: int
    hexagram_str: str  # 6-char binary string
    hexagram_name: str  # e.g. "䷀ 乾為天"
    drift_score: float  # 0.0 (perfect) - 1.0 (complete drift)
    hamming_to_goal: int  # 0-6
    faulty_yaos: List[int]  # indices where bit = 0
    lifecycle_mode: str  # "FULL", "STANDARD", "EXPRESS"
    current_yao: str  # "初爻" ...
    task_type: str
    error_count: int
    last_seen: datetime
    registered_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Agent 健康：drift < 0.34 (最多 2 個爻位異常)"""
        return self.hamming_to_goal <= 2

    @property
    def is_critical(self) -> bool:
        """Agent 危急：drift >= 0.5 (≥3 個爻位異常)"""
        return self.hamming_to_goal >= 3

    @property
    def age_seconds(self) -> float:
        """Agent 註冊至今秒數"""
        return (datetime.now() - self.registered_at).total_seconds()


class AgentRegistry:
    """䷀ 中央 Agent 註冊表

    Thread-safe registry for tracking all active agents' hexagram states.
    Provides system-wide health aggregation and agent discovery.
    """

    def __init__(self, stale_timeout: float = 300.0):
        """
        Args:
            stale_timeout: 逾時秒數，超過此時間未更新視為離線
        """
        self._agents: Dict[str, AgentInfo] = {}
        self._lock = threading.RLock()
        self._stale_timeout = stale_timeout

    # ── Lifecycle ──

    def register(
        self,
        agent_id: str,
        hexagram_int: int = 0b111111,
        lifecycle_mode: str = "FULL",
        current_yao: str = "初爻",
        task_type: str = "generic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentInfo:
        """註冊一個新 Agent

        Returns:
            AgentInfo: 註冊後嘅 Agent 資訊快照
        """
        with self._lock:
            now = datetime.now()
            info = self._build_info(
                agent_id=agent_id,
                hexagram_int=hexagram_int,
                lifecycle_mode=lifecycle_mode,
                current_yao=current_yao,
                task_type=task_type,
                metadata=metadata or {},
                now=now,
                registered_at=now,
            )
            self._agents[agent_id] = info
            return info

    def unregister(self, agent_id: str) -> bool:
        """取消註冊一個 Agent

        Returns:
            True if agent was found and removed.
        """
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                return True
            return False

    # ── State Updates ──

    def update(
        self,
        agent_id: str,
        hexagram_int: int,
        lifecycle_mode: str = "FULL",
        current_yao: str = "初爻",
        task_type: str = "generic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AgentInfo]:
        """更新 Agent 狀態。

        如果 Agent 未註冊，自動註冊。
        Returns AgentInfo snapshot.
        """
        with self._lock:
            now = datetime.now()
            existing = self._agents.get(agent_id)
            registered_at = existing.registered_at if existing else now

            info = self._build_info(
                agent_id=agent_id,
                hexagram_int=hexagram_int,
                lifecycle_mode=lifecycle_mode,
                current_yao=current_yao,
                task_type=task_type,
                metadata=metadata or {},
                now=now,
                registered_at=registered_at,
            )
            self._agents[agent_id] = info
            return info

    def update_from_state(self, agent_id: str, state: YiJingAgentState) -> Optional[AgentInfo]:
        """從 YiJingAgentState 實例更新 Agent 註冊資訊"""
        from ..agent_state import YiJingAgentState, LifecycleMode

        if not isinstance(state, YiJingAgentState):
            raise TypeError("state must be a YiJingAgentState instance")

        return self.update(
            agent_id=agent_id,
            hexagram_int=state.hexagram_int,
            lifecycle_mode=state.lifecycle_mode.name if hasattr(state.lifecycle_mode, 'name') else str(state.lifecycle_mode),
            current_yao=state.current_yao.chinese_name if hasattr(state.current_yao, 'chinese_name') else str(state.current_yao),
            task_type="generic",
            metadata={
                "error_history": state.error_history,
                "active_moving_yaos": state.active_moving_yaos,
            },
        )

    # ── Queries ──

    def get(self, agent_id: str) -> Optional[AgentInfo]:
        """查詢指定 Agent 嘅最新狀態"""
        with self._lock:
            info = self._agents.get(agent_id)
            if info is None:
                return None
            # Check staleness
            if (datetime.now() - info.last_seen).total_seconds() > self._stale_timeout:
                return None
            return info

    def list_agents(self, include_stale: bool = False) -> List[AgentInfo]:
        """列出所有 Agent（預設排除過期）"""
        with self._lock:
            now = datetime.now()
            agents = []
            for info in self._agents.values():
                if include_stale or (now - info.last_seen).total_seconds() <= self._stale_timeout:
                    agents.append(info)
            return agents

    def count(self) -> int:
        """目前活躍 Agent 數量"""
        return len(self.list_agents())

    def prune_stale(self) -> int:
        """清除過期 Agent，返回清除數量"""
        with self._lock:
            now = datetime.now()
            stale_ids = [
                aid
                for aid, info in self._agents.items()
                if (now - info.last_seen).total_seconds() > self._stale_timeout
            ]
            for aid in stale_ids:
                del self._agents[aid]
            return len(stale_ids)

    # ── System Health ──

    def get_system_health(self) -> dict:
        """系統健康度聚合報告"""
        agents = self.list_agents()
        if not agents:
            return {
                "status": "idle",
                "agent_count": 0,
                "healthy_count": 0,
                "critical_count": 0,
                "avg_drift": 0.0,
                "agents": [],
            }

        healthy = sum(1 for a in agents if a.is_healthy)
        critical = sum(1 for a in agents if a.is_critical)
        avg_drift = sum(a.drift_score for a in agents) / len(agents)

        # 尋找最常見卦象（團隊主流狀態）
        hex_counts: Dict[int, int] = {}
        for a in agents:
            hex_counts[a.hexagram_int] = hex_counts.get(a.hexagram_int, 0) + 1
        dominant_hex = max(hex_counts, key=lambda k: hex_counts[k]) if hex_counts else 0b111111

        from ..hexagram_table import get_hexagram_name

        return {
            "status": "healthy" if critical == 0 else "degraded" if critical < len(agents) else "critical",
            "agent_count": len(agents),
            "healthy_count": healthy,
            "critical_count": critical,
            "avg_drift": round(avg_drift, 3),
            "dominant_hexagram": get_hexagram_name(dominant_hex),
            "dominant_hexagram_int": dominant_hex,
            "agents": [a.agent_id for a in agents],
        }

    def find_by_state(self, hexagram_int: int) -> List[AgentInfo]:
        """搵出所有處於特定卦象嘅 Agent"""
        return [a for a in self.list_agents() if a.hexagram_int == hexagram_int]

    def find_by_role(self, role: str) -> List[AgentInfo]:
        """搵出所有特定角色/任務類型嘅 Agent"""
        return [a for a in self.list_agents() if a.metadata.get("role") == role]

    # ── Internal ──

    def _build_info(
        self,
        agent_id: str,
        hexagram_int: int,
        lifecycle_mode: str,
        current_yao: str,
        task_type: str,
        metadata: dict,
        now: datetime,
        registered_at: datetime,
    ) -> AgentInfo:
        """Build AgentInfo from raw fields."""
        from ..hexagram_table import get_hexagram_name, popcount, get_faulty_yaos

        hamming = (hexagram_int ^ 0b111111).bit_count()
        faulty = get_faulty_yaos(hexagram_int)
        error_count = len(metadata.get("error_history", []))

        return AgentInfo(
            agent_id=agent_id,
            hexagram_int=hexagram_int,
            hexagram_str=f"{hexagram_int:06b}",
            hexagram_name=get_hexagram_name(hexagram_int),
            drift_score=hamming / 6.0,
            hamming_to_goal=hamming,
            faulty_yaos=faulty,
            lifecycle_mode=lifecycle_mode,
            current_yao=current_yao,
            task_type=task_type,
            error_count=error_count,
            last_seen=now,
            registered_at=registered_at,
            metadata=metadata,
        )
