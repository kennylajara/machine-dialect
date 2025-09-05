from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tests.helpers import collect_all_tokens
from machine_dialect.lexer.tokens import Token, TokenType


class TestLexerPosition:
    def test_single_line_positions(self) -> None:
        """Test that tokens on a single line have correct positions."""
        source = "Set x = 42"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_IDENT, "x", line=1, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=7),
            Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=9),
        ]

        assert tokens == expected

    def test_multiline_positions(self) -> None:
        """Test that tokens across multiple lines have correct line numbers."""
        source = """if Yes then
    give back 42
else
    gives back 0"""

        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        expected = [
            Token(TokenType.KW_IF, "if", line=1, position=1),
            Token(TokenType.LIT_YES, "Yes", line=1, position=4),
            Token(TokenType.KW_THEN, "then", line=1, position=8),
            Token(TokenType.KW_RETURN, "give back", line=2, position=5),
            Token(TokenType.LIT_WHOLE_NUMBER, "42", line=2, position=15),
            Token(TokenType.KW_ELSE, "else", line=3, position=1),
            Token(TokenType.KW_RETURN, "gives back", line=4, position=5),
            Token(TokenType.LIT_WHOLE_NUMBER, "0", line=4, position=16),
        ]

        assert tokens == expected

    def test_string_literal_position(self) -> None:
        """Test that string literals maintain correct position."""
        source = 'Set msg = "hello world"'
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_IDENT, "msg", line=1, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=9),
            Token(TokenType.LIT_TEXT, '"hello world"', line=1, position=11),
        ]

        assert tokens == expected

    def test_empty_lines_position(self) -> None:
        """Test position tracking with empty lines."""
        source = """Set x = 1

Set y = 2"""

        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_IDENT, "x", line=1, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=7),
            Token(TokenType.LIT_WHOLE_NUMBER, "1", line=1, position=9),
            Token(TokenType.KW_SET, "Set", line=3, position=1),
            Token(TokenType.MISC_IDENT, "y", line=3, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=3, position=7),
            Token(TokenType.LIT_WHOLE_NUMBER, "2", line=3, position=9),
        ]

        assert tokens == expected

    def test_tab_position(self) -> None:
        """Test position tracking with tabs."""
        source = "Set\tx\t=\t42"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        # Tabs count as single characters for position
        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_IDENT, "x", line=1, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=7),
            Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=9),
        ]

        assert tokens == expected

    def test_illegal_character_position(self) -> None:
        """Test that illegal characters have correct position."""
        source = "Set x = @"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        # Lexer no longer reports errors (parser will handle them)

        expected = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_IDENT, "x", line=1, position=5),
            Token(TokenType.OP_ASSIGN, "=", line=1, position=7),
            Token(TokenType.MISC_ILLEGAL, "@", line=1, position=9),
        ]

        assert tokens == expected
