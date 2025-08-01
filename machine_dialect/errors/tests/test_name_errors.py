"""Tests for parser error handling.

This module tests the parser's ability to collect and report errors
from the lexer, including lexical errors like illegal characters.
"""

from machine_dialect.errors.exceptions import MDNameError
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser


class TestParserErrors:
    """Test cases for parser error handling."""

    def test_parser_collects_lexer_errors(self) -> None:
        """Test that parser collects errors from the lexer."""
        # Source with illegal character
        source = "Set `X` to @"
        lexer = Lexer(source)
        parser = Parser(lexer)

        # Parser should have collected the error
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDNameError)
        assert "@" in str(parser.errors[0])

    def test_parser_has_errors_method(self) -> None:
        """Test the has_errors() method."""
        # Valid source - no errors
        source = "Set `X` to 42"
        lexer = Lexer(source)
        parser = Parser(lexer)

        assert parser.has_errors() is False
        assert len(parser.errors) == 0

        # Invalid source - with illegal character
        source_with_error = "Set `Y` to §"  # § is not a valid token
        lexer_with_error = Lexer(source_with_error)
        parser_with_error = Parser(lexer_with_error)

        assert parser_with_error.has_errors() is True
        assert len(parser_with_error.errors) == 1

    def test_parser_collects_multiple_errors(self) -> None:
        """Test that parser collects multiple errors from the lexer."""
        # Source with multiple illegal characters
        source = "Set `A` to @ Set `B` to $ Set `C` to %"
        lexer = Lexer(source)
        parser = Parser(lexer)

        # Should have 3 errors for illegal characters
        assert len(parser.errors) == 3
        assert all(isinstance(error, MDNameError) for error in parser.errors)

        # Check that all illegal characters are in the errors
        error_messages = [str(error) for error in parser.errors]
        assert any("@" in msg for msg in error_messages)
        assert any("$" in msg for msg in error_messages)
        assert any("%" in msg for msg in error_messages)

    def test_parser_continues_after_lexer_errors(self) -> None:
        """Test that parser continues parsing despite lexer errors."""
        # Source with an error but valid structure
        source = "Set `X` to @ Set `Y` to 123"
        lexer = Lexer(source)
        parser = Parser(lexer)

        # Parse the program
        program = parser.parse()

        # Should have one error for illegal character
        assert parser.has_errors() is True
        assert len(parser.errors) == 1

        # But should still parse the valid statements
        assert len(program.statements) == 2
        # Type assertions to help mypy
        from machine_dialect.ast import SetStatement

        assert isinstance(program.statements[0], SetStatement)
        assert isinstance(program.statements[1], SetStatement)
        assert program.statements[0].name is not None
        assert program.statements[0].name.value == "X"
        assert program.statements[1].name is not None
        assert program.statements[1].name.value == "Y"

    def test_empty_source_no_errors(self) -> None:
        """Test that empty source produces no errors."""
        source = ""
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert parser.has_errors() is False
        assert len(parser.errors) == 0
        assert len(program.statements) == 0

    def test_parser_error_details(self) -> None:
        """Test that parser errors contain correct location information."""
        source = "Set `X` to &"
        lexer = Lexer(source)
        parser = Parser(lexer)

        assert len(parser.errors) == 1
        error = parser.errors[0]

        # Check error has location information
        assert hasattr(error, "_line")
        assert hasattr(error, "_column")
        assert error._line == 1  # First line
        assert error._column > 0  # Should have a column position
