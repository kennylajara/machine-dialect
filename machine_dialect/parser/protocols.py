from collections.abc import Callable

from machine_dialect.ast import Expression
from machine_dialect.lexer import TokenType

PrefixParseFunc = Callable[[], Expression]
InfixParseFunc = Callable[[Expression], Expression]
PostfixParseFunc = Callable[[Expression], Expression]
PrefixParseFuncs = dict[TokenType, PrefixParseFunc]
InfixParseFuncs = dict[TokenType, InfixParseFunc]
PostfixParseFuncs = dict[TokenType, PostfixParseFunc]
