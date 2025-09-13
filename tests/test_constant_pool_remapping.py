"""Tests for constant pool index remapping during bytecode serialization."""

import struct

import pytest

from machine_dialect.codegen.bytecode_module import BytecodeModule, Chunk, ChunkType, ConstantTag
from machine_dialect.codegen.opcodes import Opcode
from machine_dialect.codegen.vm_serializer import (
    BytecodeRemapper,
    ConstantIndexError,
    ConstantMapping,
    DeduplicationStats,
    InvalidBytecodeError,
    VMBytecodeSerializer,
    build_constant_mapping,
    generate_remapping_report,
)


class TestConstantMapping:
    """Test constant mapping and deduplication."""

    def test_simple_remapping(self) -> None:
        """Test basic constant index remapping."""
        # Create module with 2 chunks
        module = BytecodeModule("test")

        # Chunk 0: main with constants [42, "hello"]
        main_chunk = Chunk(
            name="main",
            chunk_type=ChunkType.MAIN,
            bytecode=bytearray(
                [
                    Opcode.LOAD_CONST_R,
                    0,
                    0,
                    0,  # Load const[0]=42
                    Opcode.LOAD_CONST_R,
                    1,
                    1,
                    0,  # Load const[1]="hello"
                    Opcode.RETURN_R,
                    0,  # Return void (has_value=0)
                ]
            ),
            constants=[(ConstantTag.INT, 42), (ConstantTag.STRING, "hello")],
            num_locals=2,
            num_params=0,
        )

        # Chunk 1: func with constants ["world", 99]
        func_chunk = Chunk(
            name="func",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(
                [
                    Opcode.LOAD_CONST_R,
                    2,
                    0,
                    0,  # Load const[0]="world"
                    Opcode.LOAD_CONST_R,
                    3,
                    1,
                    0,  # Load const[1]=99
                    Opcode.RETURN_R,
                    1,
                    3,  # Return reg[3]
                ]
            ),
            constants=[(ConstantTag.STRING, "world"), (ConstantTag.INT, 99)],
            num_locals=4,
            num_params=0,
        )

        module.chunks = [main_chunk, func_chunk]
        module.function_table = {"func": 1}

        # Build mapping
        mapping = build_constant_mapping(module)

        # Verify global constants
        assert len(mapping.global_constants) == 4
        assert mapping.global_constants[0] == (ConstantTag.INT, 42)
        assert mapping.global_constants[1] == (ConstantTag.STRING, "hello")
        assert mapping.global_constants[2] == (ConstantTag.STRING, "world")
        assert mapping.global_constants[3] == (ConstantTag.INT, 99)

        # Verify mappings
        assert mapping.chunk_mappings[0] == {0: 0, 1: 1}  # main: no change
        assert mapping.chunk_mappings[1] == {0: 2, 1: 3}  # func: offset by 2

        # Test remapping
        remapper = BytecodeRemapper(mapping)

        # Main chunk should be unchanged
        main_remapped = remapper.remap_chunk(0, bytes(main_chunk.bytecode))
        assert main_remapped == main_chunk.bytecode

        # Func chunk should be remapped
        func_remapped = remapper.remap_chunk(1, bytes(func_chunk.bytecode))
        # Check that const indices were updated
        assert func_remapped[2:4] == struct.pack("<H", 2)  # Was 0, now 2
        assert func_remapped[6:8] == struct.pack("<H", 3)  # Was 1, now 3

    def test_deduplication(self) -> None:
        """Test that duplicate constants are deduplicated."""
        module = BytecodeModule("test")

        chunk1 = Chunk(
            name="chunk1",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(),
            constants=[
                (ConstantTag.STRING, "shared"),
                (ConstantTag.INT, 42),
                (ConstantTag.STRING, "unique1"),
            ],
            num_locals=0,
            num_params=0,
        )

        chunk2 = Chunk(
            name="chunk2",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(),
            constants=[
                (ConstantTag.STRING, "shared"),  # Duplicate
                (ConstantTag.INT, 42),  # Duplicate
                (ConstantTag.STRING, "unique2"),
            ],
            num_locals=0,
            num_params=0,
        )

        module.chunks = [chunk1, chunk2]

        mapping = build_constant_mapping(module)

        # Should deduplicate "shared" and 42
        assert len(mapping.global_constants) == 4  # Not 6

        # Verify deduplication stats
        assert mapping.stats.original_count == 6
        assert mapping.stats.deduped_count == 4
        assert mapping.stats.bytes_saved > 0

        # Check duplicate chains
        assert len(mapping.stats.duplicate_chains) > 0

    def test_empty_chunk(self) -> None:
        """Test handling of chunks with no constants."""
        module = BytecodeModule("test")

        empty_chunk = Chunk(
            name="empty",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(
                [
                    Opcode.MOVE_R,
                    0,
                    1,  # No constant reference
                    Opcode.ADD_R,
                    2,
                    0,
                    1,  # No constant reference
                    Opcode.RETURN_R,
                    1,
                    2,
                ]
            ),
            constants=[],
            num_locals=3,
            num_params=0,
        )

        module.chunks = [empty_chunk]

        mapping = build_constant_mapping(module)
        remapper = BytecodeRemapper(mapping)

        # Should handle empty constants gracefully
        remapped = remapper.remap_chunk(0, bytes(empty_chunk.bytecode))
        assert remapped == empty_chunk.bytecode  # No changes
        assert len(mapping.global_constants) == 0


