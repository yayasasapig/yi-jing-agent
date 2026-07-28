"""Tests for YiJingAgentState and related dataclasses."""
import pytest
from yi_jing_agent.agent_state import (
    YiJingAgentState,
    TaskGraph,
    FeasibilityReport,
    SafetyReport,
    HexagramTransition,
    Reflection3D,
    MemoryEntry,
    LifecycleMode,
)
from yi_jing_agent.yao_positions import YaoPosition


class TestDefaultValues:
    """Initialization with default values."""

    def test_default_current_yao(self):
        state = YiJingAgentState()
        assert state.current_yao == YaoPosition.FIRST_HIDDEN

    def test_default_hexagram_code(self):
        state = YiJingAgentState()
        assert state.hexagram_code == "111111"

    def test_default_active_moving_yaos_empty(self):
        state = YiJingAgentState()
        assert state.active_moving_yaos == []

    def test_default_hexagram_history_empty(self):
        state = YiJingAgentState()
        assert state.hexagram_history == []

    def test_default_long_term_memory_empty(self):
        state = YiJingAgentState()
        assert state.long_term_memory == []

    def test_default_task_graph_none(self):
        state = YiJingAgentState()
        assert state.task_graph is None

    def test_default_safety_report_none(self):
        state = YiJingAgentState()
        assert state.safety_report is None


