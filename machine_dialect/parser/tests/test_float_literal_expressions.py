"""Tests for parsing float literal expressions."""

import pytest

from machine_dialect.ast import ExpressionStatement
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_literal_expression,
    assert_program_statements,
)


class TestFloatLiteralExpressions:
    """Test cases for parsing float literal expressions."""

    @pytest.mark.parametrize(
        "source,expected_value",
        [
            # Simple floats
            ("0.0", 0.0),
            ("1.0", 1.0),
            ("3.14", 3.14),
            ("2.71", 2.71),
            # Floats without leading zero
            (".5", 0.5),
            (".25", 0.25),
            (".125", 0.125),
            # Floats with many decimal places
            ("3.14159", 3.14159),
            ("2.71828", 2.71828),
            ("0.123456789", 0.123456789),
            # Large floats
            ("123.456", 123.456),
            ("9999.9999", 9999.9999),
            ("1000000.0", 1000000.0),
            # Small floats
            ("0.001", 0.001),
            ("0.0001", 0.0001),
            ("0.00001", 0.00001),
            # Edge cases
            ("999999999.999999999", 999999999.999999999),
            # Floats with underscores (one on each side)
            ("_3.14_", 3.14),
            ("_0.5_", 0.5),
            ("_1.0_", 1.0),
            ("_123.456_", 123.456),
            ("_.25_", 0.25),
            ("_0.001_", 0.001),
            ("_0.0_", 0.0),
        ],
    )
    def test_float_literal_expression(self, source: str, expected_value: float) -> None:
        """Test parsing various float literal expressions.

        Args:
            source: The source code to parse.
            expected_value: The expected float value.
        """
        parser = Parser()

        program = parser.parse(source)

        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, expected_value)

    def test_float_with_period(self) -> None:
        """Test parsing float literal followed by period."""
        source = "3.14."
        parser = Parser()

        program = parser.parse(source)

        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, 3.14)

    def test_multiple_float_statements(self) -> None:
        """Test parsing multiple float literal statements."""
        source = "1.1. 2.2. 3.3."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 3

        # Check each statement
        for i, expected_value in enumerate([1.1, 2.2, 3.3]):
            statement = program.statements[i]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None
            assert_literal_expression(statement.expression, expected_value)

    @pytest.mark.parametrize(
        "source,error_substring",
        [
            # Underscore only on left side
            ("_3.14", "_3.14"),
            ("_0.5", "_0.5"),
            ("_123.456", "_123.456"),
            ("_.25", "_.25"),
            # Underscore only on right side
            ("3.14_", "3.14_"),
            ("0.5_", "0.5_"),
            ("123.456_", "123.456_"),
            (".25_", ".25_"),
            # Multiple underscores
            ("__3.14__", "__3.14__"),
            ("___0.5___", "___0.5___"),
            ("__123.456__", "__123.456__"),
            # Mixed multiple and single
            ("__3.14_", "__3.14_"),
            ("_3.14__", "_3.14__"),
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

    def test_mixed_integer_and_float_statements(self) -> None:
        """Test parsing mixed integer and float literal statements."""
        source = "42. 3.14. 100. 0.5."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 4

        # Check each statement with expected values and types
        expected_values = [42, 3.14, 100, 0.5]
        for i, expected_value in enumerate(expected_values):
            statement = program.statements[i]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None
            assert_literal_expression(statement.expression, expected_value)
