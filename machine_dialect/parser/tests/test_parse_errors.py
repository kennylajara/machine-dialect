"""Tests for parser error handling.

This module tests the parser's ability to properly report errors
when encountering invalid syntax or missing parse functions.
"""

import pytest

from machine_dialect.errors.exceptions import MDSyntaxError
from machine_dialect.parser import Parser


class TestParseErrors:
    """Test parsing error handling."""

    @pytest.mark.parametrize(
        "source,expected_literal,expected_message",
        [
            ("* 42", "*", "unexpected token '*' at start of expression"),  # Multiplication operator at start
            ("+ 5", "+", "unexpected token '+' at start of expression"),  # Plus operator at start
            ("/ 10", "/", "unexpected token '/' at start of expression"),  # Division operator at start
            (") x", ")", "No suitable parse function was found to handle ')'"),  # Right parenthesis at start
            ("} x", "}", "No suitable parse function was found to handle '}'"),  # Right brace at start
            (", x", ",", "No suitable parse function was found to handle ','"),  # Comma at start
            ("; x", ";", "No suitable parse function was found to handle ';'"),  # Semicolon at start
        ],
    )
    def test_no_prefix_parse_function_error(self, source: str, expected_literal: str, expected_message: str) -> None:
        """Test error reporting when no prefix parse function exists.

        Args:
            source: The source code that should trigger an error.
            expected_literal: The literal that should appear in the error message.
            expected_message: The expected error message.
        """
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

        # Should have exactly one error
        assert len(parser.errors) == 1

        # Check the error type and message
        error = parser.errors[0]
        assert isinstance(error, MDSyntaxError)
        assert expected_message in str(error)

        # The program should still be created
        assert program is not None
        # Parser continues after errors, so we'll have statements with ErrorExpression
        # Check that the first statement has an error expression
        if program.statements:
            from machine_dialect.ast import ErrorExpression, ExpressionStatement

            stmt = program.statements[0]
            assert isinstance(stmt, ExpressionStatement)
            assert isinstance(stmt.expression, ErrorExpression)

    def test_multiple_parse_errors(self) -> None:
        """Test that multiple parse errors are collected."""
        source = "* 42. + 5. / 10."
        parser = Parser()

        parser.parse(source, check_semantics=False)

        # Should have three errors (one for each invalid prefix)
        assert len(parser.errors) == 3

        # Check the error messages
        expected_messages = [
            "unexpected token '*' at start of expression",
            "unexpected token '+' at start of expression",
            "unexpected token '/' at start of expression",
        ]

        for error, expected_msg in zip(parser.errors, expected_messages, strict=True):
            assert isinstance(error, MDSyntaxError)
            assert expected_msg in str(error), f"Expected '{expected_msg}' in '{error!s}'"

    def test_error_location_tracking(self) -> None:
        """Test that errors track correct line and column positions."""
        source = "   * 42"  # 3 spaces before *
        parser = Parser()

        _ = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 1
        error = parser.errors[0]

        # The * should be at column 4 (1-indexed)
        assert "column 4" in str(error)
        assert "line 1" in str(error)

    def test_valid_expression_no_errors(self) -> None:
        """Test that valid expressions don't produce parse errors."""
        valid_sources = [
            "42",
            "-42",
            "not Yes",
            "x",
            "`my variable`",
            "_123_",
            "Yes",
            "No",
        ]

        for source in valid_sources:
            parser = Parser()

            program = parser.parse(source, check_semantics=False)

            # Should have no errors
            assert len(parser.errors) == 0, f"Unexpected error for source: {source}"
            assert len(program.statements) == 1
