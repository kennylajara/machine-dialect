"""Literal expression AST nodes for Machine Dialect."""

from machine_dialect.ast import Expression
from machine_dialect.lexer import Token


class IntegerLiteral(Expression):
    """Represents an integer literal expression."""

    def __init__(self, token: Token, value: int) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        return f"_{self.value}_"


class FloatLiteral(Expression):
    """Represents a float literal expression."""

    def __init__(self, token: Token, value: float) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        return f"_{self.value}_"


class StringLiteral(Expression):
    """Represents a string literal expression."""

    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        # The value includes the quotes
        return f"_{self.value}_"
