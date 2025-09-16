"""Tests for parser error handling.

This module tests the parser's ability to collect and report errors
from the lexer, including lexical errors like illegal characters.
"""

from machine_dialect.errors.exceptions import MDSyntaxError
from machine_dialect.parser import Parser


class TestParserErrors:
    """Test cases for parser error handling."""

    def test_parser_collects_lexer_errors(self) -> None:
        """Test that parser reports errors for illegal tokens during parsing."""
        # Source with illegal character
        source = "Define `X` as Empty. Set `X` to @."
        # Lexer instantiation moved to Parser.parse()
        parser = Parser()

        # Errors are reported during parsing, not before
        parser.parse(source)

        # Parser should have reported the error for @ as a syntax error (illegal token)
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "@" in str(parser.errors[0])

    def test_parser_has_errors_method(self) -> None:
        """Test the has_errors() method."""
        # Valid source - no errors
        source = "Define `X` as Whole Number. Set `X` to 42."
        parser = Parser()
        parser.parse(source)

        assert parser.has_errors() is False
        assert len(parser.errors) == 0

        # Invalid source - with illegal character
        source_with_error = "Define `Y` as Empty. Set `Y` to §."  # § is not a valid token
        parser_with_error = Parser()
        parser_with_error.parse(source_with_error)

        assert parser_with_error.has_errors() is True
        assert len(parser_with_error.errors) == 1

    def test_parser_collects_multiple_errors(self) -> None:
        """Test that parser reports multiple errors through panic recovery."""
        # Source with multiple illegal characters - periods are mandatory
        source = (
            "Define `A` as Empty. Define `B` as Empty. Define `C` as Empty. Set `A` to @. Set `B` to $. Set `C` to %."
        )
        parser = Parser()
        parser.parse(source)

        # Should have 3 errors for illegal characters (all syntax errors)
        assert len(parser.errors) == 3
        assert all(isinstance(error, MDSyntaxError) for error in parser.errors)

        # Check that all illegal characters are in the errors
        error_messages = [str(error) for error in parser.errors]
        assert any("@" in msg for msg in error_messages)
        assert any("$" in msg for msg in error_messages)
        assert any("%" in msg for msg in error_messages)

    def test_parser_continues_after_lexer_errors(self) -> None:
        """Test that parser continues parsing despite lexer errors."""
        # Source with an error but valid structure
        source = "Define `X` as Empty. Define `result` as Whole Number. Set `X` to @. Set `result` to _123_."
        # Lexer instantiation moved to Parser.parse()
        parser = Parser()

        # Parse the program
        program = parser.parse(source)

        # Should have one error for illegal character
        assert parser.has_errors() is True
        assert len(parser.errors) == 1

        # But should still parse the valid statements
        assert len(program.statements) == 4  # 2 defines + 2 sets
        # Type assertions to help mypy
        from machine_dialect.ast import DefineStatement, SetStatement

        assert isinstance(program.statements[0], DefineStatement)
        assert isinstance(program.statements[1], DefineStatement)
        assert isinstance(program.statements[2], SetStatement)
        assert isinstance(program.statements[3], SetStatement)
        assert program.statements[2].name is not None
        assert program.statements[2].name.value == "X"
        assert program.statements[3].name is not None
        assert program.statements[3].name.value == "result"

    def test_empty_source_no_errors(self) -> None:
        """Test that empty source produces no errors."""
        source = ""
        parser = Parser()

        program = parser.parse(source)

        assert parser.has_errors() is False
        assert len(parser.errors) == 0
        assert len(program.statements) == 0

    def test_parser_error_details(self) -> None:
        """Test that parser errors contain correct location information."""
        source = "Define `X` as Empty. Set `X` to &."
        parser = Parser()
        parser.parse(source)

        assert len(parser.errors) == 1
        error = parser.errors[0]

        # Check error has location information
        assert hasattr(error, "_line")
        assert hasattr(error, "_column")
        assert error._line == 1  # First line
        assert error._column > 0  # Should have a column position
