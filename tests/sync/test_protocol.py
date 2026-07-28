"""䷀ Tests: SyncProtocol — Agent 狀態同步協定"""

import pytest
from yi_jing_agent.sync import AgentRegistry, SyncProtocol, SyncMessage, SyncAction


class TestSyncProtocol:
    """測試 Push/Pull/Broadcast 同步協定"""

    @pytest.fixture
    def setup(self):
        registry = AgentRegistry()
        protocol = SyncProtocol(registry)
        # Register two agents
        registry.register("alice", hexagram_int=0b111111)
        registry.register("bob", hexagram_int=0b111111)
        return registry, protocol

    def test_push_updates_registry(self, setup):
        """push 應更新 registry 中嘅 Agent 狀態"""
        registry, protocol = setup
        msg = protocol.push("alice", hexagram_int=0b000111)

        assert msg.action == SyncAction.PUSH
        assert msg.source_agent == "alice"
        assert msg.hexagram_int == 0b000111

        # Registry should reflect the push
        info = registry.get("alice")
        assert info.hexagram_int == 0b000111

    def test_push_delivers_to_others(self, setup):
        """push 應將訊息放入其他 Agent 嘅 inbox"""
        registry, protocol = setup
        protocol.push("alice", hexagram_int=0b000111)

        # Bob should have a message in his inbox
        msgs = protocol.poll_updates("bob")
        assert len(msgs) >= 1
        assert msgs[0].source_agent == "alice"

    def test_push_does_not_deliver_to_self(self, setup):
        """push 唔應該將訊息放入自己 inbox"""
        registry, protocol = setup
        protocol.push("alice", hexagram_int=0b000111)

        alice_msgs = protocol.poll_updates("alice")
        assert len(alice_msgs) == 0  # Should be empty since alice sent it

    def test_pull_returns_agent_state(self, setup):
        """pull 應返回目標 Agent 嘅狀態"""
        registry, protocol = setup
        # Alice pulls Bob's state
        msg = protocol.pull("alice", "bob")

        assert msg is not None
        assert msg.source_agent == "bob"
        assert msg.target_agent == "alice"
        assert msg.action == SyncAction.PULL
        assert msg.hexagram_int == 0b111111

    def test_pull_nonexistent_agent(self, setup):
        """pull 唔存在嘅 Agent 回傳 None"""
        registry, protocol = setup
        msg = protocol.pull("alice", "nonexistent")
        assert msg is None

    def test_pull_delivers_to_inbox(self, setup):
        """pull 嘅結果應放入請求者嘅 inbox"""
        registry, protocol = setup
        protocol.pull("alice", "bob")

        msgs = protocol.poll_updates("alice")
        assert len(msgs) >= 1
        assert msgs[0].source_agent == "bob"

    def test_broadcast_updates_registry(self, setup):
        """broadcast 應更新 registry"""
        registry, protocol = setup
        protocol.broadcast("alice", hexagram_int=0b000000)

        info = registry.get("alice")
        assert info.hexagram_int == 0b000000

    def test_broadcast_sends_to_all(self, setup):
        """broadcast 應發送俾所有 Agent（包括自己）"""
        registry, protocol = setup
        protocol.broadcast("alice", hexagram_int=0b000000)

        alice_msgs = protocol.poll_updates("alice")
        bob_msgs = protocol.poll_updates("bob")

        assert len(alice_msgs) >= 1  # broadcast includes self
        assert len(bob_msgs) >= 1
        assert alice_msgs[0].source_agent == "alice"
        assert bob_msgs[0].source_agent == "alice"

    def test_alert_sends_to_all(self, setup):
        """alert 應發送俾所有 Agent"""
        registry, protocol = setup
        msg = protocol.alert("alice", severity="critical", message="Executor crashed")

        assert msg.action == SyncAction.ALERT
        assert msg.payload["severity"] == "critical"
        assert msg.payload["alert_message"] == "Executor crashed"

        # Both agents should get alert
        bob_msgs = protocol.poll_updates("bob")
        assert len(bob_msgs) >= 1
        assert bob_msgs[0].action == SyncAction.ALERT

    def test_poll_updates_clears_inbox(self, setup):
        """poll_updates 預設清除 inbox"""
        registry, protocol = setup
        protocol.push("alice", hexagram_int=0b000111)

        first_poll = protocol.poll_updates("bob")
        second_poll = protocol.poll_updates("bob")

        assert len(first_poll) >= 1
        assert len(second_poll) == 0  # Should be empty now

    def test_poll_updates_keep(self, setup):
        """poll_updates(clear=False) 保留 inbox 內容"""
        registry, protocol = setup
        protocol.push("alice", hexagram_int=0b000111)

        first_poll = protocol.poll_updates("bob", clear=False)
        second_poll = protocol.poll_updates("bob", clear=False)

        assert len(first_poll) >= 1
        assert len(second_poll) >= 1  # Still there

    def test_get_inbox_size(self, setup):
        """get_inbox_size 返回正確數量"""
        registry, protocol = setup
        assert protocol.get_inbox_size("alice") == 0

        protocol.broadcast("bob", hexagram_int=0b000000)
        assert protocol.get_inbox_size("alice") >= 1

    def test_clear_inbox(self, setup):
        """clear_inbox 清空指定 inbox"""
        registry, protocol = setup
        protocol.push("alice", hexagram_int=0b000000)
        protocol.clear_inbox("bob")

        assert protocol.get_inbox_size("bob") == 0

    def test_sync_message_auto_id(self):
        """SyncMessage 自動生成 message_id"""
        msg1 = SyncMessage(action=SyncAction.PUSH, source_agent="test")
        msg2 = SyncMessage(action=SyncAction.PUSH, source_agent="test")
        assert msg1.message_id != ""
        assert msg1.message_id != msg2.message_id

    def test_push_critical_triggers_on_critical(self, setup):
        """critical push 應該觸發 on_critical event"""
        registry, protocol = setup
        triggered = []

        def on_critical(msg):
            triggered.append(msg)

        protocol.subscribe("on_critical", on_critical)
        protocol.push("alice", hexagram_int=0b000000)  # all bits off → critical

        assert len(triggered) == 1
        assert triggered[0].source_agent == "alice"
        assert triggered[0].hamming_to_goal == 6

    def test_subscriber_system(self, setup):
        """subscribe/unsubscribe 正常運作"""
        registry, protocol = setup
        calls = []

        def callback(msg):
            calls.append(msg)

        protocol.subscribe("on_push", callback)
        protocol.push("alice", hexagram_int=0b000111)
        assert len(calls) == 1

        protocol.unsubscribe("on_push", callback)
        protocol.push("alice", hexagram_int=0b000000)
        assert len(calls) == 1  # no new call
