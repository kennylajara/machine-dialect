from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import Token, TokenType


class TestLexerPosition:
    def test_single_line_positions(self) -> None:
        """Test that tokens on a single line have correct positions."""
        source = "Set x = 42"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=0),
            Token(TokenType.MISC_IDENT, "x", line=1, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=6),
            Token(TokenType.LIT_INT, "42", line=1, position=8),
        ]

        assert tokens == expected

    def test_multiline_positions(self) -> None:
        """Test that tokens across multiple lines have correct line numbers."""
        source = """if True then
    give back 42
else
    gives back 0"""

        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        expected = [
            Token(TokenType.KW_IF, "if", line=1, position=0),
            Token(TokenType.LIT_TRUE, "True", line=1, position=3),
            Token(TokenType.KW_THEN, "then", line=1, position=8),
            Token(TokenType.KW_RETURN, "give back", line=2, position=4),
            Token(TokenType.LIT_INT, "42", line=2, position=14),
            Token(TokenType.KW_ELSE, "else", line=3, position=0),
            Token(TokenType.KW_RETURN, "gives back", line=4, position=4),
            Token(TokenType.LIT_INT, "0", line=4, position=15),
        ]

        assert tokens == expected

    def test_string_literal_position(self) -> None:
        """Test that string literals maintain correct position."""
        source = 'Set msg = "hello world"'
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=0),
            Token(TokenType.MISC_IDENT, "msg", line=1, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=8),
            Token(TokenType.LIT_TEXT, '"hello world"', line=1, position=10),
        ]

        assert tokens == expected

    def test_empty_lines_position(self) -> None:
        """Test position tracking with empty lines."""
        source = """Set x = 1

Set y = 2"""

        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=0),
            Token(TokenType.MISC_IDENT, "x", line=1, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=6),
            Token(TokenType.LIT_INT, "1", line=1, position=8),
            Token(TokenType.KW_SET, "Set", line=3, position=0),
            Token(TokenType.MISC_STOPWORD, "y", line=3, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=3, position=6),
            Token(TokenType.LIT_INT, "2", line=3, position=8),
        ]

        assert tokens == expected

    def test_tab_position(self) -> None:
        """Test position tracking with tabs."""
        source = "Set\tx\t=\t42"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # Tabs count as single characters for position
        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=0),
            Token(TokenType.MISC_IDENT, "x", line=1, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=6),
            Token(TokenType.LIT_INT, "42", line=1, position=8),
        ]

        assert tokens == expected

    def test_illegal_character_position(self) -> None:
        """Test that illegal characters have correct position."""
        source = "Set x = @"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        # We expect one error for the illegal character
        assert len(errors) == 1, f"Expected 1 error, got {len(errors)}: {errors}"
        assert "@" in str(errors[0])

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=0),
            Token(TokenType.MISC_IDENT, "x", line=1, position=4),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=6),
            Token(TokenType.MISC_ILLEGAL, "@", line=1, position=8),
        ]

        assert tokens == expected
