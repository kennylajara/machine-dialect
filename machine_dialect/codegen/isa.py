"""Instruction Set Architecture for Machine Dialect VM.

This module defines the bytecode instructions and their specifications
for the Machine Dialect virtual machine.
"""

from enum import IntEnum, auto
from typing import NamedTuple


class Opcode(IntEnum):
    """VM instruction opcodes."""

    # Load/Store operations
    LOAD_CONST = 0  # Load constant from pool [u16 index]
    LOAD_LOCAL = auto()  # Load local variable [u16 slot]
    STORE_LOCAL = auto()  # Store to local variable [u16 slot]
    LOAD_GLOBAL = auto()  # Load global by name [u16 name_idx]
    STORE_GLOBAL = auto()  # Store global by name [u16 name_idx]

    # Stack manipulation
    POP = auto()  # Remove top of stack
    DUP = auto()  # Duplicate top of stack
    SWAP = auto()  # Swap top two stack items

    # Arithmetic operations (binary)
    ADD = auto()  # Addition
    SUB = auto()  # Subtraction
    MUL = auto()  # Multiplication
    DIV = auto()  # Division
    MOD = auto()  # Modulo

    # Unary operations
    NEG = auto()  # Negation (unary minus)
    NOT = auto()  # Logical NOT

    # Comparison operations
    EQ = auto()  # Equal (value equality)
    NEQ = auto()  # Not equal (value inequality)
    LT = auto()  # Less than
    GT = auto()  # Greater than
    LTE = auto()  # Less than or equal
    GTE = auto()  # Greater than or equal
    STRICT_EQ = auto()  # Strict equality (type and value)
    STRICT_NEQ = auto()  # Strict inequality (type or value)

    # Logical operations (no short-circuit)
    AND = auto()  # Logical AND
    OR = auto()  # Logical OR

    # Control flow
    JUMP = auto()  # Unconditional jump [i16 offset]
    JUMP_IF_FALSE = auto()  # Jump if top is falsy [i16 offset]
    RETURN = auto()  # Return from function

    # Function calls
    CALL = auto()  # Call function [u8 nargs]
    LOAD_FUNCTION = auto()  # Load function by name [u16 name_idx]

    # Miscellaneous
    NOP = auto()  # No operation
    HALT = auto()  # Stop execution


class OperandType(IntEnum):
    """Types of instruction operands."""

    NONE = 0  # No operand
    U8 = auto()  # Unsigned 8-bit
    U16 = auto()  # Unsigned 16-bit
    I16 = auto()  # Signed 16-bit


class InstructionSpec(NamedTuple):
    """Specification for an instruction."""

    opcode: Opcode
    name: str
    operands: list[OperandType]
    stack_effect: int  # Net change to stack (-n consumed, +n produced)


# Instruction specifications
INSTRUCTIONS: dict[Opcode, InstructionSpec] = {
    # Load/Store
    Opcode.LOAD_CONST: InstructionSpec(Opcode.LOAD_CONST, "LOAD_CONST", [OperandType.U16], 1),
    Opcode.LOAD_LOCAL: InstructionSpec(Opcode.LOAD_LOCAL, "LOAD_LOCAL", [OperandType.U16], 1),
    Opcode.STORE_LOCAL: InstructionSpec(Opcode.STORE_LOCAL, "STORE_LOCAL", [OperandType.U16], -1),
    Opcode.LOAD_GLOBAL: InstructionSpec(Opcode.LOAD_GLOBAL, "LOAD_GLOBAL", [OperandType.U16], 1),
    Opcode.STORE_GLOBAL: InstructionSpec(Opcode.STORE_GLOBAL, "STORE_GLOBAL", [OperandType.U16], -1),
    # Stack
    Opcode.POP: InstructionSpec(Opcode.POP, "POP", [], -1),
    Opcode.DUP: InstructionSpec(Opcode.DUP, "DUP", [], 1),
    Opcode.SWAP: InstructionSpec(Opcode.SWAP, "SWAP", [], 0),
    # Arithmetic
    Opcode.ADD: InstructionSpec(Opcode.ADD, "ADD", [], -1),
    Opcode.SUB: InstructionSpec(Opcode.SUB, "SUB", [], -1),
    Opcode.MUL: InstructionSpec(Opcode.MUL, "MUL", [], -1),
    Opcode.DIV: InstructionSpec(Opcode.DIV, "DIV", [], -1),
    Opcode.MOD: InstructionSpec(Opcode.MOD, "MOD", [], -1),
    # Unary
    Opcode.NEG: InstructionSpec(Opcode.NEG, "NEG", [], 0),
    Opcode.NOT: InstructionSpec(Opcode.NOT, "NOT", [], 0),
    # Comparison
    Opcode.EQ: InstructionSpec(Opcode.EQ, "EQ", [], -1),
    Opcode.NEQ: InstructionSpec(Opcode.NEQ, "NEQ", [], -1),
    Opcode.LT: InstructionSpec(Opcode.LT, "LT", [], -1),
    Opcode.GT: InstructionSpec(Opcode.GT, "GT", [], -1),
    Opcode.LTE: InstructionSpec(Opcode.LTE, "LTE", [], -1),
    Opcode.GTE: InstructionSpec(Opcode.GTE, "GTE", [], -1),
    Opcode.STRICT_EQ: InstructionSpec(Opcode.STRICT_EQ, "STRICT_EQ", [], -1),
    Opcode.STRICT_NEQ: InstructionSpec(Opcode.STRICT_NEQ, "STRICT_NEQ", [], -1),
    # Logical
    Opcode.AND: InstructionSpec(Opcode.AND, "AND", [], -1),
    Opcode.OR: InstructionSpec(Opcode.OR, "OR", [], -1),
    # Control
    Opcode.JUMP: InstructionSpec(Opcode.JUMP, "JUMP", [OperandType.I16], 0),
    Opcode.JUMP_IF_FALSE: InstructionSpec(Opcode.JUMP_IF_FALSE, "JUMP_IF_FALSE", [OperandType.I16], -1),
    Opcode.RETURN: InstructionSpec(Opcode.RETURN, "RETURN", [], 0),
    # Functions
    Opcode.CALL: InstructionSpec(Opcode.CALL, "CALL", [OperandType.U8], 0),
    Opcode.LOAD_FUNCTION: InstructionSpec(Opcode.LOAD_FUNCTION, "LOAD_FUNCTION", [OperandType.U16], 1),
    # Misc
    Opcode.NOP: InstructionSpec(Opcode.NOP, "NOP", [], 0),
    Opcode.HALT: InstructionSpec(Opcode.HALT, "HALT", [], 0),
}


def get_instruction_size(opcode: Opcode) -> int:
    """Get the total size in bytes for an instruction.

    Args:
        opcode: The opcode to get size for.

    Returns:
        Total size including opcode and operands.
    """
    spec = INSTRUCTIONS[opcode]
    size = 1  # Opcode byte

    for operand_type in spec.operands:
        if operand_type == OperandType.U8:
            size += 1
        elif operand_type in (OperandType.U16, OperandType.I16):
            size += 2

    return size
