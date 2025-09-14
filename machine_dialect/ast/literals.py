"""Literal expression AST nodes for Machine Dialect™."""

from typing import TYPE_CHECKING

from machine_dialect.ast import Expression
from machine_dialect.lexer import Token

if TYPE_CHECKING:
    from machine_dialect.ast import Expression as ExpressionType


class WholeNumberLiteral(Expression):
    """Represents a Whole Number literal expression."""

    def __init__(self, token: Token, value: int) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax
        return f"_{self.value}_"

    def desugar(self) -> "WholeNumberLiteral":
        """Whole Number literals are already in simplest form.

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
        # Display with underscores and quotes for the new syntax
        # The value doesn't include quotes, so add them for display
        return f'_"{self.value}"_'

    def desugar(self) -> "StringLiteral":
        """String literals are already in simplest form.

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


class YesNoLiteral(Expression):
    """Represents a boolean literal expression."""

    def __init__(self, token: Token, value: bool) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        # Display with underscores for the new syntax using canonical Yes/No
        return f"_{'Yes' if self.value else 'No'}_"

    def desugar(self) -> "YesNoLiteral":
        """Boolean literals are already normalized by lexer.

        Returns:
            Self unchanged.
        """
        return self


class UnorderedListLiteral(Expression):
    """Unordered list literal (dash markers).

    Represents a list created with dash markers (-).
    Example:
        - item1
        - item2
    """

    def __init__(self, token: Token, elements: list["ExpressionType"]) -> None:
        """Initialize unordered list literal.

        Args:
            token: The token representing the start of the list.
            elements: List of expressions that are the list elements.
        """
        super().__init__(token)
        self.elements = elements

    def __str__(self) -> str:
        """String representation of the unordered list."""
        if not self.elements:
            return "[]"
        elements_str = ", ".join(str(elem) for elem in self.elements)
        return f"[{elements_str}]"

    def desugar(self) -> "UnorderedListLiteral":
        """Desugar the unordered list literal.

        Returns:
            Self with desugared elements.
        """
        desugared_elements = [elem.desugar() for elem in self.elements]
        return UnorderedListLiteral(self.token, desugared_elements)

    def to_hir(self) -> "UnorderedListLiteral":
        """Convert unordered list to HIR representation.

        Returns:
            HIR representation with desugared elements.
        """
        hir_elements = []
        for elem in self.elements:
            if hasattr(elem, "to_hir"):
                hir_elements.append(elem.to_hir())
            else:
                hir_elements.append(elem)
        return UnorderedListLiteral(self.token, hir_elements)


class OrderedListLiteral(Expression):
    """Ordered list literal (numbered markers).

    Represents a list created with numbered markers (1., 2., etc).
    Example:
        1. item1
        2. item2
    """

    def __init__(self, token: Token, elements: list["ExpressionType"]) -> None:
        """Initialize ordered list literal.

        Args:
            token: The token representing the start of the list.
            elements: List of expressions that are the list elements.
        """
        super().__init__(token)
        self.elements = elements

    def __str__(self) -> str:
        """String representation of the ordered list."""
        if not self.elements:
            return "[]"
        elements_str = ", ".join(str(elem) for elem in self.elements)
        return f"[{elements_str}]"

    def desugar(self) -> "OrderedListLiteral":
        """Desugar the ordered list literal.

        Returns:
            Self with desugared elements.
        """
        desugared_elements = [elem.desugar() for elem in self.elements]
        return OrderedListLiteral(self.token, desugared_elements)

    def to_hir(self) -> "OrderedListLiteral":
        """Convert ordered list to HIR representation.

        Returns:
            HIR representation with desugared elements.
        """
        hir_elements = []
        for elem in self.elements:
            if hasattr(elem, "to_hir"):
                hir_elements.append(elem.to_hir())
            else:
                hir_elements.append(elem)
        return OrderedListLiteral(self.token, hir_elements)


class NamedListLiteral(Expression):
    """Named list literal (dictionary).

    Represents a dictionary created with name-content pairs using dash markers.
    Example:
        - name: content
        - key: value
    """

    def __init__(self, token: Token, entries: list[tuple[str, "ExpressionType"]]) -> None:
        """Initialize named list literal.

        Args:
            token: The token representing the start of the list.
            entries: List of (name, content) pairs.
        """
        super().__init__(token)
        self.entries = entries

    def __str__(self) -> str:
        """String representation of the named list."""
        if not self.entries:
            return "{}"
        entries_str = ", ".join(f"{name}: {content}" for name, content in self.entries)
        return f"{{{entries_str}}}"

    def desugar(self) -> "NamedListLiteral":
        """Desugar the named list literal.

        Returns:
            Self with desugared content expressions.
        """
        desugared_entries = [(name, content.desugar()) for name, content in self.entries]
        return NamedListLiteral(self.token, desugared_entries)

    def to_hir(self) -> "NamedListLiteral":
        """Convert named list to HIR representation.

        Returns:
            HIR representation with desugared content expressions.
        """
        hir_entries = []
        for name, content in self.entries:
            if hasattr(content, "to_hir"):
                hir_entries.append((name, content.to_hir()))
            else:
                hir_entries.append((name, content))
        return NamedListLiteral(self.token, hir_entries)


class BlankLiteral(Expression):
    """Represents a blank literal for empty collections.

    Used in expressions like:
    - Set `list` to blank.
    - Set `dict` to blank.
    """

    def __init__(self, token: Token) -> None:
        """Initialize blank literal.

        Args:
            token: The 'blank' token.
        """
        self.token = token

    def __str__(self) -> str:
        """Return string representation."""
        return "blank"

    def desugar(self) -> "BlankLiteral":
        """Desugar to self."""
        return self

    def to_hir(self) -> "BlankLiteral":
        """Convert to HIR representation."""
        return self
