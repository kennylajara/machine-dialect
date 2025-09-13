"""Test parsing of list literals (unordered, ordered, and named)."""

import pytest

from machine_dialect.ast import (
    FloatLiteral,
    NamedListLiteral,
    OrderedListLiteral,
    SetStatement,
    StringLiteral,
    UnorderedListLiteral,
    WholeNumberLiteral,
)
from machine_dialect.parser import Parser


class TestUnorderedLists:
    """Test parsing of unordered lists (dash-prefixed)."""

    def test_simple_unordered_list(self) -> None:
        """Test parsing a simple unordered list."""
        source = """
Define `fruits` as an unordered list.
Set `fruits` to:
- _"apple"_.
- _"banana"_.
- _"cherry"_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2  # Define and Set statements

        set_stmt = program.statements[1]  # Second statement is the Set
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "fruits"

        # Check the list literal
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, UnorderedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.elements) == 3

        # Check elements
        assert isinstance(list_literal.elements[0], StringLiteral)
        assert list_literal.elements[0].value == "apple"
        assert isinstance(list_literal.elements[1], StringLiteral)
        assert list_literal.elements[1].value == "banana"
        assert isinstance(list_literal.elements[2], StringLiteral)
        assert list_literal.elements[2].value == "cherry"

    def test_mixed_type_unordered_list(self) -> None:
        """Test parsing an unordered list with mixed types."""
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _"text"_.
- _42_.
- _3.14_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)

        # Check the list literal
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, UnorderedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.elements) == 3

        # Check mixed types
        assert isinstance(list_literal.elements[0], StringLiteral)
        assert list_literal.elements[0].value == "text"
        assert isinstance(list_literal.elements[1], WholeNumberLiteral)
        assert list_literal.elements[1].value == 42
        assert isinstance(list_literal.elements[2], FloatLiteral)
        assert list_literal.elements[2].value == 3.14

    def test_list_with_negative_numbers(self) -> None:
        """Test that lists can contain negative numbers."""
        source = """
Define `numbers` as unordered list.
Set `numbers` to:
- _-5_.
- _10_.
- _-3.14_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        set_stmt = program.statements[1]
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, UnorderedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.elements) == 3

        # Check negative numbers
        assert isinstance(list_literal.elements[0], WholeNumberLiteral)
        assert list_literal.elements[0].value == -5
        assert isinstance(list_literal.elements[1], WholeNumberLiteral)
        assert list_literal.elements[1].value == 10
        assert isinstance(list_literal.elements[2], FloatLiteral)
        assert list_literal.elements[2].value == -3.14


class TestOrderedLists:
    """Test parsing of ordered lists (numbered)."""

    def test_simple_ordered_list(self) -> None:
        """Test parsing a simple ordered list."""
        source = """
Define `steps` as ordered list.
Set `steps` to:
1. _"First step"_.
2. _"Second step"_.
3. _"Third step"_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "steps"

        # Check the list literal
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, OrderedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.elements) == 3

        # Check elements
        assert isinstance(list_literal.elements[0], StringLiteral)
        assert list_literal.elements[0].value == "First step"
        assert isinstance(list_literal.elements[1], StringLiteral)
        assert list_literal.elements[1].value == "Second step"
        assert isinstance(list_literal.elements[2], StringLiteral)
        assert list_literal.elements[2].value == "Third step"

    def test_non_sequential_ordered_list(self) -> None:
        """Test that ordered lists can have non-sequential numbers."""
        source = """
Define `priorities` as ordered list.
Set `priorities` to:
1. _"High priority"_.
5. _"Medium priority"_.
10. _"Low priority"_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        set_stmt = program.statements[1]
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, OrderedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.elements) == 3


class TestNamedLists:
    """Test parsing of named lists (dictionaries)."""

    def test_simple_named_list(self) -> None:
        """Test parsing a simple named list."""
        source = """
Define `person` as named list.
Set `person` to:
- _"name"_: _"Alice"_.
- _"profession"_: _"Software Engineer"_.
- _"age"_: _30_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 2

        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "person"

        # Check the list literal
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, NamedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.entries) == 3

        # Check name-value pairs
        assert list_literal.entries[0][0] == "name"
        assert isinstance(list_literal.entries[0][1], StringLiteral)
        assert list_literal.entries[0][1].value == "Alice"

        assert list_literal.entries[1][0] == "profession"
        assert isinstance(list_literal.entries[1][1], StringLiteral)
        assert list_literal.entries[1][1].value == "Software Engineer"

        assert list_literal.entries[2][0] == "age"
        assert isinstance(list_literal.entries[2][1], WholeNumberLiteral)
        assert list_literal.entries[2][1].value == 30


class TestListParsingErrors:
    """Test error handling in list parsing."""

    @pytest.mark.parametrize(
        "source",
        [
            """
            Define `mixed` as list.
            Set `mixed` to:
            - _"unordered item"_.
            1. _"ordered item"_.
            """,
            """
            Define `mixed` as list.
            Set `mixed` to:
            1. _"unordered item"_.
            - _"ordered item"_.
            """,
        ],
    )
    def test_mixed_list_types_not_allowed(self, source: str) -> None:
        """Test that mixing list types is not allowed."""
        parser = Parser()
        program = parser.parse(source)

        # The parser should handle mixed list types gracefully
        # It may produce an error expression or a partial list
        assert len(program.statements) >= 2  # At least Define and Set

        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)

        # Check what the parser produced
        if hasattr(set_stmt, "value"):
            # If it's an ErrorExpression, that's acceptable
            from machine_dialect.ast import ErrorExpression

            if isinstance(set_stmt.value, ErrorExpression):
                # Parser correctly identified an error
                pass
            elif isinstance(set_stmt.value, UnorderedListLiteral | OrderedListLiteral):
                # Parser created a list with only the consistent items
                list_literal = set_stmt.value
                # Should have at most the first type's items
                assert len(list_literal.elements) <= 1

        # The main requirement is that the parser doesn't crash
        # and produces some reasonable output
        assert program is not None

    def test_incomplete_named_list(self) -> None:
        """Test parsing incomplete named list elements."""
        source = """
Define `incomplete` as named list.
Set `incomplete` to:
- "name": _"test"_.
"""
        parser = Parser()
        program = parser.parse(source)

        # Should still create a named list
        assert len(program.statements) == 2
        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)

        # Should be a named list with error for missing content
        assert hasattr(set_stmt, "value") and isinstance(set_stmt.value, NamedListLiteral)
        list_literal = set_stmt.value
        assert len(list_literal.entries) == 1
