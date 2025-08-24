"""Bytecode emitter for Machine Dialect.

This module provides the Emitter class that assembles bytecode
instructions with proper encoding and jump patching.
"""

from typing import Any

from machine_dialect.codegen.isa import INSTRUCTIONS, Opcode, OperandType
from machine_dialect.codegen.objects import Chunk


class Emitter:
    """Bytecode emitter that assembles instructions into a chunk."""

    def __init__(self, chunk: Chunk) -> None:
        """Initialize the emitter with a target chunk.

        Args:
            chunk: The chunk to emit bytecode into.
        """
        self.chunk = chunk

    def emit(self, opcode: Opcode) -> int:
        """Emit an instruction with no operands.

        Args:
            opcode: The opcode to emit.

        Returns:
            Position where instruction was emitted.

        Raises:
            ValueError: If opcode expects operands.
        """
        spec = INSTRUCTIONS[opcode]
        if spec.operands:
            raise ValueError(f"Opcode {spec.name} expects operands")

        return self.chunk.write_byte(opcode)

    def emit_byte(self, opcode: Opcode, operand: int) -> int:
        """Emit an instruction with a single byte operand.

        Args:
            opcode: The opcode to emit.
            operand: The byte operand (0-255).

        Returns:
            Position where instruction was emitted.

        Raises:
            ValueError: If opcode doesn't expect a U8 operand.
        """
        spec = INSTRUCTIONS[opcode]
        if len(spec.operands) != 1 or spec.operands[0] != OperandType.U8:
            raise ValueError(f"Opcode {spec.name} doesn't expect a U8 operand")

        pos = self.chunk.write_byte(opcode)
        self.chunk.write_byte(operand)
        return pos

    def emit_u16(self, opcode: Opcode, operand: int) -> int:
        """Emit an instruction with a 16-bit unsigned operand.

        Args:
            opcode: The opcode to emit.
            operand: The u16 operand (0-65535).

        Returns:
            Position where instruction was emitted.

        Raises:
            ValueError: If opcode doesn't expect a U16 operand.
        """
        spec = INSTRUCTIONS[opcode]
        if len(spec.operands) != 1 or spec.operands[0] != OperandType.U16:
            raise ValueError(f"Opcode {spec.name} doesn't expect a U16 operand")

        pos = self.chunk.write_byte(opcode)
        self.chunk.write_u16(operand)
        return pos

    def emit_i16(self, opcode: Opcode, operand: int) -> int:
        """Emit an instruction with a 16-bit signed operand.

        Args:
            opcode: The opcode to emit.
            operand: The i16 operand (-32768 to 32767).

        Returns:
            Position where instruction was emitted.

        Raises:
            ValueError: If opcode doesn't expect an I16 operand.
        """
        spec = INSTRUCTIONS[opcode]
        if len(spec.operands) != 1 or spec.operands[0] != OperandType.I16:
            raise ValueError(f"Opcode {spec.name} doesn't expect an I16 operand")

        pos = self.chunk.write_byte(opcode)
        self.chunk.write_i16(operand)
        return pos

    def emit_jump(self, opcode: Opcode) -> int:
        """Emit a jump instruction with placeholder offset.

        The offset should be patched later with patch_jump().

        Args:
            opcode: The jump opcode (JUMP or JUMP_IF_FALSE).

        Returns:
            Position of the offset bytes to be patched.

        Raises:
            ValueError: If opcode is not a jump instruction.
        """
        if opcode not in (Opcode.JUMP, Opcode.JUMP_IF_FALSE):
            raise ValueError(f"Opcode {opcode} is not a jump instruction")

        self.chunk.write_byte(opcode)
        offset_pos = self.chunk.current_position()
        self.chunk.write_i16(0)  # Placeholder
        return offset_pos

    def patch_jump(self, jump_pos: int) -> None:
        """Patch a jump instruction to jump to current position.

        Args:
            jump_pos: Position returned by emit_jump().
        """
        target = self.chunk.current_position()
        self.chunk.patch_jump(jump_pos, target)

    def emit_constant(self, value: Any) -> int:
        """Emit a LOAD_CONST instruction for a value.

        Args:
            value: The constant value to load.

        Returns:
            Position where instruction was emitted.
        """
        index = self.chunk.add_constant(value)
        return self.emit_u16(Opcode.LOAD_CONST, index)

    def emit_load_local(self, slot: int) -> int:
        """Emit a LOAD_LOCAL instruction.

        Args:
            slot: Local variable slot.

        Returns:
            Position where instruction was emitted.
        """
        return self.emit_u16(Opcode.LOAD_LOCAL, slot)

    def emit_store_local(self, slot: int) -> int:
        """Emit a STORE_LOCAL instruction.

        Args:
            slot: Local variable slot.

        Returns:
            Position where instruction was emitted.
        """
        return self.emit_u16(Opcode.STORE_LOCAL, slot)

    def emit_load_global(self, name: str) -> int:
        """Emit a LOAD_GLOBAL instruction.

        Args:
            name: Global variable name.

        Returns:
            Position where instruction was emitted.
        """
        index = self.chunk.add_constant(name)
        return self.emit_u16(Opcode.LOAD_GLOBAL, index)

    def emit_store_global(self, name: str) -> int:
        """Emit a STORE_GLOBAL instruction.

        Args:
            name: Global variable name.

        Returns:
            Position where instruction was emitted.
        """
        index = self.chunk.add_constant(name)
        return self.emit_u16(Opcode.STORE_GLOBAL, index)

    def emit_load_function(self, name: str) -> int:
        """Emit a LOAD_FUNCTION instruction.

        Args:
            name: Function name.

        Returns:
            Position where instruction was emitted.
        """
        index = self.chunk.add_constant(name)
        return self.emit_u16(Opcode.LOAD_FUNCTION, index)

    def emit_binary_op(self, opcode: Opcode) -> int:
        """Emit a binary operation.

        Args:
            opcode: Binary operation opcode (ADD, SUB, etc.).

        Returns:
            Position where instruction was emitted.
        """
        return self.emit(opcode)

    def emit_comparison(self, opcode: Opcode) -> int:
        """Emit a comparison operation.

        Args:
            opcode: Comparison opcode (LT, GT, EQ, etc.).

        Returns:
            Position where instruction was emitted.
        """
        return self.emit(opcode)

    def emit_return(self) -> int:
        """Emit a RETURN instruction.

        Returns:
            Position where instruction was emitted.
        """
        return self.emit(Opcode.RETURN)

    def emit_pop(self) -> int:
        """Emit a POP instruction.

        Returns:
            Position where instruction was emitted.
        """
        return self.emit(Opcode.POP)

    def emit_call(self, nargs: int) -> int:
        """Emit a CALL instruction.

        Args:
            nargs: Number of arguments for the function call.

        Returns:
            Position where instruction was emitted.
        """
        return self.emit_byte(Opcode.CALL, nargs)

    def current_position(self) -> int:
        """Get the current bytecode position.

        Returns:
            Current position in the chunk's bytecode.
        """
        return self.chunk.current_position()
