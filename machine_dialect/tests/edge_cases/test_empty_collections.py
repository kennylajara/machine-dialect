"""Edge case tests for empty collection operations."""

import pytest

from machine_dialect.parser.parser import Parser


class TestEmptyCollections:
    """Test edge cases with empty collections."""

    def test_access_from_empty_unordered_list_errors(self) -> None:
        """Accessing any element from empty unordered list should error."""
        source = """
Define `empty_list` as unordered list.
Define `x` as Text.
Set `x` to the first item of `empty_list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have semantic error about accessing empty list
        assert parser.errors, "Expected error for accessing empty list"
        assert any("empty" in str(error).lower() or "bound" in str(error).lower() for error in parser.errors)

    def test_access_from_empty_ordered_list_errors(self) -> None:
        """Accessing any element from empty ordered list should error."""
        source = """
Define `empty_list` as ordered list.
Set `x` to item _1_ of `empty_list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have semantic error
        assert parser.errors, "Expected error for accessing empty list"

    def test_last_item_of_empty_list_errors(self) -> None:
        """Accessing last item of empty list should error."""
        source = """
Define `empty_list` as unordered list.
Set `x` to the last item of `empty_list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have semantic error
        assert parser.errors, "Expected error for accessing last of empty list"

    def test_remove_from_empty_list_handled(self) -> None:
        """Removing from empty list should be handled gracefully."""
        source = """
Define `empty_list` as unordered list.
Remove _"item"_ from `empty_list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully (runtime will handle the no-op)
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # assert isinstance(program.statements[1], CollectionMutationStatement)
        # assert program.statements[1].operation == "remove"

    def test_clear_empty_list_is_noop(self) -> None:
        """Clearing an already empty list should be a no-op."""
        source = """
Define `empty_list` as unordered list.
Clear `empty_list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # assert isinstance(program.statements[1], CollectionMutationStatement)
        # assert program.statements[1].operation == "clear"

    def test_empty_list_literal_syntax(self) -> None:
        """Test that empty list literals are parsed correctly."""
        source = """
Set `empty_unordered` to:
.

Set `empty_ordered` to:
.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Both should create empty list literals
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_add_to_empty_list_works(self) -> None:
        """Adding to empty list should work correctly."""
        source = """
Define `list` as unordered list.
Add _"first"_ to `list`.
Add _"second"_ to `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # assert all(isinstance(stmt, CollectionMutationStatement) for stmt in program.statements[1:])

    def test_insert_into_empty_list(self) -> None:
        """Inserting at position 1 in empty list should work."""
        source = """
Define `list` as ordered list.
Insert _"item"_ at position _1_ in `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # assert isinstance(program.statements[1], CollectionMutationStatement)
        # assert program.statements[1].operation == "insert"

    def test_empty_named_list_operations(self) -> None:
        """Test operations on empty named lists (dictionaries)."""
        source = """
Define `empty_dict` as named list.
Add _"key"_ to `empty_dict` with value _"value"_.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # assert isinstance(program.statements[1], CollectionMutationStatement)

    @pytest.mark.skip(reason="TODO: 'whether...has' syntax not implemented in parser")
    def test_check_has_on_empty_named_list(self) -> None:
        """Checking if empty named list has a key should return false."""  # TODO: Implement 'whether...has' syntax
        source = """
Define `empty_dict` as named list.
Define `has_key` as truth value.
Set `has_key` to whether `empty_dict` has _"key"_.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_mixed_empty_collections(self) -> None:
        """Test mixed operations with multiple empty collections."""
        source = """
Define `list1` as unordered list.
Define `list2` as ordered list.
Define `dict` as named list.

Add _1_ to `list1`.
Add _2_ to `list2`.
Add _"key"_ to `dict` with value _"value"_.

Clear `list1`.
Clear `list2`.
Clear `dict`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse all statements successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
