from machine_dialect.ast import BooleanLiteral
from machine_dialect.lexer import Token, TokenType


class TestBooleanLiteral:
    def test_boolean_literal_true_display(self) -> None:
        """Test that BooleanLiteral displays True with underscores."""
        token = Token(TokenType.LIT_TRUE, "True", 1, 0)
        literal = BooleanLiteral(token, True)

        assert str(literal) == "_True_"

    def test_boolean_literal_false_display(self) -> None:
        """Test that BooleanLiteral displays False with underscores."""
        token = Token(TokenType.LIT_FALSE, "False", 1, 0)
        literal = BooleanLiteral(token, False)

        assert str(literal) == "_False_"

    def test_boolean_literal_value(self) -> None:
        """Test that BooleanLiteral stores the correct boolean value."""
        true_token = Token(TokenType.LIT_TRUE, "True", 1, 0)
        true_literal = BooleanLiteral(true_token, True)

        false_token = Token(TokenType.LIT_FALSE, "False", 1, 0)
        false_literal = BooleanLiteral(false_token, False)

        assert true_literal.value is True
        assert false_literal.value is False
