"""Tests for the CFG parser."""

import pytest

from machine_dialect.cfg import CFGParser


class TestCFGParser:
    """Test the CFG parser for Machine Dialect."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.parser = CFGParser()

    def test_parse_set_statement(self) -> None:
        """Test parsing Set statements."""
        code = "Set `x` to 10."
        tree = self.parser.parse(code)
        assert tree is not None
        assert tree.data == "start"

    def test_parse_say_statement(self) -> None:
        """Test parsing Say statements."""
        code = 'Say "Hello, World!".'
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_arithmetic_expression(self) -> None:
        """Test parsing arithmetic expressions."""
        code = "Set `result` to 5 + 3 * 2."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_logical_expression(self) -> None:
        """Test parsing logical expressions."""
        code = "Set `flag` to True and not False or False."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_comparison(self) -> None:
        """Test parsing comparison expressions."""
        test_cases = [
            "Set `check` to x > 5.",
            "Set `check` to y is greater than 10.",
            "Set `check` to z equals 0.",
            "Set `check` to a is not equal to b.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    @pytest.mark.skip(reason="If statements syntax differs in simplified grammar")
    def test_parse_if_statement(self) -> None:
        """Test parsing if statements."""
        code = """
        if x > 0 then {
            Say "Positive".
        }
        """
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="If-else statements syntax differs in simplified grammar")
    def test_parse_if_else_statement(self) -> None:
        """Test parsing if-else statements."""
        code = """
        if age >= 18 then {
            Say "Adult".
        } else {
            Say "Minor".
        }
        """
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_multiple_statements(self) -> None:
        """Test parsing multiple statements."""
        code = """
        Set `x` to 10.
        Set `y` to 20.
        Set `sum` to x + y.
        Say sum.
        """
        tree = self.parser.parse(code)
        assert tree is not None

    def test_parse_nested_expressions(self) -> None:
        """Test parsing nested expressions."""
        code = "Set `result` to (5 + 3) * (10 - 2)."
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Single quotes not supported in simplified grammar")
    def test_parse_string_literals(self) -> None:
        """Test parsing string literals."""
        test_cases = [
            'Say "Hello".',
            "Say 'World'.",
            'Say "Machine Dialect!".',
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_parse_boolean_literals(self) -> None:
        """Test parsing boolean literals."""
        test_cases = [
            "Set `flag` to True.",
            "Set `flag` to False.",
            "Set `flag` to Yes.",
            "Set `flag` to No.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    def test_parse_empty_literal(self) -> None:
        """Test parsing empty literal."""
        code = "Set `value` to empty."
        tree = self.parser.parse(code)
        assert tree is not None

    def test_validate_valid_code(self) -> None:
        """Test validation of valid code."""
        code = "Set `x` to 5."
        assert self.parser.validate(code) is True

    def test_validate_invalid_code(self) -> None:
        """Test validation of invalid code."""
        code = "Set x to 5"  # Missing backticks and period
        assert self.parser.validate(code) is False

    @pytest.mark.skip(reason="Case-insensitive keywords not supported in simplified grammar")
    def test_case_insensitive_keywords(self) -> None:
        """Test that keywords are case-insensitive."""
        test_cases = [
            "set `x` to 5.",
            "SET `x` to 5.",
            "Set `x` TO 5.",
            'say "Hello".',
            'SAY "Hello".',
            'IF x > 0 THEN { Say "Yes". }',
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None

    @pytest.mark.skip(reason="Complex if-else and >= operator not fully supported in simplified grammar")
    def test_complex_program(self) -> None:
        """Test parsing a complex program."""
        code = """
        Set `score` to 85.
        Set `passing_grade` to 60.
        Set `is_excellent` to score >= 90.

        if score >= passing_grade then {
            if is_excellent then {
                Say "Excellent work!".
            } else {
                Say "Good job, you passed.".
            }
        } else {
            Say "Please try again.".
        }
        """
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Identifiers with spaces not supported in simplified grammar")
    def test_identifier_with_spaces(self) -> None:
        """Test parsing identifiers with spaces."""
        code = 'Set `user name` to "Alice".'
        tree = self.parser.parse(code)
        assert tree is not None

    @pytest.mark.skip(reason="Natural language operators not supported in simplified grammar")
    def test_natural_language_operators(self) -> None:
        """Test parsing natural language operators."""
        test_cases = [
            "Set `check` to x is equal to y.",
            "Set `check` to a is not equal to b.",
            "Set `check` to m is less than n.",
            "Set `check` to p is greater than q.",
        ]

        for code in test_cases:
            tree = self.parser.parse(code)
            assert tree is not None
