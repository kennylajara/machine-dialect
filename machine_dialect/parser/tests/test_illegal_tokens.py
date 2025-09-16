"""Tests for parser handling of illegal tokens.

This module tests that the parser correctly reports MDSyntaxError
(not MDNameError) when encountering MISC_ILLEGAL tokens from the lexer.
"""

from machine_dialect.errors.exceptions import MDSyntaxError
from machine_dialect.parser import Parser


class TestIllegalTokenHandling:
    """Test that illegal tokens are reported as syntax errors."""

    def test_malformed_underscore_literal_syntax_error(self) -> None:
        """Test that malformed underscore literals produce syntax errors."""
        source = 'Define `x` as Whole Number. Set `x` to _"unclosed.'
        parser = Parser()

        parser.parse(source)

        # Should have one syntax error for the illegal token
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "Illegal token" in str(parser.errors[0])
        assert '_"unclosed.' in str(parser.errors[0])

    def test_multiple_underscores_with_number(self) -> None:
        """Test that invalid underscore patterns produce syntax errors."""
        source = "Define `x` as Whole Number. Set `x` to __42."
        parser = Parser()

        parser.parse(source)

        # Should have one syntax error for the illegal token
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "Illegal token" in str(parser.errors[0])
        assert "__42" in str(parser.errors[0])

    def test_trailing_underscore_after_number(self) -> None:
        """Test that numbers with trailing underscores produce syntax errors."""
        source = "Define `x` as Whole Number. Set `x` to 42_."
        parser = Parser()

        parser.parse(source)

        # Should have one syntax error for the illegal token
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "Illegal token" in str(parser.errors[0])
        assert "42_" in str(parser.errors[0])

    def test_incomplete_underscore_wrapped_number(self) -> None:
        """Test that incomplete underscore-wrapped numbers produce syntax errors."""
        source = "Define `x` as Whole Number. Set `x` to _42."
        parser = Parser()

        parser.parse(source)

        # Should have one syntax error for the illegal token
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "Illegal token" in str(parser.errors[0])
        assert "_42" in str(parser.errors[0])

    def test_recovery_after_illegal_token(self) -> None:
        """Test that parser recovers and continues after illegal tokens."""
        source = "Define `x` as Whole Number. Define `y` as Whole Number. Set `x` to _42. Set `y` to _10_."
        parser = Parser()

        program = parser.parse(source)

        # Should have one syntax error for the first illegal token
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "_42" in str(parser.errors[0])

        # Should have parsed four statements (2 Define + 2 Set)
        assert len(program.statements) == 4
        # First two are Define statements
        assert program.statements[0] is not None
        assert program.statements[1] is not None
        # Third statement (Set with _42) has an error
        assert program.statements[2] is not None
        # Fourth statement should be complete (10 is properly wrapped)
        assert program.statements[3] is not None
