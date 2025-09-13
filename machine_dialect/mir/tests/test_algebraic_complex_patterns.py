"""Tests for complex pattern matching in algebraic simplification."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Copy, LoadConst, UnaryOp
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification


class TestAlgebraicComplexPatterns:
    """Test complex pattern matching in algebraic simplification."""

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

    def test_add_then_subtract_pattern(self) -> None:
        """Test (a + b) - b → a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = a + b, t3 = t2 - b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "-", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3

    def test_subtract_then_add_pattern(self) -> None:
        """Test (a - b) + b → a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = a - b, t3 = t2 + b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "-", t0, t1, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "+", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3

    def test_multiply_then_divide_pattern(self) -> None:
        """Test (a * b) / b → a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = a * b, t3 = t2 / b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "*", t0, t1, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "/", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3

    def test_divide_then_multiply_pattern(self) -> None:
        """Test (a / b) * b → a."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = a / b, t3 = t2 * b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "/", t0, t1, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "*", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3

    def test_zero_minus_x_pattern(self) -> None:
        """Test 0 - x → -x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "-", Constant(0, MIRType.INT), t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], UnaryOp)
        unary_inst = instructions[1]
        assert isinstance(unary_inst, UnaryOp)
        assert unary_inst.op == "-"
        assert unary_inst.operand == t0
        assert unary_inst.dest == t1

    def test_chained_subtraction_constants(self) -> None:
        """Test (a - b) - c → a - (b + c) when b and c are constants."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # a = t0, t1 = a - 3, t2 = t1 - 2 → t2 = a - 5
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "-", t0, Constant(3, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "-", t1, Constant(2, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be BinaryOp(t2, "-", t0, Constant(5, (1, 1)))
        assert isinstance(instructions[2], BinaryOp)
        binary_inst = instructions[2]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "-"
        assert binary_inst.left == t0
        assert isinstance(binary_inst.right, Constant)
        assert isinstance(binary_inst.right, Constant)
        assert binary_inst.right.value == 5

    def test_commutative_add_subtract_pattern(self) -> None:
        """Test (b + a) - b → a (commutative version)."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = b + a, t3 = t2 - b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "+", t1, t0, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "-", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3

    def test_commutative_multiply_divide_pattern(self) -> None:
        """Test (b * a) / b → a (commutative version)."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        t3 = Temp(MIRType.INT)

        # a = 10, b = 5, t2 = b * a, t3 = t2 / b
        self.block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "*", t1, t0, (1, 1)))
        self.block.add_instruction(BinaryOp(t3, "/", t2, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("complex_pattern_matched") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t3, t0, (1, 1))
        assert isinstance(instructions[3], Copy)
        copy_inst = instructions[3]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t3
