"""Tests for bytecode serialization."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import pytest

from machine_dialect.codegen.bytecode_serializer import BytecodeWriter, serialize_bytecode_module


class TestBytecodeWriter:
    """Test bytecode writer functionality."""

    def test_create_writer(self) -> None:
        """Test creating a bytecode writer."""
        writer = BytecodeWriter()
        assert writer.module_name == "__main__"
        assert len(writer.constants) == 0
        assert len(writer.instructions) == 0
        assert len(writer.functions) == 0
        assert len(writer.global_names) == 0

    def test_add_constants(self) -> None:
        """Test adding constants to the pool."""
        writer = BytecodeWriter()

        idx1 = writer.add_int_constant(42)
        idx2 = writer.add_float_constant(3.14)
        idx3 = writer.add_string_constant("hello")
        idx4 = writer.add_bool_constant(True)
        idx5 = writer.add_empty_constant()

        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2
        assert idx4 == 3
        assert idx5 == 4
        assert len(writer.constants) == 5

        assert writer.constants[0] == (0x01, 42)
        assert writer.constants[1] == (0x02, 3.14)
        assert writer.constants[2] == (0x03, "hello")
        assert writer.constants[3] == (0x04, True)
        assert writer.constants[4] == (0x05, None)

    def test_emit_instructions(self) -> None:
        """Test emitting various instructions."""
        writer = BytecodeWriter()

        # Add some constants
        const_idx = writer.add_int_constant(100)

        # Emit instructions
        writer.emit_load_const(0, const_idx)
        writer.emit_move(1, 0)
        writer.emit_add(2, 0, 1)
        writer.emit_return(2)

        assert len(writer.instructions) == 4

        # Check instruction encoding
        assert writer.instructions[0] == struct.pack("<BBH", 0, 0, const_idx)
        assert writer.instructions[1] == struct.pack("<BBB", 1, 1, 0)
        assert writer.instructions[2] == struct.pack("<BBBB", 7, 2, 0, 1)
        assert writer.instructions[3] == struct.pack("<BBB", 26, 1, 2)

    def test_write_bytecode_file(self) -> None:
        """Test writing bytecode to a file."""
        writer = BytecodeWriter()
        writer.set_module_name("test_module")

        # Add some constants and instructions
        idx = writer.add_int_constant(42)
        writer.emit_load_const(0, idx)
        writer.emit_return(0)

        # Write to temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test"
            writer.write_to_file(path)

            # Check file was created
            bytecode_path = path.with_suffix(".mdbc")
            assert bytecode_path.exists()

            # Read and verify header
            with open(bytecode_path, "rb") as f:
                magic = f.read(4)
                assert magic == b"MDBC"

                version = struct.unpack("<I", f.read(4))[0]
                assert version == 1

                flags = struct.unpack("<I", f.read(4))[0]
                assert flags == 1  # Little-endian flag

    def test_serialize_module(self) -> None:
        """Test serialize_bytecode_module function."""
        constants = [
            (0x01, 100),
            (0x03, "test"),
            (0x04, False),
        ]

        instructions = [
            struct.pack("<BBH", 0, 0, 0),  # LoadConstR r0, 0
            struct.pack("<BBH", 0, 1, 1),  # LoadConstR r1, 1
            struct.pack("<BB", 26, 0),  # ReturnR (no value)
        ]

        data = serialize_bytecode_module(
            "my_module",
            constants,
            instructions,
            functions={"main": 0},
            global_names=["x", "y"],
        )

        # Verify magic number
        assert data[:4] == b"MDBC"

        # Verify version
        version = struct.unpack("<I", data[4:8])[0]
        assert version == 1

    def test_bytecode_format(self) -> None:
        """Test the complete bytecode format."""
        writer = BytecodeWriter()
        writer.set_module_name("format_test")

        # Add various constants
        int_idx = writer.add_int_constant(999)
        float_idx = writer.add_float_constant(2.718)
        writer.add_string_constant("bytecode")
        writer.add_bool_constant(False)

        # Add global names
        x_idx = writer.add_global_name("x")
        y_idx = writer.add_global_name("y")

        # Add instructions
        writer.emit_load_const(0, int_idx)
        writer.emit_store_global(0, x_idx)
        writer.emit_load_const(1, float_idx)
        writer.emit_store_global(1, y_idx)
        writer.emit_load_global(2, x_idx)
        writer.emit_load_global(3, y_idx)
        writer.emit_add(4, 2, 3)
        writer.emit_return(4)

        # Get serialized data
        from io import BytesIO

        stream = BytesIO()
        writer.write_to_stream(stream)
        data = stream.getvalue()

        # Parse and verify structure
        assert len(data) > 28  # At least header size

        # Check header
        assert data[0:4] == b"MDBC"
        version = struct.unpack("<I", data[4:8])[0]
        assert version == 1

        flags = struct.unpack("<I", data[8:12])[0]
        assert flags == 1

        # Check offsets are present
        name_offset = struct.unpack("<I", data[12:16])[0]
        const_offset = struct.unpack("<I", data[16:20])[0]
        func_offset = struct.unpack("<I", data[20:24])[0]
        inst_offset = struct.unpack("<I", data[24:28])[0]

        assert name_offset == 28  # Right after header
        assert const_offset > name_offset
        assert func_offset > const_offset
        assert inst_offset > func_offset


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
