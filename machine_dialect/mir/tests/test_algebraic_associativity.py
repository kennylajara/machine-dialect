"""Tests for associativity and commutativity optimizations in algebraic simplification."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification


class TestAlgebraicAssociativity:
    """Test associativity and commutativity optimizations."""

    def setup_method(self) -> None:
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

        assert changed
        assert self.opt.stats.get("associativity_applied") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "+", t0, Constant(5, (1, 1)))
        assert isinstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "+"
        assert binary_inst.left == t0
        assert isinstance(binary_inst.right, Constant)
        assert isinstance(binary_inst.right, Constant)
        assert binary_inst.right.value == 5

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

        assert changed
        assert self.opt.stats.get("associativity_applied") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "*", t0, Constant(6, (1, 1)))
        assert isinstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "*"
        assert binary_inst.left == t0
        assert isinstance(binary_inst.right, Constant)
        assert isinstance(binary_inst.right, Constant)
        assert binary_inst.right.value == 6

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

        assert changed
        assert self.opt.stats.get("associativity_applied") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "+", Constant(5), t0)
        assert isinstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "+"
        assert isinstance(binary_inst.left, Constant)
        assert isinstance(binary_inst.left, Constant)
        assert binary_inst.left.value == 5
        assert binary_inst.right == t0

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

        assert changed
        assert self.opt.stats.get("associativity_applied") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "*", Constant(6), t0)
        assert isinstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "*"
        assert isinstance(binary_inst.left, Constant)
        assert isinstance(binary_inst.left, Constant)
        assert binary_inst.left.value == 6
        assert binary_inst.right == t0

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
        assert changed

        # Should have applied associativity at least twice
        assert self.opt.stats.get("associativity_applied", 0) >= 2

        instructions = list(self.block.instructions)

        # Verify t2 = t0 + 3 (folded 1 + 2)
        t2_inst = instructions[2]
        assert isinstance(t2_inst, BinaryOp)
        assert isinstance(t2_inst, BinaryOp)
        assert t2_inst.op == "+"
        assert t2_inst.left == t0
        assert isinstance(t2_inst.right, Constant)
        assert isinstance(t2_inst.right, Constant)
        assert t2_inst.right.value == 3

        # Verify t3 = t0 + 6 (folded 3 + 3)
        t3_inst = instructions[3]
        assert isinstance(t3_inst, BinaryOp)
        assert isinstance(t3_inst, BinaryOp)
        assert t3_inst.op == "+"
        assert t3_inst.left == t0
        assert isinstance(t3_inst.right, Constant)
        assert isinstance(t3_inst.right, Constant)
        assert t3_inst.right.value == 6

        # Verify second pass finds nothing to optimize (fixed point reached)
        self.opt.stats.clear()
        changed = self.opt.run_on_function(self.func)
        assert not changed, "Second pass should find nothing to optimize"

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
        assert not changed
        assert "associativity_applied" not in self.opt.stats
        instructions = list(self.block.instructions)
        # Last instruction should remain unchanged
        assert isinstance(instructions[4], BinaryOp)
        binary_inst = instructions[4]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.left == t3
        assert binary_inst.right == t2
