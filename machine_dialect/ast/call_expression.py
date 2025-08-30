"""CallExpression AST node for function calls that return values."""

from __future__ import annotations

from typing import TYPE_CHECKING

from machine_dialect.ast.expressions import Expression

if TYPE_CHECKING:
    from machine_dialect.lexer import Token


class CallExpression(Expression):
    """A function call expression that returns a value.

    CallExpression represents a function invocation that produces a value,
    used in contexts where an expression is expected (e.g., in assignments
    with 'using', or as part of larger expressions).

    This is distinct from CallStatement, which represents standalone function
    calls that don't necessarily return values.

    Attributes:
        function_name: The identifier or expression that names the function.
        arguments: Optional Arguments node containing the function arguments.
    """

    def __init__(
        self, token: Token, function_name: Expression | None = None, arguments: Expression | None = None
    ) -> None:
        """Initialize a CallExpression node.

        Args:
            token: The token that begins the call (typically the function name).
            function_name: The expression identifying the function to call.
            arguments: Optional Arguments node containing the function arguments.
        """
        super().__init__(token)
        self.function_name = function_name
        self.arguments = arguments

    def token_literal(self) -> str:
        """Return the literal value of the call token.

        Returns:
            The literal value of the token.
        """
        return self.token.literal

    def __str__(self) -> str:
        """Return string representation of the call expression.

        Returns:
            A string showing the function call with its arguments.
        """
        parts = []

        if self.function_name:
            parts.append(str(self.function_name))

        if self.arguments:
            parts.append(f"({self.arguments})")
        else:
            parts.append("()")

        return "".join(parts)

    def desugar(self) -> CallExpression:
        """Desugar the call expression.

        Returns:
            A new CallExpression with desugared components.
        """
        desugared = CallExpression(self.token)

        if self.function_name:
            desugared.function_name = self.function_name.desugar()

        if self.arguments:
            desugared.arguments = self.arguments.desugar()

        return desugared
