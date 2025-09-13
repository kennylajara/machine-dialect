"""Bytecode serializer for the Rust VM.

This module serializes bytecode in the format expected by the Rust VM loader.
"""

from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO

# Magic number for bytecode files
MAGIC_NUMBER = b"MDBC"

# Current bytecode version
BYTECODE_VERSION = 1

# Flags
FLAG_LITTLE_ENDIAN = 0x0001


class BytecodeWriter:
    """Writes bytecode in the format expected by the Rust VM."""

    def __init__(self, module: Any = None) -> None:
        """Initialize the bytecode writer.

        Args:
            module: Optional module with bytecode data to write
        """
        self.buffer = BytesIO()

        # Initialize attributes with type hints
        self.constants: list[tuple[int, Any]]
        self.instructions: list[bytes]
        self.functions: dict[str, int]
        self.global_names: list[str]
        self.module_name: str

        if module:
            # Just use the module's attributes directly
            self.constants = module.constants
            self.instructions = module.instructions
            self.functions = getattr(module, "function_table", {})
            self.global_names = getattr(module, "global_names", [])
            self.module_name = getattr(module, "name", "__main__")
        else:
            self.constants = []  # (tag, value) pairs
            self.instructions = []
            self.functions = {}  # name -> instruction offset
            self.global_names = []
            self.module_name = "__main__"

    def set_module_name(self, name: str) -> None:
        """Set the module name."""
        self.module_name = name

    def add_constant(self, tag: int, value: Any) -> int:
        """Add a constant to the constant pool.

        Args:
            tag: Type tag (1=int, 2=float, 3=string, 4=bool, 5=empty)
            value: The constant value

        Returns:
            Index of the constant in the pool
        """
        idx = len(self.constants)
        self.constants.append((tag, value))
        return idx

    def add_int_constant(self, value: int) -> int:
        """Add an integer constant."""
        return self.add_constant(0x01, value)

    def add_float_constant(self, value: float) -> int:
        """Add a float constant."""
        return self.add_constant(0x02, value)

    def add_string_constant(self, value: str) -> int:
        """Add a string constant."""
        return self.add_constant(0x03, value)

    def add_bool_constant(self, value: bool) -> int:
        """Add a boolean constant."""
        return self.add_constant(0x04, value)

    def add_empty_constant(self) -> int:
        """Add an empty/none constant."""
        return self.add_constant(0x05, None)

    def add_global_name(self, name: str) -> int:
        """Add a global name and return its index."""
        if name not in self.global_names:
            self.global_names.append(name)
        return self.global_names.index(name)

    def add_instruction(self, instruction: bytes) -> None:
        """Add a raw instruction."""
        self.instructions.append(instruction)

    def emit_load_const(self, dst: int, const_idx: int) -> None:
        """Emit LoadConstR instruction."""
        inst = struct.pack("<BBH", 0, dst, const_idx)
        self.add_instruction(inst)

    def emit_move(self, dst: int, src: int) -> None:
        """Emit MoveR instruction."""
        inst = struct.pack("<BBB", 1, dst, src)
        self.add_instruction(inst)

    def emit_load_global(self, dst: int, name_idx: int) -> None:
        """Emit LoadGlobalR instruction."""
        inst = struct.pack("<BBH", 2, dst, name_idx)
        self.add_instruction(inst)

    def emit_store_global(self, src: int, name_idx: int) -> None:
        """Emit StoreGlobalR instruction."""
        inst = struct.pack("<BBH", 3, src, name_idx)
        self.add_instruction(inst)

    def emit_add(self, dst: int, left: int, right: int) -> None:
        """Emit AddR instruction."""
        inst = struct.pack("<BBBB", 7, dst, left, right)
        self.add_instruction(inst)

    def emit_sub(self, dst: int, left: int, right: int) -> None:
        """Emit SubR instruction."""
        inst = struct.pack("<BBBB", 8, dst, left, right)
        self.add_instruction(inst)

    def emit_mul(self, dst: int, left: int, right: int) -> None:
        """Emit MulR instruction."""
        inst = struct.pack("<BBBB", 9, dst, left, right)
        self.add_instruction(inst)

    def emit_div(self, dst: int, left: int, right: int) -> None:
        """Emit DivR instruction."""
        inst = struct.pack("<BBBB", 10, dst, left, right)
        self.add_instruction(inst)

    def emit_jump(self, offset: int) -> None:
        """Emit JumpR instruction."""
        inst = struct.pack("<Bi", 22, offset)
        self.add_instruction(inst)

    def emit_jump_if(self, cond: int, offset: int) -> None:
        """Emit JumpIfR instruction."""
        inst = struct.pack("<BBi", 23, cond, offset)
        self.add_instruction(inst)

    def emit_return(self, src: int | None = None) -> None:
        """Emit ReturnR instruction."""
        if src is not None:
            inst = struct.pack("<BBB", 26, 1, src)  # has_value=1, src
        else:
            inst = struct.pack("<BB", 26, 0)  # has_value=0
        self.add_instruction(inst)

    def emit_debug_print(self, src: int) -> None:
        """Emit DebugPrint instruction."""
        inst = struct.pack("<BB", 37, src)
        self.add_instruction(inst)

    def write(self) -> bytes:
        """Write the bytecode to bytes.

        Returns:
            The serialized bytecode as bytes.
        """
        buffer = BytesIO()
        self.write_to_stream(buffer)
        return buffer.getvalue()

    def write_to_file(self, path: Path) -> None:
        """Write the bytecode to a file.

        Args:
            path: Path to write the bytecode file (without extension)
        """
        bytecode_path = path.with_suffix(".mdbc")
        with open(bytecode_path, "wb") as f:
            self.write_to_stream(f)

    def write_to_stream(self, stream: BinaryIO) -> None:
        """Write the bytecode to a binary stream.

        Args:
            stream: Binary stream to write to
        """
        # Calculate section offsets
        header_size = 28  # 4 (magic) + 4 (version) + 4 (flags) + 16 (4 offsets)

        # Module name section
        name_bytes = self.module_name.encode("utf-8")
        name_section_size = 4 + len(name_bytes)  # length prefix + name

        # Constants section
        const_buffer = BytesIO()
        const_buffer.write(struct.pack("<I", len(self.constants)))
        for tag, value in self.constants:
            const_buffer.write(struct.pack("<B", tag))
            if tag == 0x01:  # Int
                const_buffer.write(struct.pack("<q", value))
            elif tag == 0x02:  # Float
                const_buffer.write(struct.pack("<d", value))
            elif tag == 0x03:  # String
                str_bytes = value.encode("utf-8")
                const_buffer.write(struct.pack("<I", len(str_bytes)))
                const_buffer.write(str_bytes)
            elif tag == 0x04:  # Bool
                const_buffer.write(struct.pack("<B", 1 if value else 0))
            elif tag == 0x05:  # Empty
                pass  # No data
        const_data = const_buffer.getvalue()

        # Function table section
        func_buffer = BytesIO()
        func_buffer.write(struct.pack("<I", len(self.functions)))
        for name, offset in self.functions.items():
            func_name_bytes = name.encode("utf-8")
            func_buffer.write(struct.pack("<I", len(func_name_bytes)))
            func_buffer.write(func_name_bytes)
            func_buffer.write(struct.pack("<I", offset))
        func_data = func_buffer.getvalue()

        # Instructions section
        inst_buffer = BytesIO()
        inst_buffer.write(struct.pack("<I", len(self.instructions)))
        for inst in self.instructions:
            inst_buffer.write(inst)
        inst_data = inst_buffer.getvalue()

        # Calculate offsets
        name_offset = header_size
        const_offset = name_offset + name_section_size
        func_offset = const_offset + len(const_data)
        inst_offset = func_offset + len(func_data)

        # Write header
        stream.write(MAGIC_NUMBER)  # Magic number
        stream.write(struct.pack("<I", BYTECODE_VERSION))  # Version
        stream.write(struct.pack("<I", FLAG_LITTLE_ENDIAN))  # Flags
        stream.write(struct.pack("<I", name_offset))  # Name offset
        stream.write(struct.pack("<I", const_offset))  # Constant offset
        stream.write(struct.pack("<I", func_offset))  # Function offset
        stream.write(struct.pack("<I", inst_offset))  # Instruction offset

        # Write sections
        stream.write(struct.pack("<I", len(name_bytes)))
        stream.write(name_bytes)
        stream.write(const_data)
        stream.write(func_data)
        stream.write(inst_data)

        # Write global names if any
        if self.global_names:
            stream.write(struct.pack("<I", len(self.global_names)))
            for name in self.global_names:
                name_bytes = name.encode("utf-8")
                stream.write(struct.pack("<I", len(name_bytes)))
                stream.write(name_bytes)


def serialize_bytecode_module(
    module_name: str,
    constants: list[tuple[int, Any]],
    instructions: list[bytes],
    functions: dict[str, int] | None = None,
    global_names: list[str] | None = None,
    output_path: Path | None = None,
) -> bytes:
    """Serialize a bytecode module.

    Args:
        module_name: Name of the module
        constants: List of (tag, value) pairs for the constant pool
        instructions: List of instruction bytes
        functions: Optional function table (name -> offset)
        global_names: Optional list of global variable names
        output_path: Optional path to write the bytecode file

    Returns:
        The serialized bytecode as bytes
    """
    writer = BytecodeWriter()
    writer.set_module_name(module_name)
    writer.constants = constants
    writer.instructions = instructions
    writer.functions = functions or {}
    writer.global_names = global_names or []

    if output_path:
        writer.write_to_file(output_path)

    # Also return the bytes
    buffer = BytesIO()
    writer.write_to_stream(buffer)
    return buffer.getvalue()
