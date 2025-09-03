from abc import ABC, abstractmethod


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
