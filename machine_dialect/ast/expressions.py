from machine_dialect.ast import ASTNode
from machine_dialect.lexer import Token


class Expression(ASTNode):
    def __init__(self, token: Token) -> None:
        self.token = token


class Identifier(Expression):
    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return f"`{self.value}`"
