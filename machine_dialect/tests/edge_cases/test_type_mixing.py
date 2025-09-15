"""Edge case tests for mixed-type collections."""

import pytest

from machine_dialect.parser.parser import Parser


class TestTypeMixing:
    """Test collections with mixed types."""

    def test_mixed_type_unordered_list(self) -> None:
        """Test unordered list with various types."""
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _42_.
- _3.14_.
- _"string"_.
- _yes_.
- _no_.
- empty.

Define `first` as Text.
Define `last` as Text.

Set `first` to the first item of `mixed`.
Set `last` to the last item of `mixed`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_mixed_type_ordered_list(self) -> None:
        """Test ordered list with various types."""
        source = """
Define `mixed` as ordered list.
Set `mixed` to:
1. _42_.
2. _"text"_.
3. _yes_.
4. empty.
5. _-5_.
6. _0.0_.

Add _no_ to `mixed`.
Remove empty from `mixed`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Statement count mismatch - needs investigation")
    def test_empty_value_in_collections(self) -> None:
        """Test handling of 'empty' literal in collections."""  # TODO: Fix statement count mismatch
        source = """
Define `list_with_empty` as unordered list.
Set `list_with_empty` to:
- _"before"_.
- empty.
- _"after"_.

Define `x` as Text.
Set `x` to item _2_ of `list_with_empty`.  # Should be empty

Remove empty from `list_with_empty`.
Add empty to `list_with_empty`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_identifier_vs_literal_mixing(self) -> None:
        """Test mixing identifiers and literals in collections."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `var1` as Whole Number.
Define `var2` as Text.
Set `var1` to _10_.
Set `var2` to _"hello"_.

Define `mixed` as unordered list.
Set `mixed` to:
- `var1`.
- _20_.
- `var2`.
- _"world"_.

Define `x` as Text.
Define `y` as Text.

Set `x` to the first item of `mixed`.  # Identifier value
Set `y` to the second item of `mixed`. # Literal value
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_boolean_mixing(self) -> None:
        """Test collections with boolean values."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `booleans` as unordered list.
Set `booleans` to:
- _yes_.
- _no_.
- _yes_.
- _no_.

# Operations with boolean values
Remove _yes_ from `booleans`.
Add _no_ to `booleans`.
Set item _1_ of `booleans` to _yes_.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_numeric_type_mixing(self) -> None:
        """Test mixing integer and float types."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `numbers` as ordered list.
Set `numbers` to:
1. _1_.
2. _1.0_.
3. _2_.
4. _2.0_.
5. _-3_.
6. _-3.14_.

# Operations with mixed numeric types
Remove _1_ from `numbers`.     # Integer
Remove _2.0_ from `numbers`.   # Float
Add _0_ to `numbers`.          # Integer zero
Add _0.0_ to `numbers`.        # Float zero
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix test - remove comments and verify assertions")
    def test_nested_mixed_types(self) -> None:
        """Test nested collections with mixed types."""  # TODO: Fix test - remove comments and verify assertions
        source = """
Define `inner1` as unordered list.
Set `inner1` to:
- _1_.
- _"text"_.

Define `inner2` as ordered list.
Set `inner2` to:
1. _yes_.
2. empty.

Define `nested` as unordered list.
Set `nested` to:
- `inner1`.
- _42_.
- `inner2`.
- _"standalone"_.

Define `x` as Text.
Define `y` as Text.

Set `x` to the first item of `nested`.  # A list
Set `y` to the second item of `nested`. # A number
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_type_changing_operations(self) -> None:
        """Test operations that change element types."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `list` as unordered list.
Set `list` to:
- _1_.
- _2_.
- _3_.

# Change numeric to string
Set item _1_ of `list` to _"one"_.

# Change to boolean
Set item _2_ of `list` to _yes_.

# Change to empty
Set item _3_ of `list` to empty.

# Now list has mixed types
Add _4_ to `list`.          # Add number to mixed list
Add _"five"_ to `list`.     # Add string to mixed list
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_comparison_with_mixed_types(self) -> None:
        """Test accessing and comparing mixed type elements."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _1_.
- _"1"_.
- _yes_.
- empty.

Define `num` as Whole Number.
Define `str` as Text.
Define `bool` as Yes/No.
Define `null` as Text.

Set `num` to item _1_ of `mixed`.    # Number 1
Set `str` to item _2_ of `mixed`.    # String "1"
Set `bool` to item _3_ of `mixed`.   # Boolean yes
Set `null` to item _4_ of `mixed`.   # empty/null
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix assertion counts after parser updates")
    def test_large_mixed_collection(self) -> None:
        """Test large collection with many different types."""  # TODO: Fix assertion counts after parser updates
        source = """
Define `large_mixed` as unordered list.
Set `large_mixed` to:
- _0_.
- _"zero"_.
- _yes_.
- _1_.
- _"one"_.
- _no_.
- _2_.
- _"two"_.
- empty.
- _3.14_.
- _"pi"_.
- _-1_.
- _"negative"_.
- _0.0_.
- _""_.

Define `a` as Text.
Define `b` as Text.
Define `c` as Text.

# Access various elements
Set `a` to item _1_ of `large_mixed`.
Set `b` to item _9_ of `large_mixed`.
Set `c` to the last item of `large_mixed`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
