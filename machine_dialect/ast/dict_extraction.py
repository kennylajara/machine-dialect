"""Dictionary extraction expressions for Machine Dialect™."""

from __future__ import annotations

from typing import TYPE_CHECKING

from machine_dialect.ast.expressions import Expression

if TYPE_CHECKING:
    from machine_dialect.lexer.tokens import Token


class DictExtraction(Expression):
    """Extract keys or values from a dictionary.

    Represents expressions like:
    - the names of `person` (extracts keys)
    - the contents of `person` (extracts values)

    Attributes:
        dictionary: The dictionary expression to extract from.
        extract_type: What to extract ('names' for keys, 'contents' for values).
        token: The token that begins this expression.
    """

    def __init__(self, token: Token, dictionary: Expression, extract_type: str) -> None:
        """Initialize dictionary extraction expression.

        Args:
            token: The token that begins this expression.
            dictionary: The dictionary to extract from.
            extract_type: 'names' or 'contents'.
        """
        super().__init__(token)
        self.token = token
        self.dictionary = dictionary
        self.extract_type = extract_type

    def __str__(self) -> str:
        """Return string representation."""
        if self.extract_type == "names":
            return f"the names of {self.dictionary}"
        else:
            return f"the contents of {self.dictionary}"

    def desugar(self) -> DictExtraction:
        """Desugar by recursively desugaring the dictionary."""
        return DictExtraction(
            self.token,
            self.dictionary.desugar() if hasattr(self.dictionary, "desugar") else self.dictionary,
            self.extract_type,
        )

    def to_hir(self) -> DictExtraction:
        """Convert to HIR representation."""
        return DictExtraction(
            self.token,
            self.dictionary.to_hir() if hasattr(self.dictionary, "to_hir") else self.dictionary,
            self.extract_type,
        )
