"""AST nodes for statement types in Machine Dialect.

This module defines the statement nodes used in the Abstract Syntax Tree (AST)
for Machine Dialect. Statements are complete units of execution that perform
actions but don't produce values (unlike expressions).

Statements include:
- ExpressionStatement: Wraps an expression as a statement
- ReturnStatement: Returns a value from a function or procedure
- SetStatement: Assigns a value to a variable
- ErrorStatement: Represents a statement that failed to parse
"""

from machine_dialect.ast import ASTNode, Expression, Identifier
from machine_dialect.lexer import Token


class Statement(ASTNode):
    """Base class for all statement nodes in the AST.

    A statement represents a complete unit of execution in the program.
    Unlike expressions, statements don't produce values but perform actions.
    """

    def __init__(self, token: Token) -> None:
        """Initialize a Statement node.

        Args:
            token: The token that begins this statement.
        """
        self.token = token


class ExpressionStatement(Statement):
    """A statement that wraps an expression.

    Expression statements allow expressions to be used as statements.
    For example, a function call like `print("Hello")` is an expression
    that becomes a statement when used on its own line.

    Attributes:
        expression: The expression being wrapped as a statement.
    """

    def __init__(self, token: Token, expression: Expression | None) -> None:
        """Initialize an ExpressionStatement node.

        Args:
            token: The first token of the expression.
            expression: The expression to wrap as a statement.
        """
        super().__init__(token)
        self.expression = expression

    def __str__(self) -> str:
        """Return the string representation of the expression statement.

        Returns:
            The string representation of the wrapped expression.
        """
        return str(self.expression)


class ReturnStatement(Statement):
    """A return statement that exits a function with an optional value.

    Return statements are used to exit from a function or procedure,
    optionally providing a value to return to the caller.

    Attributes:
        return_value: The expression whose value to return, or None for void return.
    """

    def __init__(self, token: Token, return_value: Expression | None = None) -> None:
        """Initialize a ReturnStatement node.

        Args:
            token: The 'return' or 'Return' token.
            return_value: Optional expression to evaluate and return.
        """
        super().__init__(token)
        self.return_value = return_value

    def __str__(self) -> str:
        """Return the string representation of the return statement.

        Returns:
            A string like "\nReturn <value>" or "\nReturn" for void returns.
        """
        out = f"\n{self.token.literal}"
        if self.return_value:
            out += f" {self.return_value}"
        return out


class SetStatement(Statement):
    """A statement that assigns a value to a variable.

    Set statements follow the natural language pattern: "Set <variable> to <value>".
    They are the primary way to assign values to variables in Machine Dialect.

    Attributes:
        name: The identifier (variable name) to assign to.
        value: The expression whose value to assign.
    """

    def __init__(self, token: Token, name: Identifier | None = None, value: Expression | None = None) -> None:
        """Initialize a SetStatement node.

        Args:
            token: The 'Set' token that begins the statement.
            name: The identifier to assign to.
            value: The expression whose value to assign.
        """
        super().__init__(token)
        self.name = name
        self.value = value

    def __str__(self) -> str:
        """Return the string representation of the set statement.

        Returns:
            A string like "Set <name> to <value>".
        """
        out = f"{self.token.literal} "
        if self.name:
            out += f"{self.name} "
        out += "to "
        if self.value:
            out += str(self.value)
        return out


class ErrorStatement(Statement):
    """A statement that failed to parse correctly.

    ErrorStatements preserve the AST structure even when parsing fails,
    allowing the parser to continue and collect multiple errors. They
    contain the tokens that were skipped during panic-mode recovery.

    Attributes:
        skipped_tokens: List of tokens that were skipped during panic recovery.
        message: Human-readable error message describing what went wrong.
    """

    def __init__(self, token: Token, skipped_tokens: list[Token] | None = None, message: str = "") -> None:
        """Initialize an ErrorStatement node.

        Args:
            token: The token where the error began.
            skipped_tokens: Tokens that were skipped during panic recovery.
            message: Error message describing the parsing failure.
        """
        super().__init__(token)
        self.skipped_tokens = skipped_tokens or []
        self.message = message

    def __str__(self) -> str:
        """Return the string representation of the error statement.

        Returns:
            A string like "<error: message>".
        """
        if self.message:
            return f"<error: {self.message}>"
        return "<error>"
