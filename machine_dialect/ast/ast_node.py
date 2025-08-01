from abc import ABC, abstractmethod


class ASTNode(ABC):
    @abstractmethod
    def token_literal(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
