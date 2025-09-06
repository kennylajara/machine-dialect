#!/usr/bin/env python3
"""Test Python-Rust bytecode interoperability.

This script generates a bytecode file using Python and then
attempts to load it with the Rust VM to verify compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

from machine_dialect.codegen.bytecode_serializer import BytecodeWriter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def create_test_bytecode() -> None:
    """Create a test bytecode file that the Rust VM can load."""
    writer = BytecodeWriter()
    writer.set_module_name("interop_test")

    # Add some constants
    const_42 = writer.add_int_constant(42)
    const_pi = writer.add_float_constant(3.14159)
    writer.add_string_constant("Hello from Python!")
    writer.add_bool_constant(True)

    # Add global names
    result_idx = writer.add_global_name("result")

    # Generate a simple program:
    # r0 = 42
    # r1 = 3.14159
    # r2 = r0 + r0  (should be 84)
    # result = r2
    # return r2

    writer.emit_load_const(0, const_42)  # r0 = 42
    writer.emit_load_const(1, const_pi)  # r1 = 3.14159
    writer.emit_add(2, 0, 0)  # r2 = r0 + r0
    writer.emit_store_global(2, result_idx)  # result = r2
    writer.emit_debug_print(2)  # print(r2)
    writer.emit_return(2)  # return r2

    # Write to file
    output_path = Path("test_bytecode")
    writer.write_to_file(output_path)
    print(f"✓ Created bytecode file: {output_path.with_suffix('.mdbc')}")

    # Display bytecode info
    print("\nBytecode Module Info:")
    print(f"  Module name: {writer.module_name}")
    print(f"  Constants: {len(writer.constants)}")
    print(f"  Instructions: {len(writer.instructions)}")
    print(f"  Global names: {writer.global_names}")

    # Display constants
    print("\nConstant Pool:")
    for i, (tag, value) in enumerate(writer.constants):
        tag_name = {0x01: "Int", 0x02: "Float", 0x03: "String", 0x04: "Bool", 0x05: "Empty"}[tag]
        print(f"  [{i}] {tag_name}: {value}")

    # Display bytecode size
    from io import BytesIO

    stream = BytesIO()
    writer.write_to_stream(stream)
    bytecode_data = stream.getvalue()
    print(f"\nBytecode size: {len(bytecode_data)} bytes")

    # Display first few bytes (header)
    print("Header (first 28 bytes):")
    header = bytecode_data[:28]
    print(f"  Magic: {header[0:4]!r}")
    print(f"  Version: {int.from_bytes(header[4:8], 'little')}")
    print(f"  Flags: {int.from_bytes(header[8:12], 'little')}")
    print(f"  Name offset: {int.from_bytes(header[12:16], 'little')}")
    print(f"  Const offset: {int.from_bytes(header[16:20], 'little')}")
    print(f"  Func offset: {int.from_bytes(header[20:24], 'little')}")
    print(f"  Inst offset: {int.from_bytes(header[24:28], 'little')}")


def verify_with_rust() -> None:
    """Attempt to load the bytecode with Rust VM (if available)."""
    try:
        # Try to import the Rust VM Python bindings
        import machine_dialect_vm

        print("\n✓ Rust VM Python bindings available")

        # Create VM and load bytecode
        if hasattr(machine_dialect_vm, "RustVM"):
            vm = machine_dialect_vm.RustVM()
        else:
            print("✗ RustVM class not available (module not built yet?)")
            return
        vm.set_debug(True)

        bytecode_path = "test_bytecode.mdbc"
        try:
            vm.load_bytecode(bytecode_path)
            print("✓ Successfully loaded bytecode into Rust VM")

            # Try to execute
            result = vm.execute()
            print(f"✓ Execution result: {result}")
            print(f"  Instruction count: {vm.instruction_count()}")

        except Exception as e:
            print(f"✗ Failed to load/execute bytecode: {e}")

    except ImportError:
        print("\n⚠ Rust VM Python bindings not available (need to build with maturin)")
        print("  To build: cd machine_dialect_vm && maturin develop")


def main() -> None:
    """Main entry point."""
    print("Python-Rust Bytecode Interoperability Test")
    print("=" * 50)

    create_test_bytecode()
    verify_with_rust()

    print("\n" + "=" * 50)
    print("Test complete!")
    print("\nTo manually test with Rust:")
    print("  1. Ensure Rust 1.80+ is installed")
    print("  2. Run: cd machine_dialect_vm && cargo test bytecode")


if __name__ == "__main__":
    main()
