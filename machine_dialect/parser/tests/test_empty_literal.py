"""Tests for parsing the empty literal."""

import pytest

from machine_dialect.ast import EmptyLiteral, ExpressionStatement
from machine_dialect.parser import Parser


class TestEmptyLiteral:
    """Test parsing of the empty literal."""

    def test_parse_empty_literal(self) -> None:
        """Test parsing the empty keyword as a literal."""
        source = "empty"
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert isinstance(statement.expression, EmptyLiteral)
        assert statement.expression.value is None
        assert str(statement.expression) == "empty"

    def test_empty_in_set_statement(self) -> None:
        """Test using empty in a set statement."""
        source = """Define `result` as Empty.
Set `result` to empty."""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        from machine_dialect.ast import DefineStatement, SetStatement

        # Check Define statement
        assert isinstance(program.statements[0], DefineStatement)

        # Check Set statement
        statement = program.statements[1]
        assert isinstance(statement, SetStatement)
        assert isinstance(statement.value, EmptyLiteral)

    def test_empty_in_comparison(self) -> None:
        """Test using empty in comparison expressions."""
        test_cases = [
            ("x equals empty", "`x`", "equals", "empty"),
            ("`value` is not empty", "`value`", "is not", "empty"),
            ("result is strictly equal to empty", "`result`", "is strictly equal to", "empty"),
        ]

        for source, expected_left, expected_op, expected_right in test_cases:
            parser = Parser()
            program = parser.parse(source, check_semantics=False)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)

            from machine_dialect.ast import InfixExpression

            expr = statement.expression
            assert isinstance(expr, InfixExpression)
            assert str(expr.left) == expected_left
            assert expr.operator == expected_op
            assert str(expr.right) == expected_right

    def test_empty_in_if_condition(self) -> None:
        """Test using empty in if statement conditions."""
        source = """
        Define `value` as Whole Number or Empty.
        Define `result` as Whole Number.
        if `value` equals empty then:
        > Set `result` to _0_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        from machine_dialect.ast import DefineStatement, IfStatement, InfixExpression

        # Check Define statements
        assert isinstance(program.statements[0], DefineStatement)
        assert isinstance(program.statements[1], DefineStatement)

        # Check If statement
        if_stmt = program.statements[2]
        assert isinstance(if_stmt, IfStatement)
        assert isinstance(if_stmt.condition, InfixExpression)
        assert str(if_stmt.condition.right) == "empty"

    def test_empty_in_return_statement(self) -> None:
        """Test using empty in a return statement."""
        source = "give back empty."
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        from machine_dialect.ast import ReturnStatement

        statement = program.statements[0]
        assert isinstance(statement, ReturnStatement)
        assert isinstance(statement.return_value, EmptyLiteral)

    def test_empty_not_confused_with_identifier(self) -> None:
        """Test that 'empty' is recognized as a keyword, not an identifier."""
        # Test that 'empty' is parsed as EmptyLiteral
        parser1 = Parser()
        program1 = parser1.parse("empty", check_semantics=False)
        assert len(parser1.errors) == 0
        stmt1 = program1.statements[0]
        assert isinstance(stmt1, ExpressionStatement)
        assert isinstance(stmt1.expression, EmptyLiteral)

        # Test that similar words are parsed as identifiers
        parser2 = Parser()
        program2 = parser2.parse("empties", check_semantics=False)
        assert len(parser2.errors) == 0

        from machine_dialect.ast import Identifier

        stmt2 = program2.statements[0]
        assert isinstance(stmt2, ExpressionStatement)
        assert isinstance(stmt2.expression, Identifier)

    @pytest.mark.parametrize(
        "source",
        [
            "Empty",  # Different case
            "EMPTY",  # All caps
            "eMpTy",  # Mixed case
        ],
    )
    def test_empty_case_insensitive(self, source: str) -> None:
        """Test that empty keyword is case-insensitive."""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert isinstance(statement.expression, EmptyLiteral)
        # String representation should always be lowercase
        assert str(statement.expression) == "empty"
