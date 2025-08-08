from machine_dialect.lexer import Lexer, Token, TokenMetaType, TokenType
from machine_dialect.lexer.tests.helpers import assert_eof


def is_literal_token(token: Token) -> bool:
    return token.type.meta_type == TokenMetaType.LIT


class TestBooleanLiterals:
    def test_wrapped_true(self) -> None:
        """Test underscore-wrapped True literal."""
        source = "_True_"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_TRUE
        assert token.literal == "True"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_wrapped_false(self) -> None:
        """Test underscore-wrapped False literal."""
        source = "_False_"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_FALSE
        assert token.literal == "False"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_unwrapped_true(self) -> None:
        """Test unwrapped True literal (backward compatibility)."""
        source = "True"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_TRUE
        assert token.literal == "True"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_unwrapped_false(self) -> None:
        """Test unwrapped False literal (backward compatibility)."""
        source = "False"
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.LIT_FALSE
        assert token.literal == "False"  # Canonical form without underscores
        assert is_literal_token(token)

        assert_eof(lexer.next_token())

    def test_boolean_in_expression(self) -> None:
        """Test boolean literals in expressions."""
        source = "if x > 0 then give back _True_ else give back False"
        lexer = Lexer(source)

        # Collect all tokens
        tokens = []
        while True:
            token = lexer.next_token()
            if token.type == TokenType.MISC_EOF:
                break
            tokens.append(token)

        # Find the boolean tokens
        boolean_tokens = [t for t in tokens if t.type in (TokenType.LIT_TRUE, TokenType.LIT_FALSE)]
        assert len(boolean_tokens) == 2

        # Both booleans are stored in canonical form
        assert boolean_tokens[0].type == TokenType.LIT_TRUE
        assert boolean_tokens[0].literal == "True"

        assert boolean_tokens[1].type == TokenType.LIT_FALSE
        assert boolean_tokens[1].literal == "False"

    def test_lowercase_not_boolean(self) -> None:
        """Test that lowercase true/false are now recognized as boolean literals."""
        source = "true false"
        lexer = Lexer(source)

        # Now lowercase booleans are recognized as boolean literals
        token1 = lexer.next_token()
        assert token1.type == TokenType.LIT_TRUE
        assert token1.literal == "True"  # Canonical form

        token2 = lexer.next_token()
        assert token2.type == TokenType.LIT_FALSE
        assert token2.literal == "False"  # Canonical form

        assert_eof(lexer.next_token())

    def test_incomplete_wrapped_boolean(self) -> None:
        """Test incomplete wrapped boolean falls back to identifier."""
        source = "_True"  # Missing closing underscore
        lexer = Lexer(source)

        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "_True"
        assert not is_literal_token(token)

        assert_eof(lexer.next_token())
