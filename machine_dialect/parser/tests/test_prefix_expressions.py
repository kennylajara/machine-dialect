"""Tests for parsing prefix expressions.

This module tests the parser's ability to handle prefix expressions including:
- Negative numbers (-42, -3.14)
- Boolean negation (not True, not False)
"""

import pytest

from machine_dialect.ast import ExpressionStatement, PrefixExpression
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_literal_expression,
    assert_program_statements,
)


class TestPrefixExpressions:
    """Test parsing of prefix expressions."""

    @pytest.mark.parametrize(
        "source,operator,value",
        [
            # Negative integers
            ("-5", "-", 5),
            ("-42", "-", 42),
            ("-123", "-", 123),
            ("-0", "-", 0),
            ("-999", "-", 999),
            # Negative integers with underscores wrapping the positive number
            ("-_5_", "-", 5),
            ("-_42_", "-", 42),
            ("-_123_", "-", 123),
            # Underscore-wrapped negative integers (entire expression)
            ("_-5_", "-", 5),
            ("_-42_", "-", 42),
            ("_-123_", "-", 123),
        ],
    )
    def test_negative_integer_expressions(self, source: str, operator: str, value: int) -> None:
        """Test parsing negative integer expressions.

        Args:
            source: The source code containing a negative integer.
            operator: The expected operator (should be "-").
            value: The expected positive integer value.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        # Check that it's a prefix expression
        assert isinstance(statement.expression, PrefixExpression)
        prefix_exp = statement.expression

        # Check the operator
        assert prefix_exp.operator == operator

        # Check the right expression (should be the positive number)
        assert prefix_exp.right is not None
        assert_literal_expression(prefix_exp.right, value)

    @pytest.mark.parametrize(
        "source,operator,value",
        [
            # Negative floats
            ("-3.14", "-", 3.14),
            ("-0.5", "-", 0.5),
            ("-123.456", "-", 123.456),
            ("-0.0", "-", 0.0),
            ("-.5", "-", 0.5),
            ("-.25", "-", 0.25),
            # Negative floats with underscores wrapping the positive number
            ("-_3.14_", "-", 3.14),
            ("-_0.5_", "-", 0.5),
            ("-_.25_", "-", 0.25),
            # Underscore-wrapped negative floats (entire expression)
            ("_-3.14_", "-", 3.14),
            ("_-0.5_", "-", 0.5),
            ("_-.25_", "-", 0.25),
        ],
    )
    def test_negative_float_expressions(self, source: str, operator: str, value: float) -> None:
        """Test parsing negative float expressions.

        Args:
            source: The source code containing a negative float.
            operator: The expected operator (should be "-").
            value: The expected positive float value.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        # Check that it's a prefix expression
        assert isinstance(statement.expression, PrefixExpression)
        prefix_exp = statement.expression

        # Check the operator
        assert prefix_exp.operator == operator

        # Check the right expression (should be the positive number)
        assert prefix_exp.right is not None
        assert_literal_expression(prefix_exp.right, value)

    @pytest.mark.parametrize(
        "source,operator,value",
        [
            # Boolean negation
            ("not True", "not", True),
            ("not False", "not", False),
            # Boolean negation with underscores
            ("not _True_", "not", True),
            ("not _False_", "not", False),
            # Underscore-wrapped entire negation expression
            ("_not True_", "not", True),
            ("_not False_", "not", False),
            # Case insensitive NOT
            ("NOT True", "not", True),
            ("NOT False", "not", False),
            ("Not True", "not", True),
            ("Not False", "not", False),
            ("nOt True", "not", True),
            ("nOt False", "not", False),
            # Case insensitive boolean values with negation
            ("not true", "not", True),
            ("not false", "not", False),
            ("NOT TRUE", "not", True),
            ("NOT FALSE", "not", False),
        ],
    )
    def test_boolean_negation_expressions(self, source: str, operator: str, value: bool) -> None:
        """Test parsing boolean negation expressions.

        Args:
            source: The source code containing a negated boolean.
            operator: The expected operator (should be "not").
            value: The expected boolean value being negated.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        # Check that it's a prefix expression
        assert isinstance(statement.expression, PrefixExpression)
        prefix_exp = statement.expression

        # Check the operator (should be lowercase "not")
        assert prefix_exp.operator == operator

        # Check the right expression (should be the boolean value)
        assert prefix_exp.right is not None
        assert_literal_expression(prefix_exp.right, value)

    def test_multiple_prefix_expressions(self) -> None:
        """Test parsing multiple prefix expressions in sequence."""
        source = "-42. not True. -3.14. not False."
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert len(program.statements) == 4

        # First statement: -42
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "-"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, 42)

        # Second statement: not True
        statement = program.statements[1]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "not"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, True)

        # Third statement: -3.14
        statement = program.statements[2]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "-"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, 3.14)

        # Fourth statement: not False
        statement = program.statements[3]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "not"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, False)

    def test_prefix_expression_with_identifier(self) -> None:
        """Test prefix expressions with identifiers."""
        source = "-x. not `is valid`."
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        # First statement: -x
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "-"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, "x")

        # Second statement: not `is valid`
        statement = program.statements[1]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "not"
        assert statement.expression.right is not None
        assert_literal_expression(statement.expression.right, "is valid")

    def test_double_negation(self) -> None:
        """Test parsing double negation expressions."""
        source = "--42. not not True."
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        # First statement: --42 (negative of negative 42)
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "-"

        # The right side should be another prefix expression
        assert statement.expression.right is not None
        assert isinstance(statement.expression.right, PrefixExpression)
        assert statement.expression.right.operator == "-"
        assert statement.expression.right.right is not None
        assert_literal_expression(statement.expression.right.right, 42)

        # Second statement: not not True
        statement = program.statements[1]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert isinstance(statement.expression, PrefixExpression)
        assert statement.expression.operator == "not"

        # The right side should be another prefix expression
        assert statement.expression.right is not None
        assert isinstance(statement.expression.right, PrefixExpression)
        assert statement.expression.right.operator == "not"
        assert statement.expression.right.right is not None
        assert_literal_expression(statement.expression.right.right, True)

    def test_prefix_expression_string_representation(self) -> None:
        """Test the string representation of prefix expressions."""
        # Test cases with expected string representations
        test_cases = [
            ("-42", "(-42)"),
            ("not True", "(not True)"),
            ("-3.14", "(-3.14)"),
            ("not False", "(not False)"),
            ("--5", "(-(-5))"),
            ("not not True", "(not (not True))"),
        ]

        for source, expected in test_cases:
            lexer = Lexer(source)
            parser = Parser(lexer)
            program = parser.parse()

            assert len(parser.errors) == 0
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            # Check string representation
            assert str(statement.expression) == expected
