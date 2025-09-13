#!/usr/bin/env python3
"""Simple test to verify VM execution works with arrays."""

from machine_dialect.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel
from machine_dialect.compiler.vm_runner import VMRunner


def test_simple_array() -> bool:
    """Test a simple array creation and access."""
    source = """
Define `numbers` as ordered list.
Set `numbers` to:
1. _10_.
2. _20_.
3. _30_.

Define `first` as whole number.
Set `first` to the first item of `numbers`.

Say `first`.
"""

    # Compile the source
    config = CompilerConfig(
        optimization_level=OptimizationLevel.NONE,
        debug=True,
    )
    compiler = Compiler(config)
    context = compiler.compile_string(source, "test_arrays")

    # Check compilation was successful
    if context.errors:
        print("Compilation errors:")
        for error in context.errors:
            print(f"  - {error}")
        return False

    if not context.bytecode_module:
        print("No bytecode generated")
        return False

    print("Compilation successful!")

    # Try to execute in VM
    try:
        runner = VMRunner(debug=True)

        # Get serialized bytecode
        bytecode = context.bytecode_module.serialize()
        print(f"Bytecode size: {len(bytecode)} bytes")

        # Execute
        result = runner.execute_bytecode(bytecode)
        print(f"VM execution result: {result}")

        return True

    except Exception as e:
        print(f"VM execution error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_array()
    exit(0 if success else 1)
