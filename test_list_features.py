#!/usr/bin/env python3
"""Test list features end-to-end compilation."""

from machine_dialect.compiler.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig


def test_unordered_list_creation() -> None:
    """Test creation of unordered lists."""
    source = """
Define `shopping` as Unordered List.
Set `shopping` to:
- _"milk"_.
- _"bread"_.
- _"eggs"_.
"""

    # Compile to bytecode
    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ Unordered list creation test passed")


def test_ordered_list_creation() -> None:
    """Test creation of ordered lists."""
    source = """
Define `tasks` as Ordered List.
Set `tasks` to:
1. _"Write docs"_.
2. _"Review code"_.
3. _"Run tests"_.
"""

    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ Ordered list creation test passed")


def test_named_list_creation() -> None:
    """Test creation of named lists (dictionaries)."""
    source = """
Define `person` as Named List.
Set `person` to:
- name: _"Alice"_.
- age: _30_.
- active: _yes_.
"""

    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ Named list creation test passed")


def test_list_mutations() -> None:
    """Test list mutation operations."""
    source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.
- _3_.

Add _4_ to `items`.
Remove _2_ from `items`.
Set the first item of `items` to _10_.
Set item _2_ of `items` to _20_.
Insert _15_ at position _2_ in `items`.
"""

    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ List mutation operations test passed")


def test_list_access() -> None:
    """Test list access patterns."""
    source = """
Define `list` as Ordered List.
Set `list` to:
1. _"first"_.
2. _"second"_.
3. _"third"_.

Define `a` as Text.
Define `b` as Text.
Define `c` as Text.

Set `a` to the first item of `list`.
Set `b` to the second item of `list`.
Set `c` to item _3_ of `list`.
"""

    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ List access patterns test passed")


def test_empty_list() -> None:
    """Test creating an empty list."""
    source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.

Define `empty_list` as Unordered List.
"""

    config = CompilerConfig(verbose=False)
    compiler = Compiler(config)
    result = compiler.compile_string(source)

    assert len(result.errors) == 0, f"Compilation failed: {result.errors}"
    assert result.bytecode_module is not None, "Should produce bytecode"

    print("✓ Empty list operation test passed")


if __name__ == "__main__":
    print("Testing list features...")
    print("-" * 40)

    test_unordered_list_creation()
    test_ordered_list_creation()
    test_named_list_creation()
    test_list_mutations()
    test_list_access()
    test_empty_list()

    print("-" * 40)
    print("✅ All list feature tests passed!")
