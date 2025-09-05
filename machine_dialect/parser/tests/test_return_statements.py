"""Tests for return statement parsing."""

from machine_dialect.ast import ReturnStatement
from machine_dialect.parser import Parser


class TestReturnStatements:
    """Test parsing of return statements."""

    def test_give_back_statement(self) -> None:
        """Test parsing 'give back' return statement."""
        source = "give back 42"
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ReturnStatement)
        assert statement.token.literal == "give back"

    def test_gives_back_statement(self) -> None:
        """Test parsing 'gives back' return statement."""
        source = "gives back true"
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

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
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

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
            Define `x` as Whole Number.
            give back 42.
            Set `x` to 10
        """
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser had errors: {parser.errors}"
        assert len(program.statements) == 3

        # First statement should be define
        from machine_dialect.ast import DefineStatement, SetStatement

        statement1 = program.statements[0]
        assert isinstance(statement1, DefineStatement)

        # Second statement should be return
        statement2 = program.statements[1]
        assert isinstance(statement2, ReturnStatement)
        assert statement2.token.literal == "give back"

        # Third statement should be set
        statement3 = program.statements[2]
        assert isinstance(statement3, SetStatement)
        assert statement3.token.literal == "Set"
