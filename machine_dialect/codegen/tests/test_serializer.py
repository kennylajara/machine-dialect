"""Tests for the binary serializer module."""

import io
import math
import struct

import pytest

from machine_dialect.codegen.objects import Chunk, Module
from machine_dialect.codegen.serializer import (
    MAGIC_NUMBER,
    InvalidMagicError,
    SerializationError,
    deserialize_module,
    serialize_module,
)


class TestChunkSerialization:
    """Test serialization of individual chunks."""

    def test_empty_chunk(self) -> None:
        """Test serializing an empty chunk."""
        chunk = Chunk(name="test")
        module = Module(name="test", main_chunk=chunk)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.main_chunk.name == "test"
        assert loaded.main_chunk.size() == 0
        assert loaded.main_chunk.constants.size() == 0
        assert loaded.main_chunk.num_locals == 0
        assert loaded.main_chunk.num_params == 0

    def test_chunk_with_bytecode(self) -> None:
        """Test serializing a chunk with bytecode."""
        chunk = Chunk(name="main")
        chunk.write_byte(0x01)  # LOAD_CONST
        chunk.write_u16(0)  # index 0
        chunk.write_byte(0x02)  # RETURN

        module = Module(name="test", main_chunk=chunk)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.main_chunk.name == "main"
        assert loaded.main_chunk.size() == 4
        assert bytes(loaded.main_chunk.bytecode) == b"\x01\x00\x00\x02"

    def test_chunk_with_constants(self) -> None:
        """Test serializing a chunk with various constant types."""
        chunk = Chunk(name="constants")

        # Add various constant types
        chunk.add_constant(42)  # int
        chunk.add_constant(3.14)  # float
        chunk.add_constant("hello")  # string
        chunk.add_constant(True)  # bool
        chunk.add_constant(False)  # bool
        chunk.add_constant(None)  # None

        module = Module(name="test", main_chunk=chunk)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.main_chunk.constants.size() == 6
        assert loaded.main_chunk.get_constant(0) == 42
        assert loaded.main_chunk.get_constant(1) == 3.14
        assert loaded.main_chunk.get_constant(2) == "hello"
        assert loaded.main_chunk.get_constant(3) == 1  # True deduplicates with 1
        assert loaded.main_chunk.get_constant(4) == 0  # False deduplicates with 0
        assert loaded.main_chunk.get_constant(5) is None

    def test_chunk_with_metadata(self) -> None:
        """Test serializing a chunk with metadata."""
        chunk = Chunk(name="metadata")
        chunk.num_locals = 5
        chunk.num_params = 2

        module = Module(name="test", main_chunk=chunk)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.main_chunk.num_locals == 5
        assert loaded.main_chunk.num_params == 2

    def test_unicode_strings(self) -> None:
        """Test serializing Unicode strings."""
        chunk = Chunk(name="unicode")
        chunk.add_constant("Hello 世界 🌍")
        chunk.add_constant("Ελληνικά")

        module = Module(name="test", main_chunk=chunk)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.main_chunk.get_constant(0) == "Hello 世界 🌍"
        assert loaded.main_chunk.get_constant(1) == "Ελληνικά"


