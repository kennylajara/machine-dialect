"""Tests for return statement parsing."""

from machine_dialect.ast import ReturnStatement
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser


class TestReturnStatements:
    """Test parsing of return statements."""

    def test_give_back_statement(self) -> None:
        """Test parsing 'give back' return statement."""
        source = "give back 42"
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ReturnStatement)
        assert statement.token.literal == "give back"

    def test_gives_back_statement(self) -> None:
        """Test parsing 'gives back' return statement."""
        source = "gives back true"
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ReturnStatement)
        assert statement.token.literal == "gives back"

    def test_multiple_return_statements(self) -> None:
        """Test parsing multiple return statements."""
        source = """
            give back 1.
            gives back 2.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 2

        # First statement
        statement1 = program.statements[0]
        assert isinstance(statement1, ReturnStatement)
        assert statement1.token.literal == "give back"

        # Second statement
        statement2 = program.statements[1]
        assert isinstance(statement2, ReturnStatement)
        assert statement2.token.literal == "gives back"

    def test_return_with_set_statement(self) -> None:
        """Test parsing return statement followed by set statement."""
        source = """
            give back 42.
            Set `x` to 10
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 2

        # First statement should be return
        statement1 = program.statements[0]
        assert isinstance(statement1, ReturnStatement)
        assert statement1.token.literal == "give back"

        # Second statement should be set
        from machine_dialect.ast import SetStatement

        statement2 = program.statements[1]
        assert isinstance(statement2, SetStatement)
        assert statement2.token.literal == "Set"
