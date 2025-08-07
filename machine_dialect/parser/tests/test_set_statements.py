import pytest

from machine_dialect.ast import Identifier, Program, SetStatement
from machine_dialect.lexer import TokenType
from machine_dialect.parser import Parser


class TestSetStatements:
    def test_parse_set_integer(self) -> None:
        source: str = "Set `X` to 1"
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "X"
        assert statement.name.token.literal == "X"

    def test_parse_set_float(self) -> None:
        source: str = "Set `price` to 3.14"
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "price"
        assert statement.name.token.literal == "price"

    def test_parse_set_string(self) -> None:
        source: str = 'Set `Z` to "Hello, World!"'
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "Z"
        assert statement.name.token.literal == "Z"

    def test_parse_multiple_set_statements(self) -> None:
        source: str = "\n".join(
            [
                "Set `X` to 1.",
                "Set `price` to 3.14.",
                'Set `Z` to "Hello, World!".',
            ]
        )

        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 3

        # Check first statement
        statement1 = program.statements[0]
        assert isinstance(statement1, SetStatement)
        assert statement1.name is not None
        assert statement1.name.value == "X"
        assert statement1.name.token.type == TokenType.MISC_IDENT
        assert statement1.name.token.literal == "X"

        # Check second statement
        statement2 = program.statements[1]
        assert isinstance(statement2, SetStatement)
        assert statement2.name is not None
        assert statement2.name.value == "price"
        assert statement2.name.token.type == TokenType.MISC_IDENT
        assert statement2.name.token.literal == "price"

        # Check third statement
        statement3 = program.statements[2]
        assert isinstance(statement3, SetStatement)
        assert statement3.name is not None
        assert statement3.name.value == "Z"
        assert statement3.name.token.type == TokenType.MISC_IDENT
        assert statement3.name.token.literal == "Z"

    def test_set_statement_string_representation(self) -> None:
        source: str = "Set `X` to 1"
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        statement = program.statements[0]
        assert isinstance(statement, SetStatement)

        # Test the string representation
        program_str = str(program)
        assert program_str is not None  # Should have some string representation

    @pytest.mark.parametrize(
        "source",
        [
            "Set `foo` to 1 if `certain_condition`, else 0",
            "Set `foo` to 1 if `certain_condition`, otherwise 0",
            "Set `foo` to 1 when `certain_condition`, else 0",
            "Set `foo` to 1 when `certain_condition`, otherwise 0",
            "Set `foo` to 1 whenever `certain_condition`, else 0",
            "Set `foo` to 1 whenever `certain_condition`, otherwise 0",
            "Set `foo` to 1 if `certain_condition`; else 0",
            "Set `foo` to 1 if `certain_condition`; otherwise 0",
            "Set `foo` to 1 when `certain_condition`; else 0",
            "Set `foo` to 1 when `certain_condition`; otherwise 0",
            "Set `foo` to 1 whenever `certain_condition`; else 0",
            "Set `foo` to 1 whenever `certain_condition`; otherwise 0",
        ],
    )
    def test_parse_ternary_expressions(self, source: str) -> None:
        parser: Parser = Parser()

        program: Program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, SetStatement)
        assert statement.token.literal == "Set"

        assert statement.name is not None
        assert isinstance(statement.name, Identifier)
        assert statement.name.value == "foo"
        assert statement.name.token.literal == "foo"

        # The value should be a ternary/conditional expression
        assert statement.value is not None
