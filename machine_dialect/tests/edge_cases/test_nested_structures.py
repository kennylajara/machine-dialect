"""Edge case tests for nested collection structures."""

import pytest

from machine_dialect.parser.parser import Parser


class TestNestedStructures:
    """Test complex nested collection scenarios."""

    @pytest.mark.skip(reason="TODO: Parser issues with deeply nested structures")
    def test_deeply_nested_lists(self) -> None:
        """Test deeply nested list structures."""  # TODO: Fix parser issues with nesting
        source = """
Set `level1` to:
- _"a"_.

Set `level2` to:
- `level1`.

Set `level3` to:
- `level2`.

Set `level4` to:
- `level3`.

# Access deeply nested element
Set `nested_list` to the first item of `level4`.
Set `nested_list2` to the first item of `nested_list`.
Set `nested_list3` to the first item of `nested_list2`.
Set `value` to the first item of `nested_list3`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix test - remove comments and verify assertions")
    def test_empty_nested_collections(self) -> None:
        """Test nested collections with empty elements."""  # TODO: Fix test - remove comments and verify assertions
        source = """
Define `empty_inner` as unordered list.

Set `outer` to:
- `empty_inner`.
- empty.

Set `another` to:
1. empty.
2. `empty_inner`.
3. empty.

# Operations on nested empties
Add _"item"_ to `empty_inner`.
Set `x` to the first item of `outer`.  # Empty list
Set `y` to the second item of `outer`. # empty literal
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Test needs investigation and fixing")
    def test_mixed_nesting_types(self) -> None:
        """Test mixing ordered, unordered, and named lists in nesting."""  # TODO: Test needs investigation and fixing
        source = """
# Unordered list
Set `unordered` to:
- _"a"_.
- _"b"_.

# Ordered list
Set `ordered` to:
1. _10_.
2. _20_.

# Named list
Set `named` to:
- key1: _"value1"_.
- key2: _"value2"_.

# Mix them all
Set `mixed_nest` to:
- `unordered`.
- `ordered`.
- `named`.

# Access nested elements
Set `first_list` to the first item of `mixed_nest`.
Set `second_list` to the second item of `mixed_nest`.
Set `third_list` to the third item of `mixed_nest`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix test - remove comments and verify assertions")
    def test_nested_mutations(self) -> None:
        """Test mutations on nested structures."""  # TODO: Fix test - remove comments and verify assertions
        source = """
Set `inner1` to:
- _1_.
- _2_.

Set `inner2` to:
1. _"a"_.
2. _"b"_.

Set `outer` to:
- `inner1`.
- `inner2`.

# Mutate inner lists
Add _3_ to `inner1`.
Remove _"a"_ from `inner2`.

# Mutate outer list
Add `inner1` to `outer`.  # Add duplicate reference
Remove `inner2` from `outer`.

# Replace nested list
Set item _1_ of `outer` to `inner2`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Test needs investigation and fixing")
    def test_matrix_like_structure(self) -> None:
        """Test 2D matrix-like nested structure."""  # TODO: Test needs investigation and fixing
        source = """
Set `row1` to:
- _1_.
- _2_.
- _3_.

Set `row2` to:
- _4_.
- _5_.
- _6_.

Set `row3` to:
- _7_.
- _8_.
- _9_.

Set `matrix` to:
1. `row1`.
2. `row2`.
3. `row3`.

# Access matrix elements
Set `first_row` to item _1_ of `matrix`.
Set `element_1_1` to item _1_ of `first_row`.

Set `second_row` to item _2_ of `matrix`.
Set `element_2_3` to item _3_ of `second_row`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Test needs investigation and fixing")
    def test_circular_reference_attempt(self) -> None:
        """Test attempting to create circular references."""  # TODO: Test needs investigation and fixing
        source = """
Define `list1` as unordered list.
Define `list2` as unordered list.

Add _"item"_ to `list1`.
Add `list1` to `list2`.
Add `list2` to `list1`.  # Creates circular reference

# Try to access circular structure
Set `x` to the first item of `list1`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse (runtime would handle circular refs)
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Test needs investigation and fixing")
    def test_heterogeneous_nesting(self) -> None:
        """Test nesting with mixed types at each level."""  # TODO: Test needs investigation and fixing
        source = """
Set `mixed_inner` to:
- _1_.
- _"text"_.
- _yes_.

Set `complex` to:
- `mixed_inner`.
- _42_.
- _"standalone"_.
- empty.

# Nested named list
Set `dict_inner` to:
- name: _"nested"_.
- values: `mixed_inner`.

Set `super_nested` to:
1. `complex`.
2. `dict_inner`.
3. _"top level string"_.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix test - remove comments and verify assertions")
    def test_nested_list_flattening_operations(self) -> None:
        """Test operations that might flatten nested structures."""
        # TODO: Fix test - remove comments and verify assertions
        source = """
Set `nested` to:
- - _1_.
  - _2_.
- - _3_.
  - _4_.

# Try to access nested elements directly
Set `inner1` to item _1_ of `nested`.
Set `inner2` to item _2_ of `nested`.

# Concatenation-like operations
Define `flattened` as unordered list.
Add `inner1` to `flattened`.  # Adds list as element
Add `inner2` to `flattened`.  # Adds list as element
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Fix test - remove comments and verify assertions")
    def test_nested_empty_lists(self) -> None:
        """Test multiple levels of empty lists."""  # TODO: Fix test - remove comments and verify assertions
        source = """
Define `empty1` as unordered list.
Define `empty2` as ordered list.
Define `empty3` as named list.

Set `all_empty` to:
- `empty1`.
- `empty2`.
- `empty3`.

# Try operations on nested empties
Set `first_empty` to the first item of `all_empty`.
Add _"item"_ to `first_empty`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Test needs investigation and fixing")
    def test_maximum_nesting_depth(self) -> None:
        """Test very deep nesting levels."""  # TODO: Test needs investigation and fixing
        source = """
Set `l1` to:
- _"deepest"_.

Set `l2` to:
- `l1`.

Set `l3` to:
- `l2`.

Set `l4` to:
- `l3`.

Set `l5` to:
- `l4`.

Set `l6` to:
- `l5`.

Set `l7` to:
- `l6`.

Set `l8` to:
- `l7`.

# Try to access the deepest element
Set `temp1` to the first item of `l8`.
Set `temp2` to the first item of `temp1`.
Set `temp3` to the first item of `temp2`.
Set `temp4` to the first item of `temp3`.
Set `temp5` to the first item of `temp4`.
Set `temp6` to the first item of `temp5`.
Set `temp7` to the first item of `temp6`.
Set `result` to the first item of `temp7`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
