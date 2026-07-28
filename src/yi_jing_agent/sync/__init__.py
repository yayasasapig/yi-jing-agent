"""䷀ 多 Agent 6-bit 狀態同步協定

Option B: Multi-Agent 6-bit State Synchronization Protocol

提供多 Agent 之間嘅分散式狀態協調機制：
1. AgentRegistry — 中央註冊表，管理所有 Agent
2. SyncProtocol — Push/Pull/Broadcast 狀態同步
3. ConsensusEngine — 多 Agent 狀態合併共識
"""

from .registry import AgentRegistry, AgentInfo
from .protocol import SyncProtocol, SyncMessage, SyncAction
from .consensus import ConsensusEngine, ConsensusStrategy

__all__ = [
    "AgentRegistry",
    "AgentInfo",
    "SyncProtocol",
    "SyncMessage",
    "SyncAction",
    "ConsensusEngine",
    "ConsensusStrategy",
]
