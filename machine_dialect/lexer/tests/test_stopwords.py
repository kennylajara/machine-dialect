import pytest

from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tests.helpers import stream_and_assert_tokens
from machine_dialect.lexer.tokens import Token, TokenType


class TestStopwords:
    @pytest.mark.parametrize(
        "input_text,expected_tokens",
        [
            # Common stopwords
            ("the", [Token(TokenType.MISC_STOPWORD, "the", line=1, position=1)]),
            ("a", [Token(TokenType.MISC_STOPWORD, "a", line=1, position=1)]),
            ("an", [Token(TokenType.MISC_STOPWORD, "an", line=1, position=1)]),
            ("on", [Token(TokenType.MISC_STOPWORD, "on", line=1, position=1)]),
            ("at", [Token(TokenType.MISC_STOPWORD, "at", line=1, position=1)]),
            ("by", [Token(TokenType.MISC_STOPWORD, "by", line=1, position=1)]),
            ("about", [Token(TokenType.MISC_STOPWORD, "about", line=1, position=1)]),
            ("against", [Token(TokenType.MISC_STOPWORD, "against", line=1, position=1)]),
            ("between", [Token(TokenType.MISC_STOPWORD, "between", line=1, position=1)]),
            ("into", [Token(TokenType.MISC_STOPWORD, "into", line=1, position=1)]),
            ("through", [Token(TokenType.MISC_STOPWORD, "through", line=1, position=1)]),
            ("during", [Token(TokenType.MISC_STOPWORD, "during", line=1, position=1)]),
            ("before", [Token(TokenType.MISC_STOPWORD, "before", line=1, position=1)]),
            ("after", [Token(TokenType.MISC_STOPWORD, "after", line=1, position=1)]),
            ("above", [Token(TokenType.MISC_STOPWORD, "above", line=1, position=1)]),
            ("below", [Token(TokenType.MISC_STOPWORD, "below", line=1, position=1)]),
            ("up", [Token(TokenType.MISC_STOPWORD, "up", line=1, position=1)]),
            ("down", [Token(TokenType.MISC_STOPWORD, "down", line=1, position=1)]),
            ("out", [Token(TokenType.MISC_STOPWORD, "out", line=1, position=1)]),
            ("off", [Token(TokenType.MISC_STOPWORD, "off", line=1, position=1)]),
            ("over", [Token(TokenType.MISC_STOPWORD, "over", line=1, position=1)]),
            ("under", [Token(TokenType.MISC_STOPWORD, "under", line=1, position=1)]),
            ("again", [Token(TokenType.MISC_STOPWORD, "again", line=1, position=1)]),
            ("further", [Token(TokenType.MISC_STOPWORD, "further", line=1, position=1)]),
            ("once", [Token(TokenType.MISC_STOPWORD, "once", line=1, position=1)]),
            # Case-insensitive stopword detection
            ("The", [Token(TokenType.MISC_STOPWORD, "The", line=1, position=1)]),
            ("THE", [Token(TokenType.MISC_STOPWORD, "THE", line=1, position=1)]),
            # Non-stopwords should be identifiers
            ("variable", [Token(TokenType.MISC_IDENT, "variable", line=1, position=1)]),
            ("myfunction", [Token(TokenType.MISC_IDENT, "myfunction", line=1, position=1)]),
            ("data", [Token(TokenType.MISC_IDENT, "data", line=1, position=1)]),
        ],
    )
    def test_stopword_detection(self, input_text: str, expected_tokens: list[Token]) -> None:
        lexer = Lexer(input_text)
        stream_and_assert_tokens(lexer, expected_tokens)

    def test_stopwords_mixed_with_code(self) -> None:
        input_text = "Set the `value` to 5"
        lexer = Lexer(input_text)

        # Expected tokens: "Set" (keyword), "the" (stopword), "value" (ident), "to" (keyword), "5" (int)
        expected_tokens = [
            Token(TokenType.KW_SET, "Set", line=1, position=1),
            Token(TokenType.MISC_STOPWORD, "the", line=1, position=5),
            Token(TokenType.MISC_IDENT, "value", line=1, position=10),
            Token(TokenType.KW_TO, "to", line=1, position=17),
            Token(TokenType.LIT_WHOLE_NUMBER, "5", line=1, position=20),
        ]

        stream_and_assert_tokens(lexer, expected_tokens)

    def test_parser_ignores_stopwords(self) -> None:
        from machine_dialect.parser import Parser

        # Test that parser skips stopwords correctly
        input_text = "Define `x` as Whole Number. Set the `x` to _5_"
        parser = Parser()
        program = parser.parse(input_text)

        # The parser should skip "the" stopword and parse correctly
        assert len(program.statements) == 2  # Define + Set
        # First statement is Define, second is Set
        assert program.statements[1].token.type == TokenType.KW_SET

        # Check no parsing errors
        assert len(parser.errors) == 0
