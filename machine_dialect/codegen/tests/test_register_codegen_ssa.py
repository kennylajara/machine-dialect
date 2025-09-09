"""Tests for SSA variable handling in register bytecode generation.

This module tests the proper handling of SSA-renamed variables (version > 0)
versus regular variables (version = 0) in the register-based bytecode generator.
"""

from __future__ import annotations

import pytest

from machine_dialect.codegen.register_codegen import RegisterBytecodeGenerator
from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    LoadConst,
    LoadVar,
    Return,
    StoreVar,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Variable


class TestSSAVariableHandling:
    """Test SSA variable handling in bytecode generation."""

    def test_ssa_variable_allocation(self) -> None:
        """Test that SSA variables are properly allocated to registers."""
        # Create a simple function with SSA variables
        func = MIRFunction("test_func", [], MIRType.INT)
        cfg = CFG()

        # Create blocks
        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        # Create SSA variables
        x_0 = Variable("x", MIRType.INT, version=0)  # Non-SSA
        x_1 = Variable("x", MIRType.INT, version=1)  # SSA
        x_2 = Variable("x", MIRType.INT, version=2)  # SSA

        # Add instructions
        entry.add_instruction(LoadConst(x_0, Constant(10, MIRType.INT), (0, 0)))
        entry.add_instruction(Copy(x_1, x_0, (0, 0)))  # SSA copy
        entry.add_instruction(BinaryOp(x_2, "+", x_1, Constant(5, MIRType.INT), (0, 0)))
        entry.add_instruction(Return((0, 0), x_2))

        func.cfg = cfg

        # Generate bytecode
        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)
        _ = generator.generate(module)

        # Check that SSA variables are allocated
        assert generator.allocation is not None
        if generator.allocation:
            assert x_1 in generator.allocation.value_to_register
            assert x_2 in generator.allocation.value_to_register

            # Check that they got different registers
            reg_x1 = generator.allocation.value_to_register[x_1]
            reg_x2 = generator.allocation.value_to_register[x_2]
            assert reg_x1 != reg_x2

    def test_ssa_variable_in_copy(self) -> None:
        """Test Copy instruction with SSA variables."""
        func = MIRFunction("test_copy", [], MIRType.INT)
        cfg = CFG()

        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        # Create variables
        x_1 = Variable("x", MIRType.INT, version=1)  # SSA
        y_0 = Variable("y", MIRType.INT, version=0)  # Non-SSA

        # First, x_1 must be defined
        entry.add_instruction(LoadConst(x_1, Constant(42, MIRType.INT), (0, 0)))
        # Copy from SSA to non-SSA
        entry.add_instruction(Copy(y_0, x_1, (0, 0)))
        entry.add_instruction(Return((0, 0), y_0))

        func.cfg = cfg

        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)
        _ = generator.generate(module)

        # Check that x_1 is allocated
        assert generator.allocation is not None
        if generator.allocation:
            assert x_1 in generator.allocation.value_to_register

    def test_ssa_variable_not_allocated_error(self) -> None:
        """Test that using an unallocated SSA variable raises an error."""
        func = MIRFunction("test_error", [], MIRType.INT)
        cfg = CFG()

        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        # Create an SSA variable but don't define it properly
        x_1 = Variable("x", MIRType.INT, version=1)

        # Create a Copy instruction that uses the undefined SSA variable
        dest_temp = func.new_temp(MIRType.INT)
        copy_inst = Copy(dest_temp, x_1, (0, 0))

        entry.add_instruction(copy_inst)
        entry.add_instruction(Return((0, 0), Constant(0)))

        func.cfg = cfg
        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)

        # Manually generate the function to get the allocation
        # but then remove x_1 from the allocation to simulate a bug
        generator.bytecode = bytearray()
        generator.constants = []
        generator.block_offsets = {}
        generator.instruction_offsets = []
        generator.pending_jumps = []

        # Allocate registers normally
        generator.allocation = generator.allocator.allocate_function(func)

        # Now remove x_1 from the allocation to simulate it not being allocated
        if x_1 in generator.allocation.value_to_register:
            del generator.allocation.value_to_register[x_1]

        # Try to generate the copy instruction - this should fail
        with pytest.raises(RuntimeError) as context:
            generator.instruction_offsets.append(len(generator.bytecode))
            generator.generate_copy(copy_inst)

        assert "SSA variable" in str(context.value)
        assert "not allocated to register" in str(context.value)

    def test_mixed_ssa_and_global_variables(self) -> None:
        """Test handling of both SSA and global variables in the same function."""
        func = MIRFunction("test_mixed", [], MIRType.INT)
        cfg = CFG()

        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        # Create variables
        global_var = Variable("global", MIRType.INT, version=0)  # Global
        local_1 = Variable("local", MIRType.INT, version=1)  # SSA
        local_2 = Variable("local", MIRType.INT, version=2)  # SSA

        # Instructions
        entry.add_instruction(LoadVar(local_1, global_var, (0, 0)))  # Load global into SSA
        entry.add_instruction(BinaryOp(local_2, "+", local_1, Constant(10, MIRType.INT), (0, 0)))
        entry.add_instruction(StoreVar(global_var, local_2, (0, 0)))  # Store SSA to global
        entry.add_instruction(Return((0, 0), local_2))

        func.cfg = cfg
        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)
        _ = generator.generate(module)

        # Check allocations
        assert generator.allocation is not None
        if generator.allocation:
            # SSA variables should be allocated
            assert local_1 in generator.allocation.value_to_register
            assert local_2 in generator.allocation.value_to_register
            # Global variable should NOT be allocated (it's loaded by name)
            assert global_var not in generator.allocation.value_to_register

    def test_function_parameters_as_ssa(self) -> None:
        """Test that function parameters work correctly with SSA versioning."""
        # Parameters start with version 0 but are allocated to registers
        param_n = Variable("n", MIRType.INT, version=0)

        func = MIRFunction("fibonacci", [param_n], MIRType.INT)
        cfg = CFG()

        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        # Create SSA versions of the parameter
        n_1 = Variable("n", MIRType.INT, version=1)

        # Use the parameter
        entry.add_instruction(Copy(param_n, n_1, (0, 0)))
        entry.add_instruction(Return((0, 0), n_1))

        func.cfg = cfg
        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)
        _ = generator.generate(module)

        # Check that both parameter and SSA version are allocated
        assert generator.allocation is not None
        if generator.allocation:
            assert param_n in generator.allocation.value_to_register
            assert n_1 in generator.allocation.value_to_register

    def test_recursive_function_with_ssa(self) -> None:
        """Test a recursive function with SSA variables."""
        # Create a simplified recursive function
        param_n = Variable("n", MIRType.INT, version=0)

        func = MIRFunction("recursive", [param_n], MIRType.INT)
        cfg = CFG()

        # Create blocks
        entry = BasicBlock("entry")
        base_case = BasicBlock("base_case")
        recursive_case = BasicBlock("recursive_case")

        cfg.add_block(entry)
        cfg.add_block(base_case)
        cfg.add_block(recursive_case)
        cfg.set_entry_block(entry)

        # Connect blocks
        cfg.connect(entry, base_case)
        cfg.connect(entry, recursive_case)

        # Entry: check if n <= 1
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(BinaryOp(cond, "<=", param_n, Constant(1, MIRType.INT), (0, 0)))
        entry.add_instruction(ConditionalJump(cond, "base_case", (0, 0), "recursive_case"))

        # Base case: return 1
        base_case.add_instruction(Return((0, 0), Constant(1)))

        # Recursive case: return recursive(n - 1) + n
        n_minus_1 = Variable("n_minus_1", MIRType.INT, version=1)  # SSA
        recursive_result = func.new_temp(MIRType.INT)
        final_result = func.new_temp(MIRType.INT)

        recursive_case.add_instruction(BinaryOp(n_minus_1, "-", param_n, Constant(1, MIRType.INT), (0, 0)))
        recursive_case.add_instruction(Call(recursive_result, FunctionRef("recursive"), [n_minus_1], (0, 0)))
        recursive_case.add_instruction(BinaryOp(final_result, "+", recursive_result, param_n, (0, 0)))
        recursive_case.add_instruction(Return((0, 0), final_result))

        func.cfg = cfg
        module = MIRModule("test")
        module.add_function(func)

        generator = RegisterBytecodeGenerator(debug=False)
        _ = generator.generate(module)

        # Check that SSA variable is allocated
        assert generator.allocation is not None
        if generator.allocation:
            assert n_minus_1 in generator.allocation.value_to_register

    def test_is_ssa_variable_helper(self) -> None:
        """Test the is_ssa_variable helper method."""
        generator = RegisterBytecodeGenerator(debug=False)

        # Test SSA variables (version > 0)
        ssa_var = Variable("x", MIRType.INT, version=1)
        assert generator.is_ssa_variable(ssa_var)

        ssa_var2 = Variable("y", MIRType.INT, version=5)
        assert generator.is_ssa_variable(ssa_var2)

        # Test non-SSA variables (version = 0)
        regular_var = Variable("z", MIRType.INT, version=0)
        assert not generator.is_ssa_variable(regular_var)

        # Test non-Variable types
        # Create a dummy function to get a proper Temp
        dummy_func = MIRFunction("dummy", [], MIRType.INT)
        temp = dummy_func.new_temp(MIRType.INT)
        assert not generator.is_ssa_variable(temp)

        constant = Constant(42, MIRType.INT)
        assert not generator.is_ssa_variable(constant)

    def test_debug_mode(self) -> None:
        """Test that debug mode controls output."""
        func = MIRFunction("test_debug", [], MIRType.INT)
        cfg = CFG()

        entry = BasicBlock("entry")
        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        x = Variable("x", MIRType.INT, version=1)
        entry.add_instruction(LoadConst(x, Constant(42, MIRType.INT), (0, 0)))
        entry.add_instruction(Return((0, 0), x))

        func.cfg = cfg
        module = MIRModule("test")
        module.add_function(func)

        # Test with debug=False (no output expected)
        generator_no_debug = RegisterBytecodeGenerator(debug=False)
        bytecode_no_debug = generator_no_debug.generate(module)

        # Test with debug=True (would produce output if we captured it)
        generator_debug = RegisterBytecodeGenerator(debug=True)
        bytecode_debug = generator_debug.generate(module)

        # Both should produce the same bytecode
        assert bytecode_no_debug.chunks[0].bytecode == bytecode_debug.chunks[0].bytecode