class TestModuleSerialization:
    """Test serialization of complete modules."""

    def test_module_with_functions(self) -> None:
        """Test serializing a module with function chunks."""
        main_chunk = Chunk(name="main")
        main_chunk.add_constant("main constant")

        func1 = Chunk(name="func1")
        func1.num_params = 2
        func1.add_constant("func1 constant")

        func2 = Chunk(name="func2")
        func2.num_params = 1
        func2.add_constant("func2 constant")

        module = Module(name="test", main_chunk=main_chunk)
        module.add_function("func1", func1)
        module.add_function("func2", func2)

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.name == "test"
        assert loaded.main_chunk.name == "main"
        assert len(loaded.functions) == 2

        assert "func1" in loaded.functions
        assert loaded.functions["func1"].num_params == 2
        assert loaded.functions["func1"].get_constant(0) == "func1 constant"

        assert "func2" in loaded.functions
        assert loaded.functions["func2"].num_params == 1
        assert loaded.functions["func2"].get_constant(0) == "func2 constant"

    def test_module_with_metadata(self) -> None:
        """Test serializing a module with metadata."""
        chunk = Chunk(name="main")
        module = Module(name="test", main_chunk=chunk)
        module.metadata["version"] = "1.0.0"
        module.metadata["author"] = "Test Author"
        module.metadata["description"] = "A test module"

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        assert loaded.metadata["version"] == "1.0.0"
        assert loaded.metadata["author"] == "Test Author"
        assert loaded.metadata["description"] == "A test module"

    def test_complex_module(self) -> None:
        """Test serializing a complex module with everything."""
        # Main chunk with various constants and bytecode
        main = Chunk(name="__main__")
        main.num_locals = 3
        main.add_constant(100)
        main.add_constant("global string")
        main.write_bytes(0x01, 0x00, 0x00)  # LOAD_CONST 0
        main.write_bytes(0x02, 0x01, 0x00)  # STORE_LOCAL 1

        # Function with parameters and locals
        func = Chunk(name="calculate")
        func.num_params = 2
        func.num_locals = 4
        func.add_constant(3.14159)
        func.write_bytes(0x03, 0x00, 0x00)  # LOAD_LOCAL 0

        # Create module
        module = Module(name="complex", main_chunk=main)
        module.add_function("calculate", func)
        module.metadata["complexity"] = "high"

        # Serialize
        output = io.BytesIO()
        serialize_module(module, output)

        # Deserialize
        output.seek(0)
        loaded = deserialize_module(output)

        # Verify everything
        assert loaded.name == "complex"
        assert loaded.main_chunk.name == "__main__"
        assert loaded.main_chunk.num_locals == 3
        assert loaded.main_chunk.get_constant(0) == 100
        assert loaded.main_chunk.get_constant(1) == "global string"
        assert bytes(loaded.main_chunk.bytecode) == b"\x01\x00\x00\x02\x01\x00"

        assert "calculate" in loaded.functions
        calc = loaded.functions["calculate"]
        assert calc.num_params == 2
        assert calc.num_locals == 4
        assert calc.get_constant(0) == 3.14159
        assert bytes(calc.bytecode) == b"\x03\x00\x00"

        assert loaded.metadata["complexity"] == "high"


class TestMagicNumberValidation:
    """Test magic number validation."""

    def test_valid_magic_number(self) -> None:
        """Test that valid magic number is accepted."""
        chunk = Chunk(name="test")
        module = Module(name="test", main_chunk=chunk)

        output = io.BytesIO()
        serialize_module(module, output)

        # Verify magic number is at offset 0 (big-endian)
        output.seek(0)
        magic = struct.unpack(">I", output.read(4))[0]
        assert magic == MAGIC_NUMBER

        # Should deserialize without error
        output.seek(0)
        loaded = deserialize_module(output)
        assert loaded.main_chunk.name == "test"

    def test_invalid_magic_number(self) -> None:
        """Test that invalid magic number is rejected."""
        output = io.BytesIO()

        # Write invalid magic number at offset 0 (big-endian)
        output.write(struct.pack(">I", 0xDEADBEEF))
        output.write(b"\x00" * 100)  # Some dummy data

        output.seek(0)
        with pytest.raises(InvalidMagicError) as exc_info:
            deserialize_module(output)

        assert "Invalid magic number" in str(exc_info.value)
        assert "0xDEADBEEF" in str(exc_info.value)

    def test_truncated_file(self) -> None:
        """Test that truncated files are handled gracefully."""
        output = io.BytesIO()

        # Write only partial magic number
        output.write(b"\xbe\xbe")

        output.seek(0)
        with pytest.raises(SerializationError) as exc_info:
            deserialize_module(output)

        assert "EOF" in str(exc_info.value)

    def test_corrupted_data(self) -> None:
        """Test handling of corrupted data after valid magic."""
        output = io.BytesIO()

        # Write valid magic but then truncate (big-endian)
        output.write(struct.pack(">I", MAGIC_NUMBER))
        output.write(b"\x01")  # Incomplete version

        output.seek(0)
        with pytest.raises(SerializationError) as exc_info:
            deserialize_module(output)

        assert "EOF" in str(exc_info.value) or "version" in str(exc_info.value).lower()


