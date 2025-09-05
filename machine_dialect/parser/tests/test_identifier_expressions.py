"""Tests for parsing identifier expressions."""

import pytest

from machine_dialect.ast import ExpressionStatement
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_literal_expression,
    assert_program_statements,
)


class TestIdentifierExpressions:
    """Test cases for parsing identifier expressions."""

    @pytest.mark.parametrize(
        "source,expected_value",
        [
            # Simple identifiers
            ("foobar", "foobar"),
            ("x", "x"),
            ("myVariableName", "myVariableName"),
            ("test_variable_name", "test_variable_name"),
            # Backtick identifiers
            ("`myVariable`", "myVariable"),
            ("`x`", "x"),
            # Multi-word identifiers
            ("`email address`", "email address"),
            ("`user name`", "user name"),
            ("`first name`", "first name"),
            ("`shopping cart total`", "shopping cart total"),
            ("`is logged in`", "is logged in"),
            ("`has been processed`", "has been processed"),
            # Complex multi-word identifiers
            ("`customer email address`", "customer email address"),
            ("`total order amount`", "total order amount"),
            ("`user account status`", "user account status"),
        ],
    )
    def test_identifier_expression(self, source: str, expected_value: str) -> None:
        """Test parsing various identifier expressions.

        Args:
            source: The source code to parse.
            expected_value: The expected identifier value.
        """
        parser = Parser()

        program = parser.parse(source, check_semantics=False)

        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_literal_expression(statement.expression, expected_value)
