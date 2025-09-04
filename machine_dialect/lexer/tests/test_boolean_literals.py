from machine_dialect.lexer import Lexer, Token, TokenMetaType, TokenType
from machine_dialect.lexer.tests.helpers import assert_eof


def is_literal_token(token: Token) -> bool:
    return token.type.meta_type == TokenMetaType.LIT


class TestBooleanLiterals:
    def test_wrapped_yes(self) -> None:
        """Test underscore-wrapped Yes literal."""
        source = "_Yes_"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_YES
        assert token.literal == "Yes"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_wrapped_no(self) -> None:
        """Test underscore-wrapped No literal."""
        source = "_No_"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_NO
        assert token.literal == "No"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_unwrapped_yes(self) -> None:
        """Test unwrapped Yes literal."""
        source = "Yes"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_YES
        assert token.literal == "Yes"
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_unwrapped_no(self) -> None:
        """Test unwrapped No literal."""
        source = "No"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_NO
        assert token.literal == "No"
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_boolean_in_expression(self) -> None:
        """Test boolean literals in expressions."""
        source = "if x > 0 then give back _Yes_ else give back No"
        lexer = Lexer(source)

        # Collect all tokens
        tokens = []
        while True:
            token = lexer.next_token()
            if token.type == TokenType.MISC_EOF:
                break
            tokens.append(token)

        # Find the boolean tokens
        boolean_tokens = [t for t in tokens if t.type in (TokenType.LIT_YES, TokenType.LIT_NO)]
        assert len(boolean_tokens) == 2

        # Both booleans are stored in canonical form
        assert boolean_tokens[0].type == TokenType.LIT_YES
        assert boolean_tokens[0].literal == "Yes"

        assert boolean_tokens[1].type == TokenType.LIT_NO
        assert boolean_tokens[1].literal == "No"

    def test_lowercase_yes_no(self) -> None:
        """Test that lowercase yes/no are recognized as boolean literals."""
        source = "yes no"
        lexer = Lexer(source)

        # Lowercase yes/no are recognized as boolean literals
        token1 = lexer.next_token()
        assert token1.type == TokenType.LIT_YES
        assert token1.literal == "Yes"  # Canonical form

        token2 = lexer.next_token()
        assert token2.type == TokenType.LIT_NO
        assert token2.literal == "No"  # Canonical form

        assert_eof(lexer.next_token())

    def test_incomplete_wrapped_boolean(self) -> None:
        """Test incomplete wrapped boolean falls back to identifier."""
        source = "_Yes"  # Missing closing underscore
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "_Yes"
        assert not is_literal_token(token)

        assert_eof(lexer.next_token())
