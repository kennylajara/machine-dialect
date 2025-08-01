from machine_dialect.ast import Identifier, Program, SetStatement
from machine_dialect.lexer import Lexer, TokenType
from machine_dialect.parser import Parser


class TestSetStatements:
    def test_parse_set_integer(self) -> None:
        source: str = "Set `X` to 1"
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "X"
        assert statement.name.token.literal == "`X`"

    def test_parse_set_float(self) -> None:
        source: str = "Set `Y` to 3.14"
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "Y"
        assert statement.name.token.literal == "`Y`"

    def test_parse_set_string(self) -> None:
        source: str = 'Set `Z` to "Hello, World!"'
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "Z"
        assert statement.name.token.literal == "`Z`"

    def test_parse_multiple_set_statements(self) -> None:
        source: str = "\n".join(
            [
                "Set `X` to 1",
                "Set `Y` to 3.14",
                'Set `Z` to "Hello, World!"',
            ]
        )

        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        assert len(program.statements) == 3

        # Check first statement
        statement1 = program.statements[0]
        assert isinstance(statement1, SetStatement)
        assert statement1.name is not None
        assert statement1.name.value == "X"
        assert statement1.name.token.type == TokenType.LIT_BACKTICK
        assert statement1.name.token.literal == "`X`"

        # Check second statement
        statement2 = program.statements[1]
        assert isinstance(statement2, SetStatement)
        assert statement2.name is not None
        assert statement2.name.value == "Y"
        assert statement2.name.token.type == TokenType.LIT_BACKTICK
        assert statement2.name.token.literal == "`Y`"

        # Check third statement
        statement3 = program.statements[2]
        assert isinstance(statement3, SetStatement)
        assert statement3.name is not None
        assert statement3.name.value == "Z"
        assert statement3.name.token.type == TokenType.LIT_BACKTICK
        assert statement3.name.token.literal == "`Z`"

    def test_set_statement_string_representation(self) -> None:
        source: str = "Set `X` to 1"
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse()

        assert program is not None
        statement = program.statements[0]
        assert isinstance(statement, SetStatement)

        # Test the string representation
        program_str = str(program)
        assert program_str is not None  # Should have some string representation
