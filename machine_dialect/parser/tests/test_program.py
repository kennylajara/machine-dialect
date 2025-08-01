from machine_dialect.ast import Program
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser


class TestParser:
    def test_parse_program(self) -> None:
        source: str = "Set `X` to 5."
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        assert isinstance(program, Program)
