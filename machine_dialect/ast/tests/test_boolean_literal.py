from machine_dialect.ast import YesNoLiteral
from machine_dialect.lexer import Token, TokenType


class TestBooleanLiteral:
    def test_boolean_literal_true_display(self) -> None:
        """Test that YesNoLiteral displays Yes with underscores."""
        token = Token(TokenType.LIT_YES, "Yes", 1, 0)
        literal = YesNoLiteral(token, True)

        assert str(literal) == "_Yes_"

    def test_boolean_literal_false_display(self) -> None:
        """Test that YesNoLiteral displays No with underscores."""
        token = Token(TokenType.LIT_NO, "No", 1, 0)
        literal = YesNoLiteral(token, False)

        assert str(literal) == "_No_"

    def test_boolean_literal_value(self) -> None:
        """Test that YesNoLiteral stores the correct boolean value."""
        true_token = Token(TokenType.LIT_YES, "Yes", 1, 0)
        true_literal = YesNoLiteral(true_token, True)

        false_token = Token(TokenType.LIT_NO, "No", 1, 0)
        false_literal = YesNoLiteral(false_token, False)

        assert true_literal.value is True
        assert false_literal.value is False
