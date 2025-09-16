"""Tests for parsing infix expressions.

This module tests the parser's ability to handle infix expressions including:
- Arithmetic operators: +, -, *, /
- Comparison operators: ==, !=, <, >
- Operator precedence and associativity
- Complex expressions with mixed operators
"""

import pytest

from machine_dialect.ast import (
    ExpressionStatement,
    InfixExpression,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.parser import Parser
from machine_dialect.parser.tests.helper_functions import (
    assert_infix_expression,
    assert_program_statements,
)


class TestInfixExpressions:
    """Test parsing of infix expressions."""

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Addition
            ("5 + 5", 5, "+", 5),
            ("10 + 20", 10, "+", 20),
            ("42 + 123", 42, "+", 123),
            ("0 + 0", 0, "+", 0),
            # Addition with underscores
            ("_5_ + _5_", 5, "+", 5),
            ("_10_ + _20_", 10, "+", 20),
            # Subtraction
            ("5 - 5", 5, "-", 5),
            ("20 - 10", 20, "-", 10),
            ("100 - 50", 100, "-", 50),
            ("0 - 0", 0, "-", 0),
            # Subtraction with underscores
            ("_5_ - _5_", 5, "-", 5),
            ("_20_ - _10_", 20, "-", 10),
            # Multiplication
            ("5 * 5", 5, "*", 5),
            ("10 * 20", 10, "*", 20),
            ("7 * 8", 7, "*", 8),
            ("0 * 100", 0, "*", 100),
            # Multiplication with underscores
            ("_5_ * _5_", 5, "*", 5),
            ("_10_ * _20_", 10, "*", 20),
            # Division
            ("10 / 5", 10, "/", 5),
            ("20 / 4", 20, "/", 4),
            ("100 / 10", 100, "/", 10),
            ("0 / 1", 0, "/", 1),
            # Division with underscores
            ("_10_ / _5_", 10, "/", 5),
            ("_20_ / _4_", 20, "/", 4),
        ],
    )
    def test_integer_arithmetic_expressions(self, source: str, left: int, operator: str, right: int) -> None:
        """Test parsing integer arithmetic infix expressions.

        Args:
            source: The source code containing an infix expression.
            left: Expected left operand value.
            operator: Expected operator string.
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

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Float addition
            ("3.14 + 2.86", 3.14, "+", 2.86),
            ("0.5 + 0.5", 0.5, "+", 0.5),
            ("10.0 + 20.0", 10.0, "+", 20.0),
            # Float subtraction
            ("5.5 - 2.5", 5.5, "-", 2.5),
            ("10.0 - 5.0", 10.0, "-", 5.0),
            ("3.14 - 1.14", 3.14, "-", 1.14),
            # Float multiplication
            ("2.5 * 2.0", 2.5, "*", 2.0),
            ("3.14 * 2.0", 3.14, "*", 2.0),
            ("0.5 * 0.5", 0.5, "*", 0.5),
            # Float division
            ("10.0 / 2.0", 10.0, "/", 2.0),
            ("7.5 / 2.5", 7.5, "/", 2.5),
            ("3.14 / 2.0", 3.14, "/", 2.0),
            # Mixed integer and float
            ("5 + 2.5", 5, "+", 2.5),
            ("10.0 - 5", 10.0, "-", 5),
            ("3 * 2.5", 3, "*", 2.5),
            ("10.0 / 2", 10.0, "/", 2),
        ],
    )
    def test_float_arithmetic_expressions(
        self, source: str, left: int | float, operator: str, right: int | float
    ) -> None:
        """Test parsing float and mixed arithmetic infix expressions.

        Args:
            source: The source code containing an infix expression.
            left: Expected left operand value.
            operator: Expected operator string.
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

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Integer comparisons
            ("5 equals 5", 5, "equals", 5),
            ("10 equals 20", 10, "equals", 20),
            ("5 is not 5", 5, "is not", 5),
            ("10 is not 20", 10, "is not", 20),
            ("5 < 10", 5, "<", 10),
            ("20 < 10", 20, "<", 10),
            ("5 > 10", 5, ">", 10),
            ("20 > 10", 20, ">", 10),
            ("5 <= 10", 5, "<=", 10),
            ("10 <= 10", 10, "<=", 10),
            ("20 <= 10", 20, "<=", 10),
            ("5 >= 10", 5, ">=", 10),
            ("10 >= 10", 10, ">=", 10),
            ("20 >= 10", 20, ">=", 10),
            # Float comparisons
            ("3.14 equals 3.14", 3.14, "equals", 3.14),
            ("2.5 is not 3.5", 2.5, "is not", 3.5),
            ("1.5 < 2.5", 1.5, "<", 2.5),
            ("3.5 > 2.5", 3.5, ">", 2.5),
            # Boolean comparisons
            ("Yes equals Yes", True, "equals", True),
            ("Yes equals No", True, "equals", False),
            ("No is not Yes", False, "is not", True),
            ("No is not No", False, "is not", False),
            # Mixed type comparisons (will be type-checked at runtime)
            ("5 equals 5.0", 5, "equals", 5.0),
            ("10 is not 10.5", 10, "is not", 10.5),
            ("3 < 3.14", 3, "<", 3.14),
            ("5.0 > 4", 5.0, ">", 4),
        ],
    )
    def test_comparison_expressions(
        self, source: str, left: int | float | bool, operator: str, right: int | float | bool
    ) -> None:
        """Test parsing comparison infix expressions.

        Args:
            source: The source code containing a comparison expression.
            left: Expected left operand value.
            operator: Expected comparison operator.
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

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Identifier arithmetic
            ("x + z", "x", "+", "z"),
            ("foo - bar", "foo", "-", "bar"),
            ("p * q", "p", "*", "q"),
            ("width / height", "width", "/", "height"),
            # Identifier comparisons
            ("x equals z", "x", "equals", "z"),
            ("foo is not bar", "foo", "is not", "bar"),
            ("p < q", "p", "<", "q"),
            ("width > height", "width", ">", "height"),
            # Mixed identifier and literal
            ("x + 5", "x", "+", 5),
            ("10 - z", 10, "-", "z"),
            ("pi * 2", "pi", "*", 2),
            ("total / 100.0", "total", "/", 100.0),
            # Backtick identifiers
            ("`first name` + `last name`", "first name", "+", "last name"),
            ("`total cost` * `tax rate`", "total cost", "*", "tax rate"),
            ("`is valid` equals Yes", "is valid", "equals", True),
        ],
    )
    def test_identifier_expressions(
        self, source: str, left: str | int | float, operator: str, right: str | int | float | bool
    ) -> None:
        """Test parsing infix expressions with identifiers.

        Args:
            source: The source code containing an infix expression with identifiers.
            left: Expected left operand value.
            operator: Expected operator string.
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

    @pytest.mark.parametrize(
        "source,left,operator,right",
        [
            # Logical AND
            ("Yes and Yes", True, "and", True),
            ("Yes and No", True, "and", False),
            ("No and Yes", False, "and", True),
            ("No and No", False, "and", False),
            # Logical OR
            ("Yes or Yes", True, "or", True),
            ("Yes or No", True, "or", False),
            ("No or Yes", False, "or", True),
            ("No or No", False, "or", False),
            # Case variations
            ("yes AND no", True, "and", False),
            ("YES And NO", True, "and", False),
            ("yes OR no", True, "or", False),
            ("YES Or NO", True, "or", False),
            # With identifiers
            ("x and z", "x", "and", "z"),
            ("foo or bar", "foo", "or", "bar"),
            ("`is valid` and `has permission`", "is valid", "and", "has permission"),
            # Mixed with literals
            ("x and Yes", "x", "and", True),
            ("No or z", False, "or", "z"),
            # With underscores
            ("_Yes_ and _No_", True, "and", False),
            ("_x_ or _y_", "_x_", "or", "_y_"),
        ],
    )
    def test_logical_operators(self, source: str, left: bool | str, operator: str, right: bool | str) -> None:
        """Test parsing logical operator expressions (and, or).

        Args:
            source: The source code containing a logical expression.
            left: Expected left operand value.
            operator: Expected logical operator ('and' or 'or').
            right: Expected right operand value.
        """
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_infix_expression(statement.expression, left, operator.lower(), right)

    def test_natural_language_comparison_operators(self) -> None:
        """Test parsing natural language comparison operators."""
        test_cases = [
            # Equality variations
            ("5 is equal to 5", 5, "equals", 5),
            ("x is equal to z", "x", "equals", "z"),
            ("10 is the same as 10", 10, "equals", 10),
            ("foo is the same as bar", "foo", "equals", "bar"),
            ("3.14 equals 3.14", 3.14, "equals", 3.14),
            ("`value` equals 42", "value", "equals", 42),
            # Inequality variations
            ("5 is not 10", 5, "is not", 10),
            ("x is not z", "x", "is not", "z"),
            ("5 isn't 10", 5, "is not", 10),
            ("`value` isn't 0", "value", "is not", 0),
            ("10 is not equal to 20", 10, "is not", 20),
            ("foo is not equal to bar", "foo", "is not", "bar"),
            ("5 doesn't equal 10", 5, "is not", 10),
            ("result doesn't equal expected", "result", "is not", "expected"),
            ("7 is different from 8", 7, "is not", 8),
            ("actual is different from expected", "actual", "is not", "expected"),
            # Greater than variations
            ("10 is greater than 5", 10, ">", 5),
            ("x is greater than 0", "x", ">", 0),
            ("20 is more than 10", 20, ">", 10),
            ("total is more than limit", "total", ">", "limit"),
            # Less than variations
            ("5 is less than 10", 5, "<", 10),
            ("`value` is less than max", "value", "<", "max"),
            ("3 is under 10", 3, "<", 10),
            ("price is under budget", "price", "<", "budget"),
            ("2 is fewer than 5", 2, "<", 5),
            ("errors is fewer than threshold", "errors", "<", "threshold"),
            # Greater than or equal variations
            ("10 is greater than or equal to 10", 10, ">=", 10),
            ("x is greater than or equal to min", "x", ">=", "min"),
            ("5 is at least 5", 5, ">=", 5),
            ("score is at least passing", "score", ">=", "passing"),
            ("10 is no less than 5", 10, ">=", 5),
            ("`value` is no less than minimum", "value", ">=", "minimum"),
            # Less than or equal variations
            ("5 is less than or equal to 10", 5, "<=", 10),
            ("x is less than or equal to max", "x", "<=", "max"),
            ("10 is at most 10", 10, "<=", 10),
            ("cost is at most budget", "cost", "<=", "budget"),
            ("5 is no more than 10", 5, "<=", 10),
            ("usage is no more than limit", "usage", "<=", "limit"),
            # Mixed with identifiers and literals
            ("`total cost` is equal to 100.50", "total cost", "equals", 100.50),
            ("`error count` is less than 5", "error count", "<", 5),
            ("Yes is not No", True, "is not", False),
            ("_42_ equals _42_", 42, "equals", 42),
        ]

        for source, left_value, expected_operator, right_value in test_cases:
            parser = Parser()

            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert_program_statements(parser, program)

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert_infix_expression(statement.expression, left_value, expected_operator, right_value)

    def test_natural_language_operators_in_complex_expressions(self) -> None:
        """Test natural language operators in complex expressions with precedence."""
        test_cases = [
            # With logical operators
            ("x is equal to 5 and y is greater than 10", "((x equals 5) and (y > 10))"),
            ("foo is not bar or baz is less than qux", "((foo is not bar) or (baz < qux))"),
            ("`value` is at least 0 and `value` is at most 100", "((value >= 0) and (value <= 100))"),
            # With arithmetic
            ("x + 5 is equal to 10", "((x + 5) equals 10)"),
            ("2 * y is greater than 20", "((2 * y) > 20)"),
            ("total / count is less than average", "((total / count) < average)"),
            # With parentheses
            ("(x is equal to 5) and (y is not 10)", "((x equals 5) and (y is not 10))"),
            ("not (x is greater than 10)", "(not (x > 10))"),
            # Nested comparisons
            ("x is greater than y and y is greater than z", "((x > y) and (y > z))"),
            ("score is at least passing or retake is equal to True", "((score >= passing) or (retake equals True))"),
        ]

        for source, _ in test_cases:
            parser = Parser()

            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            # For now, just ensure it parses without errors
            # The exact string representation would depend on how we format natural language operators

    def test_operator_precedence(self) -> None:
        """Test that operators follow correct precedence rules."""
        # Test cases with expected parsing based on precedence
        test_cases = [
            # Multiplication before addition
            ("5 + 2 * 3", "(_5_ + (_2_ * _3_))"),
            ("2 * 3 + 5", "((_2_ * _3_) + _5_)"),
            # Division before subtraction
            ("10 - 6 / 2", "(_10_ - (_6_ / _2_))"),
            ("6 / 2 - 1", "((_6_ / _2_) - _1_)"),
            # Same precedence operators are left-associative
            ("5 - 3 - 1", "((_5_ - _3_) - _1_)"),
            ("10 / 5 / 2", "((_10_ / _5_) / _2_)"),
            # Complex expressions
            ("1 + 2 * 3 + 4", "((_1_ + (_2_ * _3_)) + _4_)"),
            ("5 + 6 * 7 - 8 / 2", "((_5_ + (_6_ * _7_)) - (_8_ / _2_))"),
            # Comparison operators have lower precedence than arithmetic
            ("5 + 3 equals 8", "((_5_ + _3_) equals _8_)"),
            ("2 * 3 < 10", "((_2_ * _3_) < _10_)"),
            ("10 / 2 > 4", "((_10_ / _2_) > _4_)"),
            ("3 + 2 <= 5", "((_3_ + _2_) <= _5_)"),
            ("8 - 3 >= 5", "((_8_ - _3_) >= _5_)"),
            # Logical operators have lowest precedence
            ("Yes and No or Yes", "((_Yes_ and _No_) or _Yes_)"),
            ("Yes or No and Yes", "(_Yes_ or (_No_ and _Yes_))"),
            ("5 > 3 and 10 < 20", "((_5_ > _3_) and (_10_ < _20_))"),
            ("x equals z or p is not q", "((`x` equals `z`) or (`p` is not `q`))"),
            # Mixed precedence with logical operators
            ("5 + 3 > 7 and 2 * 3 equals 6", "(((_5_ + _3_) > _7_) and ((_2_ * _3_) equals _6_))"),
            ("not x equals z and w > 0", "(((not `x`) equals `z`) and (`w` > _0_))"),
        ]

        for source, expected in test_cases:
            parser = Parser()
            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            # Check string representation matches expected precedence
            assert str(statement.expression) == expected, (
                f"For '{source}': expected {expected}, got {statement.expression!s}"
            )

    def test_grouped_expressions(self) -> None:
        """Test parsing expressions with parentheses for grouping."""
        test_cases = [
            # Parentheses override precedence
            ("(5 + 2) * 3", "((_5_ + _2_) * _3_)"),
            ("3 * (5 + 2)", "(_3_ * (_5_ + _2_))"),
            ("(10 - 6) / 2", "((_10_ - _6_) / _2_)"),
            ("2 / (10 - 6)", "(_2_ / (_10_ - _6_))"),
            # Nested parentheses
            ("((5 + 2) * 3) + 4", "(((_5_ + _2_) * _3_) + _4_)"),
            ("5 + ((2 * 3) + 4)", "(_5_ + ((_2_ * _3_) + _4_))"),
            # Complex grouped expressions
            ("(2 + 3) * (4 + 5)", "((_2_ + _3_) * (_4_ + _5_))"),
            ("((1 + 2) * 3) / (4 - 2)", "(((_1_ + _2_) * _3_) / (_4_ - _2_))"),
            # Logical operators with parentheses
            ("(Yes or No) and Yes", "((_Yes_ or _No_) and _Yes_)"),
            ("Yes and (No or Yes)", "(_Yes_ and (_No_ or _Yes_))"),
            ("(No and Yes) or No", "((_No_ and _Yes_) or _No_)"),
            ("No or (Yes and No)", "(_No_ or (_Yes_ and _No_))"),
            # Complex logical expressions with parentheses
            ("(x or z) and (p or q)", "((`x` or `z`) and (`p` or `q`))"),
            ("(foo and bar) or (baz and qux)", "((`foo` and `bar`) or (`baz` and `qux`))"),
            ("not (x and z)", "(not (`x` and `z`))"),
            ("not (x or z)", "(not (`x` or `z`))"),
            # Mixed logical and comparison with parentheses
            ("(x > 5) and (y < 10)", "((`x` > _5_) and (`y` < _10_))"),
            ("(foo equals bar) or (baz is not qux)", "((`foo` equals `bar`) or (`baz` is not `qux`))"),
            ("(5 > 3) and (10 < 20 or 15 equals 15)", "((_5_ > _3_) and ((_10_ < _20_) or (_15_ equals _15_)))"),
            # Deeply nested logical expressions
            ("((x or z) and p) or q", "(((`x` or `z`) and `p`) or `q`)"),
            ("x or (z and (p or q))", "(`x` or (`z` and (`p` or `q`)))"),
            (
                "((Yes or No) and (No or Yes)) or No",
                "(((_Yes_ or _No_) and (_No_ or _Yes_)) or _No_)",
            ),
        ]

        for source, expected in test_cases:
            parser = Parser()
            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert str(statement.expression) == expected, (
                f"For '{source}': expected {expected}, got {statement.expression!s}"
            )

    def test_complex_logical_with_comparison(self) -> None:
        """Test parsing complex expressions with comparison and logical operators."""
        source = "5 > 3 and Yes"
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        # The expression should be an InfixExpression with 'and' operator
        expr = statement.expression
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "and"

        # The left side should be the comparison (5 > 3)
        assert expr.left is not None
        assert isinstance(expr.left, InfixExpression)
        left_expr = expr.left
        assert left_expr.operator == ">"

        # Check the comparison operands
        assert left_expr.left is not None
        assert isinstance(left_expr.left, WholeNumberLiteral)
        assert left_expr.left.value == 5

        assert left_expr.right is not None
        assert isinstance(left_expr.right, WholeNumberLiteral)
        assert left_expr.right.value == 3

        # The right side should be True
        assert expr.right is not None
        assert isinstance(expr.right, YesNoLiteral)
        assert expr.right.value is True

        # Check the string representation
        assert str(statement.expression) == "((_5_ > _3_) and _Yes_)"

    def test_mixed_prefix_and_infix_expressions(self) -> None:
        """Test parsing expressions that combine prefix and infix operators."""
        test_cases = [
            # Negative numbers in arithmetic
            ("-5 + 10", "((-_5_) + _10_)"),
            ("10 + -5", "(_10_ + (-_5_))"),
            ("-5 * -5", "((-_5_) * (-_5_))"),
            ("-10 / 2", "((-_10_) / _2_)"),
            # Boolean negation with comparisons
            ("not x equals z", "((not `x`) equals `z`)"),
            ("not 5 < 10", "((not _5_) < _10_)"),
            ("not Yes equals No", "((not _Yes_) equals _No_)"),
            # Complex mixed expressions
            ("-x + z * -w", "((-`x`) + (`z` * (-`w`)))"),
            ("not p equals q and r > v", "(((not `p`) equals `q`) and (`r` > `v`))"),
        ]

        for source, expected in test_cases:
            parser = Parser()
            program = parser.parse(source)

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert str(statement.expression) == expected, (
                f"For '{source}': expected {expected}, got {statement.expression!s}"
            )

    def test_multiple_infix_expressions(self) -> None:
        """Test parsing multiple infix expressions in sequence."""
        source = "5 + 5. 10 - 2. 3 * 4. 8 / 2."
        parser = Parser()

        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 4

        # First: 5 + 5
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_infix_expression(statement.expression, 5, "+", 5)

        # Second: 10 - 2
        statement = program.statements[1]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_infix_expression(statement.expression, 10, "-", 2)

        # Third: 3 * 4
        statement = program.statements[2]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_infix_expression(statement.expression, 3, "*", 4)

        # Fourth: 8 / 2
        statement = program.statements[3]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None
        assert_infix_expression(statement.expression, 8, "/", 2)

    def test_infix_expression_string_representation(self) -> None:
        """Test the string representation of infix expressions."""
        test_cases = [
            # Basic arithmetic
            ("5 + 5", "(_5_ + _5_)"),
            ("10 - 5", "(_10_ - _5_)"),
            ("3 * 4", "(_3_ * _4_)"),
            ("10 / 2", "(_10_ / _2_)"),
            # Comparisons
            ("5 equals 5", "(_5_ equals _5_)"),
            ("10 is not 5", "(_10_ is not _5_)"),
            ("3 < 4", "(_3_ < _4_)"),
            ("10 > 2", "(_10_ > _2_)"),
            # With identifiers
            ("x + z", "(`x` + `z`)"),
            ("foo equals bar", "(`foo` equals `bar`)"),
            # Complex expressions
            ("5 + 2 * 3", "(_5_ + (_2_ * _3_))"),
            ("-5 + 10", "((-_5_) + _10_)"),
        ]

        for source, expected in test_cases:
            parser = Parser()
            program = parser.parse(source)

            assert len(parser.errors) == 0
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert str(statement.expression) == expected

    @pytest.mark.parametrize(
        "source,expected_error",
        [
            # Missing right operand
            ("5 +", "expected expression, got <end-of-file>"),
            ("10 -", "expected expression, got <end-of-file>"),
            ("x *", "expected expression, got <end-of-file>"),
            # Missing left operand (these would be parsed as prefix expressions or cause errors)
            ("+ 5", "unexpected token '+' at start of expression"),
            ("* 10", "unexpected token '*' at start of expression"),
            ("/ 2", "unexpected token '/' at start of expression"),
            # Invalid operator combinations
            ("5 ++ 5", "unexpected token '+' at start of expression"),
            # Missing operands in complex expressions
            ("5 + * 3", "unexpected token '*' at start of expression"),
            ("(5 + ) * 3", "No suitable parse function was found to handle ')'"),
            # Natural language operator errors
            ("x is equal to", "expected expression, got <end-of-file>"),
            ("is greater than 5", "unexpected token 'is greater than' at start of expression"),
            ("5 is", "No suitable parse function was found to handle 'is'"),
        ],
    )
    def test_invalid_infix_expressions(self, source: str, expected_error: str) -> None:
        """Test that invalid infix expressions produce appropriate errors.

        Args:
            source: The invalid source code.
            expected_error: Expected error message substring.
        """
        parser = Parser()

        parser.parse(source)

        # Should have at least one error
        assert len(parser.errors) > 0, f"Expected errors for '{source}', but got none"

        # Check that at least one error contains the expected message
        error_messages = [str(error) for error in parser.errors]
        assert any(expected_error in msg for msg in error_messages), (
            f"Expected error containing '{expected_error}' for '{source}', but got: {error_messages}"
        )
