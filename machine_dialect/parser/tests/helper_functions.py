"""Helper functions for parser tests.

This module provides utility functions used across parser tests to verify
program structure, statements, and expressions. These helpers reduce code
duplication and make tests more readable.
"""

from typing import Any, cast

from machine_dialect.ast import (
    Expression,
    ExpressionStatement,
    FloatLiteral,
    Identifier,
    InfixExpression,
    Program,
    WholeNumberLiteral,
    YesNoLiteral,
)
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
        _assert_identifier(expression, expected_value)
    elif value_type is int:
        _assert_integer_literal(expression, expected_value)
    elif value_type is float:
        _assert_float_literal(expression, expected_value)
    elif value_type is bool:
        _assert_boolean_literal(expression, expected_value)
    else:
        raise AssertionError(f"Unhandled literal expression: {expression}. Got={value_type}")


def _assert_identifier(expression: Expression, expected_value: str) -> None:
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


def _assert_integer_literal(expression: Expression, expected_value: int) -> None:
    """Test that an integer literal expression has the expected value.

    Verifies both the integer literal's value attribute and its token's literal
    match the expected value.

    Args:
        expression: The expression to test (must be a WholeNumberLiteral).
        expected_value: The expected integer value.

    Raises:
        AssertionError: If the expression is not a WholeNumberLiteral or if
            the value doesn't match the expected value.
    """
    assert isinstance(expression, WholeNumberLiteral), f"Expected WholeNumberLiteral, got {type(expression).__name__}"
    integer_literal = expression
    assert integer_literal.value == expected_value, f"Integer value={integer_literal.value} != {expected_value}"
    assert integer_literal.token.literal == str(expected_value), (
        f"Integer token literal={integer_literal.token.literal} != {expected_value}"
    )


def _assert_float_literal(expression: Expression, expected_value: float) -> None:
    """Test that a float literal expression has the expected value.

    Verifies both the float literal's value attribute and its token's literal
    match the expected value.

    Args:
        expression: The expression to test (must be a FloatLiteral).
        expected_value: The expected float value.

    Raises:
        AssertionError: If the expression is not a FloatLiteral or if
            the value doesn't match the expected value.
    """
    assert isinstance(expression, FloatLiteral), f"Expected FloatLiteral, got {type(expression).__name__}"
    float_literal = expression
    assert float_literal.value == expected_value, f"Float value={float_literal.value} != {expected_value}"
    # For float literals, we compare the string representation to avoid precision issues
    expected_str = str(expected_value)
    actual_str = float_literal.token.literal
    # Handle cases like 3.0 vs 3.0 or 3.14 vs 3.14
    assert float(actual_str) == float(expected_str), f"Float token literal={actual_str} != {expected_str}"


def _assert_boolean_literal(expression: Expression, expected_value: bool) -> None:
    """Test that a boolean literal expression has the expected value.

    Verifies both the boolean literal's value attribute and its token's literal
    match the expected value. The token literal should be in canonical form
    ("Yes" or "No") regardless of the original case in the source.

    Args:
        expression: The expression to test (must be a YesNoLiteral).
        expected_value: The expected boolean value.

    Raises:
        AssertionError: If the expression is not a YesNoLiteral or if
            the value doesn't match the expected value.
    """
    assert isinstance(expression, YesNoLiteral), f"Expected YesNoLiteral, got {type(expression).__name__}"
    boolean_literal = expression
    assert boolean_literal.value == expected_value, f"Boolean value={boolean_literal.value} != {expected_value}"
    # Check that the token literal is in canonical form (Yes/No)
    expected_literal = "Yes" if expected_value else "No"
    actual_literal = boolean_literal.token.literal
    assert actual_literal == expected_literal, f"Boolean token literal={actual_literal} != {expected_literal}"


def assert_infix_expression(
    expression: Expression,
    left_value: Any,
    operator: str,
    right_value: Any,
) -> None:
    """Assert that an infix expression has the expected values and operator.

    This function verifies that an expression is an InfixExpression with the
    correct operator and operand values. It uses assert_literal_expression to
    check the operands.

    Args:
        expression: The expression to verify (must be an InfixExpression).
        left_value: Expected value of the left operand.
        operator: Expected operator string.
        right_value: Expected value of the right operand.

    Raises:
        AssertionError: If the expression is not an InfixExpression or if any
            part of the expression doesn't match expectations.
    """
    assert isinstance(expression, InfixExpression), f"Expected InfixExpression, got {type(expression).__name__}"

    # Check the operator
    assert expression.operator == operator, f"Expected operator '{operator}', got '{expression.operator}'"

    # Check left operand
    assert expression.left is not None, "Left operand is None"
    assert_literal_expression(expression.left, left_value)

    # Check right operand
    assert expression.right is not None, "Right operand is None"
    assert_literal_expression(expression.right, right_value)
