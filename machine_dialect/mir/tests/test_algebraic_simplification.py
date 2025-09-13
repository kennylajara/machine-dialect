"""Tests for algebraic simplification and strength reduction optimization passes."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Copy, LoadConst
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification
from machine_dialect.mir.optimizations.strength_reduction import StrengthReduction


class TestAlgebraicSimplificationComparison:
    """Test comparison operation simplifications in AlgebraicSimplification."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.module = MIRModule("test")
        self.func = MIRFunction("test_func", [], MIRType.BOOL)
        self.block = BasicBlock("entry")
        self.func.cfg.add_block(self.block)
        self.func.cfg.entry_block = self.block
        self.module.add_function(self.func)
        self.transformer = MIRTransformer(self.func)
        self.opt = AlgebraicSimplification()

    def test_equal_same_value(self) -> None:
        """Test x == x → true."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "==", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is True

    def test_not_equal_same_value(self) -> None:
        """Test x != x → false."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "!=", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is False

    def test_less_than_same_value(self) -> None:
        """Test x < x → false."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "<", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is False

    def test_greater_than_same_value(self) -> None:
        """Test x > x → false."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, ">", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is False

    def test_less_equal_same_value(self) -> None:
        """Test x <= x → true."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "<=", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is True

    def test_greater_equal_same_value(self) -> None:
        """Test x >= x → true."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, ">=", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("comparison_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is True

    def test_comparison_different_values_no_change(self) -> None:
        """Test that comparisons with different values are not simplified."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.BOOL)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(43, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "==", t0, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert not changed
        assert "comparison_simplified" not in self.opt.stats
        instructions = list(self.block.instructions)
        assert isinstance(instructions[2], BinaryOp)


class TestAlgebraicSimplificationBitwise:
    """Test bitwise operation simplifications in AlgebraicSimplification."""

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

    def test_and_with_zero(self) -> None:
        """Test x & 0 → 0."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "&", t0, Constant(0, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_and_with_self(self) -> None:
        """Test x & x → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "&", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_and_with_all_ones(self) -> None:
        """Test x & -1 → x (all ones)."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "&", t0, Constant(-1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_or_with_zero(self) -> None:
        """Test x | 0 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "|", t0, Constant(0, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_or_with_self(self) -> None:
        """Test x | x → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "|", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_or_with_all_ones(self) -> None:
        """Test x | -1 → -1 (all ones)."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "|", t0, Constant(-1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == -1

    def test_xor_with_zero(self) -> None:
        """Test x ^ 0 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "^", t0, Constant(0, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_xor_with_self(self) -> None:
        """Test x ^ x → 0."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "^", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("bitwise_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_left_shift_zero(self) -> None:
        """Test x << 0 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "<<", t0, Constant(0, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("shift_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_right_shift_zero(self) -> None:
        """Test x >> 0 → x."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, ">>", t0, Constant(0, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("shift_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0


class TestAlgebraicSimplificationModulo:
    """Test modulo operation simplifications in AlgebraicSimplification."""

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

    def test_modulo_one(self) -> None:
        """Test x % 1 → 0."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "%", t0, Constant(1, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("modulo_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_modulo_self(self) -> None:
        """Test x % x → 0."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "%", t0, t0, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("modulo_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_zero_modulo(self) -> None:
        """Test 0 % x → 0."""
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "%", Constant(0, MIRType.INT), Constant(42, MIRType.INT), (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("modulo_simplified") == 1
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_modulo_no_simplification(self) -> None:
        """Test that x % y with different values is not simplified."""
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(LoadConst(t1, Constant(5, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t2, "%", t0, t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert not changed
        assert "modulo_simplified" not in self.opt.stats
        instructions = list(self.block.instructions)
        assert isinstance(instructions[2], BinaryOp)


class TestAlgebraicSimplificationUnary:
    """Test unary operation simplifications in AlgebraicSimplification."""

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

    def test_double_negation(self) -> None:
        """Test -(-x) → x."""
        from machine_dialect.mir.mir_instructions import UnaryOp

        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.INT)

        # Create x = 42, t1 = -x, t2 = -t1
        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(UnaryOp(t1, "-", t0, (1, 1)))
        self.block.add_instruction(UnaryOp(t2, "-", t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("double_negation_eliminated") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t2, t0, (1, 1))
        assert isinstance(instructions[2], Copy)
        copy_inst = instructions[2]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t2

    def test_double_not(self) -> None:
        """Test not(not(x)) → x."""
        from machine_dialect.mir.mir_instructions import UnaryOp

        t0 = Temp(MIRType.BOOL)
        t1 = Temp(MIRType.BOOL)
        t2 = Temp(MIRType.BOOL)

        # Create x = true, t1 = not x, t2 = not t1
        self.block.add_instruction(LoadConst(t0, Constant(True, MIRType.BOOL), (1, 1)))
        self.block.add_instruction(UnaryOp(t1, "not", t0, (1, 1)))
        self.block.add_instruction(UnaryOp(t2, "not", t1, (1, 1)))

        changed = self.opt.run_on_function(self.func)

        assert changed
        assert self.opt.stats.get("double_not_eliminated") == 1
        instructions = list(self.block.instructions)
        # The last instruction should be Copy(t2, t0, (1, 1))
        assert isinstance(instructions[2], Copy)
        copy_inst = instructions[2]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0
        assert copy_inst.dest == t2


class TestAlgebraicSimplificationPower:
    """Test power operation simplifications in AlgebraicSimplification."""

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

    def test_power_zero_simplification(self) -> None:
        """Test x ** 0 → 1."""
        # Create: t0 = 5 ** 0 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(5, MIRType.INT), Constant(0, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 1
        assert changed
        assert self.opt.stats.get("power_simplified") == 1

        # Check that the power op was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 1

    def test_power_one_simplification(self) -> None:
        """Test x ** 1 → x."""
        # Create: t1 = t0 ** 1 where t0 is a temp with value 7
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(7, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "**", t0, Constant(1, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed
        assert self.opt.stats.get("power_simplified") == 1

        # Check that the power op was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_power_two_to_multiply(self) -> None:
        """Test x ** 2 → x * x."""
        # Create: t1 = t0 ** 2 where t0 is a temp
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(3, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "**", t0, Constant(2, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should convert to t1 = t0 * t0
        assert changed
        assert self.opt.stats.get("power_to_multiply") == 1

        # Check that the power op was replaced with multiply
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], BinaryOp)
        binary_inst = instructions[1]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "*"
        assert binary_inst.left == t0
        assert binary_inst.right == t0

    def test_zero_power_simplification(self) -> None:
        """Test 0 ** x → 0 (for x > 0)."""
        # Create: t0 = 0 ** 5 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(0, MIRType.INT), Constant(5, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 0
        assert changed
        assert self.opt.stats.get("power_simplified") == 1

        # Check that the power op was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_one_power_simplification(self) -> None:
        """Test 1 ** x → 1."""
        # Create: t0 = 1 ** 10 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(1, MIRType.INT), Constant(10, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 1
        assert changed
        assert self.opt.stats.get("power_simplified") == 1

        # Check that the power op was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 1

    def test_power_no_simplification(self) -> None:
        """Test that x ** 3 is not simplified (no rule for it)."""
        # Create: t0 = 2 ** 3 (using constants directly)
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "**", Constant(2, MIRType.INT), Constant(3, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should not change (no rule for x ** 3)
        assert not changed
        assert "power_simplified" not in self.opt.stats
        assert "power_to_multiply" not in self.opt.stats

        # The power op should still be there
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], BinaryOp)
        binary_inst = instructions[0]
        assert isinstance(binary_inst, BinaryOp)
        assert binary_inst.op == "**"


class TestStrengthReductionArithmetic:
    """Test arithmetic simplifications in StrengthReduction."""

    def setup_method(self) -> None:
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

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "+", t0, Constant(0, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed

        # Check that the add was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_multiply_by_zero(self) -> None:
        """Test x * 0 → 0 and 0 * x → 0."""
        # Test x * 0 with constant
        t0 = Temp(MIRType.INT)
        self.block.add_instruction(BinaryOp(t0, "*", Constant(42, MIRType.INT), Constant(0, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = 0
        assert changed

        # Check that the multiply was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_multiply_by_one(self) -> None:
        """Test x * 1 → x and 1 * x → x."""
        # Test x * 1 with temp and constant
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "*", t0, Constant(1, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed

        # Check that the multiply was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_subtract_self(self) -> None:
        """Test x - x → 0."""
        # Test t0 - t0
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "-", t0, t0, (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = 0
        assert changed

        # Check that the subtract was replaced with LoadConst(0)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 0

    def test_divide_by_one(self) -> None:
        """Test x / 1 → x."""
        # Test x / 1 with temp and constant
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, Constant(1, MIRType.INT), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed

        # Check that the divide was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_divide_self(self) -> None:
        """Test x / x → 1 (for x != 0)."""
        # Test t0 / t0
        t0 = Temp(MIRType.INT)
        t1 = Temp(MIRType.INT)

        self.block.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "/", t0, t0, (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = 1
        assert changed

        # Check that the divide was replaced with LoadConst(1)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], LoadConst)
        load_inst = instructions[1]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value == 1


class TestStrengthReductionBoolean:
    """Test boolean operation simplifications in StrengthReduction."""

    def setup_method(self) -> None:
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

        self.block.add_instruction(LoadConst(t0, Constant(False, MIRType.BOOL), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "and", t0, Constant(True, MIRType.BOOL), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed

        # Check that the and was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_and_with_false(self) -> None:
        """Test x and false → false."""
        # Test x and false with constant
        t0 = Temp(MIRType.BOOL)
        self.block.add_instruction(
            BinaryOp(t0, "and", Constant(True, MIRType.BOOL), Constant(False, MIRType.BOOL), (1, 1))
        )

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = false
        assert changed

        # Check that the and was replaced with LoadConst(False)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is False

    def test_or_with_false(self) -> None:
        """Test x or false → x."""
        # Test x or false with temp and constant
        t0 = Temp(MIRType.BOOL)
        t1 = Temp(MIRType.BOOL)

        self.block.add_instruction(LoadConst(t0, Constant(True, MIRType.BOOL), (1, 1)))
        self.block.add_instruction(BinaryOp(t1, "or", t0, Constant(False, MIRType.BOOL), (1, 1)))

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t1 = t0
        assert changed

        # Check that the or was replaced with Copy
        instructions = list(self.block.instructions)
        assert isinstance(instructions[1], Copy)
        copy_inst = instructions[1]
        assert isinstance(copy_inst, Copy)
        assert copy_inst.source == t0

    def test_or_with_true(self) -> None:
        """Test x or true → true."""
        # Test x or true with constant
        t0 = Temp(MIRType.BOOL)
        self.block.add_instruction(
            BinaryOp(t0, "or", Constant(False, MIRType.BOOL), Constant(True, MIRType.BOOL), (1, 1))
        )

        # Run optimization
        changed = self.opt.run_on_function(self.func)

        # Should simplify to t0 = true
        assert changed

        # Check that the or was replaced with LoadConst(True)
        instructions = list(self.block.instructions)
        assert isinstance(instructions[0], LoadConst)
        load_inst = instructions[0]
        assert isinstance(load_inst, LoadConst)
        assert load_inst.constant.value is True