class TestBytecodeRemapping:
    """Test bytecode instruction remapping."""

    def test_load_const_remapping(self) -> None:
        """Test LOAD_CONST_R instruction remapping."""
        mapping = build_test_mapping()
        remapper = BytecodeRemapper(mapping)

        # Create bytecode with LOAD_CONST_R
        bytecode = bytearray(
            [
                Opcode.LOAD_CONST_R,
                5,
                0,
                0,  # Load const[0]
                Opcode.LOAD_CONST_R,
                6,
                1,
                0,  # Load const[1]
            ]
        )

        # Remap with offset
        chunk_map = {0: 10, 1: 11}
        mapping.chunk_mappings = [chunk_map]

        remapped = remapper.remap_chunk(0, bytes(bytecode))

        # Verify indices were updated
        assert struct.unpack("<H", remapped[2:4])[0] == 10
        assert struct.unpack("<H", remapped[6:8])[0] == 11

    def test_assert_remapping(self) -> None:
        """Test ASSERT_R instruction message index remapping."""
        mapping = build_test_mapping()
        remapper = BytecodeRemapper(mapping)

        # Create bytecode with ASSERT_R (5 bytes: opcode, reg, assert_type, msg_idx)
        bytecode = bytearray(
            [
                Opcode.ASSERT_R,
                0,  # condition register
                0,  # assert_type (0 = AssertType::True)
                2,  # msg_idx low byte
                0,  # msg_idx high byte - Assert reg[0], msg at const[2]
            ]
        )

        # Setup mapping with valid constants
        mapping.global_constants = [
            (ConstantTag.BOOL, True),
            (ConstantTag.INT, 42),
            (ConstantTag.STRING, "Assertion failed"),
        ]
        chunk_map = {2: 2}  # Map local 2 to global 2
        mapping.chunk_mappings = [chunk_map]

        remapped = remapper.remap_chunk(0, bytes(bytecode))

        # Verify message index unchanged (already correct) - now at bytes 3:5 due to assert_type
        assert struct.unpack("<H", remapped[3:5])[0] == 2

    def test_global_var_remapping(self) -> None:
        """Test LOAD_GLOBAL_R/STORE_GLOBAL_R remapping."""
        mapping = build_test_mapping()
        remapper = BytecodeRemapper(mapping)

        bytecode = bytearray(
            [
                Opcode.LOAD_GLOBAL_R,
                0,
                1,
                0,  # Load global with name at const[1]
                Opcode.STORE_GLOBAL_R,
                0,
                2,
                0,  # Store to global with name at const[2]
            ]
        )

        chunk_map = {1: 5, 2: 6}
        mapping.chunk_mappings = [chunk_map]

        remapped = remapper.remap_chunk(0, bytes(bytecode))

        # Verify name indices were updated
        assert struct.unpack("<H", remapped[2:4])[0] == 5
        assert struct.unpack("<H", remapped[6:8])[0] == 6

    def test_variable_length_instructions(self) -> None:
        """Test that variable-length instructions are handled correctly."""
        mapping = build_test_mapping()
        remapper = BytecodeRemapper(mapping)

        # CALL_R with 3 arguments
        bytecode = bytearray(
            [
                Opcode.CALL_R,
                0,
                1,
                3,
                2,
                3,
                4,  # func=r0, dst=r1, 3 args
                Opcode.RETURN_R,
                1,
                1,  # Return r1
            ]
        )

        # No constants to remap in CALL_R
        mapping.chunk_mappings = [{}]

        remapped = remapper.remap_chunk(0, bytes(bytecode))
        assert remapped == bytecode  # Should be unchanged

    def test_malformed_bytecode(self) -> None:
        """Test handling of truncated/malformed bytecode."""
        mapping = build_test_mapping()
        # Add a non-empty chunk mapping so remapping is attempted
        mapping.chunk_mappings = [{0: 0}]  # Minimal mapping
        remapper = BytecodeRemapper(mapping)

        # Truncated LOAD_CONST_R (missing 2 bytes)
        truncated = bytearray([Opcode.LOAD_CONST_R, 0])

        with pytest.raises(InvalidBytecodeError) as exc_info:
            remapper.remap_chunk(0, bytes(truncated))

        assert "Truncated instruction" in str(exc_info.value)
        assert "chunk 0" in str(exc_info.value)

    def test_invalid_constant_index(self) -> None:
        """Test detection of invalid constant indices."""
        mapping = build_test_mapping()
        mapping.global_constants = [(ConstantTag.INT, 42)]  # Only 1 constant

        remapper = BytecodeRemapper(mapping)

        # ASSERT_R with invalid message index (5 bytes format)
        bytecode = bytearray(
            [
                Opcode.ASSERT_R,
                0,  # condition register
                0,  # assert_type
                5,  # msg_idx low byte
                0,  # msg_idx high byte - msg_idx=5 but only 1 constant exists
            ]
        )

        chunk_map = {5: 5}  # Map to invalid index
        mapping.chunk_mappings = [chunk_map]

        with pytest.raises(ConstantIndexError) as exc_info:
            remapper.remap_chunk(0, bytes(bytecode))

        assert "Invalid constant index 5" in str(exc_info.value)
        assert "max: 0" in str(exc_info.value)


