"""Tests for associativity and commutativity optimizations in algebraic simplification."""

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification


class TestAlgebraicAssociativity(unittest.TestCase):
    """Test associativity and commutativity optimizations."""

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

    def test_addition_associativity_left(self) -> None:
        """Test (a + 2) + 3 → a + 5."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # t0 = x, t1 = t0 + 2, t2 = t1 + 3
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "+", t0, Constant(2, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "+", t1, Constant(3, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("associativity_applied", 0), 1)
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "+", t0, Constant(5, (1, 1)))
        self.assertIsInstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "+")
        self.assertEqual(binary_inst.left, t0)
        self.assertIsInstance(binary_inst.right, Constant)
        assert isinstance(binary_inst.right, Constant)
        self.assertEqual(binary_inst.right.value, 5)

    def test_multiplication_associativity_left(self) -> None:
        """Test (a * 2) * 3 → a * 6."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # t0 = x, t1 = t0 * 2, t2 = t1 * 3
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "*", t0, Constant(2, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "*", t1, Constant(3, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("associativity_applied", 0), 1)
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "*", t0, Constant(6, (1, 1)))
        self.assertIsInstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "*")
        self.assertEqual(binary_inst.left, t0)
        self.assertIsInstance(binary_inst.right, Constant)
        assert isinstance(binary_inst.right, Constant)
        self.assertEqual(binary_inst.right.value, 6)

    def test_addition_commutativity_right(self) -> None:
        """Test 3 + (a + 2) → 5 + a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # t0 = x, t1 = t0 + 2, t2 = 3 + t1
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "+", t0, Constant(2, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "+", Constant(3, MIRType.INT), t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("associativity_applied", 0), 1)
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "+", Constant(5), t0)
        self.assertIsInstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "+")
        self.assertIsInstance(binary_inst.left, Constant)
        assert isinstance(binary_inst.left, Constant)
        self.assertEqual(binary_inst.left.value, 5)
        self.assertEqual(binary_inst.right, t0)

    def test_multiplication_commutativity_right(self) -> None:
        """Test 3 * (a * 2) → 6 * a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # t0 = x, t1 = t0 * 2, t2 = 3 * t1
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "*", t0, Constant(2, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "*", Constant(3, MIRType.INT), t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        self.assertTrue(changed)
        self.assertEqual(self.opt.stats.get("associativity_applied", 0), 1)
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "*", Constant(6), t0)
        self.assertIsInstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.op, "*")
        self.assertIsInstance(binary_inst.left, Constant)
        assert isinstance(binary_inst.left, Constant)
        self.assertEqual(binary_inst.left.value, 6)
        self.assertEqual(binary_inst.right, t0)

    def test_nested_addition_associativity(self) -> None:
        """Test ((a + 1) + 2) + 3 → a + 6 in a single pass."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # t0 = x, t1 = t0 + 1, t2 = t1 + 2, t3 = t2 + 3
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "+", t0, Constant(1, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "+", t1, Constant(2, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "+", t2, Constant(3, MIRType.INT), (1, 1)))

        # Run optimization - should fold nested additions in single pass
        changed = self.opt.run_on_function(self.func)
        self.assertTrue(changed)

        # Should have applied associativity at least twice
        self.assertGreaterEqual(self.opt.stats.get("associativity_applied", 0), 2)

        instructions = list(self.block.instructions)

        # Verify t2 = t0 + 3 (folded 1 + 2)
        t2_inst = instructions[2]
        self.assertIsInstance(t2_inst, BinaryOp)
        assert isinstance(t2_inst, BinaryOp)
        self.assertEqual(t2_inst.op, "+")
        self.assertEqual(t2_inst.left, t0)
        self.assertIsInstance(t2_inst.right, Constant)
        assert isinstance(t2_inst.right, Constant)
        self.assertEqual(t2_inst.right.value, 3)

        # Verify t3 = t0 + 6 (folded 3 + 3)
        t3_inst = instructions[3]
        self.assertIsInstance(t3_inst, BinaryOp)
        assert isinstance(t3_inst, BinaryOp)
        self.assertEqual(t3_inst.op, "+")
        self.assertEqual(t3_inst.left, t0)
        self.assertIsInstance(t3_inst.right, Constant)
        assert isinstance(t3_inst.right, Constant)
        self.assertEqual(t3_inst.right.value, 6)

        # Verify second pass finds nothing to optimize (fixed point reached)
        self.opt.stats.clear()
        changed = self.opt.run_on_function(self.func)
        self.assertFalse(changed, "Second pass should find nothing to optimize")

    def test_no_associativity_without_constants(self) -> None:
        """Test that (a + b) + c doesn't change without constants."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)
        t4 = Temp(MIRType.INT)

        # All variables, no constants
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(20, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t2, Constant(30, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "+", t0, t1, (1, 1)))
        self.block.add_instruction(BinaryOp(t4, "+", t3, t2, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        # Should not apply associativity since there are no constant pairs to fold
        self.assertFalse(changed)
        self.assertEqual(self.opt.stats.get("associativity_applied", 0), 0)
        instructions = list(self.block.instructions)
        # Last instruction should remain unchanged
        self.assertIsInstance(instructions[4], BinaryOp)
        binary_inst = instructions[4]
        assert isinstance(binary_inst, BinaryOp)
        self.assertEqual(binary_inst.left, t3)
        self.assertEqual(binary_inst.right, t2)


if __name__ == "__main__":
    unittest.main()
