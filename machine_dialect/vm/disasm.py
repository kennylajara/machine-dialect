"""Disassembler for Machine Dialect bytecode.

This module provides utilities to convert bytecode back to human-readable
assembly for debugging purposes.
"""

from typing import Any

from machine_dialect.codegen.isa import INSTRUCTIONS, Opcode, OperandType
from machine_dialect.codegen.objects import Chunk


def read_u8(code: bytes, i: int) -> tuple[int, int]:
    """Read an unsigned 8-bit value.

    Args:
        code: Bytecode array.
        i: Current position.

    Returns:
        Tuple of (value, new_position).
    """
    return code[i], i + 1


def read_u16(code: bytes, i: int) -> tuple[int, int]:
    """Read an unsigned 16-bit value (little-endian).

    Args:
        code: Bytecode array.
        i: Current position.

    Returns:
        Tuple of (value, new_position).
    """
    value = int.from_bytes(code[i : i + 2], "little", signed=False)
    return value, i + 2


def read_i16(code: bytes, i: int) -> tuple[int, int]:
    """Read a signed 16-bit value (little-endian).

    Args:
        code: Bytecode array.
        i: Current position.

    Returns:
        Tuple of (value, new_position).
    """
    value = int.from_bytes(code[i : i + 2], "little", signed=True)
    return value, i + 2


def disassemble_chunk(chunk: Chunk, show_lines: bool = False) -> str:
    """Disassemble a chunk to human-readable format.

    Args:
        chunk: The chunk to disassemble.
        show_lines: Whether to show source line annotations.

    Returns:
        String containing the disassembled code.
    """
    return disassemble_bytes(
        bytes(chunk.bytecode),
        chunk.constants.constants(),
        chunk.source_map if show_lines else None,
    )


def disassemble_bytes(
    code: bytes,
    const_pool: list[Any],
    lineinfo: dict[int, tuple[int, int]] | None = None,
) -> str:
    """Disassemble raw bytecode to human-readable format.

    Args:
        code: Raw bytecode.
        const_pool: Constant pool.
        lineinfo: Optional mapping of PC to (line, col).

    Returns:
        String containing the disassembled code.
    """
    lines = []
    i = 0
    last_line = -1

    while i < len(code):
        # Show line info if available
        if lineinfo and i in lineinfo:
            line, col = lineinfo[i]
            if line != last_line:
                lines.append(f"# line {line}")
                last_line = line

        # Save offset for display
        offset = i

        # Read opcode
        opcode_val = code[i]
        i += 1

        try:
            opcode = Opcode(opcode_val)
            spec = INSTRUCTIONS[opcode]
        except (ValueError, KeyError):
            lines.append(f"{offset:04d}: <unknown opcode {opcode_val}>")
            continue

        # Read operands
        operands = []
        for operand_type in spec.operands:
            if operand_type == OperandType.U8:
                val, i = read_u8(code, i)
                operands.append(val)
            elif operand_type == OperandType.U16:
                val, i = read_u16(code, i)
                operands.append(val)
            elif operand_type == OperandType.I16:
                val, i = read_i16(code, i)
                operands.append(val)

        # Format instruction
        name = spec.name
        operand_str = ""
        comment = ""

        if operands:
            operand_str = " ".join(f"{op:5d}" for op in operands)

            # Add comments for certain instructions
            if opcode in (Opcode.LOAD_CONST, Opcode.LOAD_GLOBAL, Opcode.STORE_GLOBAL):
                idx = operands[0]
                if 0 <= idx < len(const_pool):
                    value = const_pool[idx]
                    if isinstance(value, str):
                        comment = f'  ; "{value}"'
                    else:
                        comment = f"  ; {value}"
                else:
                    comment = "  ; <out of range>"

            elif opcode in (Opcode.JUMP, Opcode.JUMP_IF_FALSE):
                # Show target address for jumps
                target = i + operands[0]
                comment = f"  ; -> {target:04d}"

        # Format the line
        padding = " " * max(1, 15 - len(name))
        line_str = f"{offset:04d}: {name}{padding}{operand_str}{comment}".rstrip()
        lines.append(line_str)

    return "\n".join(lines)


def disassemble(obj: Chunk | bytes, show_lines: bool = False) -> str:
    """Disassemble a chunk or raw bytes.

    Args:
        obj: Chunk or bytes to disassemble.
        show_lines: Whether to show source lines.

    Returns:
        Disassembled output.
    """
    if isinstance(obj, Chunk):
        return disassemble_chunk(obj, show_lines)
    elif isinstance(obj, bytes):
        return disassemble_bytes(obj, [], None)
    else:
        raise TypeError(f"Cannot disassemble {type(obj).__name__}")


def print_disassembly(chunk: Chunk, show_lines: bool = False) -> None:
    """Print disassembled chunk with header.

    Args:
        chunk: The chunk to disassemble.
        show_lines: Whether to show source lines.
    """
    print(f"=== Disassembly of '{chunk.name}' ===")
    print(f"Constants: {chunk.constants.size()}")
    for i, const in enumerate(chunk.constants.constants()):
        if isinstance(const, str):
            print(f'  [{i:3d}] "{const}"')
        else:
            print(f"  [{i:3d}] {const}")
    print("\nBytecode:")
    print(disassemble_chunk(chunk, show_lines))
    print()