class TestCrossChunkDeduplication:
    """Test deduplication across multiple chunks."""

    def test_cross_chunk_duplicates(self) -> None:
        """Test that duplicates across chunks are properly deduplicated."""
        module = BytecodeModule("test")

        chunk1 = Chunk(
            name="chunk1",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(
                [
                    Opcode.LOAD_CONST_R,
                    0,
                    0,
                    0,  # Load "shared"
                    Opcode.LOAD_CONST_R,
                    1,
                    1,
                    0,  # Load 42
                ]
            ),
            constants=[(ConstantTag.STRING, "shared"), (ConstantTag.INT, 42)],
            num_locals=2,
            num_params=0,
        )

        chunk2 = Chunk(
            name="chunk2",
            chunk_type=ChunkType.FUNCTION,
            bytecode=bytearray(
                [
                    Opcode.LOAD_CONST_R,
                    2,
                    0,
                    0,  # Load "shared"
                    Opcode.LOAD_CONST_R,
                    3,
                    1,
                    0,  # Load 99
                ]
            ),
            constants=[(ConstantTag.STRING, "shared"), (ConstantTag.INT, 99)],
            num_locals=4,
            num_params=0,
        )

        module.chunks = [chunk1, chunk2]

        mapping = build_constant_mapping(module)

        # "shared" should appear only once
        shared_count = sum(
            1 for (tag, val) in mapping.global_constants if tag == ConstantTag.STRING and val == "shared"
        )
        assert shared_count == 1

        # Total should be 3 constants: "shared", 42, 99
        assert len(mapping.global_constants) == 3

        # Verify mappings point to the same global index for "shared"
        shared_global_idx = mapping.chunk_mappings[0][0]  # chunk1's "shared"
        assert mapping.chunk_mappings[1][0] == shared_global_idx  # chunk2's "shared"


