from machine_dialect.ast import Program
from machine_dialect.parser import Parser


class TestParser:
    def test_parse_program(self) -> None:
        source: str = "Set `X` to 5."
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert isinstance(program, Program)
