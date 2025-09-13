"""Bytecode module representation.

This module defines the bytecode module structure for the Rust VM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class ChunkType(IntEnum):
    """Type of bytecode chunk."""

    MAIN = 0
    FUNCTION = 1


class ConstantTag(IntEnum):
    """Tags for constant pool values."""

    EMPTY = 0x05
    INT = 0x01
    FLOAT = 0x02
    STRING = 0x03
    BOOL = 0x04


@dataclass
class Chunk:
    """A bytecode chunk (function or main)."""

    name: str
    chunk_type: ChunkType
    bytecode: bytearray
    constants: list[tuple[ConstantTag, Any]]
    num_locals: int
    num_params: int


@dataclass
class BytecodeModule:
    """A complete bytecode module."""

    name: str = "__main__"
    chunks: list[Chunk] = field(default_factory=list)
    function_table: dict[str, int] = field(default_factory=dict)
    global_names: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_chunk(self, chunk: Chunk) -> int:
        """Add a chunk and return its index.

        Args:
            chunk: Chunk to add.

        Returns:
            Index of the added chunk.
        """
        index = len(self.chunks)
        self.chunks.append(chunk)
        if chunk.chunk_type == ChunkType.FUNCTION:
            # Record function entry point (bytecode offset)
            self.function_table[chunk.name] = index
        return index

    def add_global(self, name: str) -> int:
        """Add a global name and return its index.

        Args:
            name: Global name to add.

        Returns:
            Index of the global name.
        """
        if name not in self.global_names:
            self.global_names.append(name)
        return self.global_names.index(name)

    def serialize(self) -> bytes:
        """Serialize the module to bytecode format.

        Returns:
            Serialized bytecode.
        """
        from machine_dialect.codegen.vm_serializer import VMBytecodeSerializer

        return VMBytecodeSerializer.serialize(self)
