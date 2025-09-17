"""Tests for the CFG parser."""

import pytest

from machine_dialect.cfg import CFGParser


class TestCFGParser:
    """Test the CFG parser for Machine Dialect™."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.parser = CFGParser()

    def test_parse_set_statement(self) -> None:
        """Test parsing Set statements."""
        code = "Set `x` to _10_."
        tree = self.parser.parse(code)
        assert tree is not None
        assert tree.data == "start"

    def test_parse_give_back_statement(self) -> None:
        """Test parsing Give back statements."""
        code = 'Give back _"Hello, World!"_.'
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_arithmetic_expression(self) -> None:
        """Test parsing arithmetic expressions."""
        code = "Set `result` to _5_ + _3_ * _2_."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_logical_expression(self) -> None:
        """Test parsing logical expressions."""
        code = "Set `flag` to _yes_ and not _yes_ or _yes_."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_comparison(self) -> None:
        """Test parsing comparison expressions."""
        test_cases = [
            "Set `check` to `x` > _5_.",
            "Set `check` to `y` is greater than _10_.",
            "Set `check` to `z` equals _0_.",
            "Set `check` to `a` is not equal to `b`.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_parse_if_statement(self) -> None:
        """Test parsing if statements."""
        code = """If `x` > _0_ then:
> Give back _"Positive"_."""
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_if_else_statement(self) -> None:
        """Test parsing if-else statements."""
        code = """If `age` >= _18_ then:
> Give back _"Adult"_.
Else:
> Give back _"Minor"_."""
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_multiple_statements(self) -> None:
        """Test parsing multiple statements."""
        code = """Set `x` to _10_.
Set `y` to _20_.
Set `sum` to `x` + `y`.
Give back `sum`."""
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_nested_expressions(self) -> None:
        """Test parsing nested expressions."""
        code = "Set `result` to (_5_ + _3_) * (_10_ - _2_)."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_string_literals(self) -> None:
        """Test parsing string literals."""
        test_cases = [
            'Give back _"Hello"_.',
            "Give back _'World'_.",
            'Give back _"Machine Dialect™!"_.',
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_parse_boolean_literals(self) -> None:
        """Test parsing boolean literals."""
        test_cases = [
            "Set `flag` to _yes_.",
            "Set `flag` to _no_.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_parse_empty_literal(self) -> None:
        """Test parsing empty literal."""
        code = "Set `value` to _empty_."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_validate_valid_code(self) -> None:
        """Test validation of valid code."""
        code = "Set `x` to _5_."
        assert self.parser.validate(code) is True

    def test_validate_invalid_code(self) -> None:
        """Test validation of invalid code."""
        code = "Set `x` to 5"  # Missing underscores and period
        assert self.parser.validate(code) is False

    def test_case_insensitive_keywords(self) -> None:
        """Test that keywords are case-insensitive."""
        test_cases = [
            "set `x` to _5_.",
            "SET `x` to _5_.",
            "Set `x` TO _5_.",
            'give back _"Hello"_.',
            'GIVE BACK _"Hello"_.',
            'If `x` > _0_ then:\n> Give back _"Yes"_.',
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_complex_program(self) -> None:
        """Test parsing a complex program."""
        code = """Set `score` to _85_.
Set `passing_grade` to _60_.
Set `is_excellent` to `score` >= _90_.
If `score` >= `passing_grade` then:
> If `is_excellent` then:
> > Give back _"Excellent work!"_.
> Else:
> > Give back _"Good job, you passed."_.
Else:
> Give back _"Please try again."_."""
        tree = self.parser.parse(code)
        assert tree is not None

    def test_identifier_with_underscores(self) -> None:
        """Test parsing identifiers with underscores."""
        code = 'Set `user_name` to _"Alice"_.'
        tree = self.parser.parse(code)
        assert tree is not None

    def test_natural_language_operators(self) -> None:
        """Test parsing natural language operators."""
        test_cases = [
            "Set `check` to `x` is equal to `y`.",
            "Set `check` to `a` is not equal to `b`.",
            "Set `check` to `m` is less than `n`.",
            "Set `check` to `p` is greater than `q`.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_strict_equality_operators(self) -> None:
        """Test parsing strict equality operators."""
        test_cases = [
            "Give back _5_ is strictly equal to _5_.",
            "Give back _5_ is not strictly equal to _5.0_.",
            "Give back _5_ is exactly equal to _5_.",
            "Give back _5_ is not exactly equal to _5.0_.",
            "Give back _5_ is identical to _5_.",
            "Give back _5_ is not identical to _5.0_.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_float_literals(self) -> None:
        """Test parsing float literals."""
        test_cases = [
            "Set `pi` to _3.14_.",
            "Give back _2.5_ + _1.5_.",
            "Set `result` to _10.0_ / _3.0_.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_use_statement(self) -> None:
        """Test parsing Use statements."""
        code = 'Use `print` with _"Hello"_, _42_.'
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Actions not yet implemented in main parser")
    def test_action_statement(self) -> None:
        """Test parsing Action statements with inputs, outputs, and body."""
        # Action with parameters and Say statement
        code = """Action make_noise with `sound` as Text, `volume` as Number = _60_:
> Set `noise` to `sound`.
> Say `noise`."""
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Actions with complex syntax not yet implemented")
    def test_action_with_markdown_format(self) -> None:
        """Test parsing Action in markdown documentation format."""
        # This represents the full markdown format with details tags
        # The parser would need to handle this documentation-style format
        code = """Action `make noise`:
<details>
<summary>Emits the sound of the alarm.</summary>

> Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.
> Say `noise`.

</details>"""
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Interactions not yet implemented in main parser")
    def test_interaction_statement(self) -> None:
        """Test parsing Interaction statements."""
        code = """Interaction turn_alarm_off:
> If `alarm_is_on` then:
> > Set `alarm_is_on` to _no_.
> > Say _"Alarm has been turned off"_."""
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Say statements not yet implemented in main parser")
    def test_say_statement(self) -> None:
        """Test parsing Say statements (used in actions/interactions)."""
        test_cases = [
            'Say _"Hello, World!"_.',
            "Say `noise`.",
            'Say _"Alarm is "_ + `status` + _"."_.',
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None