class TestIntegration:
    """Integration tests with full serialization."""

    def test_full_serialization_with_remapping(self) -> None:
        """Test complete serialization with remapping."""
        module = create_test_module()

        # Serialize with remapping
        serialized = VMBytecodeSerializer.serialize(module)

        # Parse serialized data
        assert serialized[:4] == b"MDBC"  # Magic

        # Read constant count
        const_offset = struct.unpack("<I", serialized[16:20])[0]
        const_count = struct.unpack("<I", serialized[const_offset : const_offset + 4])[0]

        # Should have deduplicated constants
        assert const_count < sum(len(c.constants) for c in module.chunks)

    def test_debug_report(self) -> None:
        """Test generation of debugging report."""
        module = create_test_module()
        mapping = build_constant_mapping(module)

        report = generate_remapping_report(module, mapping)

        # Verify report contains expected sections
        assert "Constant Pool Remapping Report" in report
        assert "Original constants:" in report
        assert "After deduplication:" in report
        assert "Per-chunk remapping:" in report

    def test_serialize_with_debug(self) -> None:
        """Test serialization with debug output."""
        module = create_test_module()

        # Capture debug output
        import io
        import sys

        captured = io.StringIO()
        old_stdout = sys.stdout

        try:
            sys.stdout = captured
            VMBytecodeSerializer.serialize(module, debug=True)
            output = captured.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify debug report was printed
        assert "Constant Pool Remapping Report" in output


# Helper functions


def build_test_mapping() -> ConstantMapping:
    """Build a simple test mapping."""
    return ConstantMapping(
        chunk_mappings=[],
        global_constants=[],
        stats=DeduplicationStats(original_count=0, deduped_count=0, bytes_saved=0, duplicate_chains={}),
    )


def create_test_module() -> BytecodeModule:
    """Create a test module with multiple chunks."""
    module = BytecodeModule("test")

    main_chunk = Chunk(
        name="main",
        chunk_type=ChunkType.MAIN,
        bytecode=bytearray(
            [
                Opcode.LOAD_CONST_R,
                0,
                0,
                0,
                Opcode.LOAD_CONST_R,
                1,
                1,
                0,
                Opcode.CALL_R,
                0,
                2,
                1,
                1,
                Opcode.RETURN_R,
                0,  # Return void
            ]
        ),
        constants=[
            (ConstantTag.STRING, "TestFunc"),
            (ConstantTag.INT, 100),
        ],
        num_locals=3,
        num_params=0,
    )

    func_chunk = Chunk(
        name="TestFunc",
        chunk_type=ChunkType.FUNCTION,
        bytecode=bytearray(
            [
                Opcode.LOAD_CONST_R,
                0,
                0,
                0,
                Opcode.LOAD_CONST_R,
                1,
                1,
                0,
                Opcode.ADD_R,
                2,
                0,
                1,
                Opcode.RETURN_R,
                1,
                2,
            ]
        ),
        constants=[
            (ConstantTag.INT, 100),  # Duplicate of main's constant
            (ConstantTag.INT, 200),
        ],
        num_locals=3,
        num_params=1,
    )

    module.chunks = [main_chunk, func_chunk]
    module.function_table = {"TestFunc": 1}

    return module


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
