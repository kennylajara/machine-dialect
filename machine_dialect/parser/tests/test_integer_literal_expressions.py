"""Tests for parsing integer literal expressions."""

import pytest

from machine_dialect.ast import ExpressionStatement
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_literal_expression,
    assert_program_statements,
)


class TestWholeNumberLiteralExpressions:
    """Test cases for parsing integer literal expressions."""

    @pytest.mark.parametrize(
        "source,expected_value",
        [
            # Single digit integers
            ("0", 0),
            ("1", 1),
            ("5", 5),
            ("9", 9),
            # Multi-digit integers
            ("10", 10),
            ("42", 42),
            ("123", 123),
            ("999", 999),
            # Large integers
            ("1000", 1000),
            ("12345", 12345),
            ("99999", 99999),
            ("1000000", 1000000),
            # Edge cases
            ("2147483647", 2147483647),  # Max 32-bit signed int
            ("9223372036854775807", 9223372036854775807),  # Max 64-bit signed int
            # Integers with underscores (one on each side)
            ("_42_", 42),
            ("_123_", 123),
            ("_1_", 1),
            ("_999_", 999),
            ("_12345_", 12345),
            ("_0_", 0),
        ],
    )
    def test_integer_literal_expression(self, source: str, expected_value: int) -> None:
        """Test parsing various integer literal expressions.

        Args:
            source: The source code to parse.
            expected_value: The expected integer value.
        """
        parser = Parser()

        program = parser.parse(source)

        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, expected_value)

    def test_integer_with_period(self) -> None:
        """Test parsing integer literal followed by period."""
        source = "42."
        parser = Parser()

        program = parser.parse(source)

        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, 42)

    def test_multiple_integer_statements(self) -> None:
        """Test parsing multiple integer literal statements."""
        source = "1. 2. 3."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 3

        # Check each statement
        for i, expected_value in enumerate([1, 2, 3]):
            statement = program.statements[i]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None
            assert_literal_expression(statement.expression, expected_value)

    @pytest.mark.parametrize(
        "source,error_substring",
        [
            # Underscore only on left side
            ("_42", "_42"),
            ("_123", "_123"),
            ("_1", "_1"),
            # Underscore only on right side
            ("42_", "42_"),
            ("123_", "123_"),
            ("1_", "1_"),
            # Multiple underscores
            ("__42__", "__42__"),
            ("___123___", "___123___"),
            ("__1__", "__1__"),
            # Mixed multiple and single
            ("__42_", "__42_"),
            ("_42__", "_42__"),
        ],
    )
    def test_invalid_underscore_formats_produce_errors(self, source: str, error_substring: str) -> None:
        """Test that invalid underscore formats produce lexer errors.

        Args:
            source: The source code with invalid underscore format.
            error_substring: Expected substring in the error message.
        """
        # Lexer instantiation moved to Parser.parse()
        parser = Parser()

        # Parse the program (parser collects lexer errors)
        _ = parser.parse(source)

        # Should have at least one error
        assert len(parser.errors) >= 1, f"Expected error for invalid format: {source}"

        # Check that the error mentions the invalid token
        error_messages = [str(error) for error in parser.errors]
        assert any(error_substring in msg for msg in error_messages), (
            f"Expected error to mention '{error_substring}', got errors: {error_messages}"
        )
