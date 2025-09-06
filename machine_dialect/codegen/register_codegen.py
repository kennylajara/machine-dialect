"""Register-based bytecode generator for the Rust VM.

This module generates register-based bytecode from MIR for the new Rust VM.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

from machine_dialect.codegen.constpool import ConstantPool
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Nop,
    Phi,
    Print,
    Return,
    Scope,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_values import Constant, MIRValue, Variable

# TODO: Import from new bytecode module when implemented
# from machine_dialect.codegen.objects import BytecodeModule, Chunk, ChunkType

# Placeholder classes until real implementation
BytecodeModule = Any
Chunk = Any
ChunkType = Any


@dataclass
class RegisterAllocation:
    """Register allocation for a function."""

    # Map from MIR values to register numbers
    value_to_register: dict[MIRValue, int] = field(default_factory=dict)
    # Next available register
    next_register: int = 0
    # Maximum registers used
    max_registers: int = 256


class RegisterAllocator:
    """Allocates registers for MIR values."""

    def allocate_function(self, func: MIRFunction) -> RegisterAllocation:
        """Allocate registers for a function.

        Args:
            func: MIR function to allocate registers for.

        Returns:
            Register allocation.
        """
        allocation = RegisterAllocation()

        # Allocate registers for parameters
        for param in func.params:
            self.allocate_register(param, allocation)

        # Allocate registers for all instructions
        for block_name in func.cfg.blocks:
            block = func.cfg.blocks[block_name]
            for inst in block.instructions:
                # Allocate for definitions
                for value in inst.get_defs():
                    if value not in allocation.value_to_register:
                        self.allocate_register(value, allocation)

                # Ensure uses are allocated
                for value in inst.get_uses():
                    if value not in allocation.value_to_register:
                        if not isinstance(value, Constant):
                            self.allocate_register(value, allocation)

        return allocation

    def allocate_register(self, value: MIRValue, allocation: RegisterAllocation) -> int:
        """Allocate a register for a value.

        Args:
            value: Value to allocate register for.
            allocation: Current allocation state.

        Returns:
            Allocated register number.
        """
        if value in allocation.value_to_register:
            return allocation.value_to_register[value]

        if allocation.next_register >= allocation.max_registers:
            raise RuntimeError(f"Out of registers (max {allocation.max_registers})")

        reg = allocation.next_register
        allocation.value_to_register[value] = reg
        allocation.next_register += 1
        return reg


class RegisterBytecodeGenerator:
    """Generate register-based bytecode from MIR."""

    def __init__(self) -> None:
        """Initialize the generator."""
        self.allocator = RegisterAllocator()
        self.constants = ConstantPool()
        self.bytecode: bytearray = bytearray()
        self.allocation: RegisterAllocation | None = None
        # Map from basic block labels to bytecode offsets
        self.block_offsets: dict[str, int] = {}
        # Pending jumps to resolve
        self.pending_jumps: list[tuple[int, str]] = []

    def generate(self, mir_module: MIRModule) -> BytecodeModule:
        """Generate bytecode module from MIR.

        Args:
            mir_module: MIR module to generate bytecode from.

        Returns:
            Bytecode module.
        """
        module = BytecodeModule()

        # Process main function
        if main_func := mir_module.get_function("main"):
            chunk = self.generate_function(main_func)
            module.chunks.append(chunk)

        # Process other functions
        for name, func in mir_module.functions.items():
            if name != "main":
                chunk = self.generate_function(func)
                module.add_chunk(chunk)

        return module

    def generate_function(self, func: MIRFunction) -> Chunk:
        """Generate bytecode chunk for a function.

        Args:
            func: MIR function to generate bytecode for.

        Returns:
            Bytecode chunk.
        """
        # Reset state
        self.bytecode = bytearray()
        self.constants = ConstantPool()
        self.block_offsets = {}
        self.pending_jumps = []

        # Allocate registers
        self.allocation = self.allocator.allocate_function(func)

        # Generate code for each block
        for block_name in func.cfg.blocks:
            block = func.cfg.blocks[block_name]
            # Record block offset
            self.block_offsets[block.label] = len(self.bytecode)
            # Generate instructions
            for inst in block.instructions:
                self.generate_instruction(inst)

        # Resolve pending jumps
        self.resolve_jumps()

        # Create chunk
        chunk = Chunk(
            name=func.name,
            chunk_type=ChunkType.FUNCTION if func.name != "main" else ChunkType.MAIN,
            bytecode=self.bytecode,
            constants=self.constants,
            num_locals=self.allocation.next_register,
            num_params=len(func.params),
        )

        return chunk

    def generate_instruction(self, inst: MIRInstruction) -> None:
        """Generate bytecode for a MIR instruction.

        Args:
            inst: MIR instruction to generate bytecode for.
        """
        if isinstance(inst, LoadConst):
            self.generate_load_const(inst)
        elif isinstance(inst, Copy):
            self.generate_copy(inst)
        elif isinstance(inst, LoadVar):
            self.generate_load_var(inst)
        elif isinstance(inst, StoreVar):
            self.generate_store_var(inst)
        elif isinstance(inst, BinaryOp):
            self.generate_binary_op(inst)
        elif isinstance(inst, UnaryOp):
            self.generate_unary_op(inst)
        elif isinstance(inst, Jump):
            self.generate_jump(inst)
        elif isinstance(inst, ConditionalJump):
            self.generate_conditional_jump(inst)
        elif isinstance(inst, Call):
            self.generate_call(inst)
        elif isinstance(inst, Return):
            self.generate_return(inst)
        elif isinstance(inst, Phi):
            self.generate_phi(inst)
        elif isinstance(inst, Assert):
            self.generate_assert(inst)
        elif isinstance(inst, Scope):
            self.generate_scope(inst)
        elif isinstance(inst, Print):
            self.generate_print(inst)
        elif isinstance(inst, Nop):
            pass  # No operation
        # TODO: Add more instruction types

    def generate_load_const(self, inst: LoadConst) -> None:
        """Generate LoadConstR instruction."""
        dst = self.get_register(inst.dest)
        const_idx = self.add_constant(inst.constant)
        self.emit_opcode(0)  # LoadConstR
        self.emit_u8(dst)
        self.emit_u16(const_idx)

    def generate_copy(self, inst: Copy) -> None:
        """Generate MoveR instruction."""
        dst = self.get_register(inst.dest)
        src = self.get_register(inst.source)

        self.emit_opcode(1)  # MoveR
        self.emit_u8(dst)
        self.emit_u8(src)

    def generate_load_var(self, inst: LoadVar) -> None:
        """Generate LoadGlobalR instruction."""
        dst = self.get_register(inst.dest)
        name_idx = self.add_string_constant(inst.var.name)

        self.emit_opcode(2)  # LoadGlobalR
        self.emit_u8(dst)
        self.emit_u16(name_idx)

    def generate_store_var(self, inst: StoreVar) -> None:
        """Generate StoreGlobalR instruction."""
        src = self.get_register(inst.source)
        name_idx = self.add_string_constant(inst.var.name)

        self.emit_opcode(3)  # StoreGlobalR
        self.emit_u8(src)
        self.emit_u16(name_idx)

    def generate_binary_op(self, inst: BinaryOp) -> None:
        """Generate binary operation instruction."""
        dst = self.get_register(inst.dest)
        left = self.get_register(inst.left)
        right = self.get_register(inst.right)

        # Map operators to opcodes
        op_map = {
            "+": 7,  # AddR
            "-": 8,  # SubR
            "*": 9,  # MulR
            "/": 10,  # DivR
            "%": 11,  # ModR
            "and": 14,  # AndR
            "or": 15,  # OrR
            "==": 16,  # EqR
            "!=": 17,  # NeqR
            "<": 18,  # LtR
            ">": 19,  # GtR
            "<=": 20,  # LteR
            ">=": 21,  # GteR
        }

        if opcode := op_map.get(inst.op):
            self.emit_opcode(opcode)
            self.emit_u8(dst)
            self.emit_u8(left)
            self.emit_u8(right)

    def generate_unary_op(self, inst: UnaryOp) -> None:
        """Generate unary operation instruction."""
        dst = self.get_register(inst.dest)
        src = self.get_register(inst.operand)

        if inst.op == "-":
            self.emit_opcode(12)  # NegR
        elif inst.op == "not":
            self.emit_opcode(13)  # NotR
        else:
            return

        self.emit_u8(dst)
        self.emit_u8(src)

    def generate_jump(self, inst: Jump) -> None:
        """Generate JumpR instruction."""
        self.emit_opcode(22)  # JumpR
        # Record position for later resolution
        self.pending_jumps.append((len(self.bytecode), inst.label))
        self.emit_i32(0)  # Placeholder offset

    def generate_conditional_jump(self, inst: ConditionalJump) -> None:
        """Generate JumpIfR instruction with true and false targets."""
        cond = self.get_register(inst.condition)

        # Generate jump to true target
        self.emit_opcode(23)  # JumpIfR
        self.emit_u8(cond)
        # Record position for later resolution
        self.pending_jumps.append((len(self.bytecode), inst.true_label))
        self.emit_i32(0)  # Placeholder offset

        # If there's a false label, generate unconditional jump to it
        # (this executes if the condition was false)
        if inst.false_label:
            self.emit_opcode(22)  # JumpR
            self.pending_jumps.append((len(self.bytecode), inst.false_label))
            self.emit_i32(0)  # Placeholder offset

    def generate_call(self, inst: Call) -> None:
        """Generate CallR instruction."""
        dst = self.get_register(inst.dest) if inst.dest else 0
        func = self.get_register(inst.func)
        args = [self.get_register(arg) for arg in inst.args]

        self.emit_opcode(25)  # CallR
        self.emit_u8(func)
        self.emit_u8(dst)
        self.emit_u8(len(args))
        for arg in args:
            self.emit_u8(arg)

    def generate_return(self, inst: Return) -> None:
        """Generate ReturnR instruction."""
        self.emit_opcode(26)  # ReturnR
        if inst.value:
            self.emit_u8(1)  # Has return value
            self.emit_u8(self.get_register(inst.value))
        else:
            self.emit_u8(0)  # No return value

    def generate_phi(self, inst: Phi) -> None:
        """Generate PhiR instruction."""
        dst = self.get_register(inst.dest)
        sources = []
        for value, _ in inst.sources:  # type: ignore[attr-defined]
            src = self.get_register(value)
            # TODO: Map label to block ID
            block_id = 0
            sources.append((src, block_id))

        self.emit_opcode(27)  # PhiR
        self.emit_u8(dst)
        self.emit_u8(len(sources))
        for src, block_id in sources:
            self.emit_u8(src)
            self.emit_u16(block_id)

    def generate_assert(self, inst: Assert) -> None:
        """Generate AssertR instruction."""
        reg = self.get_register(inst.condition)
        msg = inst.message or "Assertion failed"
        msg_idx = self.add_string_constant(msg)

        self.emit_opcode(28)  # AssertR
        self.emit_u8(reg)
        self.emit_u8(0)  # AssertType::True
        self.emit_u16(msg_idx)

    def generate_scope(self, inst: Scope) -> None:
        """Generate ScopeEnterR/ScopeExitR instruction."""
        scope_id = inst.scope_id  # type: ignore[attr-defined]
        if inst.action == "enter":  # type: ignore[attr-defined]
            self.emit_opcode(29)  # ScopeEnterR
        else:
            self.emit_opcode(30)  # ScopeExitR

        self.emit_u16(scope_id)

    def generate_print(self, inst: Print) -> None:
        """Generate DebugPrint instruction."""
        src = self.get_register(inst.value)

        self.emit_opcode(37)  # DebugPrint
        self.emit_u8(src)

    def resolve_jumps(self) -> None:
        """Resolve pending jump offsets."""
        for jump_pos, target_label in self.pending_jumps:
            if target_label in self.block_offsets:
                target_offset = self.block_offsets[target_label]
                # Calculate relative offset
                offset = target_offset - (jump_pos + 4)
                # Write offset at jump position
                struct.pack_into("<i", self.bytecode, jump_pos, offset)

    def get_register(self, value: MIRValue) -> int:
        """Get register number for a value.

        Args:
            value: MIR value.

        Returns:
            Register number.
        """
        if isinstance(value, Constant):
            # Load constant into a register
            assert self.allocation is not None
            reg = self.allocation.next_register
            if reg >= self.allocation.max_registers:
                raise RuntimeError("Out of registers")
            self.allocation.next_register += 1

            const_idx = self.add_constant(value.value)
            self.emit_opcode(0)  # LoadConstR
            self.emit_u8(reg)
            self.emit_u16(const_idx)
            return reg

        assert self.allocation is not None
        return self.allocation.value_to_register.get(value, 0)

    def add_constant(self, value: Any) -> int:
        """Add a constant to the pool.

        Args:
            value: Constant value.

        Returns:
            Constant index.
        """
        # For now, just add value directly to constants
        # TODO: Implement proper constant value types
        return len(self.bytecode)  # Placeholder

    def add_string_constant(self, value: str) -> int:
        """Add a string constant to the pool.

        Args:
            value: String value.

        Returns:
            Constant index.
        """
        # For now, just return a placeholder
        return len(self.bytecode)  # Placeholder

    def emit_opcode(self, opcode: int) -> None:
        """Emit an opcode."""
        self.bytecode.append(opcode)

    def emit_u8(self, value: int) -> None:
        """Emit an unsigned 8-bit value."""
        self.bytecode.append(value & 0xFF)

    def emit_u16(self, value: int) -> None:
        """Emit an unsigned 16-bit value."""
        self.bytecode.extend(struct.pack("<H", value))

    def emit_i32(self, value: int) -> None:
        """Emit a signed 32-bit value."""
        self.bytecode.extend(struct.pack("<i", value))


class MetadataCollector:
    """Collect metadata from MIR for the Rust VM.

    This collects minimal metadata needed for:
    - Type information for registers
    - Symbol table for debugging
    - SSA phi node information
    - Basic block boundaries
    """

    def __init__(self, debug_mode: bool = False) -> None:
        """Initialize the metadata collector.

        Args:
            debug_mode: Whether to collect full debug metadata.
        """
        self.debug_mode = debug_mode

    def collect(self, mir_module: MIRModule, allocation: RegisterAllocation) -> dict[str, Any]:
        """Collect metadata from MIR module.

        Args:
            mir_module: MIR module to extract metadata from.
            allocation: Register allocation for the module.

        Returns:
            Metadata object.
        """
        metadata: dict[str, Any] = {
            "version": 1,
            "metadata_level": "full" if self.debug_mode else "minimal",
            "functions": [],
        }

        # Process each function
        for _name, func in mir_module.functions.items():
            func_metadata = self.collect_function_metadata(func, allocation)
            metadata["functions"].append(func_metadata)

        return metadata

    def collect_function_metadata(self, func: MIRFunction, allocation: RegisterAllocation) -> dict[str, Any]:
        """Collect metadata for a function.

        Args:
            func: MIR function to extract metadata from.
            allocation: Register allocation for the function.

        Returns:
            Function metadata dictionary.
        """
        func_metadata = {
            "name": func.name,
            "signature": {
                "param_types": [str(p.type) for p in func.params],
                "return_type": str(func.return_type) if func.return_type else "empty",
            },
            "register_types": self.extract_register_types(func, allocation),
            "basic_blocks": self.extract_basic_blocks(func),
            "phi_nodes": self.extract_phi_nodes(func, allocation),
        }

        if self.debug_mode:
            # Add debug information
            func_metadata["variable_names"] = self.extract_variable_names(func, allocation)
            func_metadata["source_map"] = []  # TODO: Implement source mapping

        return func_metadata

    def extract_register_types(self, func: MIRFunction, allocation: RegisterAllocation) -> dict[str, str]:
        """Extract type information for registers.

        Args:
            func: MIR function.
            allocation: Register allocation.

        Returns:
            Mapping of register numbers to type names.
        """
        register_types = {}

        for value, reg_num in allocation.value_to_register.items():
            if hasattr(value, "type"):
                register_types[f"r{reg_num}"] = str(value.type)
            else:
                register_types[f"r{reg_num}"] = "unknown"

        return register_types

    def extract_basic_blocks(self, func: MIRFunction) -> list[dict[str, Any]]:
        """Extract basic block information.

        Args:
            func: MIR function.

        Returns:
            List of basic block metadata.
        """
        blocks = []
        offset = 0

        for block_name in func.cfg.blocks:
            block = func.cfg.blocks[block_name]
            block_info = {
                "label": block.label,
                "start_offset": offset,
                "end_offset": offset + len(block.instructions),
            }
            blocks.append(block_info)
            offset += len(block.instructions)
        return blocks

    def extract_phi_nodes(self, func: MIRFunction, allocation: RegisterAllocation) -> list[dict[str, Any]]:
        """Extract phi node information.

        Args:
            func: MIR function.
            allocation: Register allocation.

        Returns:
            List of phi node metadata.
        """
        phi_nodes = []

        for block_name in func.cfg.blocks:
            block = func.cfg.blocks[block_name]
            for inst in block.instructions:
                if isinstance(inst, Phi):
                    dest_reg = allocation.value_to_register.get(inst.dest, -1)
                    sources = []
                    for value, label in inst.sources:  # type: ignore[attr-defined]
                        src_reg = allocation.value_to_register.get(value, -1)
                        sources.append(
                            {
                                "register": f"r{src_reg}",
                                "block": label,
                            }
                        )

                    phi_nodes.append(
                        {
                            "block": block.label,
                            "register": f"r{dest_reg}",
                            "sources": sources,
                        }
                    )

        return phi_nodes

    def extract_variable_names(self, func: MIRFunction, allocation: RegisterAllocation) -> dict[str, str]:
        """Extract variable names for debugging.

        Args:
            func: MIR function.
            allocation: Register allocation.

        Returns:
            Mapping of register numbers to variable names.
        """
        var_names = {}

        for value, reg_num in allocation.value_to_register.items():
            if isinstance(value, Variable):
                var_names[f"r{reg_num}"] = value.name

        return var_names


def generate_bytecode_from_mir(mir_module: MIRModule) -> tuple[BytecodeModule, dict[str, Any] | None]:
    """Generate bytecode and metadata from MIR module.

    This is the main entry point for bytecode generation.

    Args:
        mir_module: MIR module to generate bytecode from.

    Returns:
        Tuple of (bytecode module, metadata).
    """
    generator = RegisterBytecodeGenerator()
    bytecode = generator.generate(mir_module)

    # Collect metadata
    if generator.allocation is not None:
        collector = MetadataCollector(debug_mode=False)
        metadata = collector.collect(mir_module, generator.allocation)
    else:
        metadata = None

    return bytecode, metadata
