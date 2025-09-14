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
            ("Yes is strictly equal to Yes", True, "is strictly equal to", True),
            ("No is identical to No", False, "is strictly equal to", False),
            # Strict equality with identifiers
            ("x is strictly equal to y", "x", "is strictly equal to", "y"),
            ("foo is exactly equal to bar", "foo", "is strictly equal to", "bar"),
            ("`value` is identical to expected", "value", "is strictly equal to", "expected"),
            # Mixed types (would fail at runtime for strict equality)
            ("5 is strictly equal to 5.0", 5, "is strictly equal to", 5.0),
            ("Yes is strictly equal to 1", True, "is strictly equal to", 1),
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
        program = parser.parse(source, check_semantics=False)

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
            ("5 + 3 is strictly equal to 8", "((_5_ + _3_) is strictly equal to _8_)"),
            ("2 * 3 is exactly equal to 6", "((_2_ * _3_) is strictly equal to _6_)"),
            # Logical operators have lower precedence
            (
                "x is strictly equal to 5 and y is strictly equal to 10",
                "((`x` is strictly equal to _5_) and (`y` is strictly equal to _10_))",
            ),
            (
                "`a` is identical to `b` or `c` is not identical to `d`",
                "((`a` is strictly equal to `b`) or (`c` is not strictly equal to `d`))",
            ),
            # Mixed with regular equality
            (
                "x equals y and z is strictly equal to w",
                "((`x` equals `y`) and (`z` is strictly equal to `w`))",
            ),
            # Strict inequality with precedence
            (
                "5 + 3 is not strictly equal to 10",
                "((_5_ + _3_) is not strictly equal to _10_)",
            ),
            (
                "x * 2 is not exactly equal to y",
                "((`x` * _2_) is not strictly equal to `y`)",
            ),
        ]

        for source, expected_structure in test_cases:
            parser = Parser()
            program = parser.parse(source, check_semantics=False)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            # Check string representation matches expected precedence
            actual = str(statement.expression)
            assert actual == expected_structure, f"For '{source}': expected {expected_structure}, got {actual}"

    def test_strict_equality_in_conditionals(self) -> None:
        """Test strict equality in if statements."""
        from machine_dialect.ast import BlockStatement, IfStatement

        test_cases = [
            # Basic if with strict equality
            (
                """
                if x is strictly equal to 5 then:
                > give back _yes_.
                """,
                "x",
                "is strictly equal to",
                5,
            ),
            # If with strict inequality
            (
                """
                Define `result` as Text or Empty.
                if `value` is not strictly equal to empty then:
                > set `result` to `value`.
                """,
                "value",
                "is not strictly equal to",
                "empty",
            ),
            # If-else with strict equality
            (
                """
                if `a` is exactly equal to `b` then:
                > give back _Same_.
                else:
                > give back _Different_.
                """,
                "a",
                "is strictly equal to",
                "b",
            ),
            # Complex condition with strict equality
            (
                """
                Define `flag` as Yes/No.
                if x is identical to 0 or y is not identical to 0 then:
                > set `flag` to _yes_.
                """,
                None,  # Complex condition, skip simple checks
                None,
                None,
            ),
        ]

        for test_input in test_cases:
            source = test_input[0]
            expected_left = test_input[1]
            expected_op = test_input[2]
            expected_right = test_input[3]

            parser = Parser()
            program = parser.parse(source, check_semantics=False)

            assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"

            # Skip Define statement if present
            stmt_idx = 0
            if "Define" in source:
                stmt_idx = 1
                assert len(program.statements) == 2
            else:
                assert len(program.statements) == 1

            # Check it's an if statement
            if_stmt = program.statements[stmt_idx]
            assert isinstance(if_stmt, IfStatement)

            # Check the condition is parsed correctly
            if expected_left is not None:  # Simple condition check
                condition = if_stmt.condition
                assert isinstance(condition, InfixExpression)
                assert condition.operator == expected_op

                # Check left operand
                if isinstance(expected_left, str):
                    assert str(condition.left) == f"`{expected_left}`"
                else:
                    assert str(condition.left) == f"_{expected_left}_"

                # Check right operand
                if isinstance(expected_right, str):
                    # Special keywords like empty are parsed differently
                    if expected_right == "empty":
                        assert str(condition.right) == "empty"
                    else:
                        assert str(condition.right) == f"`{expected_right}`"
                else:
                    assert str(condition.right) == f"_{expected_right}_"

            # Check consequence block exists
            assert isinstance(if_stmt.consequence, BlockStatement)
            assert len(if_stmt.consequence.statements) > 0

    def test_complex_expressions_with_strict_equality(self) -> None:
        """Test complex expressions involving strict equality."""
        test_cases = [
            "not x is strictly equal to y",
            "(x + 5) is exactly equal to (y - 3)",
            "`first` is identical to `second`",
            "result is not strictly equal to empty",
        ]

        for source in test_cases:
            parser = Parser()
            program = parser.parse(source, check_semantics=False)

            # Should parse without errors
            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1
