"""Helper functions for parser tests.

This module provides utility functions used across parser tests to verify
program structure, statements, and expressions. These helpers reduce code
duplication and make tests more readable.
"""

from typing import Any, cast

from machine_dialect.ast import Expression, ExpressionStatement, Identifier, Program
from machine_dialect.parser import Parser


def assert_program_statements(parser: Parser, program: Program, expected_statement_count: int = 1) -> None:
    """Verify that a program has the expected number of statements and no errors.

    Args:
        parser: The parser instance to check for errors.
        program: The parsed program to verify.
        expected_statement_count: Expected number of statements in the program.

    Raises:
        AssertionError: If parser has errors, statement count is wrong, or
            first statement is not an ExpressionStatement.
    """
    assert len(parser.errors) == 0, f"Program statement errors found: {parser.errors}"
    assert len(program.statements) == expected_statement_count
    assert isinstance(program.statements[0], ExpressionStatement)


def assert_literal_expression(
    expression: Expression,
    expected_value: Any,
) -> None:
    """Test that a literal expression has the expected value.

    This function dispatches to the appropriate test function based on the
    type of the expected value. Currently only handles string identifiers.

    Args:
        expression: The expression to test.
        expected_value: The expected value of the literal.

    Raises:
        AssertionError: If the expression doesn't match the expected value
            or if the value type is not handled.
    """
    value_type: type = type(expected_value)

    if value_type is str:
        assert_identifier(expression, expected_value)
    else:
        raise AssertionError(f"Unhandled literal expression: {expression}. Got={value_type}")


def assert_identifier(expression: Expression, expected_value: str) -> None:
    """Test that an identifier expression has the expected value.

    Verifies both the identifier's value attribute and its token's literal
    match the expected value.

    Args:
        expression: The expression to test (must be an Identifier).
        expected_value: The expected string value of the identifier.

    Raises:
        AssertionError: If the identifier's value or token literal don't
            match the expected value.
    """
    identifier: Identifier = cast(Identifier, expression)
    assert identifier.value == expected_value, f"Identifier value={identifier.value} != {expected_value}"
    assert identifier.token.literal == expected_value, f"Identifier token={identifier.token} != {expected_value}"
