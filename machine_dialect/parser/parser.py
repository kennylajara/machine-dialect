from machine_dialect.ast import Program
from machine_dialect.lexer import Lexer


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

    def parse(self) -> Program:
        program: Program = Program(statements=[])

        return program
