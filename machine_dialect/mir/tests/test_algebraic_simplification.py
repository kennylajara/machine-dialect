"""Tests for algebraic simplification and strength reduction optimization passes."""

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Copy, LoadConst
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification
from machine_dialect.mir.optimizations.strength_reduction import StrengthReduction


class TestAlgebraicSimplificationPower(unittest.TestCase):
    """Test power operation simplifications in AlgebraicSimplification."""

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

    def test_power_zero_simplification(self) -> None:
        """Test x ** 0 → 1."""
        # Create: t0 = 5 ** 0 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(5, MIRType.INT), Constant(0, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 1
        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("power_simplified", 0), 1)

        # Check that the power op was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 1)

    def test_power_one_simplification(self) -> None:
        """Test x ** 1 → x."""
        # Create: t1 = t0 ** 1 where t0 is a temp with value 7
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(7, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "**", t0, Constant(1, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("power_simplified", 0), 1)

        # Check that the power op was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_power_two_to_multiply(self) -> None:
        """Test x ** 2 → x * x."""
        # Create: t1 = t0 ** 2 where t0 is a temp
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(3, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "**", t0, Constant(2, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should convert to t1 = t0 * t0
        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("power_to_multiply", 0), 1)

        # Check that the power op was replaced with multiply
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], BinaryOp)
        binary_inst = instructions[1]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "*")
        self.assertEqual(binary_inst.left, t0)
        self.assertEqual(binary_inst.right, t0)

    def test_zero_power_simplification(self) -> None:
        """Test 0 ** x → 0 (for x > 0)."""
        # Create: t0 = 0 ** 5 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(0, MIRType.INT), Constant(5, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 0
        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("power_simplified", 0), 1)

        # Check that the power op was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 0)

    def test_one_power_simplification(self) -> None:
        """Test 1 ** x → 1."""
        # Create: t0 = 1 ** 10 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(1, MIRType.INT), Constant(10, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 1
        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("power_simplified", 0), 1)

        # Check that the power op was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 1)

    def test_power_no_simplification(self) -> None:
        """Test that x ** 3 is not simplified (no rule for it)."""
        # Create: t0 = 2 ** 3 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(2, MIRType.INT), Constant(3, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should not change (no rule for x ** 3)
        self.assertFalse(changed)
        self.assertEqual(self.opt.stats.get("power_simplified", 0), 0)
        self.assertEqual(self.opt.stats.get("power_to_multiply", 0), 0)

        # The power op should still be there
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], BinaryOp)
        binary_inst = instructions[0]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "**")


class TestStrengthReductionArithmetic(unittest.TestCase):
    """Test arithmetic simplifications in StrengthReduction."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.module = MIRModule("test")
        self.func = MIRFunction("test_func", [], MIRType.INT)
        self.block = BasicBlock("entry")
        self.func.cfg.add_block(self.block)
        self.func.cfg.entry_block = self.block
        self.module.add_function(self.func)
        self.transformer = MIRTransformer(self.func)
        self.opt = StrengthReduction()

    def test_add_zero_simplification(self) -> None:
        """Test x + 0 → x and 0 + x → x."""
        # Test x + 0 with temp and constant
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "+", t0, Constant(0, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)

        # Check that the add was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_multiply_by_zero(self) -> None:
        """Test x * 0 → 0 and 0 * x → 0."""
        # Test x * 0 with constant
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "*", Constant(42, MIRType.INT), Constant(0, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 0
        self.assertTrue(changed)

        # Check that the multiply was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 0)

    def test_multiply_by_one(self) -> None:
        """Test x * 1 → x and 1 * x → x."""
        # Test x * 1 with temp and constant
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "*", t0, Constant(1, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)

        # Check that the multiply was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_subtract_self(self) -> None:
        """Test x - x → 0."""
        # Test t0 - t0
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "-", t0, t0))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = 0
        self.assertTrue(changed)

        # Check that the subtract was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 0)

    def test_divide_by_one(self) -> None:
        """Test x / 1 → x."""
        # Test x / 1 with temp and constant
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(1, MIRType.INT)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)

        # Check that the divide was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_divide_self(self) -> None:
        """Test x / x → 1 (for x != 0)."""
        # Test t0 / t0
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, t0))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = 1
        self.assertTrue(changed)

        # Check that the divide was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, 1)


class TestStrengthReductionBoolean(unittest.TestCase):
    """Test boolean operation simplifications in StrengthReduction."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.module = MIRModule("test")
        self.func = MIRFunction("test_func", [], MIRType.BOOL)
        self.block = BasicBlock("entry")
        self.func.cfg.add_block(self.block)
        self.func.cfg.entry_block = self.block
        self.module.add_function(self.func)
        self.transformer = MIRTransformer(self.func)
        self.opt = StrengthReduction()

    def test_and_with_true(self) -> None:
        """Test x and true → x."""
        # Test x and true with temp and constant
        t0 = Temp(MIRType.BOOL)
        t1 = Temp(MIRType.BOOL)

        self.block.add_instruction(LoadConst(t0, Constant(False, MIRType.BOOL)))
        self.block.add_instruction(BinaryOp(t1, "and", t0, Constant(True, MIRType.BOOL)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)

        # Check that the and was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_and_with_false(self) -> None:
        """Test x and false → false."""
        # Test x and false with constant
        t0 = Temp(MIRType.BOOL)
        self.block.add_instruction(BinaryOp(t0, "and", Constant(True, MIRType.BOOL), Constant(False, MIRType.BOOL)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = false
        self.assertTrue(changed)

        # Check that the and was replaced with LoadConst(False)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, False)

    def test_or_with_false(self) -> None:
        """Test x or false → x."""
        # Test x or false with temp and constant
        t0 = Temp(MIRType.BOOL)
        t1 = Temp(MIRType.BOOL)

        self.block.add_instruction(LoadConst(t0, Constant(True, MIRType.BOOL)))
        self.block.add_instruction(BinaryOp(t1, "or", t0, Constant(False, MIRType.BOOL)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        self.assertTrue(changed)

        # Check that the or was replaced with Copy
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        self.assertEqual(copy_inst.source, t0)

    def test_or_with_true(self) -> None:
        """Test x or true → true."""
        # Test x or true with constant
        t0 = Temp(MIRType.BOOL)
        self.block.add_instruction(BinaryOp(t0, "or", Constant(False, MIRType.BOOL), Constant(True, MIRType.BOOL)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = true
        self.assertTrue(changed)

        # Check that the or was replaced with LoadConst(True)
        instructions = list(self.block.instructions)
        self.assertIsInstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        self.assertEqual(load_inst.constant.value, True)


if __name__ == "__main__":
    unittest.main()
