from machine_dialect.ast import ASTNode
from machine_dialect.lexer import Token


class Expression(ASTNode):
    def __init__(self, token: Token) -> None:
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal
