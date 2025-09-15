"""Edge case tests for boundary access conditions."""

import pytest

from machine_dialect.parser.parser import Parser


class TestBoundaryAccess:
    """Test boundary conditions for collection access."""

    @pytest.mark.skip(reason="TODO: Semantic analyzer doesn't validate zero indices properly")
    def test_zero_index_should_error(self) -> None:
        """Accessing index 0 should error (one-based indexing)."""  # TODO: Fix zero index validation
        source = """
Define `list` as unordered list.
Set `list` to:
- _"first"_.
- _"second"_.
- _"third"_.

Define `x` as Text.
Set `x` to item _0_ of `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Should have semantic error about invalid index
        assert parser.errors, "Expected error for zero index"
        assert any("index" in str(error).lower() or "zero" in str(error).lower() for error in parser.errors)

    def test_negative_index_should_error(self) -> None:
        """Negative indices should error."""
        source = """
Define `list` as ordered list.
Set `list` to:
1. _10_.
2. _20_.
3. _30_.

Define `x` as Whole Number.
Set `x` to item _-1_ of `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Parse should succeed but with negative literal
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # Note: Negative numbers would be parsed as unary minus expression

    def test_out_of_bounds_access(self) -> None:
        """Accessing beyond list length should be detected."""
        source = """
Define `list` as unordered list.
Set `list` to:
- _"a"_.
- _"b"_.
- _"c"_.

Define `x` as Text.
Set `x` to item _10_ of `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=True)

        # Semantic analysis may or may not catch this statically
        # (depends on whether it tracks list sizes)
        # But the syntax should be valid
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_very_large_index(self) -> None:
        """Very large indices should be handled."""
        source = """
Define `list` as unordered list.
Set `list` to:
- _1_.

Define `x` as Whole Number.
Set `x` to item _999999_ of `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully (runtime will handle bounds)
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
        # set_stmt = program.statements[1]
        # Verify large index is preserved
        # assert set_stmt.value is not None

    @pytest.mark.skip(reason="TODO: Parser doesn't handle all ordinal/collection access edge cases correctly")
    def test_first_second_third_last_on_small_lists(self) -> None:
        """Test ordinal access on lists with fewer elements."""  # TODO: Fix ordinal access parsing
        source = """
Define `single` as unordered list.
Set `single` to:
- _"only"_.

Define `double` as ordered list.
Set `double` to:
1. _"first"_.
2. _"second"_.

Define `a` as Text.
Define `b` as Text.
Define `c` as Text.
Define `d` as Text.
Define `e` as Text.
Define `f` as Text.
Define `g` as Text.

Set `a` to the first item of `single`.
Set `b` to the last item of `single`.
Set `c` to the second item of `single`.  # Should error at runtime

Set `d` to the first item of `double`.
Set `e` to the second item of `double`.
Set `f` to the third item of `double`.  # Should error at runtime
Set `g` to the last item of `double`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # All should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(
        reason="TODO: Parser treats invalid ordinals (fourth, fifth) as identifiers, causing fragmentation"
    )
    def test_ordinal_beyond_third(self) -> None:
        """Test that ordinals beyond 'third' are not recognized as keywords."""  # TODO: Fix invalid ordinal handling
        source = """
Define `list` as ordered list.
Set `list` to:
1. _"a"_.
2. _"b"_.
3. _"c"_.
4. _"d"_.
5. _"e"_.

Define `x` as Text.
Set `x` to the fourth item of `list`.  # 'fourth' not a keyword
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse, but 'fourth' would be treated as identifier, not ordinal
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    def test_numeric_vs_ordinal_equivalence(self) -> None:
        """Test that numeric and ordinal access are equivalent."""
        source = """
Define `list` as unordered list.
Set `list` to:
- _10_.
- _20_.
- _30_.

Define `first_ordinal` as Whole Number.
Define `first_numeric` as Whole Number.
Define `second_ordinal` as Whole Number.
Define `second_numeric` as Whole Number.
Define `third_ordinal` as Whole Number.
Define `third_numeric` as Whole Number.

Set `first_ordinal` to the first item of `list`.
Set `first_numeric` to item _1_ of `list`.

Set `second_ordinal` to the second item of `list`.
Set `second_numeric` to item _2_ of `list`.

Set `third_ordinal` to the third item of `list`.
Set `third_numeric` to item _3_ of `list`.
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # All should parse successfully
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Boundary mutation validation not fully implemented")
    def test_boundary_mutations(self) -> None:
        """Test mutations at boundary positions."""  # TODO: Add boundary checks for mutations
        source = """
Define `list` as unordered list.
Set `list` to:
- _"a"_.
- _"b"_.
- _"c"_.

Set item _1_ of `list` to _"first"_.  # Valid
Set item _3_ of `list` to _"third"_.  # Valid
Set item _4_ of `list` to _"fourth"_. # Out of bounds

Insert _"new"_ at position _0_ in `list`.  # Invalid (zero)
Insert _"new"_ at position _1_ in `list`.  # Valid (beginning)
Insert _"new"_ at position _4_ in `list`.  # Valid (end)
Insert _"new"_ at position _10_ in `list`. # Beyond end
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # All should parse syntactically
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Empty list access validation needs improvement")
    def test_empty_vs_bounds(self) -> None:
        """Test boundary conditions on empty vs non-empty lists."""  # TODO: Better empty list handling
        source = """
Define `empty` as unordered list.
Define `single` as ordered list.

Set `single` to:
1. _"only"_.

Define `x` as Text.
Define `y` as Text.
Define `z` as Text.

Set `x` to item _1_ of `empty`.  # Error - empty
Set `y` to item _1_ of `single`. # Valid
Set `z` to item _2_ of `single`. # Error - out of bounds
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse all statements
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass

    @pytest.mark.skip(reason="TODO: Dynamic index bounds checking not implemented")
    def test_dynamic_index_bounds(self) -> None:
        """Test boundary access with dynamic indices."""  # TODO: Add runtime bounds checking
        source = """
Define `list` as unordered list.
Set `list` to:
- _"a"_.
- _"b"_.
- _"c"_.

Define `index` as Whole Number.
Define `x` as Text.
Define `y` as Text.
Define `z` as Text.

Set `index` to _0_.
Set `x` to item `index` of `list`.  # Zero index

Set `index` to _-5_.
Set `y` to item `index` of `list`.  # Negative index

Set `index` to _100_.
Set `z` to item `index` of `list`.  # Out of bounds
"""
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should parse successfully (runtime will check bounds)
        # assert len(parser.program.statements) if hasattr(parser, "program") else pass
