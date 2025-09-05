"""Tests for conditional (ternary) expressions in the parser.

This module tests the parsing of conditional expressions which follow the pattern:
    consequence if/when/whenever condition, else/otherwise alternative
"""

import pytest

from machine_dialect.ast import (
    ConditionalExpression,
    ExpressionStatement,
    Identifier,
    InfixExpression,
    PrefixExpression,
    StringLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.parser import Parser


class TestConditionalExpressions:
    """Test parsing of conditional/ternary expressions."""

    @pytest.mark.parametrize(
        "source,expected_consequence,expected_condition,expected_alternative",
        [
            # Basic integer literals
            ("1 if Yes, else 0", "1", "Yes", "0"),
            ("1 if Yes, otherwise 0", "1", "Yes", "0"),
            ("1 when Yes, else 0", "1", "Yes", "0"),
            ("1 when Yes, otherwise 0", "1", "Yes", "0"),
            ("1 whenever Yes, else 0", "1", "Yes", "0"),
            ("1 whenever Yes, otherwise 0", "1", "Yes", "0"),
            # Semicolon separator
            ("1 if Yes; else 0", "1", "Yes", "0"),
            ("1 if Yes; otherwise 0", "1", "Yes", "0"),
            ("1 when Yes; else 0", "1", "Yes", "0"),
            ("1 when Yes; otherwise 0", "1", "Yes", "0"),
            ("1 whenever Yes; else 0", "1", "Yes", "0"),
            ("1 whenever Yes; otherwise 0", "1", "Yes", "0"),
        ],
    )
    def test_parse_basic_conditional_expression(
        self, source: str, expected_consequence: str, expected_condition: str, expected_alternative: str
    ) -> None:
        """Test parsing of basic conditional expressions with literals."""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        assert statement.expression is not None

        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check consequence
        assert conditional.consequence is not None
        if expected_consequence in ["Yes", "No"]:
            assert isinstance(conditional.consequence, YesNoLiteral)
            # Already in canonical Yes/No representation
            assert str(conditional.consequence) == f"_{expected_consequence}_"
        else:
            assert isinstance(conditional.consequence, WholeNumberLiteral)
            assert conditional.consequence.value == int(expected_consequence)

        # Check condition
        assert conditional.condition is not None
        assert isinstance(conditional.condition, YesNoLiteral)
        # Already in canonical Yes/No representation
        assert str(conditional.condition) == f"_{expected_condition}_"

        # Check alternative
        assert conditional.alternative is not None
        if expected_alternative in ["Yes", "No"]:
            assert isinstance(conditional.alternative, YesNoLiteral)
            # Already in canonical Yes/No representation
            assert str(conditional.alternative) == f"_{expected_alternative}_"
        else:
            assert isinstance(conditional.alternative, WholeNumberLiteral)
            assert conditional.alternative.value == int(expected_alternative)

    def test_conditional_with_identifiers(self) -> None:
        """Test conditional expressions using identifiers."""
        source = "`result` if `some condition`, else `some value`"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check consequence is an identifier
        assert isinstance(conditional.consequence, Identifier)
        assert conditional.consequence.value == "result"

        # Check condition is an identifier
        assert isinstance(conditional.condition, Identifier)
        assert conditional.condition.value == "some condition"

        # Check alternative is an identifier
        assert isinstance(conditional.alternative, Identifier)
        assert conditional.alternative.value == "some value"

    def test_conditional_with_string_literals(self) -> None:
        """Test conditional expressions with string literals."""
        source = '"yes" if `flag`, else "no"'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check consequence is a string
        assert isinstance(conditional.consequence, StringLiteral)
        assert conditional.consequence.value == "yes"

        # Check condition is an identifier
        assert isinstance(conditional.condition, Identifier)
        assert conditional.condition.value == "flag"

        # Check alternative is a string
        assert isinstance(conditional.alternative, StringLiteral)
        assert conditional.alternative.value == "no"

    def test_conditional_with_complex_condition(self) -> None:
        """Test conditional with complex boolean condition."""
        source = "1 if `x` > 0, else -1"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check consequence
        assert isinstance(conditional.consequence, WholeNumberLiteral)
        assert conditional.consequence.value == 1

        # Check condition is an infix expression
        assert isinstance(conditional.condition, InfixExpression)
        assert conditional.condition.operator == ">"
        assert isinstance(conditional.condition.left, Identifier)
        assert conditional.condition.left.value == "x"
        assert isinstance(conditional.condition.right, WholeNumberLiteral)
        assert conditional.condition.right.value == 0

        # Check alternative
        # TODO: In the future, negative numbers should be parsed as WholeNumberLiteral, not PrefixExpression
        assert isinstance(conditional.alternative, PrefixExpression)
        assert conditional.alternative.operator == "-"
        assert isinstance(conditional.alternative.right, WholeNumberLiteral)
        assert conditional.alternative.right.value == 1

    def test_nested_conditional_expressions(self) -> None:
        """Test nested conditional expressions."""
        source = "1 if `a`, else 2 if `b`, else 3"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        outer_conditional = statement.expression
        assert isinstance(outer_conditional, ConditionalExpression)

        # Check outer consequence
        assert isinstance(outer_conditional.consequence, WholeNumberLiteral)
        assert outer_conditional.consequence.value == 1

        # Check outer condition
        assert isinstance(outer_conditional.condition, Identifier)
        assert outer_conditional.condition.value == "a"

        # Check outer alternative is another conditional
        inner_conditional = outer_conditional.alternative
        assert isinstance(inner_conditional, ConditionalExpression)

        # Check inner conditional
        assert isinstance(inner_conditional.consequence, WholeNumberLiteral)
        assert inner_conditional.consequence.value == 2
        assert isinstance(inner_conditional.condition, Identifier)
        assert inner_conditional.condition.value == "b"
        assert isinstance(inner_conditional.alternative, WholeNumberLiteral)
        assert inner_conditional.alternative.value == 3

    def test_conditional_with_arithmetic_expressions(self) -> None:
        """Test conditional with arithmetic expressions."""
        source = "`x` + 1 if `flag`, else `x` - 1"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check consequence is an addition
        assert isinstance(conditional.consequence, InfixExpression)
        assert conditional.consequence.operator == "+"
        assert isinstance(conditional.consequence.left, Identifier)
        assert conditional.consequence.left.value == "x"
        assert isinstance(conditional.consequence.right, WholeNumberLiteral)
        assert conditional.consequence.right.value == 1

        # Check condition
        assert isinstance(conditional.condition, Identifier)
        assert conditional.condition.value == "flag"

        # Check alternative is a subtraction
        assert isinstance(conditional.alternative, InfixExpression)
        assert conditional.alternative.operator == "-"
        assert isinstance(conditional.alternative.left, Identifier)
        assert conditional.alternative.left.value == "x"
        assert isinstance(conditional.alternative.right, WholeNumberLiteral)
        assert conditional.alternative.right.value == 1

    def test_conditional_string_representation(self) -> None:
        """Test the string representation of conditional expressions."""
        source = "1 if Yes, else 0"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression

        # Check string representation
        assert str(conditional) == "(_1_ if _Yes_ else _0_)"

    def test_conditional_with_logical_operators(self) -> None:
        """Test conditional with logical operators in condition."""
        source = "1 if `a` and `b`, else 0"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check condition is a logical AND
        assert isinstance(conditional.condition, InfixExpression)
        assert conditional.condition.operator == "and"
        assert isinstance(conditional.condition.left, Identifier)
        assert conditional.condition.left.value == "a"
        assert isinstance(conditional.condition.right, Identifier)
        assert conditional.condition.right.value == "b"

    def test_conditional_without_else_clause(self) -> None:
        """Test that conditional without else clause is handled gracefully."""
        source = "1 if True"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Check that alternative is None when else clause is missing
        assert conditional.consequence is not None
        assert conditional.condition is not None
        assert conditional.alternative is None

    @pytest.mark.parametrize(
        "keyword",
        ["if", "when", "whenever"],
    )
    def test_all_condition_keywords(self, keyword: str) -> None:
        """Test that all condition keywords work correctly."""
        source = f"1 {keyword} Yes, else 0"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Verify the expression was parsed correctly
        assert isinstance(conditional.consequence, WholeNumberLiteral)
        assert conditional.consequence.value == 1
        assert isinstance(conditional.condition, YesNoLiteral)
        assert isinstance(conditional.alternative, WholeNumberLiteral)
        assert conditional.alternative.value == 0

    @pytest.mark.parametrize(
        "else_keyword",
        ["else", "otherwise"],
    )
    def test_all_else_keywords(self, else_keyword: str) -> None:
        """Test that all else keywords work correctly."""
        source = f"1 if Yes, {else_keyword} 0"
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        statement = program.statements[0]
        assert isinstance(statement, ExpressionStatement)
        conditional = statement.expression
        assert isinstance(conditional, ConditionalExpression)

        # Verify the expression was parsed correctly
        assert isinstance(conditional.consequence, WholeNumberLiteral)
        assert conditional.consequence.value == 1
        assert isinstance(conditional.condition, YesNoLiteral)
        assert isinstance(conditional.alternative, WholeNumberLiteral)
        assert conditional.alternative.value == 0
