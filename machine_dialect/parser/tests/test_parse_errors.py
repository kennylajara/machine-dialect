"""Tests for parser error handling.

This module tests the parser's ability to properly report errors
when encountering invalid syntax or missing parse functions.
"""

import pytest

from machine_dialect.errors.exceptions import MDSyntaxError
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser


class TestParseErrors:
    """Test parsing error handling."""

    @pytest.mark.parametrize(
        "source,expected_literal",
        [
            ("* 42", "*"),  # Multiplication operator at start
            ("+ 5", "+"),  # Plus operator at start
            ("/ 10", "/"),  # Division operator at start
            (") x", ")"),  # Right parenthesis at start
            ("} x", "}"),  # Right brace at start
            (", x", ","),  # Comma at start
            ("; x", ";"),  # Semicolon at start
        ],
    )
    def test_no_prefix_parse_function_error(self, source: str, expected_literal: str) -> None:
        """Test error reporting when no prefix parse function exists.

        Args:
            source: The source code that should trigger an error.
            expected_literal: The literal that should appear in the error message.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        # Should have exactly one error
        assert len(parser.errors) == 1

        # Check the error type and message
        error = parser.errors[0]
        assert isinstance(error, MDSyntaxError)
        assert f"No parse function was found to parse '{expected_literal}'" in str(error)

        # The program should still be created
        assert program is not None
        # Parser continues after errors, so we'll have statements (but with None expressions)
        # Check that the first statement has no valid expression
        if program.statements:
            from machine_dialect.ast import ExpressionStatement

            stmt = program.statements[0]
            assert isinstance(stmt, ExpressionStatement)
            assert stmt.expression is None

    def test_multiple_parse_errors(self) -> None:
        """Test that multiple parse errors are collected."""
        source = "* 42. + 5. / 10."
        lexer = Lexer(source)
        parser = Parser(lexer)

        parser.parse()

        # Should have three errors (one for each invalid prefix)
        assert len(parser.errors) == 3

        # Check each error
        expected_literals = ["*", "+", "/"]
        for error, expected_literal in zip(parser.errors, expected_literals, strict=True):
            assert isinstance(error, MDSyntaxError)
            assert f"No parse function was found to parse '{expected_literal}'" in str(error)

    def test_error_location_tracking(self) -> None:
        """Test that errors track correct line and column positions."""
        source = "   * 42"  # 3 spaces before *
        lexer = Lexer(source)
        parser = Parser(lexer)

        _ = parser.parse()

        assert len(parser.errors) == 1
        error = parser.errors[0]

        # The * should be at column 3 (0-indexed)
        assert "column 3" in str(error)
        assert "line 1" in str(error)

    def test_valid_expression_no_errors(self) -> None:
        """Test that valid expressions don't produce parse errors."""
        valid_sources = [
            "42",
            "-42",
            "not True",
            "x",
            "`my variable`",
            "_123_",
            "True",
            "False",
        ]

        for source in valid_sources:
            lexer = Lexer(source)
            parser = Parser(lexer)

            program = parser.parse()

            # Should have no errors
            assert len(parser.errors) == 0, f"Unexpected error for source: {source}"
            assert len(program.statements) == 1
