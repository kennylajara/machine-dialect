"""Register-based bytecode generator for the Rust VM.

This module generates register-based bytecode from MIR for the new Rust VM.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

from machine_dialect.codegen.bytecode_module import BytecodeModule, Chunk, ChunkType, ConstantTag
from machine_dialect.codegen.opcodes import Opcode

# Note: ConstantPool is now just a list of (tag, value) tuples
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    ArrayAppend,
    ArrayClear,
    ArrayCreate,
    ArrayFindIndex,
    ArrayGet,
    ArrayInsert,
    ArrayLength,
    ArrayRemove,
    ArraySet,
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    DictClear,
    DictContains,
    DictCreate,
    DictGet,
    DictKeys,
    DictRemove,
    DictSet,
    DictValues,
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

    def _is_global_variable(self, var: MIRValue, func: MIRFunction) -> bool:
        """Check if a variable is a global variable.

        Global variables are Variables with version 0 that are NOT function parameters
        or function-local variables. Function parameters and locals are allocated to registers.

        Args:
            var: The MIR value to check.
            func: The current function.

        Returns:
            True if the variable is a global variable.
        """
        from machine_dialect.mir.mir_values import ScopedVariable, VariableScope

        # Check if it's a ScopedVariable with explicit scope
        if isinstance(var, ScopedVariable):
            return var.scope == VariableScope.GLOBAL

        if not isinstance(var, Variable) or var.version != 0:
            return False

        # Check if it's a function parameter by name (not object identity)
        for param in func.params:
            if param.name == var.name:
                return False

        # Check if it's a function-local variable by name
        if var.name in func.locals:
            return False

        return True

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
                        # Skip global variables (Variables with version=0 that are not parameters)
                        if self._is_global_variable(value, func):
                            continue  # Skip global variables
                        self.allocate_register(value, allocation)

                # Ensure uses are allocated
                for value in inst.get_uses():
                    if value not in allocation.value_to_register:
                        if not isinstance(value, Constant):
                            # Skip global variables (Variables with version=0 that are not parameters)
                            if self._is_global_variable(value, func):
                                continue  # Skip global variables
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

    def __init__(self, debug: bool = False) -> None:
        """Initialize the generator.

        Args:
            debug: Enable debug output for bytecode generation.
        """
        self.allocator = RegisterAllocator()
        self.constants: list[tuple[ConstantTag, Any]] = []
        self.bytecode: bytearray = bytearray()
        self.allocation: RegisterAllocation | None = None
        # Map from basic block labels to instruction indices (not byte offsets)
        self.block_offsets: dict[str, int] = {}
        # Map from instruction index to byte offset
        self.instruction_offsets: list[int] = []
        # Pending jumps to resolve: (byte_pos, target_label, source_inst_idx)
        self.pending_jumps: list[tuple[int, str, int]] = []
        self.debug = debug
        self.current_function: MIRFunction | None = None
        # Label counter for generating unique labels
        self.label_counter = 0

    @staticmethod
    def is_ssa_variable(var: MIRValue) -> bool:
        """Check if a variable is an SSA-renamed variable.

        SSA variables have version > 0, indicating they've been
        renamed during SSA construction. Non-SSA variables (globals,
        original parameters) have version 0.

        Args:
            var: The MIR value to check.

        Returns:
            True if the variable is an SSA-renamed variable.
        """
        return isinstance(var, Variable) and var.version > 0

    def is_global_variable(self, var: MIRValue) -> bool:
        """Check if a variable is a global variable.

        Global variables are Variables with version 0 that are NOT function parameters
        or function-local variables. Function parameters and locals are allocated to registers.

        Args:
            var: The MIR value to check.

        Returns:
            True if the variable is a global variable.
        """
        from machine_dialect.mir.mir_values import ScopedVariable, VariableScope

        # Check if it's a ScopedVariable with explicit scope
        if isinstance(var, ScopedVariable):
            return var.scope == VariableScope.GLOBAL

        if not isinstance(var, Variable) or var.version != 0:
            return False

        # Check if it's a function parameter by name (not object identity)
        if self.current_function:
            for param in self.current_function.params:
                if param.name == var.name:
                    return False

            # Check if it's a function-local variable by name
            if var.name in self.current_function.locals:
                return False

        return True

    def generate(self, mir_module: MIRModule) -> BytecodeModule:
        """Generate bytecode module from MIR.

        Args:
            mir_module: MIR module to generate bytecode from.

        Returns:
            Bytecode module.
        """
        module = BytecodeModule()

        # Process main function
        if main_func := mir_module.get_function("__main__"):
            chunk = self.generate_function(main_func)
            module.chunks.append(chunk)

        # Process other functions
        for name, func in mir_module.functions.items():
            if name != "__main__":
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
        self.constants = []
        self.block_offsets = {}  # Will store instruction indices
        self.instruction_offsets = []  # Track byte offset of each instruction
        self.pending_jumps = []
        self.current_function = func

        # Allocate registers
        self.allocation = self.allocator.allocate_function(func)

        # Debug output for register allocation
        if self.debug:
            print(f"\nDEBUG Function {func.name}:")
            print(f"  Parameters: {[p.name for p in func.params]}")
            for param in func.params:
                if param in self.allocation.value_to_register:
                    print(f"    {param.name} -> r{self.allocation.value_to_register[param]}")
                else:
                    print(f"    {param.name} -> NOT ALLOCATED!")

        # Generate code for each block in topological order
        blocks_in_order = func.cfg.topological_sort()
        for block in blocks_in_order:
            # Record block offset in instruction count
            self.block_offsets[block.label] = len(self.instruction_offsets)
            # Generate instructions
            for inst in block.instructions:
                # Note: Each generate_* method is responsible for tracking
                # the VM instructions it generates using track_vm_instruction()
                self.generate_instruction(inst)

        # Resolve pending jumps
        self.resolve_jumps()

        # Create chunk
        chunk = Chunk(
            name=func.name,
            chunk_type=ChunkType.FUNCTION if func.name != "__main__" else ChunkType.MAIN,
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
        elif isinstance(inst, ArrayCreate):
            self.generate_array_create(inst)
        elif isinstance(inst, ArrayGet):
            self.generate_array_get(inst)
        elif isinstance(inst, ArraySet):
            self.generate_array_set(inst)
        elif isinstance(inst, ArrayLength):
            self.generate_array_length(inst)
        elif isinstance(inst, ArrayAppend):
            self.generate_array_append(inst)
        elif isinstance(inst, ArrayRemove):
            self.generate_array_remove(inst)
        elif isinstance(inst, ArrayInsert):
            self.generate_array_insert(inst)
        elif isinstance(inst, ArrayClear):
            self.generate_array_clear(inst)
        elif isinstance(inst, ArrayFindIndex):
            self.generate_array_find_index(inst)
        elif isinstance(inst, DictCreate):
            self.generate_dict_create(inst)
        elif isinstance(inst, DictGet):
            self.generate_dict_get(inst)
        elif isinstance(inst, DictSet):
            self.generate_dict_set(inst)
        elif isinstance(inst, DictRemove):
            self.generate_dict_remove(inst)
        elif isinstance(inst, DictContains):
            self.generate_dict_contains(inst)
        elif isinstance(inst, DictKeys):
            self.generate_dict_keys(inst)
        elif isinstance(inst, DictValues):
            self.generate_dict_values(inst)
        elif isinstance(inst, DictClear):
            self.generate_dict_clear(inst)
        elif isinstance(inst, Scope):
            self.generate_scope(inst)
        elif isinstance(inst, Print):
            self.generate_print(inst)
        elif isinstance(inst, Nop):
            pass  # No operation

    def generate_load_const(self, inst: LoadConst) -> None:
        """Generate LoadConstR instruction."""
        dst = self.get_register(inst.dest)
        # Extract the actual value from the Constant object
        if hasattr(inst.constant, "value"):
            const_value = inst.constant.value
        else:
            const_value = inst.constant
        const_idx = self.add_constant(const_value)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(dst)
        self.emit_u16(const_idx)

    def generate_copy(self, inst: Copy) -> None:
        """Generate MoveR or LoadGlobalR instruction based on source type.

        This method handles both SSA-renamed variables (version > 0) and
        regular variables (version = 0). SSA variables should always be
        allocated to registers during the allocation phase, while regular
        variables may be globals that need to be loaded by name.
        """
        dst = self.get_register(inst.dest)

        # Debug output
        if self.debug:
            print(f"DEBUG Copy: source={inst.source}, dest={inst.dest}")
            if isinstance(inst.source, Variable):
                print(f"  source is Variable, name={inst.source.name}, version={inst.source.version}")
                if self.allocation:
                    print(f"  in allocation? {inst.source in self.allocation.value_to_register}")

        # Handle ScopedVariable parameters
        from machine_dialect.mir.mir_values import ScopedVariable, VariableScope

        if isinstance(inst.source, ScopedVariable) and inst.source.scope == VariableScope.PARAMETER:
            # This is a parameter reference - it might be the same object or a different one
            # First check if the ScopedVariable itself is allocated
            if self.allocation and inst.source in self.allocation.value_to_register:
                src = self.allocation.value_to_register[inst.source]
                self.track_vm_instruction()
                self.emit_opcode(Opcode.MOVE_R)
                self.emit_u8(dst)
                self.emit_u8(src)
                if self.debug:
                    print(f"  -> Generated MoveR from r{src} (param {inst.source.name} direct) to r{dst}")
                return
            # Otherwise look for the parameter by name in the function
            elif self.current_function:
                for param in self.current_function.params:
                    if param.name == inst.source.name:
                        if self.allocation and param in self.allocation.value_to_register:
                            src = self.allocation.value_to_register[param]
                            self.track_vm_instruction()
                            self.emit_opcode(Opcode.MOVE_R)
                            self.emit_u8(dst)
                            self.emit_u8(src)
                            if self.debug:
                                print(f"  -> Generated MoveR from r{src} (param {inst.source.name} by name) to r{dst}")
                            return

        # Check if source is already in a register (local variable, parameter, or SSA variable)
        if self.allocation and inst.source in self.allocation.value_to_register:
            # This is a local variable, parameter, or SSA variable in a register
            src = self.allocation.value_to_register[inst.source]
            self.track_vm_instruction()
            self.emit_opcode(Opcode.MOVE_R)
            self.emit_u8(dst)
            self.emit_u8(src)
            if self.debug:
                print(f"  -> Generated MoveR from r{src} to r{dst}")
        elif isinstance(inst.source, Variable):
            # Special handling for parameters - check by name
            if self.current_function:
                for param in self.current_function.params:
                    if param.name == inst.source.name and inst.source.version == 0:
                        # This is a parameter - find its register
                        if self.allocation and param in self.allocation.value_to_register:
                            src = self.allocation.value_to_register[param]
                            self.track_vm_instruction()
                            self.emit_opcode(Opcode.MOVE_R)
                            self.emit_u8(dst)
                            self.emit_u8(src)
                            if self.debug:
                                print(f"  -> Generated MoveR from r{src} (param {param.name}) to r{dst}")
                            return
                        else:
                            raise RuntimeError(f"Parameter {param.name} not allocated to register")
            # Check if this is an SSA variable that should have been allocated
            if self.is_ssa_variable(inst.source):
                raise RuntimeError(
                    f"SSA variable {inst.source} (version {inst.source.version}) not allocated to register"
                )

            # This is a true global variable that needs to be loaded by name
            name_idx = self.add_string_constant(inst.source.name)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_GLOBAL_R)
            self.emit_u8(dst)
            self.emit_u16(name_idx)
            if self.debug:
                print(f"  -> Generated LoadGlobalR for {inst.source.name}")
        else:
            # Handle other types (constants, etc.)
            src = self.get_register(inst.source)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.MOVE_R)
            self.emit_u8(dst)
            self.emit_u8(src)
            if self.debug:
                print(f"  -> Generated MoveR from r{src} to r{dst}")

    def generate_load_var(self, inst: LoadVar) -> None:
        """Generate LoadGlobalR instruction for variables or MoveR for parameters.

        SSA variables (version > 0) and function parameters are expected to be
        in registers. Global variables (version = 0) need to be loaded by name
        from the global scope.
        """
        dst = self.get_register(inst.dest)

        # Debug output
        if self.debug:
            print(f"DEBUG LoadVar: var={inst.var}, var.name={inst.var.name}, version={inst.var.version}")
            if self.allocation:
                print(f"  in allocation? {inst.var in self.allocation.value_to_register}")
                if inst.var in self.allocation.value_to_register:
                    print(f"  allocated to register {self.allocation.value_to_register[inst.var]}")
            if self.current_function:
                print(f"  function params: {[p.name for p in self.current_function.params]}")
                print(f"  is param? {inst.var in self.current_function.params}")

        # Check if the variable is already in a register (function parameter, local var, or SSA var)
        if self.allocation and inst.var in self.allocation.value_to_register:
            # This is a function parameter, local variable, or SSA variable in a register
            src = self.allocation.value_to_register[inst.var]
            self.track_vm_instruction()
            self.emit_opcode(Opcode.MOVE_R)
            self.emit_u8(dst)
            self.emit_u8(src)
        else:
            # Check if this is an SSA variable that should have been allocated
            if self.is_ssa_variable(inst.var):
                raise RuntimeError(f"SSA variable {inst.var} (version {inst.var.version}) not allocated to register")

            # Check if this variable is a function parameter by name
            # Parameters have version 0 but should be in registers
            is_param = False
            if self.current_function and self.allocation:
                if self.debug:
                    print(f"  Checking if {inst.var.name} is a parameter...")
                    print(f"  Allocation keys: {list(self.allocation.value_to_register.keys())}")
                for param in self.current_function.params:
                    if self.debug:
                        print(f"    Comparing {param.name} == {inst.var.name}: {param.name == inst.var.name}")
                    if param.name == inst.var.name:
                        is_param = True
                        # Try to find the parameter's register
                        if param in self.allocation.value_to_register:
                            src = self.allocation.value_to_register[param]
                            if self.debug:
                                print(f"  Found parameter {inst.var.name} in register {src}!")
                            self.track_vm_instruction()
                            self.emit_opcode(Opcode.MOVE_R)
                            self.emit_u8(dst)
                            self.emit_u8(src)
                            return
                        else:
                            if self.debug:
                                print(f"  Parameter {inst.var.name} not in allocation!")
                            raise RuntimeError(f"Function parameter {inst.var.name} not allocated to register")

            if is_param:
                raise RuntimeError(f"Function parameter {inst.var.name} handling failed")

            # This is a true global variable that needs to be loaded by name
            name_idx = self.add_string_constant(inst.var.name)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_GLOBAL_R)
            self.emit_u8(dst)
            self.emit_u16(name_idx)

    def generate_store_var(self, inst: StoreVar) -> None:
        """Generate StoreGlobalR instruction or register move for SSA variables.

        SSA variables (version > 0) are stored in registers using MoveR.
        Global variables (version = 0) are stored to the global scope using
        StoreGlobalR with the variable name.
        """
        if self.debug:
            print(f"DEBUG StoreVar: var={inst.var}, source={inst.source}")
        src = self.get_register(inst.source)

        # Check if the destination variable is allocated to a register (SSA or local)
        if self.allocation and inst.var in self.allocation.value_to_register:
            # This is an SSA or local variable - use register move
            dst = self.allocation.value_to_register[inst.var]
            self.track_vm_instruction()
            self.emit_opcode(Opcode.MOVE_R)
            self.emit_u8(dst)
            self.emit_u8(src)
            if self.debug:
                print(f"  -> Generated MoveR from r{src} to r{dst} for {inst.var}")
        else:
            # Check if this is an SSA variable that should have been allocated
            if self.is_ssa_variable(inst.var):
                raise RuntimeError(f"SSA variable {inst.var} (version {inst.var.version}) not allocated to register")

            # This is a true global variable
            name_idx = self.add_string_constant(inst.var.name if hasattr(inst.var, "name") else str(inst.var))
            self.track_vm_instruction()
            self.emit_opcode(Opcode.STORE_GLOBAL_R)
            self.emit_u8(src)
            self.emit_u16(name_idx)
            if self.debug:
                print(f"  -> Generated StoreGlobalR for {inst.var}")

    def generate_binary_op(self, inst: BinaryOp) -> None:
        """Generate binary operation instruction."""
        # Load constants first if needed
        if isinstance(inst.left, Constant):
            left = self.get_register(inst.left)
            const_val = inst.left.value if hasattr(inst.left, "value") else inst.left
            const_idx = self.add_constant(const_val)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(left)
            self.emit_u16(const_idx)
        else:
            left = self.get_register(inst.left)

        if isinstance(inst.right, Constant):
            right = self.get_register(inst.right)
            const_val = inst.right.value if hasattr(inst.right, "value") else inst.right
            const_idx = self.add_constant(const_val)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(right)
            self.emit_u16(const_idx)
        else:
            right = self.get_register(inst.right)

        # Get destination register
        dst = self.get_register(inst.dest)

        if self.debug:
            print(
                f"DEBUG BinaryOp: op={inst.op}, left={inst.left} "
                f"(type={type(inst.left).__name__}), "
                f"right={inst.right} (type={type(inst.right).__name__})"
            )
            print(f"  left register: r{left}, right register: r{right}, dest register: r{dst}")

        # Map operators to opcodes
        op_map = {
            "+": Opcode.ADD_R,
            "-": Opcode.SUB_R,
            "*": Opcode.MUL_R,
            "/": Opcode.DIV_R,
            "%": Opcode.MOD_R,
            "and": Opcode.AND_R,
            "or": Opcode.OR_R,
            "==": Opcode.EQ_R,
            "!=": Opcode.NEQ_R,
            "<": Opcode.LT_R,
            ">": Opcode.GT_R,
            "<=": Opcode.LTE_R,
            ">=": Opcode.GTE_R,
        }

        if opcode := op_map.get(inst.op):
            self.track_vm_instruction()
            self.emit_opcode(opcode)
            self.emit_u8(dst)
            self.emit_u8(left)
            self.emit_u8(right)
        else:
            # Debug: print unmapped operator
            if self.debug:
                print(f"Warning: Unmapped operator '{inst.op}'")

    def generate_unary_op(self, inst: UnaryOp) -> None:
        """Generate unary operation instruction."""
        dst = self.get_register(inst.dest)
        src = self.get_register(inst.operand)

        if inst.op == "-":
            self.track_vm_instruction()
            self.emit_opcode(Opcode.NEG_R)
        elif inst.op == "not":
            self.track_vm_instruction()
            self.emit_opcode(Opcode.NOT_R)
        else:
            return

        self.emit_u8(dst)
        self.emit_u8(src)

    def generate_jump(self, inst: Jump) -> None:
        """Generate JumpR instruction."""
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        # Record position for later resolution (byte pos, target, current instruction index)
        self.pending_jumps.append((len(self.bytecode), inst.label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder offset

    def generate_conditional_jump(self, inst: ConditionalJump) -> None:
        """Generate JumpIfR instruction with true and false targets."""
        cond = self.get_register(inst.condition)

        # Generate jump to true target
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_R)
        self.emit_u8(cond)
        # Record position for later resolution (byte pos, target, current instruction index)
        current_inst_idx = len(self.instruction_offsets) - 1
        self.pending_jumps.append((len(self.bytecode), inst.true_label, current_inst_idx))
        self.emit_i32(0)  # Placeholder offset

        # If there's a false label, generate unconditional jump to it
        # (this executes if the condition was false)
        if inst.false_label:
            # This will be a new instruction
            self.track_vm_instruction()
            self.emit_opcode(Opcode.JUMP_R)
            current_inst_idx = len(self.instruction_offsets) - 1
            self.pending_jumps.append((len(self.bytecode), inst.false_label, current_inst_idx))
            self.emit_i32(0)  # Placeholder offset

    def generate_call(self, inst: Call) -> None:
        """Generate CallR instruction."""
        if self.debug:
            print(f"DEBUG Call: func={inst.func}, args={inst.args}, dest={inst.dest}")
        dst = self.get_register(inst.dest) if inst.dest else 0

        # Handle function reference - could be a string name, FunctionRef, or a register value
        from machine_dialect.mir.mir_values import FunctionRef

        if isinstance(inst.func, str):
            # Function name as string - load it as a constant
            assert self.allocation is not None
            func_reg = self.allocation.next_register
            if func_reg >= self.allocation.max_registers:
                raise RuntimeError("Out of registers")
            self.allocation.next_register += 1

            # Add function name as string constant
            if self.debug:
                print(f"  DEBUG: Loading function name '{inst.func}' as constant into r{func_reg}")
            const_idx = self.add_constant(inst.func)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(func_reg)
            self.emit_u16(const_idx)
            func = func_reg
        elif isinstance(inst.func, FunctionRef):
            # FunctionRef - extract the name and load as constant
            assert self.allocation is not None
            func_reg = self.allocation.next_register
            if func_reg >= self.allocation.max_registers:
                raise RuntimeError("Out of registers")
            self.allocation.next_register += 1

            # Add function name as string constant
            if self.debug:
                print(f"  DEBUG: Loading FunctionRef '{inst.func.name}' as constant into r{func_reg}")
            const_idx = self.add_constant(inst.func.name)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(func_reg)
            self.emit_u16(const_idx)
            func = func_reg
        else:
            # Already a register value
            if self.debug:
                print(f"  DEBUG: Function is already in register: {inst.func}")
            func = self.get_register(inst.func)

        # Load argument constants if needed
        args = []
        for arg in inst.args:
            if isinstance(arg, Constant):
                arg_reg = self.get_register(arg)
                const_val = arg.value if hasattr(arg, "value") else arg
                const_idx = self.add_constant(const_val)
                self.track_vm_instruction()
                self.emit_opcode(Opcode.LOAD_CONST_R)
                self.emit_u8(arg_reg)
                self.emit_u16(const_idx)
                args.append(arg_reg)
            else:
                args.append(self.get_register(arg))

        if self.debug:
            print(f"  Function register: r{func}, dest register: r{dst}")
            print(f"  Argument registers: {[f'r{a}' for a in args]}")

        self.track_vm_instruction()
        self.emit_opcode(Opcode.CALL_R)
        self.emit_u8(func)
        self.emit_u8(dst)
        self.emit_u8(len(args))
        for arg_reg in args:
            self.emit_u8(arg_reg)

    def generate_return(self, inst: Return) -> None:
        """Generate ReturnR instruction."""
        if self.debug:
            print(f"DEBUG Return: value={inst.value}")
            if inst.value:
                print(f"  value type: {type(inst.value)}")
                if hasattr(inst.value, "name"):
                    print(f"  value name: {inst.value.name}")
                if hasattr(inst.value, "version"):
                    print(f"  value version: {inst.value.version}")
                # Debug: show allocation map
                if self.allocation:
                    print(f"  Allocation map has {len(self.allocation.value_to_register)} entries")
                    for val, reg in self.allocation.value_to_register.items():
                        if hasattr(val, "name"):
                            print(f"    {val.name} (v{getattr(val, 'version', '?')}) -> r{reg}")

        if inst.value:
            # If the value is a constant, we need to load it first
            if isinstance(inst.value, Constant):
                # Load constant into register 0 (return register)
                const_value = inst.value.value if hasattr(inst.value, "value") else inst.value
                const_idx = self.add_constant(const_value)
                if self.debug:
                    print(f"  -> Loading constant {const_value} into r0 for return")
                self.track_vm_instruction()
                self.emit_opcode(Opcode.LOAD_CONST_R)
                self.emit_u8(0)  # Use register 0 for return
                self.emit_u16(const_idx)

                # Now return from register 0
                self.track_vm_instruction()
                self.emit_opcode(Opcode.RETURN_R)
                self.emit_u8(1)  # Has return value
                self.emit_u8(0)  # Return from register 0
            else:
                # Value is already in a register
                reg = self.get_register(inst.value)
                if self.debug:
                    print(f"  -> Returning from register r{reg}")
                self.track_vm_instruction()
                self.emit_opcode(Opcode.RETURN_R)
                self.emit_u8(1)  # Has return value
                self.emit_u8(reg)
        else:
            if self.debug:
                print("  -> Returning with no value")
            self.track_vm_instruction()
            self.emit_opcode(Opcode.RETURN_R)
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

        self.track_vm_instruction()
        self.emit_opcode(Opcode.PHI_R)
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

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ASSERT_R)
        self.emit_u8(reg)
        self.emit_u8(0)  # AssertType::True
        self.emit_u16(msg_idx)

    def generate_scope(self, inst: Scope) -> None:
        """Generate ScopeEnterR/ScopeExitR instruction."""
        scope_id = inst.scope_id  # type: ignore[attr-defined]
        if inst.action == "enter":  # type: ignore[attr-defined]
            self.track_vm_instruction()
            self.emit_opcode(Opcode.SCOPE_ENTER_R)
        else:
            self.track_vm_instruction()
            self.emit_opcode(Opcode.SCOPE_EXIT_R)

        self.emit_u16(scope_id)

    def generate_print(self, inst: Print) -> None:
        """Generate DebugPrint instruction."""
        # If the value is a constant, we need to load it first
        if isinstance(inst.value, Constant):
            # Allocate a register for the constant
            src = self.get_register(inst.value)
            # Add the constant to the constant pool
            const_idx = self.add_constant(inst.value.value)
            # Emit LOAD_CONST_R to load the constant into the register
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(src)
            self.emit_u16(const_idx)
        else:
            # For non-constants, just get the register
            src = self.get_register(inst.value)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DEBUG_PRINT)
        self.emit_u8(src)

    def resolve_jumps(self) -> None:
        """Resolve pending jump offsets."""
        for jump_offset_pos, target_label, source_inst_idx in self.pending_jumps:
            if target_label in self.block_offsets:
                target_inst_idx = self.block_offsets[target_label]
                # The VM uses instruction-based PC, not byte offsets
                # The offset is in instructions, relative to the NEXT instruction
                # source_inst_idx is the index of the jump instruction itself
                # After execution, PC will be source_inst_idx + 1
                offset = target_inst_idx - (source_inst_idx + 1)
                # Write offset at jump position
                struct.pack_into("<i", self.bytecode, jump_offset_pos, offset)

    def get_register(self, value: MIRValue) -> int:
        """Get register number for a value.

        For constants, this allocates a register and remembers it,
        but does NOT emit the LOAD_CONST_R instruction.
        The caller is responsible for loading constants.

        Args:
            value: MIR value.

        Returns:
            Register number.
        """
        if isinstance(value, Constant):
            # Check if we already allocated a register for this constant
            if self.allocation and value in self.allocation.value_to_register:
                return self.allocation.value_to_register[value]

            # Allocate a new register for this constant
            assert self.allocation is not None
            reg = self.allocation.next_register
            if reg >= self.allocation.max_registers:
                raise RuntimeError("Out of registers")
            self.allocation.next_register += 1
            self.allocation.value_to_register[value] = reg

            # Note: We do NOT emit LOAD_CONST_R here!
            # The caller must handle loading the constant
            if self.debug:
                print(f"  DEBUG: Allocated r{reg} for constant {value.value if hasattr(value, 'value') else value}")
            return reg

        assert self.allocation is not None
        if value not in self.allocation.value_to_register:
            # Special case: check if this is a parameter by name
            if self.current_function and isinstance(value, Variable):
                for param in self.current_function.params:
                    if param.name == value.name:
                        # Found the parameter, look it up in allocation
                        if param in self.allocation.value_to_register:
                            if self.debug:
                                reg = self.allocation.value_to_register[param]
                                print(f"  DEBUG: Found parameter {value.name} by name -> r{reg}")
                            return self.allocation.value_to_register[param]
                        else:
                            raise RuntimeError(f"Parameter {value.name} not allocated to register")

            # Check if this is an SSA variable that should have been allocated
            if self.is_ssa_variable(value) and isinstance(value, Variable):
                raise RuntimeError(f"SSA variable {value.name} (version {value.version}) not allocated to register")

            # For non-SSA variables, check if we should error
            if self.debug:
                print(f"  WARNING: Value {value} not in allocation map, returning r23 (uninitialized!)")
            # This is likely the bug - returning an arbitrary register
            return 23  # This will help us identify the issue
        return self.allocation.value_to_register[value]

    def add_constant(self, value: Any) -> int:
        """Add a constant to the pool.

        Args:
            value: Constant value.

        Returns:
            Constant index.
        """
        # Determine constant type and add to pool
        tag: ConstantTag
        val: Any
        if value is None:
            tag = ConstantTag.EMPTY
            val = 0
        elif isinstance(value, bool):
            tag = ConstantTag.BOOL
            val = value
        elif isinstance(value, int):
            tag = ConstantTag.INT
            val = value
        elif isinstance(value, float):
            tag = ConstantTag.FLOAT
            val = value
        elif isinstance(value, str):
            tag = ConstantTag.STRING
            val = value
        else:
            # Default to string representation
            tag = ConstantTag.STRING
            val = str(value)

        # Check if constant already exists
        for i, (t, v) in enumerate(self.constants):
            if t == tag and v == val:
                return i

        # Add new constant
        idx = len(self.constants)
        self.constants.append((tag, val))
        return idx

    def add_string_constant(self, value: str) -> int:
        """Add a string constant to the pool.

        Args:
            value: String value.

        Returns:
            Constant index.
        """
        # Check if string already exists
        for i, (tag, val) in enumerate(self.constants):
            if tag == ConstantTag.STRING and val == value:
                return i

        # Add new string constant
        idx = len(self.constants)
        self.constants.append((ConstantTag.STRING, value))
        return idx

    def track_vm_instruction(self) -> None:
        """Track the start of a new VM instruction.

        This must be called before emitting each VM instruction to maintain
        proper instruction offset tracking for jump resolution.
        """
        self.instruction_offsets.append(len(self.bytecode))

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

    def add_label(self, label: str) -> None:
        """Add a label at the current bytecode position.

        Args:
            label: The label to add.
        """
        # Map label to current instruction index
        self.block_offsets[label] = len(self.instruction_offsets)

    def generate_array_create(self, inst: ArrayCreate) -> None:
        """Generate NewArrayR instruction from MIR ArrayCreate."""
        dst = self.get_register(inst.dest)

        # Handle size - load constant if needed
        if isinstance(inst.size, Constant):
            size = self.get_register(inst.size)
            # Load the constant into the register
            const_idx = self.add_constant(inst.size.value if hasattr(inst.size, "value") else inst.size)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(size)
            self.emit_u16(const_idx)
        else:
            size = self.get_register(inst.size)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.NEW_ARRAY_R)
        self.emit_u8(dst)
        self.emit_u8(size)

        if self.debug:
            print(f"  -> Generated NewArrayR: r{dst} = new_array(r{size})")

    def generate_array_get(self, inst: ArrayGet) -> None:
        """Generate ArrayGetR instruction from MIR ArrayGet."""
        dst = self.get_register(inst.dest)
        array = self.get_register(inst.array)
        index = self.get_register(inst.index)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(dst)
        self.emit_u8(array)
        self.emit_u8(index)

        if self.debug:
            print(f"  -> Generated ArrayGetR: r{dst} = r{array}[r{index}]")

    def generate_array_set(self, inst: ArraySet) -> None:
        """Generate ArraySetR instruction from MIR ArraySet."""
        array = self.get_register(inst.array)

        # Handle index - load constant if needed
        if isinstance(inst.index, Constant):
            index = self.get_register(inst.index)
            # Load the constant into the register
            const_idx = self.add_constant(inst.index.value if hasattr(inst.index, "value") else inst.index)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(index)
            self.emit_u16(const_idx)
        else:
            index = self.get_register(inst.index)

        # Handle value - load constant if needed
        if isinstance(inst.value, Constant):
            value = self.get_register(inst.value)
            # Load the constant into the register
            const_idx = self.add_constant(inst.value.value if hasattr(inst.value, "value") else inst.value)
            self.track_vm_instruction()
            self.emit_opcode(Opcode.LOAD_CONST_R)
            self.emit_u8(value)
            self.emit_u16(const_idx)
        else:
            value = self.get_register(inst.value)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(array)
        self.emit_u8(index)
        self.emit_u8(value)

        if self.debug:
            print(f"  -> Generated ArraySetR: r{array}[r{index}] = r{value}")

    def generate_array_length(self, inst: ArrayLength) -> None:
        """Generate ArrayLenR instruction from MIR ArrayLength."""
        dst = self.get_register(inst.dest)
        array = self.get_register(inst.array)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_LEN_R)
        self.emit_u8(dst)
        self.emit_u8(array)

        if self.debug:
            print(f"  -> Generated ArrayLenR: r{dst} = len(r{array})")

    def generate_array_append(self, inst: ArrayAppend) -> None:
        """Generate array append as set at length position."""
        array = self.get_register(inst.array)
        value = self.get_register(inst.value)

        # First get the current length into a temp register
        # We need to allocate a temp register for the length
        length_reg = 255  # Use highest register as temp

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_LEN_R)
        self.emit_u8(length_reg)
        self.emit_u8(array)

        # Then set array[length] = value
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(array)
        self.emit_u8(length_reg)
        self.emit_u8(value)

        if self.debug:
            print(f"  -> Generated ArrayAppend: r{array}.append(r{value})")

    def generate_dict_create(self, inst: DictCreate) -> None:
        """Generate DictNewR instruction from MIR DictCreate."""
        dst = self.get_register(inst.dest)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_NEW_R)
        self.emit_u8(dst)

        if self.debug:
            print(f"  -> Generated DictNewR: r{dst} = new_dict()")

    def generate_dict_get(self, inst: DictGet) -> None:
        """Generate DictGetR instruction from MIR DictGet."""
        dst = self.get_register(inst.dest)
        dict_reg = self.get_register(inst.dict_val)
        key_reg = self.get_register(inst.key)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_GET_R)
        self.emit_u8(dst)
        self.emit_u8(dict_reg)
        self.emit_u8(key_reg)

        if self.debug:
            print(f"  -> Generated DictGetR: r{dst} = r{dict_reg}[r{key_reg}]")

    def generate_dict_set(self, inst: DictSet) -> None:
        """Generate DictSetR instruction from MIR DictSet."""
        dict_reg = self.get_register(inst.dict_val)
        key_reg = self.get_register(inst.key)
        value_reg = self.get_register(inst.value)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_SET_R)
        self.emit_u8(dict_reg)
        self.emit_u8(key_reg)
        self.emit_u8(value_reg)

        if self.debug:
            print(f"  -> Generated DictSetR: r{dict_reg}[r{key_reg}] = r{value_reg}")

    def generate_dict_remove(self, inst: DictRemove) -> None:
        """Generate DictRemoveR instruction from MIR DictRemove."""
        dict_reg = self.get_register(inst.dict_val)
        key_reg = self.get_register(inst.key)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_REMOVE_R)
        self.emit_u8(dict_reg)
        self.emit_u8(key_reg)

        if self.debug:
            print(f"  -> Generated DictRemoveR: del r{dict_reg}[r{key_reg}]")

    def generate_dict_contains(self, inst: DictContains) -> None:
        """Generate DictHasKeyR instruction from MIR DictContains."""
        dst = self.get_register(inst.dest)
        dict_reg = self.get_register(inst.dict_val)
        key_reg = self.get_register(inst.key)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_CONTAINS_R)
        self.emit_u8(dst)
        self.emit_u8(dict_reg)
        self.emit_u8(key_reg)

        if self.debug:
            print(f"  -> Generated DictContainsR: r{dst} = r{key_reg} in r{dict_reg}")

    def generate_array_remove(self, inst: ArrayRemove) -> None:
        """Generate array remove at index using copy emulation.

        Emulates array.remove_at(index) by:
        1. Get original array length
        2. Create new array with length - 1
        3. Copy elements [0:index] to new array
        4. Copy elements [index+1:] to new[index:]
        5. Replace original array with new array
        """
        array = self.get_register(inst.array)
        index = self.get_register(inst.index)

        # Allocate temporary registers
        old_len_reg = 247  # Original length
        new_len_reg = 248  # New length (old - 1)
        new_array_reg = 249  # New array
        i_reg = 250  # Loop counter for source
        j_reg = 251  # Loop counter for destination
        element_reg = 252  # Temporary for element
        cmp_reg = 253  # Comparison result
        const_one_reg = 254  # Constant 1

        # Get original array length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_LEN_R)
        self.emit_u8(old_len_reg)
        self.emit_u8(array)

        # Calculate new length (old - 1)
        const_one = self.add_constant(1)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(const_one_reg)
        self.emit_u16(const_one)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.SUB_R)
        self.emit_u8(new_len_reg)
        self.emit_u8(old_len_reg)
        self.emit_u8(const_one_reg)

        # Create new array with new length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.NEW_ARRAY_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(new_len_reg)

        # Initialize loop counters to 0
        const_zero = self.add_constant(0)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(i_reg)
        self.emit_u16(const_zero)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(j_reg)
        self.emit_u16(const_zero)

        # Generate unique labels
        copy_loop_label = f"remove_copy_{self.label_counter}"
        skip_removed_label = f"remove_skip_{self.label_counter}"
        copy_element_label = f"remove_element_{self.label_counter}"
        remove_done_label = f"remove_done_{self.label_counter}"
        self.label_counter += 1

        # --- Main copy loop ---
        self.add_label(copy_loop_label)

        # Check if i < old_len
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LT_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(i_reg)
        self.emit_u8(old_len_reg)

        # If not (i >= old_len), we're done
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_NOT_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), remove_done_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Check if i == index (skip this element)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.EQ_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(i_reg)
        self.emit_u8(index)

        # If i == index, skip copying this element
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), skip_removed_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # --- Copy element from old[i] to new[j] ---
        self.add_label(copy_element_label)

        # Get element from original array[i]
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(element_reg)
        self.emit_u8(array)
        self.emit_u8(i_reg)

        # Set new[j] = element
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(j_reg)
        self.emit_u8(element_reg)

        # Increment j (destination index)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(j_reg)
        self.emit_u8(j_reg)
        self.emit_u8(const_one_reg)

        # --- Skip removed element (just increment i) ---
        self.add_label(skip_removed_label)

        # Increment i (source index)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(i_reg)
        self.emit_u8(i_reg)
        self.emit_u8(const_one_reg)

        # Jump back to loop start
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        self.pending_jumps.append((len(self.bytecode), copy_loop_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # --- Replace original array with new array ---
        self.add_label(remove_done_label)

        # Move new array to original array register
        self.track_vm_instruction()
        self.emit_opcode(Opcode.MOVE_R)
        self.emit_u8(array)
        self.emit_u8(new_array_reg)

        if self.debug:
            print(f"  -> Generated ArrayRemove: r{array}.remove_at(r{index}) using copy emulation")

    def generate_array_insert(self, inst: ArrayInsert) -> None:
        """Generate array insert at index using copy emulation.

        Emulates array.insert(index, value) by:
        1. Get original array length
        2. Create new array with length + 1
        3. Copy elements [0:index] to new array
        4. Set new[index] = value
        5. Copy elements [index:] to new[index+1:]
        6. Replace original array with new array
        """
        array = self.get_register(inst.array)
        index = self.get_register(inst.index)
        value = self.get_register(inst.value)

        # Allocate temporary registers
        old_len_reg = 248  # Original length
        new_len_reg = 249  # New length (old + 1)
        new_array_reg = 250  # New array
        i_reg = 251  # Loop counter
        element_reg = 252  # Temporary for element
        cmp_reg = 253  # Comparison result
        const_one_reg = 254  # Constant 1

        # Get original array length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_LEN_R)
        self.emit_u8(old_len_reg)
        self.emit_u8(array)

        # Calculate new length (old + 1)
        const_one = self.add_constant(1)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(const_one_reg)
        self.emit_u16(const_one)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(new_len_reg)
        self.emit_u8(old_len_reg)
        self.emit_u8(const_one_reg)

        # Create new array with new length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.NEW_ARRAY_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(new_len_reg)

        # Initialize loop counter to 0
        const_zero = self.add_constant(0)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(i_reg)
        self.emit_u16(const_zero)

        # Generate unique labels
        copy_before_label = f"insert_copy_before_{self.label_counter}"
        copy_after_label = f"insert_copy_after_{self.label_counter}"
        insert_done_label = f"insert_done_{self.label_counter}"
        self.label_counter += 1

        # --- Copy elements before insertion point ---
        self.add_label(copy_before_label)

        # Check if i < index
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LT_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(i_reg)
        self.emit_u8(index)

        # If not (i >= index), skip to insert value
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_NOT_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), copy_after_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Get element from original array
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(element_reg)
        self.emit_u8(array)
        self.emit_u8(i_reg)

        # Set element in new array at same position
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(i_reg)
        self.emit_u8(element_reg)

        # Increment i
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(i_reg)
        self.emit_u8(i_reg)
        self.emit_u8(const_one_reg)

        # Jump back to loop start
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        self.pending_jumps.append((len(self.bytecode), copy_before_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # --- Insert the value at index ---
        self.add_label(copy_after_label)

        # Set new[index] = value
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(index)
        self.emit_u8(value)

        # Reset i to index for copying remaining elements
        self.track_vm_instruction()
        self.emit_opcode(Opcode.MOVE_R)
        self.emit_u8(i_reg)
        self.emit_u8(index)

        # --- Copy elements after insertion point ---
        copy_rest_label = f"insert_copy_rest_{self.label_counter - 1}"
        self.add_label(copy_rest_label)

        # Check if i < old_len
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LT_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(i_reg)
        self.emit_u8(old_len_reg)

        # If not (i >= old_len), we're done
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_NOT_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), insert_done_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Get element from original array[i]
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(element_reg)
        self.emit_u8(array)
        self.emit_u8(i_reg)

        # Calculate destination index (i + 1) using element_reg temporarily
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(element_reg)
        self.emit_u8(i_reg)
        self.emit_u8(const_one_reg)

        # Get element from original array[i] again (since we overwrote element_reg)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(cmp_reg)  # Use cmp_reg temporarily for the element
        self.emit_u8(array)
        self.emit_u8(i_reg)

        # Set new[i+1] = element
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_SET_R)
        self.emit_u8(new_array_reg)
        self.emit_u8(element_reg)  # This is i+1
        self.emit_u8(cmp_reg)  # This is the element

        # Increment i
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(i_reg)
        self.emit_u8(i_reg)
        self.emit_u8(const_one_reg)

        # Jump back to copy rest loop
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        self.pending_jumps.append((len(self.bytecode), copy_rest_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # --- Replace original array with new array ---
        self.add_label(insert_done_label)

        # Move new array to original array register
        self.track_vm_instruction()
        self.emit_opcode(Opcode.MOVE_R)
        self.emit_u8(array)
        self.emit_u8(new_array_reg)

        if self.debug:
            print(f"  -> Generated ArrayInsert: r{array}.insert(r{index}, r{value}) using copy emulation")

    def generate_dict_keys(self, inst: DictKeys) -> None:
        """Generate dictionary keys extraction.

        Args:
            inst: DictKeys instruction.
        """
        dst = self.get_register(inst.dest)
        dict_reg = self.get_register(inst.dict_val)

        # Emit DictKeysR instruction
        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_KEYS_R)
        self.emit_u8(dst)
        self.emit_u8(dict_reg)

        if self.debug:
            print(f"  -> Generated DictKeysR: r{dst} = r{dict_reg}.keys()")

    def generate_dict_values(self, inst: DictValues) -> None:
        """Generate dictionary values extraction.

        Args:
            inst: DictValues instruction.
        """

        dst = self.get_register(inst.dest)
        dict_reg = self.get_register(inst.dict_val)

        # Emit DictValuesR instruction
        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_VALUES_R)
        self.emit_u8(dst)
        self.emit_u8(dict_reg)

        if self.debug:
            print(f"  -> Generated DictValuesR: r{dst} = r{dict_reg}.values()")

    def generate_dict_clear(self, inst: DictClear) -> None:
        """Generate DictClearR instruction.

        Args:
            inst: DictClear instruction.
        """
        dict_reg = self.get_register(inst.dict_val)

        # Emit DictClearR instruction
        self.track_vm_instruction()
        self.emit_opcode(Opcode.DICT_CLEAR_R)
        self.emit_u8(dict_reg)

        if self.debug:
            print(f"  -> Generated DictClearR: r{dict_reg}.clear()")

    def generate_array_clear(self, inst: ArrayClear) -> None:
        """Generate array clear.

        This can be implemented as creating a new empty array.
        """
        array = self.get_register(inst.array)

        # Create a new empty array (size 0) and assign to the array register
        zero_reg = 254  # Use a temp register for constant 0

        # Load constant 0
        const_idx = self.add_constant(0)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(zero_reg)
        self.emit_u16(const_idx)

        # Create new empty array
        self.track_vm_instruction()
        self.emit_opcode(Opcode.NEW_ARRAY_R)
        self.emit_u8(array)
        self.emit_u8(zero_reg)

        if self.debug:
            print(f"  -> Generated ArrayClear: r{array}.clear() as new_array(0)")

    def generate_array_find_index(self, inst: ArrayFindIndex) -> None:
        """Generate array find index by value using loop emulation.

        Emulates array.find(value) by iterating through the array:
        1. Get array length
        2. Initialize index to 0
        3. Loop through array:
           - Get element at current index
           - Compare with target value
           - If equal, store index and exit
           - Otherwise increment index and continue
        4. If not found, store -1
        """
        dest = self.get_register(inst.dest)
        array = self.get_register(inst.array)
        value = self.get_register(inst.value)

        # Allocate temporary registers
        length_reg = 250  # Array length
        index_reg = 251  # Current index
        element_reg = 252  # Current element
        cmp_reg = 253  # Comparison result

        # Generate unique labels for this loop
        loop_start_label = f"find_loop_{self.label_counter}"
        loop_end_label = f"find_end_{self.label_counter}"
        found_label = f"find_found_{self.label_counter}"
        self.label_counter += 1

        # Get array length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_LEN_R)
        self.emit_u8(length_reg)
        self.emit_u8(array)

        # Initialize index to 0
        const_idx = self.add_constant(0)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(index_reg)
        self.emit_u16(const_idx)

        # Loop start
        self.add_label(loop_start_label)

        # Check if index < length
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LT_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(index_reg)
        self.emit_u8(length_reg)

        # If not (index >= length), jump to end (not found)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_NOT_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), loop_end_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Get element at current index
        self.track_vm_instruction()
        self.emit_opcode(Opcode.ARRAY_GET_R)
        self.emit_u8(element_reg)
        self.emit_u8(array)
        self.emit_u8(index_reg)

        # Compare element with target value
        self.track_vm_instruction()
        self.emit_opcode(Opcode.EQ_R)
        self.emit_u8(cmp_reg)
        self.emit_u8(element_reg)
        self.emit_u8(value)

        # If equal, jump to found
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_IF_R)
        self.emit_u8(cmp_reg)
        self.pending_jumps.append((len(self.bytecode), found_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Increment index
        const_one = self.add_constant(1)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(element_reg)  # Reuse element_reg for constant 1
        self.emit_u16(const_one)

        self.track_vm_instruction()
        self.emit_opcode(Opcode.ADD_R)
        self.emit_u8(index_reg)
        self.emit_u8(index_reg)
        self.emit_u8(element_reg)

        # Jump back to loop start
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        self.pending_jumps.append((len(self.bytecode), loop_start_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Found label - copy index to dest
        self.add_label(found_label)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.MOVE_R)
        self.emit_u8(dest)
        self.emit_u8(index_reg)

        # Jump to end (skip not found case)
        end_jump_label = f"find_exit_{self.label_counter - 1}"
        self.track_vm_instruction()
        self.emit_opcode(Opcode.JUMP_R)
        self.pending_jumps.append((len(self.bytecode), end_jump_label, len(self.instruction_offsets) - 1))
        self.emit_i32(0)  # Placeholder

        # Not found - set dest to -1
        self.add_label(loop_end_label)
        const_neg_one = self.add_constant(-1)
        self.track_vm_instruction()
        self.emit_opcode(Opcode.LOAD_CONST_R)
        self.emit_u8(dest)
        self.emit_u16(const_neg_one)

        # Exit label
        self.add_label(end_jump_label)

        if self.debug:
            print(f"  -> Generated ArrayFindIndex: r{dest} = find_index(r{array}, r{value}) using loop emulation")


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


def generate_bytecode_from_mir(
    mir_module: MIRModule, debug: bool = False
) -> tuple[BytecodeModule, dict[str, Any] | None]:
    """Generate bytecode and metadata from MIR module.

    This is the main entry point for bytecode generation.

    Args:
        mir_module: MIR module to generate bytecode from.
        debug: Enable debug output for bytecode generation.

    Returns:
        Tuple of (bytecode module, metadata).
    """
    generator = RegisterBytecodeGenerator(debug=debug)
    bytecode = generator.generate(mir_module)

    # Collect metadata
    if generator.allocation is not None:
        collector = MetadataCollector(debug_mode=False)
        metadata = collector.collect(mir_module, generator.allocation)
    else:
        metadata = None

    return bytecode, metadata
