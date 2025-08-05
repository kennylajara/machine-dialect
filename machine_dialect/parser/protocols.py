from collections.abc import Callable

from machine_dialect.ast import Expression
from machine_dialect.lexer import TokenType

PrefixParseFunc = Callable[[], Expression | None]
InfixParseFunc = Callable[[Expression], Expression | None]
PostfixParseFunc = Callable[[Expression], Expression | None]
PrefixParseFuncs = dict[TokenType, PrefixParseFunc]
InfixParseFuncs = dict[TokenType, InfixParseFunc]
PostfixParseFuncs = dict[TokenType, PostfixParseFunc]
