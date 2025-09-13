"""AST nodes for expression types in Machine Dialect™.

This module defines the expression nodes used in the Abstract Syntax Tree (AST)
for Machine Dialect™. Expressions are constructs that can be evaluated to produce
a value, unlike statements which perform actions.

Expressions include:
- Identifier: Variable names and references
- Literals: Numbers, strings, booleans (to be added)
- Operations: Mathematical, logical, and other operations (to be added)
"""

from typing import Any

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

    def desugar(self) -> "Expression":
        """Default desugar for expressions returns self.

        Returns:
            The expression unchanged.
        """
        return self


class Identifier(Expression):
    """An identifier expression representing a variable or name.

    Identifiers are names that refer to variables, functions, or other
    named entities in the program. In Machine Dialect™, identifiers can
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

    def desugar(self) -> "Identifier":
        """Identifiers are already in simplest form.

        Returns:
            Self unchanged.
        """
        return self


class PrefixExpression(Expression):
    """A prefix expression with an operator applied to an expression.

    Prefix expressions consist of a prefix operator followed by an expression.
    Examples include negative numbers (-42), boolean negation (not True),
    and other unary operations.

    Attributes:
        operator: The prefix operator as a string (e.g., "-", "not").
        right: The expression that the operator is applied to.
    """

    def __init__(self, token: Token, operator: str) -> None:
        """Initialize a PrefixExpression node.

        Args:
            token: The token containing the prefix operator.
            operator: The operator string (e.g., "-", "not").
        """
        super().__init__(token)
        self.operator = operator
        self.right: Expression | None = None

    def __str__(self) -> str:
        """Return the string representation of the prefix expression.

        Returns:
            The expression in the format "(operator right)", e.g., "(-42)".
        """
        if self.operator == "not":
            return f"({self.operator} {self.right})"
        return f"({self.operator}{self.right})"

    def desugar(self) -> "PrefixExpression":
        """Desugar prefix expression by recursively desugaring operand.

        Returns:
            A new PrefixExpression with desugared right operand.
        """
        if self.right is None:
            return self

        desugared = PrefixExpression(self.token, self.operator)
        desugared.right = self.right.desugar()
        return desugared


class InfixExpression(Expression):
    """An infix expression with an operator between two expressions.

    Infix expressions consist of a left expression, an infix operator, and a
    right expression. Examples include arithmetic (5 + 3), comparisons (x > y),
    and logical operations (a and b).

    Attributes:
        left: The left operand expression.
        operator: The infix operator as a string (e.g., "+", "==", "and").
        right: The right operand expression.
    """

    # Map token types to canonical operator strings
    # Used by both desugar and canonicalize to normalize operators
    _OPERATOR_MAP = None

    @classmethod
    def _get_operator_map(cls) -> dict[Any, str]:
        """Get the operator mapping, creating it lazily if needed."""
        if cls._OPERATOR_MAP is None:
            from machine_dialect.lexer import TokenType

            cls._OPERATOR_MAP = {
                TokenType.OP_PLUS: "+",
                TokenType.OP_MINUS: "-",
                TokenType.OP_STAR: "*",
                TokenType.OP_DIVISION: "/",
                TokenType.OP_EQ: "==",
                TokenType.OP_NOT_EQ: "!=",
                TokenType.OP_STRICT_EQ: "===",
                TokenType.OP_STRICT_NOT_EQ: "!==",
                TokenType.OP_LT: "<",
                TokenType.OP_GT: ">",
                TokenType.OP_LTE: "<=",
                TokenType.OP_GTE: ">=",
                TokenType.OP_CARET: "^",
            }
        return cls._OPERATOR_MAP

    def __init__(self, token: Token, operator: str, left: Expression) -> None:
        """Initialize an InfixExpression node.

        Args:
            token: The token containing the infix operator.
            operator: The operator string (e.g., "+", "-", "==").
            left: The left-hand expression.
        """
        super().__init__(token)
        self.operator = operator
        self.left = left
        self.right: Expression | None = None

    def __str__(self) -> str:
        """Return the string representation of the infix expression.

        Returns:
            The expression in the format "(left operator right)", e.g., "(5 + 3)".
        """
        return f"({self.left} {self.operator} {self.right})"

    def desugar(self) -> "InfixExpression":
        """Desugar infix expression by normalizing operators and recursively desugaring operands.

        Normalizes operators based on their token type to symbolic equivalents.

        Returns:
            A new InfixExpression with normalized operator and desugared operands.
        """
        # Get the shared operator mapping
        operator_map = self._get_operator_map()

        # Normalize the operator based on token type
        normalized_op = operator_map.get(self.token.type, self.operator)

        # Create new expression with normalized operator
        desugared = InfixExpression(self.token, normalized_op, self.left.desugar())
        if self.right:
            desugared.right = self.right.desugar()
        return desugared


class Arguments(Expression):
    """Represents arguments for a function call.

    Arguments can be positional, named (keyword), or a mix of both.
    Positional arguments must come before named arguments.

    Attributes:
        positional: List of positional argument expressions.
        named: List of tuples (name, value) for named arguments.
    """

    def __init__(self, token: Token) -> None:
        """Initialize an Arguments node.

        Args:
            token: The token that begins the arguments (usually 'with').
        """
        super().__init__(token)
        self.positional: list[Expression] = []
        self.named: list[tuple[Identifier, Expression]] = []

    def __str__(self) -> str:
        """Return the string representation of the arguments.

        Returns:
            A comma-separated list of arguments.
        """
        parts = []
        # Add positional arguments
        for arg in self.positional:
            parts.append(str(arg))
        # Add named arguments
        for name, value in self.named:
            parts.append(f"{name}: {value}")
        return ", ".join(parts)

    def desugar(self) -> "Arguments":
        """Desugar arguments by recursively desugaring all argument expressions.

        Returns:
            A new Arguments node with desugared expressions.
        """
        desugared = Arguments(self.token)
        desugared.positional = [arg.desugar() for arg in self.positional]
        desugared.named = [
            (name.desugar() if isinstance(name, Expression) else name, value.desugar()) for name, value in self.named
        ]
        return desugared


class ConditionalExpression(Expression):
    """A conditional (ternary) expression.

    Conditional expressions evaluate to one of two values based on a condition.
    In Machine Dialect™, they follow the pattern:
    "value_if_true if/when condition, else/otherwise value_if_false"

    Attributes:
        condition: The boolean expression to evaluate.
        consequence: The expression to return if condition is true.
        alternative: The expression to return if condition is false.
    """

    def __init__(self, token: Token, consequence: Expression) -> None:
        """Initialize a ConditionalExpression node.

        Args:
            token: The token where the expression begins.
            consequence: The expression to return if condition is true.
        """
        super().__init__(token)
        self.consequence = consequence
        self.condition: Expression | None = None
        self.alternative: Expression | None = None

    def __str__(self) -> str:
        """Return the string representation of the conditional expression.

        Returns:
            The expression in the format "(consequence if condition else alternative)".
        """
        return f"({self.consequence} if {self.condition} else {self.alternative})"

    def desugar(self) -> "ConditionalExpression":
        """Desugar conditional expression by recursively desugaring all parts.

        Returns:
            A new ConditionalExpression with desugared components.
        """
        desugared = ConditionalExpression(self.token, self.consequence.desugar())
        if self.condition:
            desugared.condition = self.condition.desugar()
        if self.alternative:
            desugared.alternative = self.alternative.desugar()
        return desugared


class CollectionAccessExpression(Expression):
    """Access collection element by index or name.

    Supports multiple access patterns:
    - Ordinal access: `the first item of list`, `the second item of list`
    - Numeric access: `item _5_ of list` (one-based indexing)
    - Property access: `dict`'s name` for named lists
    - Name access: Direct name access for dictionaries

    Attributes:
        collection: The collection being accessed.
        accessor: The index, ordinal, or name used for access.
        access_type: Type of access ('ordinal', 'numeric', 'name', 'property').
    """

    def __init__(
        self, token: Token, collection: Expression, accessor: Expression | str | int, access_type: str
    ) -> None:
        """Initialize a CollectionAccessExpression.

        Args:
            token: The token that begins this expression.
            collection: The collection being accessed.
            accessor: The index, ordinal, or name used for access.
            access_type: Type of access ('ordinal', 'numeric', 'name', 'property').
        """
        super().__init__(token)
        self.collection = collection
        self.accessor = accessor
        self.access_type = access_type

    def __str__(self) -> str:
        """Return the string representation of the collection access.

        Returns:
            A string representing the collection access pattern.
        """
        if self.access_type == "ordinal":
            return f"the {self.accessor} item of {self.collection}"
        elif self.access_type == "numeric":
            return f"item _{self.accessor}_ of {self.collection}"
        elif self.access_type == "property":
            return f"{self.collection}'s {self.accessor}"
        else:  # name
            return f"{self.collection}[{self.accessor}]"

    def desugar(self) -> "CollectionAccessExpression":
        """Desugar collection access by recursively desugaring the collection.

        Returns:
            A new CollectionAccessExpression with desugared collection.
        """
        desugared = CollectionAccessExpression(self.token, self.collection.desugar(), self.accessor, self.access_type)
        # If accessor is an expression, desugar it too
        if isinstance(self.accessor, Expression):
            desugared.accessor = self.accessor.desugar()
        return desugared

    def to_hir(self) -> "CollectionAccessExpression":
        """Convert collection access to HIR representation.

        Converts one-based user indices to zero-based for internal use.

        Returns:
            HIR representation with adjusted indices.
        """
        # Convert collection to HIR
        hir_collection = self.collection.to_hir() if hasattr(self.collection, "to_hir") else self.collection

        # Process accessor based on type
        hir_accessor = self.accessor
        if self.access_type == "ordinal":
            # Convert ordinals to zero-based numeric indices
            ordinal_map = {"first": 0, "second": 1, "third": 2}
            if isinstance(self.accessor, str) and self.accessor.lower() in ordinal_map:
                hir_accessor = ordinal_map[self.accessor.lower()]
                # Change type to numeric since we converted
                return CollectionAccessExpression(self.token, hir_collection, hir_accessor, "numeric")
            elif self.accessor == "last":
                # Keep "last" as special case - will be handled in MIR generation
                hir_accessor = "last"
        elif self.access_type == "numeric":
            # Convert one-based to zero-based index
            if isinstance(self.accessor, int):
                hir_accessor = self.accessor - 1  # Convert to 0-based
            elif isinstance(self.accessor, Expression):
                # For expressions, we'll need to handle this in MIR generation
                # by subtracting 1 at runtime
                hir_accessor = self.accessor.to_hir() if hasattr(self.accessor, "to_hir") else self.accessor
        elif isinstance(self.accessor, Expression):
            hir_accessor = self.accessor.to_hir() if hasattr(self.accessor, "to_hir") else self.accessor

        return CollectionAccessExpression(self.token, hir_collection, hir_accessor, self.access_type)


class ErrorExpression(Expression):
    """An expression that failed to parse correctly.

    ErrorExpressions preserve the AST structure even when parsing fails,
    allowing the parser to continue and collect multiple errors. They
    contain information about what went wrong during parsing.

    Attributes:
        message: Human-readable error message describing what went wrong.
    """

    def __init__(self, token: Token, message: str = "") -> None:
        """Initialize an ErrorExpression node.

        Args:
            token: The token where the error began.
            message: Error message describing the parsing failure.
        """
        super().__init__(token)
        self.message = message

    def __str__(self) -> str:
        """Return the string representation of the error expression.

        Returns:
            A string like "<error: message>".
        """
        if self.message:
            return f"<error: {self.message}>"
        return "<error>"

    def desugar(self) -> "ErrorExpression":
        """Error expressions remain unchanged.

        Returns:
            Self unchanged.
        """
        return self
