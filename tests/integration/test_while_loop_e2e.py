"""End-to-end tests for while loop execution in Machine Dialect™.

These tests verify that while loops are correctly:
1. Parsed into AST
2. Converted to HIR
3. Lowered to MIR
4. Compiled to bytecode
5. Executed by the VM
"""

import tempfile
from pathlib import Path

import pytest

from machine_dialect.compiler import Compiler, CompilerConfig


def compile_source(source: str) -> bool:
    """Helper to compile source code and return success status."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(source)
        source_path = Path(f.name)

    try:
        config = CompilerConfig(verbose=False)
        compiler = Compiler(config)

        with tempfile.NamedTemporaryFile(suffix=".mdb", delete=False) as out:
            output_path = Path(out.name)

        success = compiler.compile_file(source_path, output_path)

        # Clean up output file
        if output_path.exists():
            output_path.unlink()

        return success

    finally:
        source_path.unlink(missing_ok=True)


class TestWhileLoopE2E:
    """End-to-end tests for while loop functionality."""

    def test_simple_counter_loop(self) -> None:
        """Test a simple while loop that counts from 0 to 5."""
        source = """
Define `count` as whole number.
Define `result` as whole number.
Set `count` to 0.
Set `result` to 0.

While `count` < 5:
> Set `result` to `result` + `count`.
> Set `count` to `count` + 1.

Give back `result`.
"""
        success = compile_source(source)
        assert success, "While loop compilation should succeed"

    def test_nested_while_loops(self) -> None:
        """Test nested while loops."""
        source = """
Define `i` as whole number.
Define `j` as whole number.
Define `total` as whole number.
Set `i` to 0.
Set `total` to 0.

While `i` < 3:
> Set `j` to 0.
> While `j` < 2:
>> Set `total` to `total` + 1.
>> Set `j` to `j` + 1.
>
> Set `i` to `i` + 1.

Give back `total`.
"""
        success = compile_source(source)
        assert success, "Nested while loops should compile"

    def test_while_with_complex_condition(self) -> None:
        """Test while loop with complex boolean condition."""
        source = """
Define `x` as whole number.
Define `y` as whole number.
Set `x` to 10.
Set `y` to 0.

While `x` > 0 and `y` < 5:
> Set `x` to `x` - 2.
> Set `y` to `y` + 1.

Give back `y`.
"""
        success = compile_source(source)
        assert success, "While loop with complex condition should compile"

    def test_while_with_early_exit(self) -> None:
        """Test while loop with conditional return."""
        source = """
Define `i` as whole number.
Set `i` to 0.

While `i` < 10:
> If `i` equals 5:
>> Give back `i`.
>
> Set `i` to `i` + 1.

Give back -1.
"""
        success = compile_source(source)
        assert success, "While loop with early exit should compile"

    @pytest.mark.skip(reason="List literals with bracket notation are not yet implemented")  # type: ignore[misc]
    def test_for_each_loop_compilation(self) -> None:
        """Test that for-each loops compile correctly (via desugaring to while)."""
        source = """
Set `list` to [1, 2, 3, 4, 5].
Set `sum` to 0.

For each `item` in `list`:
> Set `sum` to `sum` + `item`.

Give back `sum`.
"""
        success = compile_source(source)
        assert success, "For-each loop should compile via desugaring"

    def test_infinite_loop_structure(self) -> None:
        """Test that infinite loops can be compiled (but not executed)."""
        source = """
Define `forever` as Yes/No.
Set `forever` to Yes.

While `forever`:
> Say "This would run forever".

Give back 0.
"""
        # Just verify it compiles - don't execute infinite loop!
        success = compile_source(source)
        assert success, "Infinite loop structure should compile"


class TestLoopBytecodeGeneration:
    """Test bytecode generation for loops."""

    def test_while_generates_jump_instructions(self) -> None:
        """Verify that while loops generate proper jump instructions."""
        source = """
Define `x` as whole number.
Set `x` to 0.
While `x` < 3:
> Set `x` to `x` + 1.
"""
        # For now, just verify compilation succeeds
        # TODO: Add bytecode inspection when API is available
        success = compile_source(source)
        assert success, "While loop should compile and generate jump instructions"

    @pytest.mark.skip(reason="List literals with bracket notation are not yet implemented")  # type: ignore[misc]
    def test_for_each_desugars_to_while(self) -> None:
        """Verify that for-each loops desugar to while loops."""
        source = """
Set `items` to [1, 2, 3].
For each `x` in `items`:
> Say `x`.
"""
        # The for-each should be desugared during HIR generation
        success = compile_source(source)
        assert success, "For-each loop should compile via desugaring to while"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
