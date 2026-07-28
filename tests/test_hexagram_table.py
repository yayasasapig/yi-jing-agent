"""Tests for the 64-hexagram table (hexagram_table.py)."""
import importlib
import pytest
from yi_jing_agent.hexagram_table import (
    HEXAGRAM_NAMES,
    STRATEGIES,
    get_hexagram_name,
    get_strategy_for_hexagram,
    popcount,
    hamming_distance,
    drift_score,
    check_yao,
    get_faulty_yaos,
    flip_yao,
    apply_error_mask,
    ERROR_MASK,
    int_to_str,
    str_to_int,
)


class TestHexagramNamesDict:
    """HEXAGRAM_NAMES dictionary integrity."""

    def test_all_codes_unique(self):
        """All 64 codes are unique (no duplicates)."""
        codes = list(HEXAGRAM_NAMES.keys())
        assert len(set(codes)) == 64
        assert len(codes) == 64

    def test_each_code_length_six(self):
        """Every code string has length exactly 6."""
        for code in HEXAGRAM_NAMES:
            assert len(code) == 6, f"Code {code!r} has length {len(code)}, expected 6"

    def test_each_code_is_binary(self):
        """Every code contains only 0s and 1s."""
        for code in HEXAGRAM_NAMES:
            assert all(c in "01" for c in code), f"Code {code!r} contains non-binary chars"


class TestGetHexagramName:
    """get_hexagram_name() function."""

    @pytest.mark.parametrize("code,expected_substring", [
        ("111111", "乾為天"),
        ("000000", "坤為地"),
        ("010100", "水雷屯"),
        ("001010", "山水蒙"),
        ("010010", "坎為水"),
        ("101101", "離為火"),
        ("010101", "水火既濟"),
        ("101010", "火水未濟"),
    ])
    def test_known_code_contains_name(self, code, expected_substring):
        result = get_hexagram_name(code)
        assert expected_substring in result

    @pytest.mark.parametrize("code,expected_prefix", [
        ("111111", "䷀"),
        ("000000", "䷁"),
        ("010100", "䷂"),
    ])
    def test_known_code_contains_symbol(self, code, expected_prefix):
        result = get_hexagram_name(code)
        assert result.startswith(expected_prefix)

    def test_known_code_format(self):
        """Format is '䷀ 乾為天' (symbol + space + name)."""
        result = get_hexagram_name("111111")
        parts = result.split(" ", 1)
        assert len(parts) == 2
        assert parts[1] == "乾為天"

    def test_unknown_code_returns_fallback(self):
        result = get_hexagram_name("111112")
        assert result == "䷀ 未知"

    def test_unknown_code_empty_string(self):
        result = get_hexagram_name("")
        assert result == "䷀ 未知"

    def test_unknown_code_too_short(self):
        result = get_hexagram_name("222222")
        assert result == "䷀ 未知"

    def test_all_64_known_codes_return_non_empty(self):
        """All 64 known codes return a name without '未知'."""
        for code in HEXAGRAM_NAMES:
            name = get_hexagram_name(code)
            assert "未知" not in name, f"Known code {code} returned unknown"
            assert name != ""

    def test_all_64_codes_begin_with_bagua_symbol(self):
        """Every result should start with a ䷀-type symbol."""
        for code in HEXAGRAM_NAMES:
            result = get_hexagram_name(code)
            assert result[0] >= "\u4DC0" and result[0] <= "\u4DFF", (
                f"Code {code} result {result!r} does not start with a hexagram symbol"
            )


class TestGetStrategy:
    """get_strategy_for_hexagram() function."""

    @pytest.mark.parametrize("code", [
        "111111", "000000", "010100", "001010",
        "010010", "101101", "010101", "101010",
        "011111", "111110", "110010", "010011",
        "000001", "100000", "010001", "111001",
        "111000", "111100", "001000", "000100",
    ])
    def test_known_code_returns_non_empty(self, code):
        strategy = get_strategy_for_hexagram(code)
        assert strategy, f"Strategy for {code} was empty"
        assert len(strategy) > 5

    def test_known_code_contains_code_name(self):
        strategy = get_strategy_for_hexagram("111111")
        assert "乾為天" in strategy

    def test_unknown_code_high_yang(self):
        """Code with 5+ yang bits gets high-yang fallback."""
        result = get_strategy_for_hexagram("111112")
        assert "多陽爻" in result
        assert "資源充足" in result

    def test_unknown_code_low_yang(self):
        """Code with 1 or fewer yang bits gets low-yang fallback."""
        result = get_strategy_for_hexagram("000002")
        assert "多陰爻" in result
        assert "收斂觀察" in result

    def test_unknown_code_with_kan(self):
        """Code containing '010' gets kan-risk fallback.
        Must be a code not in STRATEGIES, with yang_count 2-4 so that
        the '010' pattern check triggers before the yang-count branches.
        """
        # "010012": not binary → not in STRATEGIES,
        # yang_count = bits.count("1") = 2 (not >=5, not <=1),
        # but contains "010" at index 0 → triggers kan branch.
        result = get_strategy_for_hexagram("010012")
        assert "坎象" in result
        assert "風險" in result

    def test_unknown_code_generic_fallback(self):
        """Other unknown codes get the generic '回到初爻' fallback."""
        result = get_strategy_for_hexagram("001122")
        assert "通用降級" in result
        assert "回到初爻" in result


