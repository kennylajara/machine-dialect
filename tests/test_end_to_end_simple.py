#!/usr/bin/env python3
"""Simplified end-to-end test for bytecode generation."""

import os
import struct
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_bytecode_generation():
    """Test basic bytecode generation without full MIR."""
    from machine_dialect.codegen.bytecode_builder import BytecodeModule
    from machine_dialect.codegen.bytecode_serializer import BYTECODE_VERSION, MAGIC_NUMBER, BytecodeWriter

    # Create a simple bytecode module manually
    module = BytecodeModule()
    module.name = "test_module"
    module.version = BYTECODE_VERSION
    module.flags = 0

    # Add some constants
    c0 = module.add_constant_int(42)
    c1 = module.add_constant_float(3.14)
    c2 = module.add_constant_string("Hello, World!")
    c3 = module.add_constant_bool(True)

    # Add some instructions (opcodes only for basic test)
    # LoadConstR r0, c0
    module.instructions.append(bytes([0, 0]) + struct.pack("<H", c0))
    # LoadConstR r1, c1
    module.instructions.append(bytes([0, 1]) + struct.pack("<H", c1))
    # AddR r2, r0, r1
    module.instructions.append(bytes([7, 2, 0, 1]))
    # ReturnR r2
    module.instructions.append(bytes([26, 1, 2]))  # has_value=1, src=2

    # Write to bytecode
    writer = BytecodeWriter(module)

    with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
        writer.write_to_stream(f)
        bytecode_path = f.name

    try:
        # Read back and verify
        with open(bytecode_path, "rb") as f:
            data = f.read()

        # Check magic number
        assert data[:4] == MAGIC_NUMBER, f"Invalid magic: {data[:4]}"
        print("✓ Magic number correct: MDBC")

        # Check version
        version = struct.unpack("<I", data[4:8])[0]
        assert version == BYTECODE_VERSION, f"Invalid version: {version}"
        print(f"✓ Version correct: {version}")

        # Check flags (1 = little-endian)
        flags = struct.unpack("<I", data[8:12])[0]
        assert flags == 1, f"Invalid flags: {flags}, expected 1 (little-endian)"
        print(f"✓ Flags correct: {flags} (little-endian)")

        # Read offsets
        name_offset = struct.unpack("<I", data[12:16])[0]
        const_offset = struct.unpack("<I", data[16:20])[0]
        func_offset = struct.unpack("<I", data[20:24])[0]
        inst_offset = struct.unpack("<I", data[24:28])[0]

        print(f"✓ Header offsets: name={name_offset}, const={const_offset}, func={func_offset}, inst={inst_offset}")

        # Verify name
        name_len = struct.unpack("<I", data[name_offset : name_offset + 4])[0]
        name = data[name_offset + 4 : name_offset + 4 + name_len].decode("utf-8")
        assert name == "test_module", f"Invalid name: {name}"
        print(f"✓ Module name: {name}")

        # Verify constants count
        const_count = struct.unpack("<I", data[const_offset : const_offset + 4])[0]
        assert const_count == 4, f"Expected 4 constants, got {const_count}"
        print(f"✓ Constants count: {const_count}")

        # Verify first constant (int)
        const_tag = data[const_offset + 4]
        assert const_tag == 0x01, f"Expected int tag 0x01, got 0x{const_tag:02x}"
        const_value = struct.unpack("<q", data[const_offset + 5 : const_offset + 13])[0]
        assert const_value == 42, f"Expected 42, got {const_value}"
        print("✓ First constant: int(42)")

        # Verify instruction count
        inst_count = struct.unpack("<I", data[inst_offset : inst_offset + 4])[0]
        assert inst_count == 4, f"Expected 4 instructions, got {inst_count}"
        print(f"✓ Instructions count: {inst_count}")

        print("\n✅ All bytecode generation tests passed!")
        return True

    finally:
        if os.path.exists(bytecode_path):
            os.unlink(bytecode_path)


def test_bytecode_roundtrip():
    """Test that we can write and read back bytecode."""
    from machine_dialect.codegen.bytecode_builder import BytecodeModule
    from machine_dialect.codegen.bytecode_serializer import BytecodeWriter

    # Create module with various types
    module = BytecodeModule()
    module.name = "roundtrip_test"
    module.version = 1
    module.flags = 1  # Little-endian flag

    # Add all constant types
    c_int = module.add_constant_int(-999)
    c_float = module.add_constant_float(2.71828)
    c_string = module.add_constant_string("Test String")
    c_bool_true = module.add_constant_bool(True)
    c_bool_false = module.add_constant_bool(False)
    c_empty = module.add_constant_empty()

    # Add a function entry
    module.function_table["test_func"] = 10

    # Add some varied instructions
    module.instructions.append(bytes([0, 0]) + struct.pack("<H", c_int))
    module.instructions.append(bytes([1, 1, 0]))  # MoveR
    module.instructions.append(bytes([7, 2, 0, 1]))  # AddR
    module.instructions.append(bytes([26, 0]))  # ReturnR without value

    # Serialize
    import io

    stream = io.BytesIO()
    writer = BytecodeWriter(module)
    writer.write_to_stream(stream)
    bytecode = stream.getvalue()

    print(f"Generated bytecode size: {len(bytecode)} bytes")

    # Basic validation
    assert bytecode[:4] == b"MDBC"
    print("✓ Roundtrip test: bytecode generated successfully")

    # Verify structure
    version = struct.unpack("<I", bytecode[4:8])[0]
    flags = struct.unpack("<I", bytecode[8:12])[0]
    assert version == 1
    assert flags == 1  # Little-endian flag
    print("✓ Roundtrip test: header verified")

    return True


if __name__ == "__main__":
    print("Running simplified end-to-end tests...\n")

    try:
        print("=" * 50)
        print("Test 1: Bytecode Generation")
        print("=" * 50)
        test_bytecode_generation()

        print("\n" + "=" * 50)
        print("Test 2: Bytecode Roundtrip")
        print("=" * 50)
        test_bytecode_roundtrip()

        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
