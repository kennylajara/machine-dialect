"""Proper bytecode serializer for the Rust VM with constant pool remapping.

This serializer correctly handles individual instruction parsing and remaps
constant indices when merging multiple chunks into a single module.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, BinaryIO

from machine_dialect.codegen.bytecode_module import BytecodeModule, ConstantTag
from machine_dialect.codegen.opcodes import Opcode

# =============================================================================
# Deduplication and Mapping Support
# =============================================================================


@dataclass
class DeduplicationStats:
    """Track deduplication effectiveness."""

    original_count: int
    deduped_count: int
    bytes_saved: int
    duplicate_chains: dict[tuple[Any, ...], list[int]] = field(default_factory=dict)


@dataclass
class ConstantMapping:
    """Maps local chunk indices to global pool indices."""

    # For each chunk, maps local index -> global index
    chunk_mappings: list[dict[int, int]]

    # Global constant pool with deduplication
    global_constants: list[tuple[ConstantTag, Any]]

    # Statistics for debugging
    stats: DeduplicationStats


# =============================================================================
# Error Handling
# =============================================================================


class RemappingError(Exception):
    """Base class for remapping errors."""

    pass


class InvalidBytecodeError(RemappingError):
    """Raised when bytecode is malformed."""

    def __init__(self, message: str, offset: int | None = None, chunk_idx: int | None = None):
        super().__init__(
            f"{message}"
            f"{f' at offset {offset:#x}' if offset is not None else ''}"
            f"{f' in chunk {chunk_idx}' if chunk_idx is not None else ''}"
        )
        self.offset = offset
        self.chunk_idx = chunk_idx


class ConstantIndexError(RemappingError):
    """Raised when a constant index is out of range."""

    def __init__(self, idx: int, max_idx: int, chunk_idx: int | None = None, offset: int | None = None):
        super().__init__(
            f"Invalid constant index {idx} (max: {max_idx})"
            f"{f' in chunk {chunk_idx}' if chunk_idx is not None else ''}"
            f"{f' at instruction offset {offset:#x}' if offset is not None else ''}"
        )
        self.index = idx
        self.max_index = max_idx
        self.chunk_idx = chunk_idx
        self.offset = offset


# =============================================================================
# Instruction Format Definitions
# =============================================================================


@dataclass
class InstructionFormat:
    """Describes the format of a bytecode instruction."""

    opcode: int
    name: str
    size: int  # Total size in bytes (-1 for variable)
    has_const_operand: bool
    operand_format: str  # Format string for struct


# Instruction format definitions
INSTRUCTION_FORMATS = {
    0x00: InstructionFormat(0x00, "LOAD_CONST_R", 4, True, "BH"),
    0x01: InstructionFormat(0x01, "MOVE_R", 3, False, "BB"),
    0x02: InstructionFormat(0x02, "LOAD_GLOBAL_R", 4, True, "BH"),
    0x03: InstructionFormat(0x03, "STORE_GLOBAL_R", 4, True, "BH"),
    # Arithmetic
    0x07: InstructionFormat(0x07, "ADD_R", 4, False, "BBB"),
    0x08: InstructionFormat(0x08, "SUB_R", 4, False, "BBB"),
    0x09: InstructionFormat(0x09, "MUL_R", 4, False, "BBB"),
    0x0A: InstructionFormat(0x0A, "DIV_R", 4, False, "BBB"),
    0x0B: InstructionFormat(0x0B, "MOD_R", 4, False, "BBB"),
    0x0C: InstructionFormat(0x0C, "NEG_R", 3, False, "BB"),
    # Logical
    0x0D: InstructionFormat(0x0D, "NOT_R", 3, False, "BB"),
    0x0E: InstructionFormat(0x0E, "AND_R", 4, False, "BBB"),
    0x0F: InstructionFormat(0x0F, "OR_R", 4, False, "BBB"),
    # Comparisons
    0x10: InstructionFormat(0x10, "EQ_R", 4, False, "BBB"),
    0x11: InstructionFormat(0x11, "NEQ_R", 4, False, "BBB"),
    0x12: InstructionFormat(0x12, "LT_R", 4, False, "BBB"),
    0x13: InstructionFormat(0x13, "GT_R", 4, False, "BBB"),
    0x14: InstructionFormat(0x14, "LTE_R", 4, False, "BBB"),
    0x15: InstructionFormat(0x15, "GTE_R", 4, False, "BBB"),
    # Control flow
    0x16: InstructionFormat(0x16, "JUMP_R", 5, False, "i"),
    0x17: InstructionFormat(0x17, "JUMP_IF_R", 6, False, "Bi"),
    0x18: InstructionFormat(0x18, "JUMP_IF_NOT_R", 6, False, "Bi"),
    0x19: InstructionFormat(0x19, "CALL_R", -1, False, ""),  # Variable size
    0x1A: InstructionFormat(0x1A, "RETURN_R", -1, False, ""),  # Variable size
    # MIR Support
    0x1B: InstructionFormat(0x1B, "PHI_R", -1, False, ""),  # Variable size
    0x1C: InstructionFormat(0x1C, "ASSERT_R", 5, True, "BBH"),  # reg + assert_type + msg_idx
    0x1D: InstructionFormat(0x1D, "SCOPE_ENTER_R", 3, False, "H"),
    0x1E: InstructionFormat(0x1E, "SCOPE_EXIT_R", 3, False, "H"),
    # String operations
    0x1F: InstructionFormat(0x1F, "CONCAT_STR_R", 4, False, "BBB"),
    0x20: InstructionFormat(0x20, "STR_LEN_R", 3, False, "BB"),
    # Arrays
    0x21: InstructionFormat(0x21, "NEW_ARRAY_R", 3, False, "BB"),
    0x22: InstructionFormat(0x22, "ARRAY_GET_R", 4, False, "BBB"),
    0x23: InstructionFormat(0x23, "ARRAY_SET_R", 4, False, "BBB"),
    0x24: InstructionFormat(0x24, "ARRAY_LEN_R", 3, False, "BB"),
    # Debug
    0x25: InstructionFormat(0x25, "DEBUG_PRINT", 2, False, "B"),
    0x26: InstructionFormat(0x26, "BREAKPOINT", 1, False, ""),
}


# =============================================================================
# Helper Functions
# =============================================================================


def make_hashable(value: Any) -> Any:
    """Convert value to hashable form for deduplication."""
    if isinstance(value, int | float | str | bool | type(None)):
        return value
    elif isinstance(value, bytes):
        return value
    elif isinstance(value, list):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    else:
        # Fallback: use string representation
        return str(value)


def build_constant_mapping(module: BytecodeModule) -> ConstantMapping:
    """Build mapping from local to global constant indices with deduplication."""

    global_constants: list[tuple[ConstantTag, Any]] = []
    chunk_mappings: list[dict[int, int]] = []
    original_count = 0
    bytes_saved = 0
    duplicate_chains: dict[tuple[Any, ...], list[int]] = {}

    # Global deduplication map: (tag, value) -> global_index
    global_dedupe: dict[tuple[Any, ...], int] = {}

    for chunk_idx, chunk in enumerate(module.chunks):
        local_to_global = {}

        for local_idx, (tag, value) in enumerate(chunk.constants):
            original_count += 1

            # Create hashable key for deduplication
            key = (tag, make_hashable(value))

            if key in global_dedupe:
                # Reuse existing global constant
                global_idx = global_dedupe[key]
                bytes_saved += estimate_constant_size(tag, value)

                # Track duplicate chains
                if key not in duplicate_chains:
                    duplicate_chains[key] = []
                duplicate_chains[key].append(chunk_idx)
            else:
                # Add new global constant
                global_idx = len(global_constants)
                global_constants.append((tag, value))
                global_dedupe[key] = global_idx

            local_to_global[local_idx] = global_idx

        chunk_mappings.append(local_to_global)

    stats = DeduplicationStats(
        original_count=original_count,
        deduped_count=len(global_constants),
        bytes_saved=bytes_saved,
        duplicate_chains=duplicate_chains,
    )

    return ConstantMapping(chunk_mappings=chunk_mappings, global_constants=global_constants, stats=stats)


def estimate_constant_size(tag: ConstantTag, value: Any) -> int:
    """Estimate the size of a constant in bytes."""
    if tag == ConstantTag.INT:
        return 9  # 1 (tag) + 8 (i64)
    elif tag == ConstantTag.FLOAT:
        return 9  # 1 (tag) + 8 (f64)
    elif tag == ConstantTag.STRING:
        return 5 + len(value.encode("utf-8"))  # 1 (tag) + 4 (len) + data
    elif tag == ConstantTag.BOOL:
        return 2  # 1 (tag) + 1 (bool)
    elif tag == ConstantTag.EMPTY:
        return 1  # 1 (tag)
    return 1


def get_instruction_size(opcode: int, bytecode: bytes, offset: int) -> int:
    """Get the actual size of an instruction at the given offset."""

    fmt = INSTRUCTION_FORMATS.get(opcode)
    if not fmt:
        return 1  # Unknown opcode, skip single byte

    if fmt.size > 0:
        return fmt.size

    # Handle variable-size instructions
    if opcode == Opcode.CALL_R:
        # Format: opcode + func + dst + num_args + args...
        if offset + 3 < len(bytecode):
            num_args = bytecode[offset + 3]
            return 4 + num_args
        return 1

    elif opcode == Opcode.PHI_R:
        # Format: opcode + dst + num_sources + (src + block_id) * num_sources
        if offset + 2 < len(bytecode):
            num_sources = bytecode[offset + 2]
            return 3 + num_sources * 3  # Each source is reg(1) + block_id(2)
        return 1

    elif opcode == Opcode.RETURN_R:
        # Format: opcode + has_value + [src]
        if offset + 1 < len(bytecode):
            has_value = bytecode[offset + 1]
            return 3 if has_value else 2
        return 1

    return 1


# =============================================================================
# Bytecode Remapper
# =============================================================================


class BytecodeRemapper:
    """Remaps constant indices in bytecode instructions."""

    def __init__(self, mapping: ConstantMapping):
        self.mapping = mapping

    def remap_chunk(self, chunk_index: int, bytecode: bytes) -> bytes:
        """Remap all constant indices in a chunk's bytecode."""

        if chunk_index >= len(self.mapping.chunk_mappings):
            # No remapping needed (e.g., chunk has no constants)
            return bytecode

        chunk_map = self.mapping.chunk_mappings[chunk_index]
        if not chunk_map:
            # Empty mapping, no constants to remap
            return bytecode

        result = bytearray()
        offset = 0

        while offset < len(bytecode):
            opcode = bytecode[offset]

            # Get instruction size
            inst_size = get_instruction_size(opcode, bytecode, offset)

            # Check if we have enough bytes
            if offset + inst_size > len(bytecode):
                raise InvalidBytecodeError(
                    f"Truncated instruction (opcode {opcode:#x}, expected {inst_size} bytes)",
                    offset=offset,
                    chunk_idx=chunk_index,
                )

            # Extract instruction bytes
            inst_bytes = bytecode[offset : offset + inst_size]

            # Check if this instruction needs remapping
            fmt = INSTRUCTION_FORMATS.get(opcode)
            if fmt and fmt.has_const_operand:
                # Remap the instruction
                result.append(opcode)
                remapped_operands = self.remap_instruction(
                    opcode, inst_bytes[1:], chunk_map, chunk_idx=chunk_index, offset=offset
                )
                result.extend(remapped_operands)
            else:
                # Copy instruction as-is
                result.extend(inst_bytes)

            offset += inst_size

        return bytes(result)

    def remap_instruction(
        self,
        opcode: int,
        operands: bytes,
        chunk_map: dict[int, int],
        chunk_idx: int | None = None,
        offset: int | None = None,
    ) -> bytes:
        """Remap constant indices in a single instruction."""

        if opcode == Opcode.LOAD_CONST_R:
            # Format: dst_reg(u8) + const_idx(u16)
            if len(operands) < 3:
                raise InvalidBytecodeError("LOAD_CONST_R operands too short", offset=offset, chunk_idx=chunk_idx)
            dst_reg = operands[0]
            old_idx = struct.unpack("<H", operands[1:3])[0]
            new_idx = chunk_map.get(old_idx, old_idx)

            return bytes([dst_reg]) + struct.pack("<H", new_idx)

        elif opcode in [Opcode.LOAD_GLOBAL_R, Opcode.STORE_GLOBAL_R]:
            # Format: reg(u8) + name_idx(u16)
            # Name index might reference string constants
            if len(operands) < 3:
                raise InvalidBytecodeError(
                    f"{INSTRUCTION_FORMATS[opcode].name} operands too short", offset=offset, chunk_idx=chunk_idx
                )
            reg = operands[0]
            old_idx = struct.unpack("<H", operands[1:3])[0]
            new_idx = chunk_map.get(old_idx, old_idx)

            return bytes([reg]) + struct.pack("<H", new_idx)

        elif opcode == Opcode.ASSERT_R:
            # Format: cond_reg(u8) + assert_type(u8) + msg_idx(u16)
            # Message index references string constant for assertion message
            if len(operands) < 4:
                raise InvalidBytecodeError("ASSERT_R operands too short", offset=offset, chunk_idx=chunk_idx)
            cond_reg = operands[0]
            assert_type = operands[1]
            old_idx = struct.unpack("<H", operands[2:4])[0]
            new_idx = chunk_map.get(old_idx, old_idx)

            # Validate the message index is valid
            if new_idx >= len(self.mapping.global_constants):
                raise ConstantIndexError(new_idx, len(self.mapping.global_constants) - 1, chunk_idx, offset)

            return bytes([cond_reg, assert_type]) + struct.pack("<H", new_idx)

        # Other opcodes don't reference constants
        return operands


