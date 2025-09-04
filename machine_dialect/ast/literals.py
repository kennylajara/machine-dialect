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

    def desugar(self) -> "IntegerLiteral":
        """Integer literals are already in simplest form.

        Returns:
            Self unchanged.
        """
        return self


class FloatLiteral(Expression):
    """Represents a float literal expression."""

    def __init__(self, token: Token, value: float) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        return f"_{self.value}_"

    def desugar(self) -> "FloatLiteral":
        """Float literals are already in simplest form.

        Returns:
            Self unchanged.
        """
        return self


class StringLiteral(Expression):
    """Represents a string literal expression."""

    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        # The value includes the quotes
        return f"_{self.value}_"

    def desugar(self) -> "StringLiteral":
        """String literals are already in simplest form.

        Returns:
            Self unchanged.
        """
        return self


class BooleanLiteral(Expression):
    """Represents a boolean literal expression."""

    def __init__(self, token: Token, value: bool) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        return f"_{self.value}_"

    def desugar(self) -> "BooleanLiteral":
        """Boolean literals are already normalized by lexer.

        Returns:
            Self unchanged.
        """
        return self


class EmptyLiteral(Expression):
    """Represents an empty/null literal expression."""

    def __init__(self, token: Token) -> None:
        super().__init__(token)
        self.value = None

    def __str__(self) -> str:
        return "empty"

    def desugar(self) -> "EmptyLiteral":
        """Empty literals represent null/none values.

        Returns:
            Self unchanged (already canonical).
        """
        return self


class URLLiteral(Expression):
    """Represents a URL literal expression."""

    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores and quotes for the new syntax
        # Add quotes for display even though the value doesn't include them
        return f'_"{self.value}"_'

    def desugar(self) -> "URLLiteral":
        """URL literals are already in simplest form.

        Returns:
            Self unchanged.
        """
        return self
