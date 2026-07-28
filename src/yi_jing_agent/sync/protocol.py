"""䷀ SyncProtocol — Push/Pull/Broadcast 狀態同步

定義 Agent 之間交換 6-bit hexagram state 嘅通訊協定：
- Push: Agent 主動上報自身狀態
- Pull: Agent 查詢另一個 Agent 嘅狀態  
- Broadcast: Agent 廣播狀態變更俾所有訂閱者
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import threading
import uuid

if TYPE_CHECKING:
    from .registry import AgentRegistry


class SyncAction(Enum):
    """同步動作類型"""
    PUSH = "push"           # Agent 推送自身狀態
    PULL = "pull"           # Agent 請求他人狀態
    BROADCAST = "broadcast" # Agent 廣播狀態變更
    SYNC_REQ = "sync_req"   # 請求全面同步
    ALERT = "alert"         # 異常警報（某 Agent 進入 critical）


@dataclass
class SyncMessage:
    """Agent 之間嘅同步訊息"""
    message_id: str = ""
    action: SyncAction = SyncAction.PUSH
    source_agent: str = ""
    target_agent: str = ""  # empty = broadcast
    hexagram_int: int = 0b111111
    hexagram_str: str = "111111"
    hexagram_name: str = "䷀ 乾為天"
    drift_score: float = 0.0
    hamming_to_goal: int = 0
    timestamp: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SyncProtocol:
    """䷀ Agent 狀態同步協定

    提供 Agent 之間點對點同步機制：
    - push(): 發布自身狀態
    - pull(): 查詢指定 Agent 狀態
    - broadcast(): 向所有已註冊 Agent 發布
    - poll_updates(): 輪詢未讀更新

    Thread-safe.
    """

    def __init__(self, registry: "AgentRegistry"):
        """
        Args:
            registry: AgentRegistry 實例（from .registry import AgentRegistry）
        """
        from .registry import AgentRegistry
        self._registry = registry
        self._inbox: Dict[str, List[SyncMessage]] = {}  # agent_id → [messages]
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable]] = {}  # event_type → [callbacks]

    # ── Push: 推送自身狀態 ──

    def push(self, agent_id: str, hexagram_int: int, **metadata) -> SyncMessage:
        """Agent 推送自身最新狀態到 registry。

        自動更新 registry 中嘅 Agent 記錄，
        並將訊息放入所有訂閱者嘅 inbox。

        Args:
            agent_id: 來源 Agent ID
            hexagram_int: 當前 6-bit hexagram state
            **metadata: 額外 payload 資訊

        Returns:
            SyncMessage: 已發送嘅訊息
        """
        from ..hexagram_table import get_hexagram_name

        # Update registry — only pass valid params
        self._registry.update(agent_id, hexagram_int)

        hamming = (hexagram_int ^ 0b111111).bit_count()
        msg = SyncMessage(
            action=SyncAction.PUSH,
            source_agent=agent_id,
            hexagram_int=hexagram_int,
            hexagram_str=f"{hexagram_int:06b}",
            hexagram_name=get_hexagram_name(hexagram_int),
            drift_score=hamming / 6.0,
            hamming_to_goal=hamming,
            payload=metadata,
        )

        # Deliver to all other agents' inboxes
        with self._lock:
            for other_id in self._registry._agents:
                if other_id != agent_id:
                    if other_id not in self._inbox:
                        self._inbox[other_id] = []
                    self._inbox[other_id].append(msg)

        # Fire callbacks
        self._fire("on_push", msg)
        if hamming >= 3:
            self._fire("on_critical", msg)

        return msg

    # ── Pull: 查詢他人狀態 ──

    def pull(self, agent_id: str, target_id: str) -> Optional[SyncMessage]:
        """查詢指定 Agent 嘅當前狀態。

        Args:
            agent_id: 請求者 ID
            target_id: 目標 Agent ID

        Returns:
            SyncMessage with target's state, or None if not found.
        """
        info = self._registry.get(target_id)
        if info is None:
            return None

        msg = SyncMessage(
            action=SyncAction.PULL,
            source_agent=target_id,
            target_agent=agent_id,
            hexagram_int=info.hexagram_int,
            hexagram_str=info.hexagram_str,
            hexagram_name=info.hexagram_name,
            drift_score=info.drift_score,
            hamming_to_goal=info.hamming_to_goal,
            payload={
                "lifecycle_mode": info.lifecycle_mode,
                "current_yao": info.current_yao,
                "faulty_yaos": info.faulty_yaos,
                "error_count": info.error_count,
            },
        )

        # Deliver to requester's inbox
        with self._lock:
            if agent_id not in self._inbox:
                self._inbox[agent_id] = []
            self._inbox[agent_id].append(msg)

        return msg

    # ── Broadcast ──

    def broadcast(self, source_agent: str, hexagram_int: int, **metadata) -> SyncMessage:
        """廣播狀態變更俾所有活躍 Agent。

        同 push 類似，但會標記為 BROADCAST action。

        Args:
            source_agent: 發送者 ID
            hexagram_int: 當前狀態
            **metadata: 額外資訊

        Returns:
            SyncMessage: 已發送嘅廣播訊息
        """
        from ..hexagram_table import get_hexagram_name

        self._registry.update(source_agent, hexagram_int)

        hamming = (hexagram_int ^ 0b111111).bit_count()
        msg = SyncMessage(
            action=SyncAction.BROADCAST,
            source_agent=source_agent,
            hexagram_int=hexagram_int,
            hexagram_str=f"{hexagram_int:06b}",
            hexagram_name=get_hexagram_name(hexagram_int),
            drift_score=hamming / 6.0,
            hamming_to_goal=hamming,
            payload=metadata,
        )

        # Deliver to ALL agents (including self) — broadcast semantics
        with self._lock:
            for other_id in self._registry._agents:
                if other_id not in self._inbox:
                    self._inbox[other_id] = []
                self._inbox[other_id].append(msg)

        self._fire("on_broadcast", msg)
        if hamming >= 3:
            self._fire("on_critical", msg)

        return msg

    # ── Alert ──

    def alert(self, source_agent: str, severity: str = "critical", message: str = "") -> SyncMessage:
        """發送異常警報（某 Agent 進入 critical 狀態）。

        所有收件人 inbox 都會收到 ALERT 訊息。
        """
        info = self._registry.get(source_agent)
        hexagram_int = info.hexagram_int if info else 0b000000

        msg = SyncMessage(
            action=SyncAction.ALERT,
            source_agent=source_agent,
            hexagram_int=hexagram_int,
            hexagram_str=f"{hexagram_int:06b}",
            hexagram_name=info.hexagram_name if info else "䷁ 坤為地",
            drift_score=info.drift_score if info else 1.0,
            hamming_to_goal=info.hamming_to_goal if info else 6,
            payload={"severity": severity, "alert_message": message},
        )

        with self._lock:
            for other_id in self._registry._agents:
                if other_id not in self._inbox:
                    self._inbox[other_id] = []
                self._inbox[other_id].append(msg)

        self._fire("on_alert", msg)
        return msg

    # ── Inbox Management ──

    def poll_updates(self, agent_id: str, clear: bool = True) -> List[SyncMessage]:
        """輪詢未讀更新。

        Args:
            agent_id: 查詢者 ID
            clear: 是否清除已讀訊息

        Returns:
            未讀訊息列表（按時間排序）
        """
        with self._lock:
            msgs = list(self._inbox.get(agent_id, []))
            if clear:
                self._inbox[agent_id] = []
            return msgs

    def clear_inbox(self, agent_id: str):
        """清空指定 Agent 嘅 inbox"""
        with self._lock:
            self._inbox[agent_id] = []

    def get_inbox_size(self, agent_id: str) -> int:
        """檢查指定 Agent 嘅未讀訊息數量"""
        with self._lock:
            return len(self._inbox.get(agent_id, []))

    # ── Subscriber System ──

    def subscribe(self, event: str, callback: Callable):
        """訂閱事件。

        Args:
            event: 'on_push', 'on_broadcast', 'on_alert', 'on_critical'
            callback: Callable[[SyncMessage], None]
        """
        with self._lock:
            if event not in self._subscribers:
                self._subscribers[event] = []
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable):
        """取消訂閱"""
        with self._lock:
            if event in self._subscribers:
                self._subscribers[event] = [cb for cb in self._subscribers[event] if cb != callback]

    def _fire(self, event: str, msg: SyncMessage):
        """觸發事件回調"""
        with self._lock:
            callbacks = list(self._subscribers.get(event, []))
        for cb in callbacks:
            try:
                cb(msg)
            except Exception:
                pass  # Don't let subscriber errors break the protocol
