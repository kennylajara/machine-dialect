"""Data structures for compiled bytecode.

This module defines the Chunk and Module classes that represent
compiled Machine Dialect programs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from machine_dialect.codegen.constpool import ConstantPool, ConstantValue


class ModuleType(Enum):
    """Type of module - procedural or class-based."""

    PROCEDURAL = "procedural"  # Traditional procedural program
    CLASS = "class"  # Class definition (future)


class ChunkType(Enum):
    """Type of chunk - determines its role in the module."""

    MAIN = "main"  # Main program chunk
    FUNCTION = "function"  # Regular function
    METHOD = "method"  # Class method (future)
    CONSTRUCTOR = "constructor"  # Class constructor (future)
    RULE_CONDITION = "rule_condition"  # Rule condition chunk (future)
    RULE_ACTION = "rule_action"  # Rule action chunk (future)
    STATIC = "static"  # Static initialization (future)


@dataclass
class Chunk:
    """A chunk of compiled bytecode.

    Represents a compiled function or top-level program with its
    bytecode, constants, and metadata.
    """

    name: str = "main"
    chunk_type: ChunkType = ChunkType.MAIN  # Type of this chunk
    bytecode: bytearray = field(default_factory=bytearray)
    constants: ConstantPool = field(default_factory=ConstantPool)
    num_locals: int = 0
    num_params: int = 0
    param_names: list[str] = field(default_factory=list)  # Parameter names in order
    param_defaults: list[Any | None] = field(default_factory=list)  # Default values for params (None if required)
    source_map: dict[int, tuple[int, int]] = field(default_factory=dict)  # pc -> (line, col)

    # Future OOP fields
    visibility: str | None = None  # "public", "private", "protected"
    is_static: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def size(self) -> int:
        """Get the size of the bytecode in bytes.

        Returns:
            Number of bytes in the bytecode.
        """
        return len(self.bytecode)

    def add_constant(self, value: ConstantValue) -> int:
        """Add a constant to the chunk's constant pool.

        Args:
            value: The constant value to add.

        Returns:
            Index of the constant.
        """
        return self.constants.add(value)

    def get_constant(self, index: int) -> ConstantValue:
        """Get a constant from the pool by index.

        Args:
            index: Index of the constant.

        Returns:
            The constant value.
        """
        return self.constants.get(index)

    def write_byte(self, byte: int) -> int:
        """Write a single byte to the bytecode.

        Args:
            byte: Byte value (0-255).

        Returns:
            Position where byte was written.

        Raises:
            ValueError: If byte is out of range.
        """
        if not 0 <= byte <= 255:
            raise ValueError(f"Byte value {byte} out of range [0, 255]")

        pos = len(self.bytecode)
        self.bytecode.append(byte)
        return pos

    def write_bytes(self, *bytes: int) -> int:
        """Write multiple bytes to the bytecode.

        Args:
            bytes: Byte values to write.

        Returns:
            Position where first byte was written.
        """
        pos = len(self.bytecode)
        for byte in bytes:
            self.write_byte(byte)
        return pos

    def write_u16(self, value: int) -> int:
        """Write a 16-bit unsigned integer (little-endian).

        Args:
            value: Value to write (0-65535).

        Returns:
            Position where first byte was written.

        Raises:
            ValueError: If value is out of range.
        """
        if not 0 <= value <= 65535:
            raise ValueError(f"U16 value {value} out of range [0, 65535]")

        pos = len(self.bytecode)
        self.bytecode.append(value & 0xFF)  # Low byte
        self.bytecode.append((value >> 8) & 0xFF)  # High byte
        return pos

    def write_i16(self, value: int) -> int:
        """Write a 16-bit signed integer (little-endian).

        Args:
            value: Value to write (-32768 to 32767).

        Returns:
            Position where first byte was written.

        Raises:
            ValueError: If value is out of range.
        """
        if not -32768 <= value <= 32767:
            raise ValueError(f"I16 value {value} out of range [-32768, 32767]")

        # Convert to unsigned representation
        if value < 0:
            value = (1 << 16) + value

        return self.write_u16(value)

    def patch_jump(self, jump_pos: int, target_pos: int) -> None:
        """Patch a jump instruction with the correct offset.

        Args:
            jump_pos: Position of the jump operand.
            target_pos: Target position to jump to.
        """
        # Calculate relative offset
        offset = target_pos - (jump_pos + 2)  # +2 for the i16 operand size

        # Validate offset fits in i16
        if not -32768 <= offset <= 32767:
            raise ValueError(f"Jump offset {offset} too large for i16")

        # Convert to unsigned representation for storage
        if offset < 0:
            offset = (1 << 16) + offset

        # Patch the bytes (little-endian)
        self.bytecode[jump_pos] = offset & 0xFF
        self.bytecode[jump_pos + 1] = (offset >> 8) & 0xFF

    def current_position(self) -> int:
        """Get the current bytecode position.

        Returns:
            Current position in bytecode array.
        """
        return len(self.bytecode)

    def __str__(self) -> str:
        """String representation of the chunk.

        Returns:
            Human-readable chunk information.
        """
        lines = [
            f"Chunk: {self.name}",
            f"  Size: {self.size()} bytes",
            f"  Locals: {self.num_locals}",
            f"  Params: {self.num_params}",
            f"  Constants: {self.constants.size()}",
        ]
        return "\n".join(lines)


@dataclass
class Module:
    """A compiled module containing multiple chunks.

    Represents a complete compiled program with its main chunk
    and any function definitions. Can be either procedural or class-based.
    """

    name: str
    main_chunk: Chunk
    module_type: ModuleType = ModuleType.PROCEDURAL  # Type of this module
    functions: dict[str, Chunk] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)

    # Future OOP fields (empty for procedural modules)
    parent_class: str | None = None  # Parent class name for inheritance
    interfaces: list[str] = field(default_factory=list)  # Implemented interfaces
    fields: dict[str, Any] = field(default_factory=dict)  # Class fields/properties
    methods: dict[str, Chunk] = field(default_factory=dict)  # Class methods
    rules: dict[str, tuple[Chunk, Chunk]] = field(default_factory=dict)  # Rules (condition, action)
    constructor_chunk: Chunk | None = None  # Constructor chunk
    static_chunk: Chunk | None = None  # Static initialization chunk

    def add_function(self, name: str, chunk: Chunk) -> None:
        """Add a function chunk to the module.

        Args:
            name: Function name.
            chunk: Compiled function chunk.
        """
        self.functions[name] = chunk

    def get_function(self, name: str) -> Chunk | None:
        """Get a function chunk by name.

        Args:
            name: Function name.

        Returns:
            The function chunk if found, None otherwise.
        """
        return self.functions.get(name)

    def total_size(self) -> int:
        """Get the total bytecode size of the module.

        Returns:
            Combined size of all chunks in bytes.
        """
        size = self.main_chunk.size()
        for chunk in self.functions.values():
            size += chunk.size()
        return size

    def is_procedural(self) -> bool:
        """Check if this is a procedural module.

        Returns:
            True if module is procedural, False otherwise.
        """
        return self.module_type == ModuleType.PROCEDURAL

    def is_class(self) -> bool:
        """Check if this is a class module.

        Returns:
            True if module is a class, False otherwise.
        """
        return self.module_type == ModuleType.CLASS

    def __str__(self) -> str:
        """String representation of the module.

        Returns:
            Human-readable module information.
        """
        lines = [
            f"Module: {self.name} ({self.module_type.value})",
            f"  Main chunk: {self.main_chunk.size()} bytes",
            f"  Functions: {len(self.functions)}",
        ]

        if self.is_class():
            lines.extend(
                [
                    f"  Methods: {len(self.methods)}",
                    f"  Fields: {len(self.fields)}",
                    f"  Rules: {len(self.rules)}",
                ]
            )

        lines.append(f"  Total size: {self.total_size()} bytes")
        return "\n".join(lines)
