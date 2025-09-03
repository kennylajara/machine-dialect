"""Tests for division optimizations in algebraic simplification."""

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Copy, LoadConst, UnaryOp
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification


class TestAlgebraicSimplificationDivision(unittest.TestCase):
    """Test division operation simplifications."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.module = MIRModule("test")
        self.func = MIRFunction("test_func", [], MIRType.INT)
        self.block = BasicBlock("entry")
        self.func.cfg.add_block(self.block)
        self.func.cfg.entry_block = self.block
        self.module.add_function(self.func)
        self.transformer = MIRTransformer(self.func)
        self.opt = AlgebraicSimplification()

    def test_divide_by_one(self) -> None:
        """Test x / 1 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(1, MIRType.INT)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_divide_self(self) -> None:
        """Test x / x → 1."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, t0))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 1)

    def test_zero_divided_by_x(self) -> None:
        """Test 0 / x → 0."""
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "/", Constant(0, MIRType.INT), Constant(42, MIRType.INT)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 0)

    def test_divide_by_negative_one(self) -> None:
        """Test x / -1 → -x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(-1, MIRType.INT)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], UnaryOp)
        unary_inst = instructions[1]
        assert isinstance(unary_inst, UnaryOp)
        self.assertEqual(unary_inst.op, "-")
        self.assertEqual(unary_inst.operand, t0)

    def test_integer_divide_by_one(self) -> None:
        """Test x // 1 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "//", t0, Constant(1, MIRType.INT)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_integer_divide_self(self) -> None:
        """Test x // x → 1."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "//", t0, t0))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("division_simplified", 0), 1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 1)


if __name__ == "__main__":
    unittest.main()