class TestRoundTrip:
    """Test round-trip serialization."""

    def test_empty_module_roundtrip(self) -> None:
        """Test round-trip of an empty module."""
        original = Module(name="empty", main_chunk=Chunk(name="main"))

        # Serialize and deserialize
        buffer = io.BytesIO()
        serialize_module(original, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        assert loaded.name == original.name
        assert loaded.main_chunk.name == original.main_chunk.name
        assert loaded.total_size() == original.total_size()

    def test_large_module_roundtrip(self) -> None:
        """Test round-trip of a large module."""
        main = Chunk(name="main")

        # Add many constants
        for i in range(100):
            main.add_constant(i)
            main.add_constant(f"string_{i}")
            main.add_constant(i * 0.1)

        # Add lots of bytecode
        for i in range(100):
            main.write_byte(i % 256)
            main.write_u16(i)

        # Create functions
        module = Module(name="large", main_chunk=main)
        for i in range(10):
            func = Chunk(name=f"func_{i}")
            func.num_params = i % 5
            func.num_locals = i * 2
            func.add_constant(f"Function {i}")
            module.add_function(f"func_{i}", func)

        # Add metadata
        for i in range(20):
            module.metadata[f"key_{i}"] = f"value_{i}"

        # Round trip
        buffer = io.BytesIO()
        serialize_module(module, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        # Verify constants
        assert loaded.main_chunk.constants.size() == 300
        for i in range(100):
            assert loaded.main_chunk.get_constant(i * 3) == i
            assert loaded.main_chunk.get_constant(i * 3 + 1) == f"string_{i}"
            assert loaded.main_chunk.get_constant(i * 3 + 2) == i * 0.1

        # Verify bytecode
        assert loaded.main_chunk.size() == 300  # 100 * (1 + 2) bytes

        # Verify functions
        assert len(loaded.functions) == 10
        for i in range(10):
            func = loaded.functions[f"func_{i}"]
            assert func.num_params == i % 5
            assert func.num_locals == i * 2
            assert func.get_constant(0) == f"Function {i}"

        # Verify metadata
        assert len(loaded.metadata) == 20
        for i in range(20):
            assert loaded.metadata[f"key_{i}"] == f"value_{i}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_integers(self) -> None:
        """Test serialization of large integers."""
        chunk = Chunk(name="test")

        # Maximum and minimum i64 values
        max_i64 = 2**63 - 1
        min_i64 = -(2**63)

        chunk.add_constant(max_i64)
        chunk.add_constant(min_i64)
        chunk.add_constant(0)
        chunk.add_constant(-1)
        chunk.add_constant(1)

        module = Module(name="test", main_chunk=chunk)

        # Round trip
        buffer = io.BytesIO()
        serialize_module(module, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        assert loaded.main_chunk.get_constant(0) == max_i64
        assert loaded.main_chunk.get_constant(1) == min_i64
        assert loaded.main_chunk.get_constant(2) == 0
        assert loaded.main_chunk.get_constant(3) == -1
        assert loaded.main_chunk.get_constant(4) == 1

    def test_special_floats(self) -> None:
        """Test serialization of special float values."""
        chunk = Chunk(name="test")

        # Special float values
        chunk.add_constant(float("inf"))
        chunk.add_constant(float("-inf"))
        chunk.add_constant(float("nan"))
        chunk.add_constant(0.0)
        # Note: -0.0 and 0.0 are deduplicated as the same constant
        # because Python treats them as equal

        module = Module(name="test", main_chunk=chunk)

        # Round trip
        buffer = io.BytesIO()
        serialize_module(module, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        assert loaded.main_chunk.get_constant(0) == float("inf")
        assert loaded.main_chunk.get_constant(1) == float("-inf")
        nan_val = loaded.main_chunk.get_constant(2)
        assert isinstance(nan_val, float) and math.isnan(nan_val)
        assert loaded.main_chunk.get_constant(3) == 0.0

    def test_empty_strings(self) -> None:
        """Test serialization of empty strings."""
        chunk = Chunk(name="test")
        chunk.add_constant("")
        chunk.add_constant("non-empty")

        module = Module(name="test", main_chunk=chunk)

        # Round trip
        buffer = io.BytesIO()
        serialize_module(module, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        assert loaded.main_chunk.get_constant(0) == ""
        assert loaded.main_chunk.get_constant(1) == "non-empty"

    def test_max_chunk_size(self) -> None:
        """Test chunks at maximum size limits."""
        chunk = Chunk(name="max")

        # Max u16 locals
        chunk.num_locals = 65535

        # Max u8 params
        chunk.num_params = 255

        # Add max constants (u16 limit)
        # Note: This would be too slow to actually test with 65535 constants
        # so we'll just test a reasonable number
        for i in range(100):
            chunk.add_constant(i)

        module = Module(name="test", main_chunk=chunk)

        # Round trip
        buffer = io.BytesIO()
        serialize_module(module, buffer)
        buffer.seek(0)
        loaded = deserialize_module(buffer)

        assert loaded.main_chunk.num_locals == 65535
        assert loaded.main_chunk.num_params == 255
        assert loaded.main_chunk.constants.size() == 100