class TestDictConsistency:
    """Consistency between HEXAGRAM_NAMES and STRATEGIES."""

    def test_keys_match_no_missing(self):
        missing = set(HEXAGRAM_NAMES.keys()) - set(STRATEGIES.keys())
        assert missing == set(), f"Missing strategies for codes: {missing}"

    def test_keys_match_no_extra(self):
        extra = set(STRATEGIES.keys()) - set(HEXAGRAM_NAMES.keys())
        assert extra == set(), f"Extra strategies with no hexagram: {extra}"

    def test_both_have_64_keys(self):
        assert len(HEXAGRAM_NAMES) == 64
        assert len(STRATEGIES) == 64


class TestModuleSideEffect:
    """Module-level print side effect on import."""

    def test_no_print_on_import(self, capsys):
        """Importing hexagram_table should not produce stdout."""
        import yi_jing_agent.hexagram_table as ht
        importlib.reload(ht)
        captured = capsys.readouterr()
        assert captured.out == "", f"Got unexpected print: {captured.out!r}"
        assert captured.err == ""

    def test_module_level_vars_computed_correctly(self):
        """The module-level checks pass because dicts match."""
        # Re-run the same logic that the module uses at import time
        missing = set(HEXAGRAM_NAMES.keys()) - set(STRATEGIES.keys())
        extra = set(STRATEGIES.keys()) - set(HEXAGRAM_NAMES.keys())
        assert not missing
        assert not extra


class TestBitwiseEngine:
    """Tests for bitwise helpers and error taxonomy."""

    def test_popcount_all_zeros(self):
        assert popcount(0b000000) == 0

    def test_popcount_all_ones(self):
        assert popcount(0b111111) == 6

    def test_popcount_mixed(self):
        assert popcount(0b101010) == 3

    def test_hamming_distance_identical(self):
        assert hamming_distance(0b111111, 0b111111) == 0

    def test_hamming_distance_opposite(self):
        assert hamming_distance(0b111111, 0b000000) == 6

    def test_hamming_distance_partial(self):
        assert hamming_distance(0b111111, 0b111000) == 3

    def test_drift_score_perfect(self):
        assert drift_score(0b111111) == 0.0

    def test_drift_score_complete(self):
        assert drift_score(0b000000) == 1.0

    def test_drift_score_half(self):
        assert drift_score(0b111000) == 0.5

    def test_check_yao_healthy(self):
        assert check_yao(0b111111, 1) == True
        assert check_yao(0b111111, 6) == True

    def test_check_yao_faulty(self):
        assert check_yao(0b000000, 1) == False

    def test_check_yao_specific(self):
        # 0b100000 → only 初爻 (bit5) is set
        assert check_yao(0b100000, 1) == True
        assert check_yao(0b100000, 2) == False

    def test_get_faulty_yaos_all_healthy(self):
        assert get_faulty_yaos(0b111111) == []

    def test_get_faulty_yaos_all_dead(self):
        assert get_faulty_yaos(0b000000) == [1, 2, 3, 4, 5, 6]

    def test_get_faulty_yaos_partial(self):
        # 0b101010 → bits 5,3,1 set → 初爻(5)=1, 二爻(4)=0, 三爻(3)=1, 四爻(2)=0, 五爻(1)=1, 上爻(0)=0
        assert get_faulty_yaos(0b101010) == [2, 4, 6]

    def test_flip_yao_toggles_bit(self):
        result = flip_yao(0b111111, 1)
        assert result == 0b011111
        # Flip back
        result = flip_yao(result, 1)
        assert result == 0b111111

    def test_flip_yao_all_positions(self):
        state = 0b000000
        for i in range(1, 7):
            state = flip_yao(state, i)
        assert state == 0b111111

    def test_flip_yao_invalid_index(self):
        with pytest.raises(ValueError):
            flip_yao(0b111111, 0)
        with pytest.raises(ValueError):
            flip_yao(0b111111, 7)

    def test_apply_error_mask(self):
        result = apply_error_mask(0b111111, "TOOL_EXECUTION_ERROR")
        assert result == 0b110111  # bit 3 flipped

    def test_apply_error_mask_unknown(self):
        with pytest.raises(ValueError):
            apply_error_mask(0b111111, "UNKNOWN_ERROR")

    def test_all_error_masks_are_distinct(self):
        masks = list(ERROR_MASK.values())
        assert len(set(masks)) == 6  # All 6 unique

    def test_int_to_str_conversion(self):
        assert int_to_str(0b111111) == "111111"
        assert int_to_str(0b000000) == "000000"

    def test_str_to_int_conversion(self):
        assert str_to_int("111111") == 0b111111

    def test_get_hexagram_name_int(self):
        name = get_hexagram_name(0b111111)
        assert "乾為天" in name

    def test_get_hexagram_name_int_invalid(self):
        name = get_hexagram_name(99)  # Out of range
        assert name == "䷀ 未知"

    def test_get_strategy_int(self):
        s = get_strategy_for_hexagram(0b111111)
        assert "Happy Path" in s
        assert "乾為天" in s

    def test_get_strategy_unknown_int(self):
        s = get_strategy_for_hexagram(0b111010)
        assert s != "" and "通用" not in s  # This is ䷅ which has a strategy
