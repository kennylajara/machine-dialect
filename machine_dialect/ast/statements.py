from machine_dialect.ast import ASTNode, Expression, Identifier
from machine_dialect.lexer import Token


class Statement(ASTNode):
    def __init__(self, token: Token) -> None:
        self.token = token


class SetStatement(Statement):
    def __init__(self, token: Token, name: Identifier | None = None, value: Expression | None = None) -> None:
        super().__init__(token)
        self.name = name
        self.value = value

    def __str__(self) -> str:
        out = f"{self.token.literal} "
        if self.name:
            out += f"`{self.name}` "
        out += "to "
        if self.value:
            out += str(self.value)
        return out