def generate_remapping_report(module: BytecodeModule, mapping: ConstantMapping) -> str:
    """Generate human-readable remapping report for debugging."""
    report = []
    report.append("=== Constant Pool Remapping Report ===\n")

    # Deduplication statistics
    stats = mapping.stats
    report.append(f"Original constants: {stats.original_count}")
    report.append(f"After deduplication: {stats.deduped_count}")
    report.append(f"Bytes saved: {stats.bytes_saved}")
    if stats.original_count > 0:
        reduction = 100 * (stats.original_count - stats.deduped_count) / stats.original_count
        report.append(f"Reduction: {reduction:.1f}%\n")
    else:
        report.append("Reduction: N/A (no constants)\n")

    # Duplicate chains
    if stats.duplicate_chains:
        report.append("Duplicate constants found:")
        for key, chunks in stats.duplicate_chains.items():
            tag, val = key
            report.append(f"  {tag}: {val} appears in chunks: {chunks}")
        report.append("")

    # Per-chunk mappings
    report.append("Per-chunk remapping:")
    for chunk_idx, chunk_map in enumerate(mapping.chunk_mappings):
        if chunk_idx < len(module.chunks):
            chunk = module.chunks[chunk_idx]
            report.append(f"\nChunk {chunk_idx} ({chunk.name}):")
            for local, global_idx in sorted(chunk_map.items()):
                if global_idx < len(mapping.global_constants):
                    tag, val = mapping.global_constants[global_idx]
                    report.append(f"  [{local}] -> [{global_idx}]: {tag.name}: {val}")

    return "\n".join(report)


