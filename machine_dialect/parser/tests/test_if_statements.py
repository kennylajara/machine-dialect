"""Tests for if statements with block statements in the parser.

This module tests the parsing of if statements which support blocks of statements
marked by '>' symbols for depth tracking.
"""

import pytest

from machine_dialect.ast import (
    BlockStatement,
    Identifier,
    IfStatement,
    InfixExpression,
    SetStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.parser import Parser


class TestIfStatements:
    """Test parsing of if statements with block statements."""

    def test_parse_basic_if_statement(self) -> None:
        """Test parsing of basic if statement with single statement in block."""
        source = """
        if Yes then:
        > Set x to 1.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.condition, YesNoLiteral)
        assert if_stmt.condition.value is True

        assert isinstance(if_stmt.consequence, BlockStatement)
        assert if_stmt.consequence.depth == 1
        assert len(if_stmt.consequence.statements) == 1

        set_stmt = if_stmt.consequence.statements[0]
        assert isinstance(set_stmt, SetStatement)
        assert isinstance(set_stmt.name, Identifier)
        assert set_stmt.name.value == "x"
        assert isinstance(set_stmt.value, WholeNumberLiteral)
        assert set_stmt.value.value == 1

        assert if_stmt.alternative is None

    def test_parse_if_else_statement(self) -> None:
        """Test parsing of if-else statement with blocks."""
        source = """
        if Yes then:
        > Set x to 1.
        > Set y to 2.
        else:
        > Set x to 3.
        > Set y to 4.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.condition, YesNoLiteral)
        assert if_stmt.condition.value is True

        # Check consequence block
        assert isinstance(if_stmt.consequence, BlockStatement)
        assert if_stmt.consequence.depth == 1
        assert len(if_stmt.consequence.statements) == 2

        # Check alternative block
        assert if_stmt.alternative is not None
        assert isinstance(if_stmt.alternative, BlockStatement)
        assert if_stmt.alternative.depth == 1
        assert len(if_stmt.alternative.statements) == 2

    def test_parse_nested_if_statements(self) -> None:
        """Test parsing of nested if statements with proper depth."""
        source = """
        if Yes then:
        >
        > Set foo to 1.
        >
        > if No then:
        > >
        > > Set bar to 2.
        > > Set baz to 3.
        >
        > Set bax to 4.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        outer_if = program.statements[0]
        assert isinstance(outer_if, IfStatement)

        assert isinstance(outer_if.consequence, BlockStatement)
        assert outer_if.consequence.depth == 1
        assert len(outer_if.consequence.statements) == 3

        # First statement in outer block
        assert isinstance(outer_if.consequence.statements[0], SetStatement)

        # Nested if statement
        inner_if = outer_if.consequence.statements[1]
        assert isinstance(inner_if, IfStatement)
        assert isinstance(inner_if.consequence, BlockStatement)
        assert inner_if.consequence.depth == 2
        assert len(inner_if.consequence.statements) == 2

        # Last statement in outer block
        assert isinstance(outer_if.consequence.statements[2], SetStatement)

    @pytest.mark.parametrize(
        "keyword,else_keyword",
        [
            ("if", "else"),
            ("if", "otherwise"),
            ("when", "else"),
            ("when", "otherwise"),
            ("whenever", "else"),
            ("whenever", "otherwise"),
        ],
    )
    def test_parse_if_keywords_variations(self, keyword: str, else_keyword: str) -> None:
        """Test parsing of if statements with different keyword variations."""
        source = f"""
        {keyword} Yes then:
        > Set x to 1.
        {else_keyword}:
        > Set x to 2.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.condition, YesNoLiteral)
        assert if_stmt.condition.value is True

        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 1

        assert if_stmt.alternative is not None
        assert isinstance(if_stmt.alternative, BlockStatement)
        assert len(if_stmt.alternative.statements) == 1

    def test_parse_if_with_complex_condition(self) -> None:
        """Test parsing of if statement with complex boolean expression."""
        source = """
        if x > 5 and y < 10 then:
        > Set result to True.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.condition, InfixExpression)
        assert if_stmt.condition.operator == "and"

        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 1

    def test_parse_empty_blocks(self) -> None:
        """Test parsing of if statement with empty blocks."""
        source = """
        if Yes then:
        >
        else:
        >
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 0

        assert if_stmt.alternative is not None
        assert isinstance(if_stmt.alternative, BlockStatement)
        assert len(if_stmt.alternative.statements) == 0

    def test_parse_if_without_then_keyword(self) -> None:
        """Test parsing of if statement with colon directly after condition."""
        source = """
        if Yes:
        > Set x to 1.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], IfStatement)

        if_stmt = program.statements[0]
        assert isinstance(if_stmt.condition, YesNoLiteral)
        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 1

    def test_block_depth_tracking(self) -> None:
        """Test that block depth is properly tracked and validated."""
        source = """
        if Yes then:
        > Set x to 1.
        > > Set y to 2.
        """
        parser = Parser()
        parser.parse(source)

        # This should produce an error - depth suddenly increases
        assert len(parser.errors) > 0
        assert any("depth" in str(error).lower() for error in parser.errors)

    def test_missing_period_error(self) -> None:
        """Test that missing periods generate appropriate errors."""
        source = """
        if Yes then:
        > Set x to 1

        x
        """
        parser = Parser()
        parser.parse(source)

        # Should have errors about missing period
        assert len(parser.errors) > 0
        assert any("period" in str(error).lower() or "TokenType.PUNCT_PERIOD" in str(error) for error in parser.errors)

    def test_multiple_if_statements(self) -> None:
        """Test parsing multiple if statements in sequence."""
        source = """
        if Yes then:
        > Set x to 1.

        if No then:
        > Set y to 2.
        else:
        > Set y to 3.
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 2
        assert all(isinstance(stmt, IfStatement) for stmt in program.statements)

        # First if statement
        if_stmt1 = program.statements[0]
        assert isinstance(if_stmt1, IfStatement)
        assert isinstance(if_stmt1.condition, YesNoLiteral)
        assert if_stmt1.condition.value is True
        assert if_stmt1.alternative is None

        # Second if statement
        if_stmt2 = program.statements[1]
        assert isinstance(if_stmt2, IfStatement)
        assert isinstance(if_stmt2.condition, YesNoLiteral)
        assert if_stmt2.condition.value is False
        assert if_stmt2.alternative is not None

    def test_if_statements_with_empty_lines(self) -> None:
        """Test parsing multiple if statements in sequence."""
        source = """
        if No then:
        >
        > Set y to 2.
        >
        else:
        >
        > Set y to 3.
        >
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        assert all(isinstance(stmt, IfStatement) for stmt in program.statements)

        # If statement
        if_stmt = program.statements[0]
        assert isinstance(if_stmt, IfStatement)
        assert isinstance(if_stmt.condition, YesNoLiteral)
        assert if_stmt.condition.value is False
        assert if_stmt.alternative is not None
