from abc import ABC, abstractmethod


class ASTNode(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass
