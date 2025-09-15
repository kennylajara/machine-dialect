"""Integration tests for emulated array operations."""

import tempfile
from pathlib import Path
from typing import Any

from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.pipeline import CompilationPipeline


def compile_source(source: str) -> Any:
    """Helper function to compile source string."""
    config = CompilerConfig(verbose=False)
    pipeline = CompilationPipeline(config)

    # Write source to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(source)
        temp_path = Path(f.name)

    try:
        context = pipeline.compile_file(temp_path)
        return context
    finally:
        temp_path.unlink(missing_ok=True)


class TestArrayOperationsEmulation:
    """Test that array operations compile and generate correct bytecode."""

    def test_insert_operation_compiles(self) -> None:
        """Test that insert operations compile to bytecode."""
        source = """
Define `items` as Ordered List.
Set `items` to:
1. _"first"_.
2. _"second"_.
3. _"third"_.

Insert _"new"_ at position _2_ in `items`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

        # Should generate bytecode
        assert context.bytecode_module is not None
        assert len(context.bytecode_module.chunks) > 0
        bytecode = context.bytecode_module.chunks[0].bytecode
        assert len(bytecode) > 0

        # Should have substantial bytecode (insert is complex)
        assert len(bytecode) > 100, "Insert should generate substantial bytecode"

    def test_remove_by_value_compiles(self) -> None:
        """Test that remove by value operations compile."""
        source = """
Define `fruits` as Unordered List.
Set `fruits` to:
- _"apple"_.
- _"banana"_.
- _"cherry"_.

Remove _"banana"_ from `fruits`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

        # Should generate bytecode
        assert context.bytecode_module is not None
        assert len(context.bytecode_module.chunks) > 0
        bytecode = context.bytecode_module.chunks[0].bytecode
        assert len(bytecode) > 0

        # Remove by value uses ArrayFindIndex + ArrayRemove, so lots of code
        assert len(bytecode) > 150, "Remove by value should generate substantial bytecode"

    def test_multiple_operations(self) -> None:
        """Test that multiple array operations work together."""
        source = """
Define `tasks` as Ordered List.
Set `tasks` to:
1. _"Task A"_.
2. _"Task B"_.
3. _"Task C"_.

Insert _"Task A.5"_ at position _2_ in `tasks`.
Remove _"Task B"_ from `tasks`.
Add _"Task D"_ to `tasks`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

        # Should generate bytecode
        assert context.bytecode_module is not None
        assert len(context.bytecode_module.chunks) > 0
        bytecode = context.bytecode_module.chunks[0].bytecode
        assert len(bytecode) > 0

    def test_insert_at_beginning(self) -> None:
        """Test inserting at the beginning of a list."""
        source = """
Define `numbers` as Unordered List.
Set `numbers` to:
- _10_.
- _20_.
- _30_.

Insert _5_ at position _1_ in `numbers`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

        # Should generate bytecode
        assert context.bytecode_module is not None

    def test_insert_at_end(self) -> None:
        """Test inserting at the end of a list (like append but with position)."""
        source = """
Define `items` as Ordered List.
Set `items` to:
1. _"one"_.
2. _"two"_.

Define `length` as Whole Number.
Set `length` to _3_.
Insert _"three"_ at position `length` in `items`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

    def test_remove_nonexistent_value(self) -> None:
        """Test removing a value that doesn't exist in the list."""
        source = """
Define `colors` as Unordered List.
Set `colors` to:
- _"red"_.
- _"green"_.
- _"blue"_.

Remove _"yellow"_ from `colors`.
"""

        context = compile_source(source)

        # Should compile without errors (runtime will handle -1 index)
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

    def test_nested_list_operations(self) -> None:
        """Test operations on lists containing lists."""
        source = """
Define `matrix` as Unordered List.
Define `row1` as Unordered List.
Set `row1` to:
- _1_.
- _2_.

Define `row2` as Unordered List.
Set `row2` to:
- _3_.
- _4_.

Set `matrix` to:
- `row1`.
- `row2`.

Define `row3` as Unordered List.
Set `row3` to:
- _5_.
- _6_.

Add `row3` to `matrix`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

    def test_bytecode_contains_loops(self) -> None:
        """Test that generated bytecode contains loop structures."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.
- _3_.

Remove _2_ from `items`.
"""

        context = compile_source(source)

        assert not context.has_errors()
        assert context.bytecode_module is not None
        assert len(context.bytecode_module.chunks) > 0

        # Check for jump instructions (indicate loops)
        bytecode = context.bytecode_module.chunks[0].bytecode
        has_jumps = False

        # Look for jump opcodes (0x16 = JUMP_R, 0x17 = JUMP_IF_R, 0x18 = JUMP_IF_NOT_R)
        for byte in bytecode:
            if byte in [0x16, 0x17, 0x18]:
                has_jumps = True
                break

        assert has_jumps, "Should contain jump instructions for loops"

    def test_operations_with_variables(self) -> None:
        """Test array operations using variables for positions and values."""
        source = """
Define `data` as Ordered List.
Set `data` to:
1. _100_.
2. _200_.
3. _300_.

Define `pos` as Whole Number.
Set `pos` to _2_.

Define `val` as Whole Number.
Set `val` to _150_.

Insert `val` at position `pos` in `data`.
"""

        context = compile_source(source)

        # Should compile without errors
        assert not context.has_errors(), f"Compilation errors: {context.errors}"

        # Should generate bytecode
        assert context.bytecode_module is not None
