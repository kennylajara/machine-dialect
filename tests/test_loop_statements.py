"""Comprehensive tests for loop statements in Machine Dialect™.

Tests both while loops and for-each loops, including:
- Basic parsing
- Nested loops
- Loop desugaring
- Error cases
"""

import pytest

from machine_dialect.ast import (
    BlockStatement,
    ForEachStatement,
    Identifier,
    InfixExpression,
    OrderedListLiteral,
    SetStatement,
    WhileStatement,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.parser import Parser


class TestWhileLoops:
    """Test while loop parsing and execution."""

    def test_parse_simple_while_loop(self) -> None:
        """Test parsing a simple while loop."""
        source = """
While `count` < 10:
> Set `count` to `count` + 1.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        while_stmt = program.statements[0]
        assert isinstance(while_stmt, WhileStatement)

        # Check condition
        assert while_stmt.condition is not None
        assert isinstance(while_stmt.condition, InfixExpression)
        assert while_stmt.condition.operator == "<"

        # Check body
        assert while_stmt.body is not None
        assert isinstance(while_stmt.body, BlockStatement)
        assert len(while_stmt.body.statements) == 1

        # Check the set statement in body
        set_stmt = while_stmt.body.statements[0]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name is not None
        assert set_stmt.name.value == "count"

    def test_parse_while_with_complex_condition(self) -> None:
        """Test while loop with complex boolean condition."""
        source = """
While `x` > 0 and `y` < 100:
> Set `x` to `x` - 1.
> Set `y` to `y` + 2.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        while_stmt = program.statements[0]
        assert isinstance(while_stmt, WhileStatement)

        # Check compound condition
        assert while_stmt.condition is not None
        assert isinstance(while_stmt.condition, InfixExpression)
        assert while_stmt.condition.operator == "and"

        # Check body has two statements
        assert while_stmt.body is not None
        assert len(while_stmt.body.statements) == 2

    def test_nested_while_loops(self) -> None:
        """Test nested while loops."""
        # Note: Empty '>' line is required after nested block due to parser limitation
        source = """
While `i` < 3:
> While `j` < 2:
>> Set `total` to `total` + 1.
>
> Set `i` to `i` + 1.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        outer_while = program.statements[0]
        assert isinstance(outer_while, WhileStatement)

        # Check outer body contains nested while
        assert outer_while.body is not None
        assert len(outer_while.body.statements) == 2

        inner_while = outer_while.body.statements[0]
        assert isinstance(inner_while, WhileStatement)

        # Check inner while body
        assert inner_while.body is not None
        assert len(inner_while.body.statements) == 1

    def test_while_empty_body_error(self) -> None:
        """Test that empty while body produces an error."""
        source = """
While `x` < 10:
"""
        parser = Parser()
        program = parser.parse(source)

        # Should still parse but with error recorded
        assert program is not None
        assert len(parser.errors) > 0
        # Check that the error message mentions empty body
        error_msg = str(parser.errors[0])
        assert "empty" in error_msg.lower()


class TestForEachLoops:
    """Test for-each loop parsing and desugaring."""

    def test_parse_simple_for_each(self) -> None:
        """Test parsing a simple for-each loop."""
        source = """
For each `item` in `list`:
> Say `item`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        for_stmt = program.statements[0]
        assert isinstance(for_stmt, ForEachStatement)

        # Check loop variable
        assert for_stmt.item is not None
        assert isinstance(for_stmt.item, Identifier)
        assert for_stmt.item.value == "item"

        # Check collection
        assert for_stmt.collection is not None
        assert isinstance(for_stmt.collection, Identifier)
        assert for_stmt.collection.value == "list"

        # Check body
        assert for_stmt.body is not None
        assert len(for_stmt.body.statements) == 1

    @pytest.mark.skip(  # type: ignore[misc]
        reason="List literals with bracket notation [1, 2, 3] are not yet implemented. "
        "Machine Dialect currently only supports numbered (1. 2. 3.) and dash (- item) list syntax "
        "in specific contexts, but not as inline expressions in for-each loops."
    )
    def test_for_each_with_literal_list(self) -> None:
        """Test for-each with a literal list."""
        source = """
For each `num` in [1, 2, 3]:
> Set `total` to `total` + `num`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        for_stmt = program.statements[0]
        assert isinstance(for_stmt, ForEachStatement)

        # Check collection is a list literal
        assert for_stmt.collection is not None
        assert isinstance(for_stmt.collection, OrderedListLiteral)
        assert len(for_stmt.collection.elements) == 3

    def test_for_each_desugaring(self) -> None:
        """Test that for-each correctly desugars to while loop."""
        source = """
For each `item` in `mylist`:
> Say `item`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        for_stmt = program.statements[0]
        assert isinstance(for_stmt, ForEachStatement)

        # Desugar the for-each statement
        desugared = for_stmt.desugar()

        # Should desugar to a block containing initialization and while loop
        assert isinstance(desugared, BlockStatement)
        # Should have: index init, length init, while loop
        assert len(desugared.statements) == 3

        # Check that the third statement is a while loop
        while_stmt = desugared.statements[2]
        assert isinstance(while_stmt, WhileStatement)

        # Check while condition (index < length)
        assert while_stmt.condition is not None
        assert isinstance(while_stmt.condition, InfixExpression)
        assert while_stmt.condition.operator == "<"

        # Check while body contains item assignment, original body, and increment
        assert while_stmt.body is not None
        # Should have: item = collection[index], Say item, index = index + 1
        assert len(while_stmt.body.statements) >= 2

    def test_nested_for_each_loops(self) -> None:
        """Test nested for-each loops."""
        source = """
For each `row` in `matrix`:
> For each `cell` in `row`:
>> Say `cell`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        outer_for = program.statements[0]
        assert isinstance(outer_for, ForEachStatement)

        # Check outer loop
        assert outer_for.item is not None
        assert outer_for.item.value == "row"
        assert outer_for.collection is not None
        assert isinstance(outer_for.collection, Identifier)
        assert outer_for.collection.value == "matrix"

        # Check inner loop
        assert outer_for.body is not None
        assert len(outer_for.body.statements) == 1

        inner_for = outer_for.body.statements[0]
        assert isinstance(inner_for, ForEachStatement)
        assert inner_for.item is not None
        assert inner_for.item.value == "cell"
        assert inner_for.collection is not None
        assert isinstance(inner_for.collection, Identifier)
        assert inner_for.collection.value == "row"

    def test_for_each_empty_body_error(self) -> None:
        """Test that empty for-each body produces an error."""
        source = """
For each `x` in `list`:
"""
        parser = Parser()
        program = parser.parse(source)

        # Should still parse but with error recorded
        assert program is not None
        assert len(parser.errors) > 0
        # Check that the error message mentions empty body
        error_msg = str(parser.errors[0])
        assert "empty" in error_msg.lower()

    def test_for_each_missing_in_keyword(self) -> None:
        """Test error when 'in' keyword is missing."""
        source = """
For each `item` `list`:
> Say `item`.
"""
        parser = Parser()
        program = parser.parse(source)

        # Should produce error for missing 'in'
        assert program is not None
        assert len(parser.errors) > 0


class TestLoopIntegration:
    """Test loop integration with other language features."""

    def test_loop_with_if_statement(self) -> None:
        """Test loop containing if statement."""
        # Note: Empty '>' line required after nested if block due to parser limitation
        source = """
Define `x` as whole number.
Set `x` to 0.

While `x` < 10:
> If `x` equals 5:
>> Say "halfway".
>
> Set `x` to `x` + 1.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(parser.errors) == 0
        assert len(program.statements) == 3  # Define + Set + While statement

        while_stmt = program.statements[2]  # Third statement is the while loop
        assert isinstance(while_stmt, WhileStatement)
        assert while_stmt.body is not None
        assert len(while_stmt.body.statements) == 2

    def test_loop_with_collection_operations(self) -> None:
        """Test for-each with collection mutations."""
        source = """
For each `item` in `source`:
> Add `item` to `destination`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(parser.errors) == 0
        assert len(program.statements) == 1

    def test_loop_with_function_calls(self) -> None:
        """Test loops with function calls."""
        source = """
Define `running` as Yes/No.
Define `current_batch` as text or empty.
Define `has_more_data` as Yes/No.
Set `running` to Yes.
Set `current_batch` to empty.
Set `has_more_data` to No.

While `running`:
> Use `process_data` with `current_batch`.
> Set `running` to `has_more_data`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(parser.errors) == 0
        assert len(program.statements) == 7  # 3 Define + 3 Set + 1 While statement


class TestLoopStrings:
    """Test string representations of loop statements."""

    def test_while_string_representation(self) -> None:
        """Test WhileStatement __str__ method."""
        # Create tokens
        while_token = Token(TokenType.KW_WHILE, "While", 0, 0)

        # Create a simple condition
        condition = Identifier(Token(TokenType.MISC_IDENT, "x", 0, 0), "x")

        # Create body
        body = BlockStatement(Token(TokenType.OP_GT, ">", 0, 0))

        # Create while statement
        while_stmt = WhileStatement(while_token, condition, body)

        # Check string representation
        str_repr = str(while_stmt)
        assert "While" in str_repr
        assert "x" in str_repr

    def test_for_each_string_representation(self) -> None:
        """Test ForEachStatement __str__ method."""
        # Create tokens
        for_token = Token(TokenType.KW_FOR, "For", 0, 0)

        # Create components
        item = Identifier(Token(TokenType.MISC_IDENT, "item", 0, 0), "item")
        collection = Identifier(Token(TokenType.MISC_IDENT, "list", 0, 0), "list")
        body = BlockStatement(Token(TokenType.OP_GT, ">", 0, 0))

        # Create for-each statement
        for_stmt = ForEachStatement(for_token, item, collection, body)

        # Check string representation
        str_repr = str(for_stmt)
        assert "For each" in str_repr
        assert "item" in str_repr
        assert "in" in str_repr
        assert "list" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
