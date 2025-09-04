"""Tests for parsing boolean literal expressions.

This module tests the parser's ability to handle boolean literal expressions
including Yes and No in both regular and underscore-wrapped forms.
"""

import pytest

from machine_dialect.ast import ExpressionStatement
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_literal_expression,
    assert_program_statements,
)


class TestBooleanLiteralExpressions:
    """Test parsing of boolean literal expressions."""

    @pytest.mark.parametrize(
        "source,expected_value",
        [
            # Simple boolean literals
            ("Yes", True),
            ("No", False),
            # Underscore-wrapped boolean literals
            ("_Yes_", True),
            ("_No_", False),
        ],
    )
    def test_boolean_literal_expression(self, source: str, expected_value: bool) -> None:
        """Test parsing various boolean literal expressions.

        Args:
            source: The source code containing a boolean literal.
            expected_value: The expected boolean value.
        """
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, expected_value)

    def test_boolean_with_period(self) -> None:
        """Test parsing boolean literal with explicit statement terminator."""
        source = "Yes."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, True)

    def test_multiple_boolean_statements(self) -> None:
        """Test parsing multiple boolean literal statements."""
        source = "Yes. No. Yes. No."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 4

        # Check each statement
        expected_values = [True, False, True, False]
        for i, expected_value in enumerate(expected_values):
            statement = program.statements[i]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None
            assert_literal_expression(statement.expression, expected_value)

    def test_mixed_literals_with_booleans(self) -> None:
        """Test parsing mixed literal types including booleans."""
        source = "Yes. 42. No. 3.14. _Yes_."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 5

        # Check boolean statements
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_literal_expression(statement.expression, True)

        statement = program.statements[2]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_literal_expression(statement.expression, False)

        statement = program.statements[4]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_literal_expression(statement.expression, True)

    @pytest.mark.parametrize(
        "source,expected_value",
        [
            # Case insensitive variations should all parse as True
            ("yes", True),
            ("YES", True),
            ("YeS", True),
            ("yEs", True),
            # Case insensitive variations should all parse as False
            ("no", False),
            ("NO", False),
            ("No", False),
            ("nO", False),
            # Underscore-wrapped case variations
            ("_yes_", True),
            ("_YES_", True),
            ("_no_", False),
            ("_NO_", False),
        ],
    )
    def test_case_insensitive_boolean_literals(self, source: str, expected_value: bool) -> None:
        """Test that boolean literals are case-insensitive.

        Boolean literals should be recognized regardless of case and stored
        in their canonical form as defined in tokens.py.

        Args:
            source: The source code with various case boolean literals.
            expected_value: The expected boolean value.
        """
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, expected_value)
