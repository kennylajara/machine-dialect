from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from machine_dialect.lexer.tokens import Token


class ASTNode(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

    def desugar(self) -> "ASTNode":
        """Simplify AST node for IR generation and optimization.

        This method transforms the AST to remove syntactic sugar and normalize
        semantically equivalent constructs. The default implementation returns
        the node unchanged.

        Returns:
            A simplified version of this node or self if no simplification needed.
        """
        return self

    def get_source_location(self) -> tuple[int, int] | None:
        """Get the source location (line, column) of this AST node.

        Returns:
            A tuple of (line, column) if location info is available, None otherwise.
        """
        # Default implementation - subclasses with tokens can override
        if hasattr(self, "token"):
            token: Token = self.token
            return (token.line, token.position)
        return None
