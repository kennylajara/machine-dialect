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
)
from machine_dialect.lexer import Lexer
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
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

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
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

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
            ("5 == 5", 5, "==", 5),
            ("10 == 20", 10, "==", 20),
            ("5 != 5", 5, "!=", 5),
            ("10 != 20", 10, "!=", 20),
            ("5 < 10", 5, "<", 10),
            ("20 < 10", 20, "<", 10),
            ("5 > 10", 5, ">", 10),
            ("20 > 10", 20, ">", 10),
            # Float comparisons
            ("3.14 == 3.14", 3.14, "==", 3.14),
            ("2.5 != 3.5", 2.5, "!=", 3.5),
            ("1.5 < 2.5", 1.5, "<", 2.5),
            ("3.5 > 2.5", 3.5, ">", 2.5),
            # Boolean comparisons
            ("True == True", True, "==", True),
            ("True == False", True, "==", False),
            ("False != True", False, "!=", True),
            ("False != False", False, "!=", False),
            # Mixed type comparisons (will be type-checked at runtime)
            ("5 == 5.0", 5, "==", 5.0),
            ("10 != 10.5", 10, "!=", 10.5),
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
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

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
            ("x == z", "x", "==", "z"),
            ("foo != bar", "foo", "!=", "bar"),
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
            ("`is valid` == True", "is valid", "==", True),
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
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

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
            ("True and True", True, "and", True),
            ("True and False", True, "and", False),
            ("False and True", False, "and", True),
            ("False and False", False, "and", False),
            # Logical OR
            ("True or True", True, "or", True),
            ("True or False", True, "or", False),
            ("False or True", False, "or", True),
            ("False or False", False, "or", False),
            # Case variations
            ("true AND false", True, "and", False),
            ("TRUE And FALSE", True, "and", False),
            ("true OR false", True, "or", False),
            ("TRUE Or FALSE", True, "or", False),
            # With identifiers
            ("x and z", "x", "and", "z"),
            ("foo or bar", "foo", "or", "bar"),
            ("`is valid` and `has permission`", "is valid", "and", "has permission"),
            # Mixed with literals
            ("x and True", "x", "and", True),
            ("False or z", False, "or", "z"),
            ("5 > 3 and True", True, "and", True),  # This would need precedence handling
            # With underscores
            ("_True_ and _False_", True, "and", False),
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
        # Special handling for complex precedence cases
        if source == "5 > 3 and True":
            # This would be parsed as ((5 > 3) and True)
            # For now, we'll skip this complex case
            pytest.skip("Complex precedence case - needs special handling")

        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert_program_statements(parser, program)

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        assert_infix_expression(statement.expression, left, operator.lower(), right)

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
            ("5 + 3 == 8", "((_5_ + _3_) == _8_)"),
            ("2 * 3 < 10", "((_2_ * _3_) < _10_)"),
            ("10 / 2 > 4", "((_10_ / _2_) > _4_)"),
            # Logical operators have lowest precedence
            ("True and False or True", "((_True_ and _False_) or _True_)"),
            ("True or False and True", "(_True_ or (_False_ and _True_))"),
            ("5 > 3 and 10 < 20", "((_5_ > _3_) and (_10_ < _20_))"),
            ("x == z or p != q", "((`x` == `z`) or (`p` != `q`))"),
            # Mixed precedence with logical operators
            ("5 + 3 > 7 and 2 * 3 == 6", "(((_5_ + _3_) > _7_) and ((_2_ * _3_) == _6_))"),
            ("not x == z and w > 0", "(((not `x`) == `z`) and (`w` > _0_))"),
        ]

        for source, expected in test_cases:
            lexer = Lexer(source)
            parser = Parser(lexer)
            program = parser.parse()

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            # Check string representation matches expected precedence
            assert (
                str(statement.expression) == expected
            ), f"For '{source}': expected {expected}, got {statement.expression!s}"

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
        ]

        for source, expected in test_cases:
            lexer = Lexer(source)
            parser = Parser(lexer)
            program = parser.parse()

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert (
                str(statement.expression) == expected
            ), f"For '{source}': expected {expected}, got {statement.expression!s}"

    def test_mixed_prefix_and_infix_expressions(self) -> None:
        """Test parsing expressions that combine prefix and infix operators."""
        test_cases = [
            # Negative numbers in arithmetic
            ("-5 + 10", "((-_5_) + _10_)"),
            ("10 + -5", "(_10_ + (-_5_))"),
            ("-5 * -5", "((-_5_) * (-_5_))"),
            ("-10 / 2", "((-_10_) / _2_)"),
            # Boolean negation with comparisons
            ("not x == z", "((not `x`) == `z`)"),
            ("not 5 < 10", "((not _5_) < _10_)"),
            ("not True == False", "((not _True_) == _False_)"),
            # Complex mixed expressions
            ("-x + z * -w", "((-`x`) + (`z` * (-`w`)))"),
            ("not p == q and r > v", "(((not `p`) == `q`) and (`r` > `v`))"),
        ]

        for source, expected in test_cases:
            lexer = Lexer(source)
            parser = Parser(lexer)
            program = parser.parse()

            assert len(parser.errors) == 0, f"Parser errors for '{source}': {parser.errors}"
            assert len(program.statements) == 1

            statement = program.statements[0]
            assert isinstance(statement, ExpressionStatement)
            assert statement.expression is not None

            assert (
                str(statement.expression) == expected
            ), f"For '{source}': expected {expected}, got {statement.expression!s}"

    def test_multiple_infix_expressions(self) -> None:
        """Test parsing multiple infix expressions in sequence."""
        source = "5 + 5. 10 - 2. 3 * 4. 8 / 2."
        lexer = Lexer(source)
        parser = Parser(lexer)

        program = parser.parse()

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
            ("5 == 5", "(_5_ == _5_)"),
            ("10 != 5", "(_10_ != _5_)"),
            ("3 < 4", "(_3_ < _4_)"),
            ("10 > 2", "(_10_ > _2_)"),
            # With identifiers
            ("x + z", "(`x` + `z`)"),
            ("foo == bar", "(`foo` == `bar`)"),
            # Complex expressions
            ("5 + 2 * 3", "(_5_ + (_2_ * _3_))"),
            ("-5 + 10", "((-_5_) + _10_)"),
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
        ],
    )
    def test_invalid_infix_expressions(self, source: str, expected_error: str) -> None:
        """Test that invalid infix expressions produce appropriate errors.

        Args:
            source: The invalid source code.
            expected_error: Expected error message substring.
        """
        lexer = Lexer(source)
        parser = Parser(lexer)

        parser.parse()

        # Should have at least one error
        assert len(parser.errors) > 0, f"Expected errors for '{source}', but got none"

        # Check that at least one error contains the expected message
        error_messages = [str(error) for error in parser.errors]
        assert any(expected_error in msg for msg in error_messages), (
            f"Expected error containing '{expected_error}' for '{source}', " f"but got: {error_messages}"
        )
