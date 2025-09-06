#!/usr/bin/env python3
"""Simplified end-to-end test for bytecode generation."""

import os
import struct
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, cast

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Minimal BytecodeModule for testing serialization
@dataclass
class BytecodeModule:
    """Minimal bytecode module for testing serialization."""

    name: str = "main"
    version: int = 1
    flags: int = 0
    constants: list[tuple[int, Any]] = field(default_factory=list)
    instructions: list[bytes] = field(default_factory=list)
    function_table: dict[str, int] = field(default_factory=dict)
    global_names: list[str] = field(default_factory=list)

    def add_constant_int(self, value: int) -> int:
        """Add an integer constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x01, value))
        return idx

    def add_constant_float(self, value: float) -> int:
        """Add a float constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x02, value))
        return idx

    def add_constant_string(self, value: str) -> int:
        """Add a string constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x03, value))
        return idx

    def add_constant_bool(self, value: bool) -> int:
        """Add a boolean constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x04, value))
        return idx

    def add_constant_empty(self) -> int:
        """Add an empty/null constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x05, None))
        return idx


def test_bytecode_generation() -> None:
    """Test basic bytecode generation without full MIR."""
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

    # Add some instructions that use all constant types
    # LoadConstR r0, c0 (load int)
    module.instructions.append(bytes([0, 0]) + struct.pack("<H", c0))
    # LoadConstR r1, c1 (load float)
    module.instructions.append(bytes([0, 1]) + struct.pack("<H", c1))
    # LoadConstR r2, c2 (load string)
    module.instructions.append(bytes([0, 2]) + struct.pack("<H", c2))
    # LoadConstR r3, c3 (load bool)
    module.instructions.append(bytes([0, 3]) + struct.pack("<H", c3))
    # AddR r4, r0, r1 (add int and float)
    module.instructions.append(bytes([7, 4, 0, 1]))
    # ReturnR r4
    module.instructions.append(bytes([26, 1, 4]))  # has_value=1, src=4

    # Write to bytecode
    writer = BytecodeWriter(module)

    with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False, mode="wb") as f:
        writer.write_to_stream(cast(BinaryIO, f))
        bytecode_path = f.name

    try:
        # Read back and verify
        with open(bytecode_path, "rb") as f:
            data = f.read()

        # Check magic number
        assert data[:4] == MAGIC_NUMBER, f"Invalid magic: {data[:4]!r}"
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

        # Verify constants
        offset = const_offset + 4

        # First constant (int)
        const_tag = data[offset]
        assert const_tag == 0x01, f"Expected int tag 0x01, got 0x{const_tag:02x}"
        const_value = struct.unpack("<q", data[offset + 1 : offset + 9])[0]
        assert const_value == 42, f"Expected 42, got {const_value}"
        print("✓ First constant: int(42)")
        offset += 9

        # Second constant (float)
        const_tag = data[offset]
        assert const_tag == 0x02, f"Expected float tag 0x02, got 0x{const_tag:02x}"
        const_value = struct.unpack("<d", data[offset + 1 : offset + 9])[0]
        assert abs(const_value - 3.14) < 0.001, f"Expected 3.14, got {const_value}"
        print("✓ Second constant: float(3.14)")
        offset += 9

        # Third constant (string)
        const_tag = data[offset]
        assert const_tag == 0x03, f"Expected string tag 0x03, got 0x{const_tag:02x}"
        str_len = struct.unpack("<I", data[offset + 1 : offset + 5])[0]
        const_value = data[offset + 5 : offset + 5 + str_len].decode("utf-8")
        assert const_value == "Hello, World!", f"Expected 'Hello, World!', got '{const_value}'"
        print("✓ Third constant: string('Hello, World!')")
        offset += 5 + str_len

        # Fourth constant (bool)
        const_tag = data[offset]
        assert const_tag == 0x04, f"Expected bool tag 0x04, got 0x{const_tag:02x}"
        const_value = data[offset + 1]
        assert const_value == 1, f"Expected True (1), got {const_value}"
        print("✓ Fourth constant: bool(True)")

        # Verify instruction count
        inst_count = struct.unpack("<I", data[inst_offset : inst_offset + 4])[0]
        assert inst_count == 6, f"Expected 6 instructions, got {inst_count}"
        print(f"✓ Instructions count: {inst_count}")

        print("\n✅ All bytecode generation tests passed!")

    finally:
        if os.path.exists(bytecode_path):
            os.unlink(bytecode_path)


def test_bytecode_roundtrip() -> None:
    """Test that we can write and read back bytecode."""
    from machine_dialect.codegen.bytecode_serializer import BYTECODE_VERSION, BytecodeWriter

    # Create module with various types
    module = BytecodeModule()
    module.name = "roundtrip_test"
    module.version = BYTECODE_VERSION
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

    # Add instructions that use all the constants
    # LoadConstR r0, c_int
    module.instructions.append(bytes([0, 0]) + struct.pack("<H", c_int))
    # LoadConstR r1, c_float
    module.instructions.append(bytes([0, 1]) + struct.pack("<H", c_float))
    # LoadConstR r2, c_string
    module.instructions.append(bytes([0, 2]) + struct.pack("<H", c_string))
    # LoadConstR r3, c_bool_true
    module.instructions.append(bytes([0, 3]) + struct.pack("<H", c_bool_true))
    # LoadConstR r4, c_bool_false
    module.instructions.append(bytes([0, 4]) + struct.pack("<H", c_bool_false))
    # LoadConstR r5, c_empty
    module.instructions.append(bytes([0, 5]) + struct.pack("<H", c_empty))
    # AddR r6, r0, r1  (test arithmetic op)
    module.instructions.append(bytes([7, 6, 0, 1]))
    # ReturnR r6
    module.instructions.append(bytes([26, 1, 6]))  # has_value=1, src=6

    # Serialize
    import io

    stream = io.BytesIO()
    writer = BytecodeWriter(module)
    writer.write_to_stream(stream)
    bytecode = stream.getvalue()

    print(f"Generated bytecode size: {len(bytecode)} bytes")

    # Verify header
    assert bytecode[:4] == b"MDBC", f"Invalid magic: {bytecode[:4]!r}"
    print("✓ Magic number correct: MDBC")

    version = struct.unpack("<I", bytecode[4:8])[0]
    assert version == BYTECODE_VERSION, f"Invalid version: {version}"
    print(f"✓ Version correct: {version}")

    flags = struct.unpack("<I", bytecode[8:12])[0]
    assert flags == 1, f"Invalid flags: {flags}"
    print("✓ Flags correct: 1 (little-endian)")

    # Read offsets
    name_offset = struct.unpack("<I", bytecode[12:16])[0]
    const_offset = struct.unpack("<I", bytecode[16:20])[0]
    func_offset = struct.unpack("<I", bytecode[20:24])[0]
    inst_offset = struct.unpack("<I", bytecode[24:28])[0]

    # Verify module name
    name_len = struct.unpack("<I", bytecode[name_offset : name_offset + 4])[0]
    name = bytecode[name_offset + 4 : name_offset + 4 + name_len].decode("utf-8")
    assert name == "roundtrip_test", f"Invalid name: {name}"
    print(f"✓ Module name: {name}")

    # Verify constants count
    const_count = struct.unpack("<I", bytecode[const_offset : const_offset + 4])[0]
    assert const_count == 6, f"Expected 6 constants, got {const_count}"
    print(f"✓ Constants count: {const_count}")

    # Verify all 6 constants
    offset = const_offset + 4

    # Constant 1: int(-999)
    const_tag = bytecode[offset]
    assert const_tag == 0x01, f"Expected int tag 0x01, got 0x{const_tag:02x}"
    const_value = struct.unpack("<q", bytecode[offset + 1 : offset + 9])[0]
    assert const_value == -999, f"Expected -999, got {const_value}"
    print("✓ Constant 1: int(-999)")
    offset += 9

    # Constant 2: float(2.71828)
    const_tag = bytecode[offset]
    assert const_tag == 0x02, f"Expected float tag 0x02, got 0x{const_tag:02x}"
    const_value = struct.unpack("<d", bytecode[offset + 1 : offset + 9])[0]
    assert abs(const_value - 2.71828) < 0.00001, f"Expected 2.71828, got {const_value}"
    print("✓ Constant 2: float(2.71828)")
    offset += 9

    # Constant 3: string("Test String")
    const_tag = bytecode[offset]
    assert const_tag == 0x03, f"Expected string tag 0x03, got 0x{const_tag:02x}"
    str_len = struct.unpack("<I", bytecode[offset + 1 : offset + 5])[0]
    const_value = bytecode[offset + 5 : offset + 5 + str_len].decode("utf-8")
    assert const_value == "Test String", f"Expected 'Test String', got '{const_value}'"
    print("✓ Constant 3: string('Test String')")
    offset += 5 + str_len

    # Constant 4: bool(True)
    const_tag = bytecode[offset]
    assert const_tag == 0x04, f"Expected bool tag 0x04, got 0x{const_tag:02x}"
    const_value = bytecode[offset + 1]
    assert const_value == 1, f"Expected True (1), got {const_value}"
    print("✓ Constant 4: bool(True)")
    offset += 2

    # Constant 5: bool(False)
    const_tag = bytecode[offset]
    assert const_tag == 0x04, f"Expected bool tag 0x04, got 0x{const_tag:02x}"
    const_value = bytecode[offset + 1]
    assert const_value == 0, f"Expected False (0), got {const_value}"
    print("✓ Constant 5: bool(False)")
    offset += 2

    # Constant 6: empty
    const_tag = bytecode[offset]
    assert const_tag == 0x05, f"Expected empty tag 0x05, got 0x{const_tag:02x}"
    print("✓ Constant 6: empty")

    # Verify function table
    func_count = struct.unpack("<I", bytecode[func_offset : func_offset + 4])[0]
    assert func_count == 1, f"Expected 1 function, got {func_count}"
    offset = func_offset + 4
    func_name_len = struct.unpack("<I", bytecode[offset : offset + 4])[0]
    func_name = bytecode[offset + 4 : offset + 4 + func_name_len].decode("utf-8")
    assert func_name == "test_func", f"Expected 'test_func', got '{func_name}'"
    func_inst_offset = struct.unpack("<I", bytecode[offset + 4 + func_name_len : offset + 8 + func_name_len])[0]
    assert func_inst_offset == 10, f"Expected offset 10, got {func_inst_offset}"
    print(f"✓ Function table: {func_name} at offset {func_inst_offset}")

    # Verify instruction count
    inst_count = struct.unpack("<I", bytecode[inst_offset : inst_offset + 4])[0]
    assert inst_count == 8, f"Expected 8 instructions, got {inst_count}"
    print(f"✓ Instructions count: {inst_count}")

    print("\n✅ All bytecode roundtrip tests passed!")


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
