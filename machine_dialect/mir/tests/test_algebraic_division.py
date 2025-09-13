"""Tests for division optimizations in algebraic simplification."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Copy, LoadConst, UnaryOp
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification


class TestAlgebraicSimplificationDivision:
    """Test division operation simplifications."""

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

    def test_divide_by_one(self) -> None:
        """Test x / 1 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_divide_self(self) -> None:
        """Test x / x → 1."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 1

    def test_zero_divided_by_x(self) -> None:
        """Test 0 / x → 0."""
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "/", Constant(0, MIRType.INT), Constant(42, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_divide_by_negative_one(self) -> None:
        """Test x / -1 → -x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(-1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], UnaryOp)
        unary_inst = instructions[1]
        assert isinstance(unary_inst, UnaryOp)
        assert unary_inst.op == "-"
        assert unary_inst.operand == t0

    def test_integer_divide_by_one(self) -> None:
        """Test x // 1 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "//", t0, Constant(1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_integer_divide_self(self) -> None:
        """Test x // x → 1."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "//", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("division_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 1