class TestStepForward:
    """step_forward() advances through yao positions."""

    def test_step_forward_first_to_second(self):
        state = YiJingAgentState()
        assert state.current_yao == YaoPosition.FIRST_HIDDEN
        state.step_forward()
        assert state.current_yao == YaoPosition.SECOND_FIELD

    def test_step_forward_second_to_third(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.SECOND_FIELD
        state.step_forward()
        assert state.current_yao == YaoPosition.THIRD_ALERT

    def test_step_forward_third_to_fourth(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.THIRD_ALERT
        state.step_forward()
        assert state.current_yao == YaoPosition.FOURTH_LEAP

    def test_step_forward_fourth_to_fifth(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.FOURTH_LEAP
        state.step_forward()
        assert state.current_yao == YaoPosition.FIFTH_FLYING

    def test_step_forward_fifth_to_sixth(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.FIFTH_FLYING
        state.step_forward()
        assert state.current_yao == YaoPosition.SIXTH_REGRET

    def test_step_forward_full_sequence(self):
        """Stepping five times from 1 should reach 6."""
        state = YiJingAgentState()
        for _ in range(5):
            state.step_forward()
        assert state.current_yao == YaoPosition.SIXTH_REGRET

    def test_step_forward_at_sixth_stays_sixth(self):
        """step_forward at max position does not advance further."""
        state = YiJingAgentState()
        state.current_yao = YaoPosition.SIXTH_REGRET
        state.step_forward()
        assert state.current_yao == YaoPosition.SIXTH_REGRET

    def test_step_forward_returns_self(self):
        """step_forward returns self for chaining."""
        state = YiJingAgentState()
        result = state.step_forward()
        assert result is state

    def test_step_forward_logs_entry(self):
        state = YiJingAgentState()
        before = len(state.execution_log)
        state.step_forward()
        assert len(state.execution_log) == before + 1
        entry = state.execution_log[-1]
        assert "step_forward" in entry["message"]


class TestStepBackward:
    """step_backward() jumps to a specified yao position."""

    def test_step_backward_to_first(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.SIXTH_REGRET
        state.step_backward(YaoPosition.FIRST_HIDDEN)
        assert state.current_yao == YaoPosition.FIRST_HIDDEN

    def test_step_backward_to_third(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.SIXTH_REGRET
        state.step_backward(YaoPosition.THIRD_ALERT)
        assert state.current_yao == YaoPosition.THIRD_ALERT

    def test_step_backward_to_same_position(self):
        state = YiJingAgentState()
        state.current_yao = YaoPosition.FOURTH_LEAP
        state.step_backward(YaoPosition.FOURTH_LEAP)
        assert state.current_yao == YaoPosition.FOURTH_LEAP

    def test_step_backward_returns_self(self):
        state = YiJingAgentState()
        result = state.step_backward(YaoPosition.FIRST_HIDDEN)
        assert result is state

    def test_step_backward_logs_entry(self):
        state = YiJingAgentState()
        before = len(state.execution_log)
        state.step_backward(YaoPosition.SECOND_FIELD)
        assert len(state.execution_log) == before + 1
        entry = state.execution_log[-1]
        assert "step_backward" in entry["message"]


class TestTriggerMovingYao:
    """trigger_moving_yao() flips bits and tracks history."""

    @pytest.mark.parametrize("position,expected_bit", [
        (1, "0"),   # 111111 → 011111
        (2, "0"),   # 111111 → 101111
        (3, "0"),   # 111111 → 110111
        (4, "0"),   # 111111 → 111011
        (5, "0"),   # 111111 → 111101
        (6, "0"),   # 111111 → 111110
    ])
    def test_trigger_flips_bit(self, position, expected_bit):
        state = YiJingAgentState()
        transition = state.trigger_moving_yao(position)
        code_list = list(state.hexagram_code)
        assert code_list[position - 1] == expected_bit

    @pytest.mark.parametrize("position", [1, 2, 3, 4, 5, 6])
    def test_trigger_returns_hexagram_transition(self, position):
        state = YiJingAgentState()
        transition = state.trigger_moving_yao(position)
        assert isinstance(transition, HexagramTransition)
        assert transition.original_code == "111111"
        assert transition.new_code != "111111"
        assert transition.moving_yaos == [position]

    @pytest.mark.parametrize("position", [0, 7, -1])
    def test_trigger_invalid_raises_value_error(self, position):
        state = YiJingAgentState()
        with pytest.raises(ValueError, match=f"Invalid yao_index: {position}"):
            state.trigger_moving_yao(position)

    def test_trigger_double_flip_restores_original(self):
        """Flipping the same bit twice restores original code."""
        state = YiJingAgentState()
        state.trigger_moving_yao(3)  # 111111 → 110111
        state.trigger_moving_yao(3)  # 110111 → 111111
        assert state.hexagram_code == "111111"

    def test_trigger_double_flip_restores_bit(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)  # 111111 → 011111
        state.trigger_moving_yao(1)  # 011111 → 111111
        assert state.hexagram_code == "111111"

    def test_trigger_modifies_hexagram_code(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)
        assert state.hexagram_code == "011111"

    def test_trigger_updates_active_moving_yaos(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(2)
        assert 2 in state.active_moving_yaos
        assert len(state.active_moving_yaos) == 1

    def test_trigger_multiple_tracks_all(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)
        state.trigger_moving_yao(3)
        state.trigger_moving_yao(5)
        assert state.active_moving_yaos == [1, 3, 5]

    def test_trigger_multiple_appends_to_history(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)
        state.trigger_moving_yao(6)
        assert len(state.hexagram_history) == 2
        assert state.hexagram_history[0].moving_yaos == [1]
        assert state.hexagram_history[1].moving_yaos == [6]

    def test_trigger_logs_execution_entry(self):
        state = YiJingAgentState()
        before = len(state.execution_log)
        state.trigger_moving_yao(1)
        assert len(state.execution_log) == before + 1
        assert "moving_yao" in state.execution_log[-1]["message"]


class TestHexagramPath:
    """get_hexagram_path() format and contents."""

    def test_path_no_history(self):
        state = YiJingAgentState()
        path = state.get_hexagram_path()
        assert "䷀" in path
        assert "初始" in path
        assert "當前" in path

    def test_path_with_one_transition(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)  # 111111 → 011111 (䷈ 風天小畜)
        path = state.get_hexagram_path()
        assert "初始" in path
        assert "當前" in path
        assert "䷈" in path  # symbol for ䷈ 風天小畜

    def test_path_with_multiple_transitions(self):
        state = YiJingAgentState()
        state.trigger_moving_yao(1)
        state.trigger_moving_yao(3)
        path = state.get_hexagram_path()
        # Should contain arrow separators
        assert "→" in path
        parts = path.split("→")
        assert len(parts) == 4  # initial + 2 history + 1 current

    def test_path_format_contains_parentheses(self):
        state = YiJingAgentState()
        path = state.get_hexagram_path()
        assert "(" in path
        assert ")" in path


class TestDataclasses:
    """Dataclass initialization works correctly."""

    def test_task_graph_defaults(self):
        tg = TaskGraph()
        assert tg.task_id == ""
        assert tg.constraints == []
        assert tg.success_criteria == []
        assert tg.forbidden_actions == []
        assert tg.estimated_complexity == "medium"

    def test_task_graph_custom(self):
        tg = TaskGraph(
            task_id="T-123",
            original_intent="Build a chatbot",
            constraints=["no external APIs"],
            estimated_complexity="hard",
        )
        assert tg.task_id == "T-123"
        assert tg.original_intent == "Build a chatbot"
        assert tg.constraints == ["no external APIs"]
        assert tg.estimated_complexity == "hard"

    def test_feasibility_report_defaults(self):
        fr = FeasibilityReport()
        assert fr.plan_a_description == ""
        assert fr.key_apis == []
        assert fr.estimated_tokens == 0
        assert fr.known_risks == []
        assert fr.fallback_plans == []

    def test_feasibility_report_custom(self):
        fr = FeasibilityReport(
            plan_a_description="Use GPT-4",
            key_apis=["openai"],
            estimated_tokens=5000,
            known_risks=["cost"],
        )
        assert fr.plan_a_description == "Use GPT-4"
        assert fr.estimated_tokens == 5000

    def test_safety_report_defaults(self):
        sr = SafetyReport()
        assert sr.passed is False
        assert sr.issues == []
        assert sr.recommendations == []
        assert sr.requires_human is False

    def test_safety_report_custom(self):
        sr = SafetyReport(
            passed=True,
            issues=["minor concern"],
            requires_human=False,
        )
        assert sr.passed is True
        assert sr.issues == ["minor concern"]

    def test_hexagram_transition_defaults(self):
        ht = HexagramTransition()
        assert ht.original_code == "111111"
        assert ht.new_code == "111111"
        assert ht.moving_yaos == []
        assert ht.transition_name == "䷀ 乾為天"
        assert ht.strategy == "Happy Path"

    def test_hexagram_transition_custom(self):
        ht = HexagramTransition(
            original_code="111111",
            new_code="011111",
            moving_yaos=[1],
            transition_name="䷈ 風天小畜",
            strategy="Reduce speed",
        )
        assert ht.new_code == "011111"
        assert ht.strategy == "Reduce speed"

    def test_reflection_3d_defaults(self):
        r3 = Reflection3D()
        assert r3.interlocking_hidden == ""
        assert r3.opposite_risk == ""
        assert r3.reversed_user == ""
        assert r3.requires_changes is False
        assert r3.changes == []

    def test_reflection_3d_custom(self):
        r3 = Reflection3D(
            interlocking_hidden="hidden motive detected",
            opposite_risk="worst case: API failure",
            reversed_user="UX needs work",
            requires_changes=True,
            changes=["add retry logic"],
        )
        assert r3.requires_changes is True
        assert r3.changes == ["add retry logic"]

    def test_memory_entry_defaults(self):
        me = MemoryEntry()
        assert me.hexagram_path == ""
        assert me.task_type == ""
        assert me.execution_summary == ""
        assert me.key_patterns == []
        assert me.failure_modes == []
        assert me.recommendations == []

    def test_memory_entry_custom(self):
        me = MemoryEntry(
            hexagram_path="䷀ (初始) → ䷈ (當前)",
            task_type="code_gen",
            execution_summary="Success",
            key_patterns=["pattern1"],
            recommendations=["add tests"],
        )
        assert me.hexagram_path == "䷀ (初始) → ䷈ (當前)"
        assert me.recommendations == ["add tests"]


class TestLifecycleMode:
    """LifecycleMode enum and state integration."""

    def test_default_mode_full(self):
        state = YiJingAgentState()
        assert state.lifecycle_mode == LifecycleMode.FULL

    def test_record_skip_adds_entry(self):
        state = YiJingAgentState()
        state.record_skip(YaoPosition.SECOND_FIELD, "test skip")
        assert YaoPosition.SECOND_FIELD in state.skipped_yaos
        assert len(state.skipped_yaos) == 1

    def test_record_skip_logs(self):
        state = YiJingAgentState()
        state.record_skip(YaoPosition.FOURTH_LEAP, "standard mode skip")
        assert len(state.skipped_stages_log) == 1
        assert "⏭️" in state.skipped_stages_log[0]
        assert "四爻" in state.skipped_stages_log[0]
        assert len(state.execution_log) >= 1
        assert "⏭️" in state.execution_log[-1]["message"]


class TestBitwiseState:
    """Tests for bitwise operations on YiJingAgentState."""

    def test_initial_hexagram_int(self):
        state = YiJingAgentState()
        assert state.hexagram_int == 0b111111

    def test_hexagram_code_property_compat(self):
        state = YiJingAgentState()
        assert state.hexagram_code == "111111"
        state.hexagram_code = "101010"
        assert state.hexagram_int == 0b101010

    def test_check_yao_on_state(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b101010
        assert state.check_yao(1) == True
        assert state.check_yao(2) == False

    def test_get_faulty_yaos_on_state(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b101010
        faulty = state.get_faulty_yaos()
        assert 2 in faulty
        assert 4 in faulty
        assert 6 in faulty

    def test_hamming_to_goal_perfect(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b111111
        assert state.hamming_to_goal() == 0

    def test_hamming_to_goal_drifted(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b000000
        assert state.hamming_to_goal() == 6

    def test_drift_score_perfect(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b111111
        assert state.drift_score() == 0.0

    def test_drift_score_half(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b111000
        assert state.drift_score() == 0.5

    def test_record_error_to_execution(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b111111
        state.record_error("TOOL_EXECUTION_ERROR", "API timeout")
        assert state.hexagram_int != 0b111111
        assert len(state.error_history) == 1
        assert state.error_history[0]["error_type"] == "TOOL_EXECUTION_ERROR"

    def test_record_error_unknown(self):
        state = YiJingAgentState()
        state.hexagram_int = 0b111111
        state.record_error("NOT_A_REAL_ERROR")
        assert state.hexagram_int == 0b111111  # unchanged
        assert len(state.error_history) == 0

    def test_trigger_moving_yao_updates_int(self):
        state = YiJingAgentState()
        t = state.trigger_moving_yao(3)
        assert state.hexagram_int == 0b110111
        assert t.original_code == "111111"
        assert t.new_code == "110111"
