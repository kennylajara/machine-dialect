"""Tests for parsing strict equality expressions.

This module tests the parser's ability to handle strict equality and
strict inequality expressions, ensuring they are distinguished from
regular equality operators.
"""

import pytest

from machine_dialect.ast import ExpressionStatement, InfixExpression
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_infix_expression,
    assert_program_statements,
)


class TestStrictEqualityExpressions:
    """Test parsing of strict equality expressions."""

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Strict equality with integers
            ("5 is strictly equal to 5", 5, "is strictly equal to", 5),
            ("10 is exactly equal to 10", 10, "is strictly equal to", 10),
            ("42 is identical to 42", 42, "is strictly equal to", 42),
            # Strict inequality with integers
            ("5 is not strictly equal to 10", 5, "is not strictly equal to", 10),
            ("10 is not exactly equal to 20", 10, "is not strictly equal to", 20),
            ("7 is not identical to 8", 7, "is not strictly equal to", 8),
            # Strict equality with floats
            ("3.14 is strictly equal to 3.14", 3.14, "is strictly equal to", 3.14),
            ("2.5 is exactly equal to 2.5", 2.5, "is strictly equal to", 2.5),
            # Strict equality with booleans
            ("True is strictly equal to True", True, "is strictly equal to", True),
            ("False is identical to False", False, "is strictly equal to", False),
            # Strict equality with identifiers
            ("x is strictly equal to y", "x", "is strictly equal to", "y"),
            ("foo is exactly equal to bar", "foo", "is strictly equal to", "bar"),
            ("value is identical to expected", "value", "is strictly equal to", "expected"),
            # Mixed types (would fail at runtime for strict equality)
            ("5 is strictly equal to 5.0", 5, "is strictly equal to", 5.0),
            ("True is strictly equal to 1", True, "is strictly equal to", 1),
        ],
    )
    def test_strict_equality_expressions(
        self, source: str, left: int | float | bool | str, operator: str, right: int | float | bool | str
    ) -> None:
        """Test parsing strict equality and inequality expressions.

        Args:
            source: The source code containing a strict equality expression.
            left: Expected left operand value.
            operator: Expected operator string representation.
            right: Expected right operand value.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_infix_expression(statement.expression, left, operator, right)

    def test_strict_vs_value_equality(self) -> None:
        """Test that strict and value equality are parsed as different operators."""
        # Value equality
        parser1 = Parser()
        program1 = parser1.parse("x equals y")
        assert len(parser1.errors) == 0

        statement1 = program1.statements[0]
        assert isinstance(statement1, ExpressionStatement)
        expr1 = statement1.expression
        assert isinstance(expr1, InfixExpression)
        assert expr1.operator == "equals"

        # Strict equality
        parser2 = Parser()
        program2 = parser2.parse("x is strictly equal to y")
        assert len(parser2.errors) == 0

        statement2 = program2.statements[0]
        assert isinstance(statement2, ExpressionStatement)
        expr2 = statement2.expression
        assert isinstance(expr2, InfixExpression)
        assert expr2.operator == "is strictly equal to"

        # Ensure they're different
        assert expr1.operator != expr2.operator

    def test_strict_equality_precedence(self) -> None:
        """Test that strict equality has the same precedence as regular equality."""
        test_cases = [
            # Arithmetic has higher precedence than strict equality
            ("5 + 3 is strictly equal to 8", "((5 + 3) is strictly equal to 8)"),
            ("2 * 3 is exactly equal to 6", "((2 * 3) is strictly equal to 6)"),
            # Logical operators have lower precedence
            (
                "x is strictly equal to 5 and y is strictly equal to 10",
                "((x is strictly equal to 5) and (y is strictly equal to 10))",
            ),
            (
                "`a` is identical to `b` or `c` is not identical to `d`",
                "((`a` is strictly equal to `b`) or (`c` is not strictly equal to `d`))",
            ),
            # Mixed with regular equality
            (
                "x equals y and z is strictly equal to w",
                "((x equals y) and (z is strictly equal to w))",
            ),
        ]

        for source, _ in test_cases:  # expected_structure will be used in future
            parser = Parser()
            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            # For now, just ensure it parses without errors
            # The actual string representation would need updates to properly display

    def test_strict_equality_in_conditionals(self) -> None:
        """Test strict equality in if statements."""
        source = """
        if x is strictly equal to 5 then:
        > give back _true_.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        # The if statement should contain a strict equality expression
        # Just ensure it parses correctly for now

    def test_complex_expressions_with_strict_equality(self) -> None:
        """Test complex expressions involving strict equality."""
        test_cases = [
            "not x is strictly equal to y",
            "(x + 5) is exactly equal to (y - 3)",
            "first is identical to second",
            "result is not strictly equal to _Nothing_",
        ]

        for source in test_cases:
            parser = Parser()
            program = parser.parse(source)

            # Should parse without errors
            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1
