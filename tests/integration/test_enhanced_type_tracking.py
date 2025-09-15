"""Test enhanced type tracking for non-literal collections.

This tests that the type system can track element types through variable assignments.
"""

from machine_dialect.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel


class TestEnhancedTypeTracking:
    """Test enhanced type tracking for collections."""

    def test_type_tracking_through_assignment(self) -> None:
        """Test that element types are tracked when a collection is assigned to a variable."""
        source = """
Define `numbers` as ordered list.
Set `numbers` to:
1. _10_.
2. _20_.
3. _30_.

Define `copy` as ordered list.
Set `copy` to `numbers`.

Define `first` as whole number.
Set `first` to the first item of `copy`.

Say `first`.
"""

        config = CompilerConfig(
            optimization_level=OptimizationLevel.NONE,
            debug=True,
        )
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_type_tracking")

        # Should compile without type errors
        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

    def test_type_inference_homogeneous_list(self) -> None:
        """Test type inference for homogeneous lists."""
        source = """
Define `strings` as unordered list.
Set `strings` to:
- _"apple"_.
- _"banana"_.
- _"cherry"_.

Define `item` as text.
Set `item` to the second item of `strings`.

Say `item`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_homogeneous")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

    def test_type_inference_mixed_list(self) -> None:
        """Test type inference for heterogeneous lists - should use Any type."""
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _42_.
- _"hello"_.
- _3.14_.

Define `any_item` as text.
Set `any_item` to the second item of `mixed`.

Define `num_item` as whole number.
Set `num_item` to the first item of `mixed`.

Say `any_item`.
Say `num_item`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_mixed")

        # Should compile - Any type is compatible with all types
        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

    def test_indirect_collection_access(self) -> None:
        """Test accessing elements from a collection variable that was assigned from another."""
        source = """
Define `original` as ordered list.
Set `original` to:
1. _100_.
2. _200_.
3. _300_.

Define `reference` as ordered list.
Set `reference` to `original`.

Define `indirect` as ordered list.
Set `indirect` to `reference`.

Define `value` as whole number.
Set `value` to item _2_ of `indirect`.

Say `value`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_indirect")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

    def test_dictionary_value_type_tracking(self) -> None:
        """Test type tracking for dictionary values."""
        source = """
Define `scores` as named list.
Set `scores` to:
- "alice": _95_.
- "bob": _87_.
- "charlie": _92_.

Define `alice_score` as whole number.
Set `alice_score` to `scores`'s _"alice"_.

Say `alice_score`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_dict")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"
