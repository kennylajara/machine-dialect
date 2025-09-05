from machine_dialect.lexer.tokens import Token, TokenType


class TestToken:
    def test_token_with_line_and_position(self) -> None:
        """Test that Token includes line and position information."""
        token = Token(type=TokenType.MISC_IDENT, literal="test", line=1, position=1)

        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "test"
        assert token.line == 1
        assert token.position == 1

    def test_token_string_representation_with_location(self) -> None:
        """Test string representation includes line and position."""
        token = Token(type=TokenType.KW_IF, literal="if", line=5, position=10)

        expected = "Type: TokenType.KW_IF, Literal: if, Line: 5, Position: 10"
        assert str(token) == expected

    def test_token_equality_with_location(self) -> None:
        """Test that tokens are equal if all attributes match."""
        token1 = Token(type=TokenType.LIT_WHOLE_NUMBER, literal="42", line=1, position=1)
        token2 = Token(type=TokenType.LIT_WHOLE_NUMBER, literal="42", line=1, position=1)
        token3 = Token(
            type=TokenType.LIT_WHOLE_NUMBER,
            literal="42",
            line=2,  # Different line
            position=1,
        )

        assert token1 == token2
        assert token1 != token3

    def test_token_creation_with_defaults(self) -> None:
        """Test Token creation with default line and position values."""
        # This test assumes we might want default values for backward compatibility
        token = Token(type=TokenType.OP_PLUS, literal="+", line=1, position=1)

        assert token.line == 1
        assert token.position == 1
