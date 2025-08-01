from enum import (
    Enum,
    auto,
    unique,
)
from typing import (
    NamedTuple,
)


@unique
class TokenType(Enum):
    AND = auto()  # not implemented
    AS = auto()  # not implemented
    ASSIGN = auto()  # not implemented
    COLON = auto()  # not implemented
    COMMA = auto()  # not implemented
    DIVISION = auto()  # not implemented
    ELSE = auto()  # not implemented
    EOF = auto()  # not implemented
    EQ = auto()  # not implemented
    FALSE = auto()  # not implemented
    FUNCTION = auto()  # not implemented
    GT = auto()  # not implemented
    IDENT = auto()  # not implemented
    IF = auto()  # not implemented
    ILLEGAL = auto()  # not implemented
    INT = auto()  # not implemented
    IS = auto()  # not implemented
    LBRACE = auto()  # not implemented
    LET = auto()  # not implemented
    LPAREN = auto()  # not implemented
    LT = auto()  # not implemented
    MINUS = auto()  # not implemented
    MULTIPLICATION = auto()  # not implemented
    NEGATION = auto()  # not implemented
    NOT_EQ = auto()  # not implemented
    OR = auto()  # not implemented
    PERIOD = auto()  # not implemented
    PLUS = auto()  # not implemented
    RBRACE = auto()  # not implemented
    RETURN = auto()  # not implemented
    RPAREN = auto()  # not implemented
    SEMICOLON = auto()  # not implemented
    STRING = auto()  # not implemented
    THEN = auto()  # not implemented
    TRUE = auto()  # not implemented
    WITH = auto()  # not implemented


class Token(NamedTuple):
    token_type: TokenType
    literal: str

    def __str__(self) -> str:
        return f"Type: {self.token_type}, Literal: {self.literal}"


def lookup_token_type(literal: str) -> TokenType:
    keywords: dict[str, TokenType] = {
        "and": TokenType.AND,  # not implemented
        "as": TokenType.AS,  # not implemented
        "define": TokenType.FUNCTION,  # not implemented
        "else": TokenType.ELSE,  # not implemented
        "equals": TokenType.EQ,  # not implemented
        "false": TokenType.FALSE,  # not implemented
        "function": TokenType.FUNCTION,  # not implemented
        "if": TokenType.IF,  # not implemented
        "is": TokenType.IS,  # not implemented
        "let": TokenType.LET,  # not implemented
        "not": TokenType.NEGATION,  # not implemented
        "or": TokenType.OR,  # not implemented
        "otherwise": TokenType.ELSE,  # not implemented
        "return": TokenType.RETURN,  # not implemented
        "returns": TokenType.RETURN,  # not implemented
        "then": TokenType.THEN,  # not implemented
        "true": TokenType.TRUE,  # not implemented
        "variable": TokenType.LET,  # not implemented
        "when": TokenType.IF,  # not implemented
        "with": TokenType.WITH,  # not implemented
    }

    return keywords.get(literal, TokenType.IDENT)
