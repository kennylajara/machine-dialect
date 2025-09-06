"""Proper bytecode serializer for the Rust VM.

This serializer correctly handles individual instruction parsing.
"""

from __future__ import annotations

import struct
from io import BytesIO
from typing import BinaryIO

from machine_dialect.codegen.bytecode_module import BytecodeModule, ConstantTag
from machine_dialect.codegen.opcodes import Opcode


class VMBytecodeSerializer:
    """Serializes bytecode modules for the Rust VM."""

    @staticmethod
    def serialize(module: BytecodeModule) -> bytes:
        """Serialize a bytecode module to bytes.

        Args:
            module: BytecodeModule to serialize.

        Returns:
            Serialized bytecode.
        """
        buffer = BytesIO()
        VMBytecodeSerializer.write_to_stream(module, buffer)
        return buffer.getvalue()

    @staticmethod
    def write_to_stream(module: BytecodeModule, stream: BinaryIO) -> None:
        """Write bytecode module to a stream.

        Args:
            module: BytecodeModule to serialize.
            stream: Binary stream to write to.
        """
        # Collect all constants and instructions from chunks
        all_constants = []
        all_instructions = []

        for chunk in module.chunks:
            # Add constants
            const_base = len(all_constants)
            all_constants.extend(chunk.constants)

            # Parse and collect individual instructions
            chunk_instructions = VMBytecodeSerializer.parse_instructions(chunk.bytecode, const_base)
            all_instructions.extend(chunk_instructions)

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

        func_section_size = 4  # count (0 for now)

        inst_section_size = 4  # count
        for inst in all_instructions:
            inst_section_size += len(inst)

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

        # Write constants
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

        # Write function table (empty for now)
        stream.write(struct.pack("<I", 0))

        # Write instructions
        stream.write(struct.pack("<I", len(all_instructions)))
        for inst in all_instructions:
            stream.write(inst)

    @staticmethod
    def parse_instructions(bytecode: bytes, const_base: int = 0) -> list[bytes]:
        """Parse bytecode into individual instructions.

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

            # Determine instruction size
            if opcode in [Opcode.LOAD_CONST_R, Opcode.LOAD_GLOBAL_R, Opcode.STORE_GLOBAL_R]:
                # opcode + u8 + u16
                inst_size = 4
            elif opcode in [Opcode.MOVE_R, Opcode.NEG_R, Opcode.NOT_R]:
                # opcode + u8 + u8
                inst_size = 3
            elif opcode in [
                Opcode.ADD_R,
                Opcode.SUB_R,
                Opcode.MUL_R,
                Opcode.DIV_R,
                Opcode.MOD_R,
                Opcode.AND_R,
                Opcode.OR_R,
                Opcode.EQ_R,
                Opcode.NEQ_R,
                Opcode.LT_R,
                Opcode.GT_R,
                Opcode.LTE_R,
                Opcode.GTE_R,
                Opcode.CONCAT_STR_R,
                Opcode.ARRAY_GET_R,
                Opcode.ARRAY_SET_R,
            ]:
                # opcode + u8 + u8 + u8
                inst_size = 4
            elif opcode in [Opcode.NEW_ARRAY_R, Opcode.ARRAY_LEN_R]:
                # opcode + u8 + u8
                inst_size = 3
            elif opcode in [Opcode.STR_LEN_R]:
                # opcode + u8 + u8
                inst_size = 3
            elif opcode == Opcode.JUMP_R:
                # opcode + i32
                inst_size = 5
            elif opcode in [Opcode.JUMP_IF_R, Opcode.JUMP_IF_NOT_R]:
                # opcode + u8 + i32
                inst_size = 6
            elif opcode == Opcode.RETURN_R:
                # opcode + has_value + [src]
                has_value = bytecode[i + 1] if i + 1 < len(bytecode) else 0
                inst_size = 3 if has_value else 2
            elif opcode == Opcode.CALL_R:
                # Variable length: opcode + func + dst + num_args + args...
                if i + 3 < len(bytecode):
                    num_args = bytecode[i + 3]
                    inst_size = 4 + num_args
                else:
                    inst_size = 1
            elif opcode == Opcode.PHI_R:
                # Variable length: opcode + dst + num_sources + sources...
                if i + 2 < len(bytecode):
                    num_sources = bytecode[i + 2]
                    inst_size = 3 + num_sources * 3
                else:
                    inst_size = 1
            elif opcode in [Opcode.ASSERT_R, Opcode.DEFINE_R]:
                # opcode + u8 + u16
                inst_size = 4
            elif opcode in [Opcode.CHECK_TYPE_R, Opcode.CAST_R]:
                # opcode + u8 + u8 + u16
                inst_size = 5
            elif opcode in [Opcode.SCOPE_ENTER_R, Opcode.SCOPE_EXIT_R]:
                # opcode + u16
                inst_size = 3
            elif opcode == Opcode.DEBUG_PRINT:
                # opcode + u8
                inst_size = 2
            elif opcode == Opcode.BREAKPOINT:
                # opcode only
                inst_size = 1
            else:
                # Unknown opcode, assume 1 byte
                inst_size = 1

            # Extract and adjust instruction if needed
            inst = bytecode[start : start + inst_size]

            # Adjust constant indices if needed
            if const_base > 0 and opcode == Opcode.LOAD_CONST_R:
                # Rebuild instruction with adjusted const_idx
                new_inst = bytearray(inst)
                old_idx = struct.unpack("<H", inst[2:4])[0]
                new_idx = old_idx + const_base
                struct.pack_into("<H", new_inst, 2, new_idx)
                inst = bytes(new_inst)

            instructions.append(inst)
            i += inst_size

        return instructions
