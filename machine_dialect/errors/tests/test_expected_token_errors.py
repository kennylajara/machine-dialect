"""Tests for parser expected token errors.

This module tests the parser's ability to detect and report syntax errors
when expected tokens are not found during parsing.
"""

from machine_dialect.errors.exceptions import MDNameError, MDSyntaxError
from machine_dialect.parser import Parser


class TestExpectedTokenErrors:
    """Test cases for expected token error handling."""

    def test_missing_identifier_after_set(self) -> None:
        """Test error when Set statement is missing the identifier."""
        source = "Set 42 to X"  # 42 is not a valid identifier
        parser = Parser()

        parser.parse(source)

        # Should have syntax error
        assert parser.has_errors() is True
        # With panic recovery, we get 1 error and skip to EOF (no period)
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)

        # Error should mention expected identifier
        error_msg = str(parser.errors[0])
        assert "misc_ident" in error_msg.lower() or "identifier" in error_msg.lower()

    def test_missing_to_keyword(self) -> None:
        """Test error when Set statement is missing the 'to' keyword."""
        source = "Set `X` 42"  # Missing 'to' keyword
        parser = Parser()

        parser.parse(source)

        # Should have two errors: undefined variable + syntax error
        assert parser.has_errors() is True
        assert len(parser.errors) == 2
        # First is NameError for undefined variable
        assert isinstance(parser.errors[0], MDNameError)
        # Second is the syntax error for missing 'to'
        assert isinstance(parser.errors[1], MDSyntaxError)

        # Syntax error should mention expected 'to' keyword
        error_msg = str(parser.errors[1])
        assert "TokenType.KW_TO" in error_msg or "to" in error_msg.lower()

    def test_multiple_expected_token_errors(self) -> None:
        """Test multiple expected token errors in one parse."""
        # Add periods so panic recovery stops at statement boundaries
        source = """Set 42 to X.
Set price 3.14.
Set to "hello".
"""
        parser = Parser()

        parser.parse(source)

        # Should have multiple errors (including undefined variable errors)
        assert parser.has_errors() is True
        # With periods, panic recovery allows finding syntax + name errors
        assert len(parser.errors) >= 3

        # Check for expected error types - mix of syntax and name errors
        syntax_errors = [e for e in parser.errors if isinstance(e, MDSyntaxError)]
        assert len(syntax_errors) >= 3  # At least 3 syntax errors from malformed Set statements

    def test_empty_identifier(self) -> None:
        """Test error with empty backtick identifier."""
        source = "Set `` to 42"  # Empty backticks produce illegal tokens
        parser = Parser()

        parser.parse(source)

        # Should have errors (from lexer producing illegal tokens)
        # Empty backticks produce two illegal backtick characters
        assert parser.has_errors() is True

    def test_unclosed_backtick(self) -> None:
        """Test error with unclosed backtick identifier."""
        source = "Set `X to 42"  # Missing closing backtick
        parser = Parser()

        parser.parse(source)

        # Should have an error (either from lexer or parser)
        assert parser.has_errors() is True

    def test_error_location_info(self) -> None:
        """Test that expected token errors have correct location information."""
        source = "Set 42 to X"  # Error at position of 42
        parser = Parser()

        parser.parse(source)

        # With panic recovery, we get 1 syntax error
        assert len(parser.errors) >= 1
        # Find the syntax error (not name error)
        error = None
        for e in parser.errors:
            if isinstance(e, MDSyntaxError):
                error = e
                break
        assert error is not None

        # Check that error has location information
        assert hasattr(error, "_line")
        assert hasattr(error, "_column")
        assert error._line == 1
        assert error._column == 5  # Points to '42'

    def test_error_message_content(self) -> None:
        """Test that error messages contain helpful information."""
        source = "Set `X` something"  # 'to' keyword missing
        parser = Parser()

        parser.parse(source)

        assert len(parser.errors) == 2  # Name error + syntax error
        # Get the syntax error
        error = parser.errors[1] if isinstance(parser.errors[1], MDSyntaxError) else parser.errors[0]
        error_msg = str(error)

        # Error message should contain what was expected and what was found
        assert "expected" in error_msg.lower() or "Expected" in error_msg
        # The parser now expects 'to' after the merged identifier 'X something'
        # and finds EOF, so check for that
        assert "TokenType.KW_TO" in error_msg or "to" in error_msg.lower()

    def test_parser_continues_after_expected_token_error(self) -> None:
        """Test that parser continues parsing after encountering expected token errors."""
        source = """Set 42 to X.
Set `price` to 3.14.
Set `Z` 99.
"""
        parser = Parser()

        program = parser.parse(source)

        # Should have errors for first and third statements
        assert parser.has_errors() is True
        # We expect at least 2 errors: expected identifier in first, missing 'to' in third
        assert len(parser.errors) >= 2

        # The parser should attempt to parse all statements, even if some fail
        # Due to error recovery, we may get fewer successfully parsed statements
        # But we should get at least the valid one (second statement)
        assert len(program.statements) >= 1

        # Check that we have the valid statement
        from machine_dialect.ast import SetStatement

        valid_statements = [
            s for s in program.statements if isinstance(s, SetStatement) and s.name and s.name.value == "price"
        ]
        assert len(valid_statements) == 1

    def test_consecutive_errors(self) -> None:
        """Test handling of consecutive expected token errors."""
        source = "Set Set Set"  # Multiple Set keywords without proper syntax
        parser = Parser()

        parser.parse(source)

        # Should have multiple errors
        assert parser.has_errors() is True
        assert len(parser.errors) >= 1

    def test_eof_during_parsing(self) -> None:
        """Test error when EOF is encountered while expecting a token."""
        source = "Define `X` as Empty. Set `X`"  # Missing 'to' and value
        parser = Parser()

        parser.parse(source)

        # Should have an error for missing 'to'
        assert parser.has_errors() is True
        assert len(parser.errors) >= 1
        # Find syntax error (may not be first if there are name errors)
        syntax_errors = [e for e in parser.errors if isinstance(e, MDSyntaxError)]
        assert len(syntax_errors) >= 1
