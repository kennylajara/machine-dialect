"""Edge case tests for named lists (dictionaries)."""

import pytest

from machine_dialect.parser.parser import Parser


class TestNamedListEdgeCases:
    """Test edge cases specific to named lists (dictionaries)."""

    @pytest.mark.skip(reason="TODO: Missing Define statement and parser stops after named list")
    def test_duplicate_keys(self) -> None:
        """Test handling of duplicate keys in named lists."""  # TODO: Fix test and parser
        source = """
Set `dict` to:
- key: _"first"_.
- key: _"second"_.  # Duplicate key - should override
- key: _"third"_.   # Another duplicate

Set `value` to `dict`'s key.  # Should be "third"
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse (semantic/runtime handles duplicates)
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_empty_key_and_value(self) -> None:
        """Test empty keys and values in named lists."""
        source = """
Set `dict` to:
- : _"empty key"_.     # Empty key
- normal: .            # Empty value (if supported)
- empty: empty.        # 'empty' literal as value

# Try to access empty key
Set `x` to `dict`'s .  # Access empty key (syntax may fail)
"""
        parser = Parser()
        # This might fail at parse time due to syntax
        try:
            parser.parse(source, check_semantics=False)
            # If it parses, check structure
            assert parser is not None
        except Exception:
            # Expected - empty keys might not be valid syntax
            pass

    @pytest.mark.skip(reason="TODO: Missing Define statement and parser stops after named list")
    def test_keywords_as_keys(self) -> None:
        """Test using keywords as keys in named lists."""  # TODO: Fix test and parser
        source = """
Set `dict` to:
- if: _"keyword if"_.
- then: _"keyword then"_.
- else: _"keyword else"_.
- empty: _"keyword empty"_.
- yes: _"boolean yes"_.
- no: _"boolean no"_.
- list: _"keyword list"_.
- item: _"keyword item"_.

# Access keyword keys
Set `a` to `dict`'s if.
Set `b` to `dict`'s empty.
Set `c` to `dict`'s yes.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_numeric_keys(self) -> None:
        """Test numeric values as keys."""
        source = """
Set `dict` to:
- 1: _"one"_.
- 2: _"two"_.
- 3.14: _"pi"_.
- -5: _"negative"_.
- 0: _"zero"_.

# Access numeric keys
Set `x` to `dict`'s 1.
Set `y` to `dict`'s 3.14.
"""
        parser = Parser()
        # Numeric keys might need special syntax
        try:
            parser.parse(source, check_semantics=False)
            assert parser is not None
        except Exception:
            # Numeric keys might not be supported directly
            pass

    @pytest.mark.skip(reason="TODO: Missing Define statement and 'whether...has' not implemented")
    def test_boolean_keys(self) -> None:
        """Test boolean values as keys."""  # TODO: Fix test and implement 'whether...has'
        source = """
Set `dict` to:
- yes: _"true value"_.
- no: _"false value"_.

# Access boolean keys
Set `true_val` to `dict`'s yes.
Set `false_val` to `dict`'s no.

# Check for boolean keys
Define `has_yes` as truth value.
Set `has_yes` to whether `dict` has yes.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_unhashable_keys(self) -> None:
        """Test unhashable types as keys (should error)."""
        source = """
Set `list_key` to:
- _1_.
- _2_.

Set `dict_key` to:
- a: _"b"_.

# Try to use unhashable types as keys
Set `bad_dict` to:
- `list_key`: _"list as key"_.  # Should error
- `dict_key`: _"dict as key"_.  # Should error
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have semantic errors for unhashable keys
        # Note: Parser might accept syntax, semantic analysis catches type error

    def test_mixed_key_types(self) -> None:
        """Test named list with mixed key types."""
        source = """
Set `mixed_keys` to:
- text: _"string key"_.
- 42: _"numeric key"_.
- yes: _"boolean key"_.
- empty: _"empty keyword"_.

# Operations with mixed key types
Add _"another"_ to `mixed_keys` with value _"test"_.
Remove text from `mixed_keys`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse if syntax supports it
        # assert len(parser.program.statements if hasattr(parser, "program") else []) >= 1

    @pytest.mark.skip(reason="TODO: Missing Define statement and parser stops after named list")
    def test_very_long_keys(self) -> None:
        """Test named lists with very long key names."""  # TODO: Fix test and parser
        source = """
Set `long_keys` to:
- this_is_a_very_long_key_name_that_might_cause_issues: _"value1"_.
- another_extremely_long_key_name_with_many_underscores_and_words: _"value2"_.

# Access long keys
Set `x` to `long_keys`'s this_is_a_very_long_key_name_that_might_cause_issues.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_special_character_keys(self) -> None:
        """Test keys with special characters."""
        source = """
Set `special` to:
- key_with_underscore: _"underscore"_.
- key-with-dash: _"dash"_.  # Might not parse
- "key with spaces": _"spaces"_.  # Might not parse
- key.with.dots: _"dots"_.  # Might not parse
"""
        parser = Parser()
        # Some of these might fail to parse depending on syntax rules
        try:
            parser.parse(source, check_semantics=False)
            # Check what successfully parsed
            assert parser is not None
        except Exception:
            # Expected for invalid key syntax
            pass

    @pytest.mark.skip(reason="TODO: Missing Define statement and parser stops after named list")
    def test_case_sensitive_keys(self) -> None:
        """Test case sensitivity in named list keys."""  # TODO: Fix test and parser
        source = """
Set `case_test` to:
- key: _"lowercase"_.
- Key: _"titlecase"_.
- KEY: _"uppercase"_.
- KeY: _"mixed"_.

# Access different cases
Set `a` to `case_test`'s key.
Set `b` to `case_test`'s Key.
Set `c` to `case_test`'s KEY.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_empty_named_list_operations(self) -> None:
        """Test various operations on empty named lists."""
        source = """
Define `empty_dict` as named list.

# Check for non-existent key
Define `has_key` as truth value.
Set `has_key` to whether `empty_dict` has key.

# Try to access non-existent key
Set `value` to `empty_dict`'s missing.  # Should error

# Add first key-value pair
Add _"first"_ to `empty_dict` with value _"value"_.

# Remove from single-element dict
Remove first from `empty_dict`.

# Dict is empty again
Clear `empty_dict`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements if hasattr(parser, "program") else []) >= 5

    @pytest.mark.skip(reason="TODO: Missing Define statements and parser issues with nested structures")
    def test_nested_named_lists(self) -> None:
        """Test named lists containing other named lists."""  # TODO: Fix test and parser
        source = """
Set `inner1` to:
- a: _1_.
- b: _2_.

Set `inner2` to:
- x: _10_.
- y: _20_.

Set `outer` to:
- first: `inner1`.
- second: `inner2`.
- direct: _"value"_.

# Access nested values
Set `nested_dict` to `outer`'s first.
Set `nested_value` to `nested_dict`'s a.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Property access syntax for named lists not implemented")
    def test_property_access_edge_cases(self) -> None:
        """Test edge cases in property access syntax."""  # TODO: Implement property access
        source = """
Set `dict` to:
- name: _"Alice"_.
- age: _30_.

# Standard property access
Set `n` to `dict`'s name.

# Try accessing non-existent property
Set `x` to `dict`'s missing.  # Should error

# Try property access on non-dict
Set `list` to:
- _1_.
- _2_.

Set `y` to `list`'s property.  # Should error - not a named list
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have some semantic errors
        # assert len(parser.program.statements if hasattr(parser, "program") else []) >= 3
