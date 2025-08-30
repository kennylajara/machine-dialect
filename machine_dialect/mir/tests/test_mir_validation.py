"""Tests for MIR validation and verification."""

from __future__ import annotations

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Jump,
    LoadConst,
    Phi,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_validation import MIRValidator, validate_function, validate_module
from machine_dialect.mir.mir_values import Constant, FunctionRef, Variable


class TestMIRValidation(unittest.TestCase):
    """Test MIR validation and verification."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.validator = MIRValidator()

    def test_valid_module(self) -> None:
        """Test validation of a valid module."""
        # Create valid module
        module = MIRModule("test_module")

        # Add main function
        main_func = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main_func.cfg.add_block(entry)
        main_func.cfg.entry_block = entry
        entry.add_instruction(Return())

        module.add_function(main_func)
        module.set_main_function("main")

        # Should validate successfully
        success, errors, warnings = validate_module(module)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

    def test_module_without_name(self) -> None:
        """Test validation fails for module without name."""
        module = MIRModule("")

        success, errors, warnings = validate_module(module)
        self.assertFalse(success)
        self.assertTrue(any("name" in error.lower() for error in errors))

    def test_module_with_invalid_main(self) -> None:
        """Test validation fails when main function doesn't exist."""
        module = MIRModule("test")
        module.set_main_function("nonexistent")

        success, errors, warnings = validate_module(module)
        self.assertFalse(success)
        self.assertTrue(any("main" in error.lower() and "not found" in error.lower() for error in errors))

    def test_function_name_mismatch(self) -> None:
        """Test validation fails when function name doesn't match."""
        func = MIRFunction("foo", [], MIRType.EMPTY)
        # Set up minimal valid CFG
        from machine_dialect.mir.basic_block import BasicBlock

        entry = BasicBlock("entry")
        from machine_dialect.mir.mir_instructions import Return

        entry.add_instruction(Return())
        func.cfg.entry_block = entry
        func.cfg.add_block(entry)

        # Validate with different name
        success, errors, warnings = validate_function(func)
        self.assertTrue(success)  # Should pass when validating directly

        # But fail when in module with wrong name
        module = MIRModule("test")
        module.functions["bar"] = func  # Wrong name in dict

        success, errors, warnings = validate_module(module)
        self.assertFalse(success)
        self.assertTrue(any("mismatch" in error.lower() for error in errors))

    def test_duplicate_parameters(self) -> None:
        """Test validation fails with duplicate parameter names."""
        # Create function with duplicate parameters
        param1 = Variable("x", MIRType.INT)
        param2 = Variable("x", MIRType.INT)  # Duplicate name

        func = MIRFunction("test", [param1, param2], MIRType.EMPTY)

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("duplicate" in error.lower() for error in errors))

    def test_cfg_without_entry(self) -> None:
        """Test validation fails when CFG has no entry block."""
        func = MIRFunction("test", [], MIRType.EMPTY)
        # Don't set entry block

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("entry" in error.lower() for error in errors))

    def test_inconsistent_cfg_edges(self) -> None:
        """Test validation fails with inconsistent CFG edges."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        block1 = BasicBlock("block1")
        block2 = BasicBlock("block2")

        func.cfg.add_block(block1)
        func.cfg.add_block(block2)
        func.cfg.entry_block = block1

        # Create inconsistent edge (only one direction)
        block1.successors.append(block2)
        # Don't add block1 to block2's predecessors

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("inconsistent" in error.lower() for error in errors))

    def test_unreachable_blocks_warning(self) -> None:
        """Test validation warns about unreachable blocks."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        unreachable = BasicBlock("unreachable")

        func.cfg.add_block(entry)
        func.cfg.add_block(unreachable)
        func.cfg.entry_block = entry

        entry.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertTrue(success)  # Should still pass
        self.assertTrue(any("unreachable" in warning.lower() for warning in warnings))

    def test_invalid_binary_operator(self) -> None:
        """Test validation fails with invalid binary operator."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        # Create binary op with invalid operator
        t1 = func.new_temp(MIRType.INT)
        t2 = func.new_temp(MIRType.INT)
        result = func.new_temp(MIRType.INT)

        entry.add_instruction(BinaryOp(result, "invalid_op", t1, t2))
        entry.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("invalid" in error.lower() and "operator" in error.lower() for error in errors))

    def test_jump_to_nonexistent_block(self) -> None:
        """Test validation fails with jump to nonexistent block."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        # Jump to block that doesn't exist
        entry.add_instruction(Jump("nonexistent"))

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("not found" in error.lower() for error in errors))

    def test_conditional_jump_validation(self) -> None:
        """Test validation of conditional jumps."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        then_block = BasicBlock("then")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.entry_block = entry

        cond = func.new_temp(MIRType.BOOL)

        # Invalid: false_label doesn't exist
        entry.add_instruction(ConditionalJump(cond, "then", "nonexistent"))

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("not found" in error.lower() for error in errors))

    def test_phi_node_validation(self) -> None:
        """Test validation of phi nodes."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create diamond CFG
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.entry_block = entry

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge)
        func.cfg.connect(else_block, merge)

        # Add terminators
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(ConditionalJump(cond, "then", "else"))
        then_block.add_instruction(Jump("merge"))
        else_block.add_instruction(Jump("merge"))

        # Add phi with wrong predecessor
        result = func.new_temp(MIRType.INT)
        val1 = Constant(1, MIRType.INT)
        val2 = Constant(2, MIRType.INT)

        # Invalid: "wrong_block" is not a predecessor
        phi = Phi(result, [(val1, "then"), (val2, "wrong_block")])
        merge.add_instruction(phi)
        merge.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertFalse(success)
        self.assertTrue(any("not a predecessor" in error.lower() for error in errors))

    def test_phi_missing_predecessor_warning(self) -> None:
        """Test warning for phi node missing predecessor."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create diamond CFG
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.entry_block = entry

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge)
        func.cfg.connect(else_block, merge)

        # Add terminators
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(ConditionalJump(cond, "then", "else"))
        then_block.add_instruction(Jump("merge"))
        else_block.add_instruction(Jump("merge"))

        # Phi missing value from "else"
        result = func.new_temp(MIRType.INT)
        val1 = Constant(1, MIRType.INT)
        phi = Phi(result, [(val1, "then")])  # Missing "else"
        merge.add_instruction(phi)
        merge.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertTrue(success)  # Should pass with warning
        self.assertTrue(any("missing" in warning.lower() for warning in warnings))

    def test_return_type_mismatch_warning(self) -> None:
        """Test warning for return type mismatch."""
        # Function that returns EMPTY but has return with value
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        val = func.new_temp(MIRType.INT)
        entry.add_instruction(Return(val))

        success, errors, warnings = validate_function(func)
        self.assertTrue(success)  # Should pass with warning
        self.assertTrue(any("return" in warning.lower() for warning in warnings))

    def test_block_with_successors_but_no_terminator(self) -> None:
        """Test warning for block with successors but no terminator."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        block1 = BasicBlock("block1")
        block2 = BasicBlock("block2")

        func.cfg.add_block(block1)
        func.cfg.add_block(block2)
        func.cfg.entry_block = block1
        func.cfg.connect(block1, block2)

        # block1 has successor but no jump instruction
        t = func.new_temp(MIRType.INT)
        block1.add_instruction(LoadConst(t, 1))
        # No terminator!

        block2.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertTrue(success)  # Should pass with warning
        self.assertTrue(any("terminator" in warning.lower() for warning in warnings))

    def test_call_validation(self) -> None:
        """Test validation of call instructions."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        # Valid call
        func_ref = FunctionRef("helper")
        arg = func.new_temp(MIRType.INT)
        result = func.new_temp(MIRType.INT)

        entry.add_instruction(Call(result, func_ref, [arg]))
        entry.add_instruction(Return())

        success, errors, warnings = validate_function(func)
        self.assertTrue(success)

    def test_complete_validation_integration(self) -> None:
        """Test complete validation of a complex module."""
        module = MIRModule("complex_module")

        # Add multiple functions
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.entry_block = entry

        # Call helper function
        helper_ref = FunctionRef("helper")
        arg = Constant(42, MIRType.INT)
        result = main.new_temp(MIRType.INT)
        entry.add_instruction(Call(result, helper_ref, [arg]))
        entry.add_instruction(Return())

        # Add helper function
        param = Variable("x", MIRType.INT)
        helper = MIRFunction("helper", [param], MIRType.INT)

        helper_entry = BasicBlock("entry")
        helper.cfg.add_block(helper_entry)
        helper.cfg.entry_block = helper_entry

        # Double the parameter
        doubled = helper.new_temp(MIRType.INT)
        two = Constant(2, MIRType.INT)
        helper_entry.add_instruction(BinaryOp(doubled, "*", param, two))
        helper_entry.add_instruction(Return(doubled))

        module.add_function(main)
        module.add_function(helper)
        module.set_main_function("main")

        # Should validate successfully
        success, errors, warnings = validate_module(module)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
