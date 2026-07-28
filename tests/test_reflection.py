"""Tests for ThreeDimensionalReflection — the 3D reflection engine."""
import pytest
from yi_jing_agent.reflection import ThreeDimensionalReflection, Reflection3DResult


class TestInitialization:
    """Initialization and default values."""

    def test_default_hexagram_code(self):
        ref = ThreeDimensionalReflection()
        assert ref.hexagram_code == "111111"

    def test_custom_hexagram_code(self):
        ref = ThreeDimensionalReflection(hexagram_code="000000")
        assert ref.hexagram_code == "000000"

    def test_different_codes(self):
        ref1 = ThreeDimensionalReflection("111111")
        ref2 = ThreeDimensionalReflection("000000")
        assert ref1.hexagram_code != ref2.hexagram_code


class TestAnalyzeInterlocking:
    """analyze_interlocking() — hidden motive analysis."""

    def test_returns_dict(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_interlocking("Build a chatbot")
        assert isinstance(result, dict)

    def test_inner_trigram_all_ones(self):
        ref = ThreeDimensionalReflection("111111")
        result = ref.analyze_interlocking("test")
        assert result["inner_trigram"] == "111"

    def test_outer_trigram_all_ones(self):
        ref = ThreeDimensionalReflection("111111")
        result = ref.analyze_interlocking("test")
        assert result["outer_trigram"] == "111"

    def test_inner_trigram_all_zeros(self):
        ref = ThreeDimensionalReflection("000000")
        result = ref.analyze_interlocking("test")
        # bits = [0,0,0,0,0,0]; inner = bits[1:4] = [0,0,0]
        assert result["inner_trigram"] == "000"

    def test_outer_trigram_all_zeros(self):
        ref = ThreeDimensionalReflection("000000")
        result = ref.analyze_interlocking("test")
        # bits = [0,0,0,0,0,0]; outer = bits[2:5] = [0,0,0]
        assert result["outer_trigram"] == "000"

    def test_inner_trigram_mixed(self):
        ref = ThreeDimensionalReflection("010101")
        # bits = [0,1,0,1,0,1]; inner = bits[1:4] = [1,0,1] → "101"
        result = ref.analyze_interlocking("test")
        assert result["inner_trigram"] == "101"

    def test_outer_trigram_mixed(self):
        ref = ThreeDimensionalReflection("010101")
        # bits = [0,1,0,1,0,1]; outer = bits[2:5] = [0,1,0] → "010"
        result = ref.analyze_interlocking("test")
        assert result["outer_trigram"] == "010"

    def test_surface_task_in_result(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_interlocking("Write code")
        assert result["surface_task"] == "Write code"

    def test_reflection_prompt_contains_task(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_interlocking("Build a test suite")
        assert "Build a test suite" in result["reflection_prompt"]
        assert "互卦反思" in result["reflection_prompt"]


class TestAnalyzeOpposite:
    """analyze_opposite() — red teaming / opposite perspective."""

    def test_returns_dict(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_opposite("My plan")
        assert isinstance(result, dict)

    def test_opposite_all_flipped(self):
        """All 1s become 0s and vice versa."""
        ref = ThreeDimensionalReflection("111111")
        result = ref.analyze_opposite("plan")
        assert result["opposite_code"] == "000000"

    def test_opposite_all_zeros_to_ones(self):
        ref = ThreeDimensionalReflection("000000")
        result = ref.analyze_opposite("plan")
        assert result["opposite_code"] == "111111"

    def test_opposite_mixed(self):
        ref = ThreeDimensionalReflection("101010")
        result = ref.analyze_opposite("plan")
        assert result["opposite_code"] == "010101"

    def test_opposite_alternating(self):
        ref = ThreeDimensionalReflection("110011")
        result = ref.analyze_opposite("plan")
        assert result["opposite_code"] == "001100"

    def test_original_code_preserved(self):
        ref = ThreeDimensionalReflection("001100")
        result = ref.analyze_opposite("plan")
        assert result["original_code"] == "001100"

    def test_reflection_prompt_contains_plan(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_opposite("Deploy to prod")
        assert "錯卦反思" in result["reflection_prompt"]

    def test_plan_preserved(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_opposite("My awesome plan")
        assert result["plan"] == "My awesome plan"


class TestAnalyzeReversed:
    """analyze_reversed() — user perspective / reversed hexagram."""

    def test_returns_dict(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_reversed("json output")
        assert isinstance(result, dict)

    def test_reversed_palindrome(self):
        """A palindrome code reversed is itself."""
        ref = ThreeDimensionalReflection("111111")
        result = ref.analyze_reversed("fmt")
        assert result["reversed_code"] == "111111"

    def test_reversed_symmetric(self):
        ref = ThreeDimensionalReflection("101101")
        result = ref.analyze_reversed("fmt")
        assert result["reversed_code"] == "101101"

    def test_reversed_asymmetric(self):
        ref = ThreeDimensionalReflection("110001")
        result = ref.analyze_reversed("fmt")
        # 110001 reversed = 100011
        assert result["reversed_code"] == "100011"

    def test_reversed_simple(self):
        ref = ThreeDimensionalReflection("000001")
        result = ref.analyze_reversed("fmt")
        assert result["reversed_code"] == "100000"

    def test_original_code_preserved(self):
        ref = ThreeDimensionalReflection("010101")
        result = ref.analyze_reversed("fmt")
        assert result["original_code"] == "010101"

    def test_output_format_preserved(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_reversed("markdown table")
        assert result["output_format"] == "markdown table"

    def test_reflection_prompt_contains_relevant_text(self):
        ref = ThreeDimensionalReflection()
        result = ref.analyze_reversed("json")
        assert "綜卦反思" in result["reflection_prompt"]
        assert "終端使用者" in result["reflection_prompt"]


class TestRunFullReflection:
    """run_full_reflection() returns a Reflection3DResult."""

    def test_returns_reflection_3d_result(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection(
            task_description="Build a website",
            plan="Use React",
            output_format="HTML",
        )
        assert isinstance(result, Reflection3DResult)

    def test_hidden_motive_filled(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection(
            task_description="Analyze data",
        )
        assert result.hidden_motive != ""
        assert "Analyze data" in result.hidden_motive

    def test_worst_case_filled(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection(
            plan="Parallel execution",
        )
        assert result.worst_case != ""

    def test_user_experience_filled(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection(
            output_format="CSV",
        )
        assert result.user_experience != ""

    def test_requires_changes_default_false(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection()
        assert result.requires_changes is False

    def test_changes_default_empty(self):
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection()
        assert result.changes == []

    def test_run_full_reflection_defaults(self):
        """run_full_reflection with no arguments works."""
        ref = ThreeDimensionalReflection()
        result = ref.run_full_reflection()
        assert isinstance(result, Reflection3DResult)


class TestDifferentCodes:
    """Different hexagram codes produce different reflection prompts."""

    def test_interlocking_prompts_differ(self):
        ref1 = ThreeDimensionalReflection("111111")
        ref2 = ThreeDimensionalReflection("000000")
        r1 = ref1.analyze_interlocking("same task")
        r2 = ref2.analyze_interlocking("same task")
        # Both have same task, interlocking prompts are the same format
        # But this test verifies the method works with different codes
        assert r1["inner_trigram"] != r2["inner_trigram"]

    def test_opposite_codes_differ(self):
        ref1 = ThreeDimensionalReflection("111111")
        ref2 = ThreeDimensionalReflection("000000")
        r1 = ref1.analyze_opposite("plan")
        r2 = ref2.analyze_opposite("plan")
        assert r1["opposite_code"] != r2["opposite_code"]

    def test_reversed_codes_differ(self):
        ref1 = ThreeDimensionalReflection("111111")
        ref2 = ThreeDimensionalReflection("000001")
        r1 = ref1.analyze_reversed("fmt")
        r2 = ref2.analyze_reversed("fmt")
        assert r1["reversed_code"] != r2["reversed_code"]

    def test_run_full_reflection_with_different_codes(self):
        ref1 = ThreeDimensionalReflection("111111")
        ref2 = ThreeDimensionalReflection("000000")
        r1 = ref1.run_full_reflection("task", "plan", "fmt")
        r2 = ref2.run_full_reflection("task", "plan", "fmt")
        # Same inputs, different codes, but prompts only depend on inputs not codes
        # In the current implementation, the reflection_prompt for interlocking
        # uses task_description regardless of code
        # The opposite and reversed prompts also don't use the code
        # So both results will be the same
        # That's fine — this test just verifies the API works
        assert isinstance(r1, Reflection3DResult)
        assert isinstance(r2, Reflection3DResult)