# =============================================================================
# Main Serializer
# =============================================================================


class VMBytecodeSerializer:
    """Serializes bytecode modules for the Rust VM with constant remapping."""

    @staticmethod
    def serialize(module: BytecodeModule, debug: bool = False) -> bytes:
        """Serialize a bytecode module to bytes.

        Args:
            module: BytecodeModule to serialize.
            debug: If True, print remapping report.

        Returns:
            Serialized bytecode.
        """
        buffer = BytesIO()
        VMBytecodeSerializer.write_to_stream(module, buffer, debug=debug)
        return buffer.getvalue()

    @staticmethod
    def write_to_stream(module: BytecodeModule, stream: BinaryIO, debug: bool = False) -> None:
        """Write bytecode module to a stream with constant index remapping.

        Args:
            module: BytecodeModule to serialize.
            stream: Binary stream to write to.
            debug: If True, print remapping report.
        """
        # Step 1: Build constant mapping with deduplication
        mapping = build_constant_mapping(module)

        # Print debug report if requested
        if debug:
            print(generate_remapping_report(module, mapping))

        # Step 2: Initialize remapper
        remapper = BytecodeRemapper(mapping)

        # Step 3: Process chunks with remapping
        all_bytecode = bytearray()
        chunk_offsets = {}

        for i, chunk in enumerate(module.chunks):
            chunk_offsets[i] = len(all_bytecode)

            # Remap this chunk's bytecode
            try:
                remapped = remapper.remap_chunk(i, bytes(chunk.bytecode))
                all_bytecode.extend(remapped)
            except RemappingError as e:
                # Add module context to error
                raise RemappingError(f"Failed to remap chunk '{chunk.name}': {e}") from e

        # Use remapped constants
        all_constants = mapping.global_constants

        # Calculate section sizes
        header_size = 28  # 4 (magic) + 4 (version) + 4 (flags) + 16 (4 offsets)

        name_bytes = module.name.encode("utf-8")
        name_section_size = 4 + len(name_bytes)

        const_section_size = 4  # count
        for tag, value in all_constants:
            const_section_size += 1  # tag
            if tag == ConstantTag.INT:
                const_section_size += 8  # i64
            elif tag == ConstantTag.FLOAT:
                const_section_size += 8  # f64
            elif tag == ConstantTag.STRING:
                str_bytes = value.encode("utf-8")
                const_section_size += 4 + len(str_bytes)  # length + data
            elif tag == ConstantTag.BOOL:
                const_section_size += 1  # u8
            # EMPTY has no data

        # Calculate function table section size
        func_section_size = 4  # count
        for func_name in module.function_table:
            func_name_bytes = func_name.encode("utf-8")
            func_section_size += 4 + len(func_name_bytes) + 4  # name length + name + offset

        # Calculate offsets
        name_offset = header_size
        const_offset = name_offset + name_section_size
        func_offset = const_offset + const_section_size
        inst_offset = func_offset + func_section_size

        # Write header
        stream.write(b"MDBC")  # Magic
        stream.write(struct.pack("<I", 1))  # Version
        stream.write(struct.pack("<I", 0x0001))  # Flags (little-endian)
        stream.write(struct.pack("<I", name_offset))
        stream.write(struct.pack("<I", const_offset))
        stream.write(struct.pack("<I", func_offset))
        stream.write(struct.pack("<I", inst_offset))

        # Write module name
        stream.write(struct.pack("<I", len(name_bytes)))
        stream.write(name_bytes)

        # Write constants (now deduplicated and remapped)
        stream.write(struct.pack("<I", len(all_constants)))
        for tag, value in all_constants:
            stream.write(struct.pack("<B", tag))
            if tag == ConstantTag.INT:
                stream.write(struct.pack("<q", value))
            elif tag == ConstantTag.FLOAT:
                stream.write(struct.pack("<d", value))
            elif tag == ConstantTag.STRING:
                str_bytes = value.encode("utf-8")
                stream.write(struct.pack("<I", len(str_bytes)))
                stream.write(str_bytes)
            elif tag == ConstantTag.BOOL:
                stream.write(struct.pack("<B", 1 if value else 0))
            # EMPTY has no data

        # Write function table (convert chunk indices to bytecode offsets)
        stream.write(struct.pack("<I", len(module.function_table)))
        for func_name, chunk_idx in module.function_table.items():
            func_name_bytes = func_name.encode("utf-8")
            stream.write(struct.pack("<I", len(func_name_bytes)))
            stream.write(func_name_bytes)
            # Convert chunk index to bytecode offset (instruction index)
            bytecode_offset = chunk_offsets.get(chunk_idx, 0)
            # Convert byte offset to instruction offset
            inst_offset = VMBytecodeSerializer.count_instructions(bytes(all_bytecode[:bytecode_offset]))
            stream.write(struct.pack("<I", inst_offset))

        # Write instructions
        # The Rust loader expects the number of instructions, not bytes
        instruction_count = VMBytecodeSerializer.count_instructions(bytes(all_bytecode))
        stream.write(struct.pack("<I", instruction_count))
        stream.write(all_bytecode)

    @staticmethod
    def count_instructions(bytecode: bytes) -> int:
        """Count the number of instructions in bytecode.

        Args:
            bytecode: Raw bytecode bytes.

        Returns:
            Number of instructions.
        """
        count = 0
        i = 0

        while i < len(bytecode):
            opcode = bytecode[i]
            count += 1

            # Use the get_instruction_size helper
            inst_size = get_instruction_size(opcode, bytecode, i)
            i += inst_size

        return count

    @staticmethod
    def parse_instructions(bytecode: bytes, const_base: int = 0) -> list[bytes]:
        """Parse bytecode into individual instructions.

        DEPRECATED: This method is kept for backward compatibility but
        the new remapping approach is used in write_to_stream.

        Args:
            bytecode: Raw bytecode bytes.
            const_base: Base offset for constant indices.

        Returns:
            List of individual instruction bytes.
        """
        instructions = []
        i = 0

        while i < len(bytecode):
            start = i
            opcode = bytecode[i]

            # Get instruction size
            inst_size = get_instruction_size(opcode, bytecode, i)

            # Extract instruction
            inst = bytecode[start : start + inst_size]

            # Legacy remapping for LOAD_CONST_R only
            if const_base > 0 and opcode == Opcode.LOAD_CONST_R:
                new_inst = bytearray(inst)
                old_idx = struct.unpack("<H", inst[2:4])[0]
                new_idx = old_idx + const_base
                struct.pack_into("<H", new_inst, 2, new_idx)
                inst = bytes(new_inst)

            instructions.append(inst)
            i += inst_size

        return instructions
