"""AST nodes for expression types in Machine Dialect.

This module defines the expression nodes used in the Abstract Syntax Tree (AST)
for Machine Dialect. Expressions are constructs that can be evaluated to produce
a value, unlike statements which perform actions.

Expressions include:
- Identifier: Variable names and references
- Literals: Numbers, strings, booleans (to be added)
- Operations: Mathematical, logical, and other operations (to be added)
"""

from machine_dialect.ast import ASTNode
from machine_dialect.lexer import Token


class Expression(ASTNode):
    """Base class for all expression nodes in the AST.

    An expression represents a construct that can be evaluated to produce
    a value. This includes identifiers, literals, operations, and function calls.
    """

    def __init__(self, token: Token) -> None:
        """Initialize an Expression node.

        Args:
            token: The token that begins this expression.
        """
        self.token = token


class Identifier(Expression):
    """An identifier expression representing a variable or name.

    Identifiers are names that refer to variables, functions, or other
    named entities in the program. In Machine Dialect, identifiers can
    be written with or without backticks (e.g., `x` or x).

    Attributes:
        value: The string value of the identifier name.
    """

    def __init__(self, token: Token, value: str) -> None:
        """Initialize an Identifier node.

        Args:
            token: The token containing the identifier.
            value: The string value of the identifier name.
        """
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        """Return the string representation of the identifier.

        Returns:
            The identifier wrapped in backticks, e.g., "`variable`".
        """
        return f"`{self.value}`"
