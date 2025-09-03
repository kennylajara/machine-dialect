"""Tests for MIR to bytecode generation."""

from __future__ import annotations

import unittest

from machine_dialect.codegen.isa import Opcode
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Print,
    Return,
    Scope,
    Select,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_to_bytecode import BytecodeGenerator, generate_bytecode
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Variable


class TestBytecodeGeneration(unittest.TestCase):
    """Test MIR to bytecode generation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = BytecodeGenerator()

    def test_generate_empty_module(self) -> None:
        """Test generating bytecode for empty module."""
        mir_module = MIRModule("test")

        bytecode_module = generate_bytecode(mir_module)

        self.assertEqual(bytecode_module.name, "test")
        self.assertIsNotNone(bytecode_module.main_chunk)
        # Should have HALT instruction
        self.assertIn(Opcode.HALT, bytecode_module.main_chunk.bytecode)

    def test_generate_main_function(self) -> None:
        """Test generating bytecode for main function."""
        mir_module = MIRModule("test")

        # Create main function
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Add simple return
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Main chunk should have RETURN instruction
        self.assertIn(Opcode.RETURN, bytecode_module.main_chunk.bytecode)

    def test_generate_constants(self) -> None:
        """Test constant pool generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Load various constants
        t1 = main.new_temp(MIRType.INT)
        t2 = main.new_temp(MIRType.STRING)
        t3 = main.new_temp(MIRType.BOOL)

        entry.add_instruction(LoadConst(t1, 42))
        entry.add_instruction(LoadConst(t2, "hello"))
        entry.add_instruction(LoadConst(t3, True))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have LOAD_CONST instructions
        self.assertIn(Opcode.LOAD_CONST, bytecode_module.main_chunk.bytecode)

        # Check constants in pool
        constants = bytecode_module.main_chunk.constants.constants()
        self.assertIn(42, constants)
        self.assertIn("hello", constants)
        self.assertIn(True, constants)

    def test_generate_variables(self) -> None:
        """Test local variable handling."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Create and use local variable
        x = Variable("x", MIRType.INT)
        main.add_local(x)

        const_val = Constant(10, MIRType.INT)
        entry.add_instruction(StoreVar(x, const_val))

        t = main.new_temp(MIRType.INT)
        entry.add_instruction(Copy(t, x))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have STORE_LOCAL and LOAD_LOCAL
        self.assertIn(Opcode.STORE_LOCAL, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.LOAD_LOCAL, bytecode_module.main_chunk.bytecode)

    def test_generate_binary_operations(self) -> None:
        """Test binary operation bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Test various binary operations
        main.new_temp(MIRType.INT)
        main.new_temp(MIRType.INT)

        const1 = Constant(10, MIRType.INT)
        const2 = Constant(5, MIRType.INT)

        # Addition
        result_add = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(result_add, "+", const1, const2))

        # Subtraction
        result_sub = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(result_sub, "-", const1, const2))

        # Comparison
        result_cmp = main.new_temp(MIRType.BOOL)
        entry.add_instruction(BinaryOp(result_cmp, "<", const1, const2))

        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have arithmetic opcodes
        self.assertIn(Opcode.ADD, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.SUB, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.LT, bytecode_module.main_chunk.bytecode)

    def test_generate_unary_operations(self) -> None:
        """Test unary operation bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Negation
        const_val = Constant(42, MIRType.INT)
        neg_result = main.new_temp(MIRType.INT)
        entry.add_instruction(UnaryOp(neg_result, "-", const_val))

        # Logical NOT
        bool_val = Constant(True, MIRType.BOOL)
        not_result = main.new_temp(MIRType.BOOL)
        entry.add_instruction(UnaryOp(not_result, "not", bool_val))

        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have unary opcodes
        self.assertIn(Opcode.NEG, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.NOT, bytecode_module.main_chunk.bytecode)

    def test_generate_control_flow(self) -> None:
        """Test control flow bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)

        # Create diamond CFG
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        main.cfg.add_block(entry)
        main.cfg.add_block(then_block)
        main.cfg.add_block(else_block)
        main.cfg.add_block(merge)
        main.cfg.set_entry_block(entry)

        main.cfg.connect(entry, then_block)
        main.cfg.connect(entry, else_block)
        main.cfg.connect(then_block, merge)
        main.cfg.connect(else_block, merge)

        # Add conditional jump
        cond = Constant(True, MIRType.BOOL)
        entry.add_instruction(ConditionalJump(cond, "then", "else"))

        then_block.add_instruction(Jump("merge"))
        else_block.add_instruction(Jump("merge"))
        merge.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have jump instructions
        self.assertIn(Opcode.JUMP, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.JUMP_IF_FALSE, bytecode_module.main_chunk.bytecode)

    def test_generate_function_calls(self) -> None:
        """Test function call bytecode generation."""
        mir_module = MIRModule("test")

        # Create main function that calls helper
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Call helper function
        func_ref = FunctionRef("helper")
        arg = Constant(42, MIRType.INT)
        result = main.new_temp(MIRType.INT)

        entry.add_instruction(Call(result, func_ref, [arg]))
        entry.add_instruction(Return())

        # Create helper function
        param = Variable("x", MIRType.INT)
        helper = MIRFunction("helper", [param], MIRType.INT)
        helper_entry = BasicBlock("entry")
        helper.cfg.add_block(helper_entry)
        helper.cfg.set_entry_block(helper_entry)
        helper_entry.add_instruction(Return(param))

        mir_module.add_function(main)
        mir_module.add_function(helper)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have LOAD_FUNCTION and CALL
        self.assertIn(Opcode.LOAD_FUNCTION, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.CALL, bytecode_module.main_chunk.bytecode)

        # Helper function should be in functions
        self.assertIn("helper", bytecode_module.functions)

    def test_generate_print_statement(self) -> None:
        """Test print statement bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Print a value
        msg = Constant("Hello, World!", MIRType.STRING)
        entry.add_instruction(Print(msg))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should call print function
        self.assertIn(Opcode.LOAD_FUNCTION, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.CALL, bytecode_module.main_chunk.bytecode)
        self.assertIn("print", bytecode_module.main_chunk.constants.constants())

    def test_generate_select_instruction(self) -> None:
        """Test select (ternary) instruction bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # result = condition ? 1 : 2
        condition = Constant(True, MIRType.BOOL)
        true_val = Constant(1, MIRType.INT)
        false_val = Constant(2, MIRType.INT)
        result = main.new_temp(MIRType.INT)

        entry.add_instruction(Select(result, condition, true_val, false_val))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have conditional jumps for select
        self.assertIn(Opcode.JUMP_IF_FALSE, bytecode_module.main_chunk.bytecode)
        self.assertIn(Opcode.JUMP, bytecode_module.main_chunk.bytecode)

    def test_generate_assert_instruction(self) -> None:
        """Test assert instruction bytecode generation."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Assert with message
        condition = Constant(False, MIRType.BOOL)
        entry.add_instruction(Assert(condition, "Assertion failed: x > 0"))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have conditional jump and error call
        self.assertIn(Opcode.JUMP_IF_FALSE, bytecode_module.main_chunk.bytecode)
        self.assertIn("__error__", bytecode_module.main_chunk.constants.constants())
        self.assertIn("Assertion failed: x > 0", bytecode_module.main_chunk.constants.constants())

    def test_generate_scope_instructions(self) -> None:
        """Test that scope instructions don't generate bytecode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Add scope instructions (should be hints only)
        entry.add_instruction(Scope(is_begin=True))
        entry.add_instruction(LoadConst(main.new_temp(MIRType.INT), 42))
        entry.add_instruction(Scope(is_begin=False))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Scope instructions shouldn't generate extra bytecode
        # Should only have LOAD_CONST, STORE_LOCAL, and RETURN
        bytecode = bytecode_module.main_chunk.bytecode
        opcode_count = sum(1 for b in bytecode if b in [op.value for op in Opcode])
        self.assertLessEqual(opcode_count, 10)  # Reasonable number of opcodes

    def test_slot_allocation(self) -> None:
        """Test stack slot allocation for locals and temporaries."""
        mir_module = MIRModule("test")
        # Use a function name other than "main" to test local slot allocation
        func = MIRFunction("test_func", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Create multiple locals and temporaries
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        z = Variable("z", MIRType.INT)

        func.add_local(x)
        func.add_local(y)
        func.add_local(z)

        # Also create temporaries
        t1 = func.new_temp(MIRType.INT)
        func.new_temp(MIRType.INT)

        # Use them
        entry.add_instruction(StoreVar(x, Constant(1, MIRType.INT)))
        entry.add_instruction(StoreVar(y, Constant(2, MIRType.INT)))
        entry.add_instruction(BinaryOp(t1, "+", x, y))
        entry.add_instruction(StoreVar(z, t1))
        entry.add_instruction(Return())

        mir_module.add_function(func)

        # Also add a main function that calls this
        main = MIRFunction("main", [], MIRType.EMPTY)
        main_entry = BasicBlock("entry")
        main.cfg.add_block(main_entry)
        main.cfg.set_entry_block(main_entry)
        main_entry.add_instruction(Return())
        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should have multiple STORE_LOCAL instructions with different slots
        # Check the test_func chunk, not main
        test_func_chunk = bytecode_module.functions["test_func"]
        bytecode = test_func_chunk.bytecode
        store_count = bytecode.count(Opcode.STORE_LOCAL)
        self.assertGreaterEqual(store_count, 3)  # At least 3 stores

    def test_complex_control_flow_generation(self) -> None:
        """Test bytecode generation for complex control flow."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)

        # Create more complex CFG with multiple paths
        entry = BasicBlock("entry")
        check1 = BasicBlock("check1")
        check2 = BasicBlock("check2")
        action1 = BasicBlock("action1")
        action2 = BasicBlock("action2")
        merge = BasicBlock("merge")

        for block in [entry, check1, check2, action1, action2, merge]:
            main.cfg.add_block(block)
        main.cfg.set_entry_block(entry)

        # Connect blocks
        main.cfg.connect(entry, check1)
        main.cfg.connect(check1, check2)
        main.cfg.connect(check1, merge)
        main.cfg.connect(check2, action1)
        main.cfg.connect(check2, action2)
        main.cfg.connect(action1, merge)
        main.cfg.connect(action2, merge)

        # Add instructions
        entry.add_instruction(Jump("check1"))

        cond1 = Constant(True, MIRType.BOOL)
        check1.add_instruction(ConditionalJump(cond1, "check2", "merge"))

        cond2 = Constant(False, MIRType.BOOL)
        check2.add_instruction(ConditionalJump(cond2, "action1", "action2"))

        action1.add_instruction(Jump("merge"))
        action2.add_instruction(Jump("merge"))
        merge.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)

        # Should handle complex control flow
        self.assertIsNotNone(bytecode_module.main_chunk)
        self.assertIn(Opcode.RETURN, bytecode_module.main_chunk.bytecode)


if __name__ == "__main__":
    unittest.main()
