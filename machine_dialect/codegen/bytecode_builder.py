"""Bytecode builder for Machine Dialect VM."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BytecodeModule:
    """Represents a bytecode module ready for serialization."""

    name: str = "main"
    version: int = 1
    flags: int = 0
    constants: list[tuple[int, Any]] = field(default_factory=list)
    instructions: list[bytes] = field(default_factory=list)
    function_table: dict[str, int] = field(default_factory=dict)
    global_names: list[str] = field(default_factory=list)

    def add_constant_int(self, value: int) -> int:
        """Add an integer constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x01, value))
        return idx

    def add_constant_float(self, value: float) -> int:
        """Add a float constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x02, value))
        return idx

    def add_constant_string(self, value: str) -> int:
        """Add a string constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x03, value))
        return idx

    def add_constant_bool(self, value: bool) -> int:
        """Add a boolean constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x04, value))
        return idx

    def add_constant_empty(self) -> int:
        """Add an empty/null constant and return its index."""
        idx = len(self.constants)
        self.constants.append((0x05, None))
        return idx


class BytecodeBuilder:
    """Builds bytecode from MIR modules."""

    def __init__(self):
        self.module = BytecodeModule()
        self.constant_map: dict[Any, int] = {}
        self.block_offsets: dict[str, int] = {}
        self.pending_jumps: list[tuple[int, str]] = []

    def build(self, mir_module) -> BytecodeModule:
        """Build bytecode from a MIR module."""
        self.module.name = mir_module.name

        # Process each function
        for func_name, func in mir_module.functions.items():
            if func_name == "main":
                # Main function starts at offset 0
                self._build_function(func, 0)
            else:
                # Other functions get added to function table
                offset = len(self.module.instructions)
                self.module.function_table[func_name] = offset
                self._build_function(func, offset)

        # Resolve pending jumps
        self._resolve_jumps()

        return self.module

    def _build_function(self, func, start_offset: int):
        """Build bytecode for a single function."""
        # Calculate block offsets
        current_offset = start_offset
        for block_name, block in func.blocks.items():
            self.block_offsets[f"{func.name}:{block_name}"] = current_offset
            # Estimate instruction size (simplified)
            current_offset += len(block.instructions) * 4

        # Generate instructions for each block
        for block_name, block in func.blocks.items():
            self._build_block(func.name, block)

    def _build_block(self, func_name: str, block):
        """Build bytecode for a single basic block."""
        for inst in block.instructions:
            self._build_instruction(func_name, inst)

    def _build_instruction(self, func_name: str, inst):
        """Build bytecode for a single instruction."""
        from machine_dialect.mir.instructions import (
            BinaryOperation,
            Call,
            Comparison,
            ConditionalJump,
            Jump,
            LoadConstant,
            Move,
            Phi,
            Return,
        )
        from machine_dialect.mir.mir import BinaryOp, ComparisonOp

        if isinstance(inst, LoadConstant):
            const_idx = self._get_or_add_constant(inst.value)
            # LoadConstR dst, const_idx
            self.module.instructions.append(bytes([0, inst.dest.index]) + struct.pack("<H", const_idx))

        elif isinstance(inst, Move):
            # MoveR dst, src
            self.module.instructions.append(bytes([1, inst.dest.index, inst.source.index]))

        elif isinstance(inst, BinaryOperation):
            opcode_map = {
                BinaryOp.ADD: 7,
                BinaryOp.SUB: 8,
                BinaryOp.MUL: 9,
                BinaryOp.DIV: 10,
                BinaryOp.MOD: 11,
            }
            opcode = opcode_map.get(inst.op, 7)
            # BinaryOp dst, left, right
            self.module.instructions.append(bytes([opcode, inst.dest.index, inst.left.index, inst.right.index]))

        elif isinstance(inst, Comparison):
            opcode_map = {
                ComparisonOp.EQ: 16,
                ComparisonOp.NE: 17,
                ComparisonOp.LT: 18,
                ComparisonOp.GT: 19,
                ComparisonOp.LTE: 20,
                ComparisonOp.GTE: 21,
            }
            opcode = opcode_map.get(inst.op, 16)
            # Comparison dst, left, right
            self.module.instructions.append(bytes([opcode, inst.dest.index, inst.left.index, inst.right.index]))

        elif isinstance(inst, Jump):
            # JumpR offset (will be patched later)
            inst_idx = len(self.module.instructions)
            self.pending_jumps.append((inst_idx, f"{func_name}:{inst.target}"))
            self.module.instructions.append(
                bytes([22]) + struct.pack("<i", 0)  # Placeholder offset
            )

        elif isinstance(inst, ConditionalJump):
            # JumpIfR cond, offset (for true branch)
            inst_idx = len(self.module.instructions)
            self.pending_jumps.append((inst_idx, f"{func_name}:{inst.true_target}"))
            self.module.instructions.append(bytes([23, inst.condition.index]) + struct.pack("<i", 0))

            # JumpR offset (for false branch)
            inst_idx = len(self.module.instructions)
            self.pending_jumps.append((inst_idx, f"{func_name}:{inst.false_target}"))
            self.module.instructions.append(bytes([22]) + struct.pack("<i", 0))

        elif isinstance(inst, Return):
            if inst.value:
                # ReturnR with value
                self.module.instructions.append(bytes([26, 1, inst.value.index]))
            else:
                # ReturnR without value
                self.module.instructions.append(bytes([26, 0]))

        elif isinstance(inst, Call):
            # For simplicity, using function index 0
            # In real implementation, would look up function
            func_idx = 0
            args = [arg.index for arg in inst.args]
            # CallR func, args, dst
            self.module.instructions.append(bytes([25, func_idx, inst.dest.index, len(args)] + args))

        elif isinstance(inst, Phi):
            # PhiR dst, sources
            sources = []
            for src, block in inst.sources:
                # Simplified: use block index as label
                sources.extend([src.index, 0, 0])  # src, label_low, label_high
            self.module.instructions.append(bytes([27, inst.dest.index, len(inst.sources)] + sources))

    def _get_or_add_constant(self, value) -> int:
        """Get or add a constant to the pool."""
        from machine_dialect.mir.mir import Constant

        if isinstance(value, Constant):
            key = (value.type, value.value)
            if key in self.constant_map:
                return self.constant_map[key]

            if value.type == "int":
                idx = self.module.add_constant_int(value.value)
            elif value.type == "float":
                idx = self.module.add_constant_float(value.value)
            elif value.type == "string":
                idx = self.module.add_constant_string(value.value)
            elif value.type == "bool":
                idx = self.module.add_constant_bool(value.value)
            else:
                idx = self.module.add_constant_empty()

            self.constant_map[key] = idx
            return idx

        # Direct value
        if isinstance(value, int):
            return self.module.add_constant_int(value)
        elif isinstance(value, float):
            return self.module.add_constant_float(value)
        elif isinstance(value, str):
            return self.module.add_constant_string(value)
        elif isinstance(value, bool):
            return self.module.add_constant_bool(value)
        else:
            return self.module.add_constant_empty()

    def _resolve_jumps(self):
        """Resolve jump targets to actual offsets."""
        # For now, leave jumps as-is (would need proper offset calculation)
        pass
