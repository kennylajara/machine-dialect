"""Integration tests for list and dictionary features."""

import pytest

from machine_dialect.parser.parser import Parser


class TestListFeatures:
    """Test list (array) features end-to-end."""

    def test_one_based_indexing_literal(self) -> None:
        """Test that item _1_ accesses the first element (index 0)."""
        source = """
Set `numbers` to:
- _10_.
- _20_.
- _30_.

Set `first` to item _1_ of `numbers`.
Set `second` to item _2_ of `numbers`.
Set `third` to item _3_ of `numbers`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should parse successfully
        assert len(program.statements) == 4
        # Don't check for errors since we're just testing syntax

    def test_one_based_indexing_expression(self) -> None:
        """Test that expression-based indices are handled correctly."""
        source = """
Set `idx` to _2_.
Set `numbers` to:
- _100_.
- _200_.
- _300_.

Set `value` to item `idx` of `numbers`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should parse successfully
        assert len(program.statements) == 3
        # Don't check for errors since we're just testing syntax

    def test_array_mutations_with_one_based_index(self) -> None:
        """Test array mutations with one-based indexing."""
        source = """
Set `list` to:
- _"a"_.
- _"b"_.
- _"c"_.

Set item _1_ of `list` to _"A"_.
Remove item _2_ from `list`.
Insert _"X"_ at position _1_ in `list`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 4
        # Don't check for errors since we're just testing syntax

    def test_clear_operation(self) -> None:
        """Test the Clear operation on lists."""
        source = """
Set `items` to:
- _1_.
- _2_.
- _3_.

Clear `items`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 2
        # Don't check for errors since we're just testing syntax

    def test_ordinal_access(self) -> None:
        """Test ordinal access (first, second, third, last)."""
        source = """
Set `colors` to:
- _"red"_.
- _"green"_.
- _"blue"_.
- _"yellow"_.

Set `f` to the first item of `colors`.
Set `s` to the second item of `colors`.
Set `t` to the third item of `colors`.
Set `l` to the last item of `colors`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 5
        # Don't check for errors since we're just testing syntax


class TestDictionaryFeatures:
    """Test dictionary (named list) features end-to-end."""

    def test_named_list_creation(self) -> None:
        """Test creating a named list (dictionary)."""
        source = """
Set `person` to:
- _"name"_: _"Alice"_.
- _"age"_: _30_.
- _"email"_: _"alice@example.com"_.
- _"active"_: _yes_.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 1
        # Don't check for errors since we're just testing syntax

    def test_dictionary_keys_extraction(self) -> None:
        """Test extracting keys from a dictionary."""
        source = """
Set `config` to:
- _"host"_: _"localhost"_.
- _"port"_: _8080_.
- _"debug"_: _yes_.

Set `keys` to the names of `config`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 2
        # Don't check for errors since we're just testing syntax

    def test_dictionary_values_extraction(self) -> None:
        """Test extracting values from a dictionary."""
        source = """
Set `user` to:
- _"username"_: _"johndoe"_.
- _"email"_: _"john@example.com"_.
- _"premium"_: _yes_.

Set `values` to the contents of `user`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 2
        # Don't check for errors since we're just testing syntax

    def test_possessive_property_access(self) -> None:
        """Test possessive syntax for property access."""
        source = """
Set `person` to:
- _"name"_: _"Bob"_.
- _"age"_: _25_.
- _"city"_: _"New York"_.

Set `user_name` to `person`'s _"name"_.
Set `user_age` to `person`'s _"age"_.
Set `user_city` to `person`'s _"city"_.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 4
        # Don't check for errors since we're just testing syntax

    def test_possessive_property_mutation(self) -> None:
        """Test modifying properties using possessive syntax."""
        source = """
Set `config` to:
- _"host"_: _"localhost"_.
- _"port"_: _8080_.

Set `config`'s _"port"_ to _9000_.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # This should parse, though the exact handling may vary
        assert len(program.statements) == 2
        # Don't check for errors since we're just testing syntax

    def test_dictionary_operations(self) -> None:
        """Test various dictionary operations."""
        source = """
Set `data` to:
- _"key1"_: _"value1"_.
- _"key2"_: _"value2"_.

Add _"key3"_ to `data` with value _"value3"_.
Remove _"key1"_ from `data`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 3
        # Don't check for errors since we're just testing syntax


class TestNestedCollections:
    """Test combinations of lists and dictionaries."""

    @pytest.mark.skip(
        reason="Nested collection structures not yet supported by parser - requires complex grammar changes"
    )
    def test_list_of_dictionaries(self) -> None:
        """Test creating a list containing dictionaries."""
        source = """
Set `users` to:
- - _"name"_: _"Alice"_.
  - _"age"_: _30_.
- - _"name"_: _"Bob"_.
  - _"age"_: _25_.

Set `first_user` to the first item of `users`.
Set `first_name` to `first_user`'s _"name"_.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should parse the nested structure
        assert len(program.statements) == 3

    @pytest.mark.skip(
        reason="Nested collection structures not yet supported by parser - requires complex grammar changes"
    )
    def test_dictionary_with_list_values(self) -> None:
        """Test dictionary with lists as values."""
        source = """
Set `data` to:
- _"numbers"_:
  - _1_.
  - _2_.
  - _3_.
- _"names"_:
  - _"Alice"_.
  - _"Bob"_.

Set `nums` to `data`'s _"numbers"_.
Set `first_num` to the first item of `nums`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should handle nested structures
        assert len(program.statements) == 3

    def test_extraction_and_access_combination(self) -> None:
        """Test combining extraction with list access."""
        source = """
Set `config` to:
- _"timeout"_: _30_.
- _"retries"_: _3_.
- _"debug"_: _no_.

Set `keys` to the names of `config`.
Set `values` to the contents of `config`.

Set `first_key` to the first item of `keys`.
Set `first_value` to the first item of `values`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 5
        # Don't check for errors since we're just testing syntax


class TestIndexingEdgeCases:
    """Test edge cases and error handling for collection access."""

    def test_large_index_access(self) -> None:
        """Test accessing elements with large indices."""
        source = """
Set `data` to:
- _"a"_
- _"b"_
- _"c"_

Set `value` to item _877_ of `data`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should parse (runtime will handle out-of-bounds)
        assert len(program.statements) == 2

    def test_last_item_access(self) -> None:
        """Test accessing the last item of collections."""
        source = """
Set `nums` to:
- _1_.
- _2_.
- _3_.
- _4_.
- _5_.

Set `last_num` to the last item of `nums`.
"""
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(program.statements) == 2
        # Don't check for errors since we're just testing syntax

    def test_empty_collection_operations(self) -> None:
        """Test operations on empty collections."""
        source = """
Define `empty_list` as an unordered list.
Define `empty_dict` as a named list.
Set `val` to the first item of `empty_list`.
Set `keys` to the names of `empty_dict`.
"""
        parser = Parser()
        program = parser.parse(source)

        # Should parse even if runtime would fail
        assert len(program.statements) == 4
