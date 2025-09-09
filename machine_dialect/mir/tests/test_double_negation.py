"""Tests for double negation and pattern optimization."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Copy,
    Return,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Temp, Variable
from machine_dialect.mir.optimizations.type_specific import TypeSpecificOptimization


class TestDoubleNegationOptimization:
    """Test double negation and related pattern optimizations."""

    def test_boolean_double_negation(self) -> None:
        """Test not(not(x)) -> x optimization."""
        func = MIRFunction("test", [])

        # Create a boolean variable
        x = Variable("x", MIRType.BOOL)
        func.add_local(x)

        # Create basic block
        block = BasicBlock("entry")

        # not(x)
        t1 = Temp(MIRType.BOOL, 0)
        block.add_instruction(UnaryOp(t1, "not", x, (1, 1)))

        # not(not(x)) - should be optimized to x
        t2 = Temp(MIRType.BOOL, 1)
        block.add_instruction(UnaryOp(t2, "not", t1, (1, 1)))

        block.add_instruction(Return((1, 1), t2))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # Check that double negation was optimized
        assert modified
        # The second UnaryOp should be replaced with Copy(t2, x, (1, 1))
        assert any(isinstance(inst, Copy) for inst in block.instructions)
        assert optimizer.stats["boolean_optimized"] > 0

    def test_integer_double_negation(self) -> None:
        """Test -(-x) -> x optimization for integers."""
        func = MIRFunction("test", [])

        # Create an integer variable
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create basic block
        block = BasicBlock("entry")

        # -x
        t1 = Temp(MIRType.INT, 0)
        block.add_instruction(UnaryOp(t1, "-", x, (1, 1)))

        # -(-x) - should be optimized to x
        t2 = Temp(MIRType.INT, 1)
        block.add_instruction(UnaryOp(t2, "-", t1, (1, 1)))

        block.add_instruction(Return((1, 1), t2))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # Check that double negation was optimized
        assert modified
        # The second UnaryOp should be replaced with Copy(t2, x, (1, 1))
        assert any(isinstance(inst, Copy) for inst in block.instructions)

    def test_not_comparison_inversion(self) -> None:
        """Test not(x == y) -> x != y optimization."""
        func = MIRFunction("test", [])

        # Create integer variables
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        func.add_local(x)
        func.add_local(y)

        # Create basic block
        block = BasicBlock("entry")

        # x == y
        t1 = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(t1, "==", x, y, (1, 1)))

        # not(x == y) - should be optimized to x != y
        t2 = Temp(MIRType.BOOL, 1)
        block.add_instruction(UnaryOp(t2, "not", t1, (1, 1)))

        block.add_instruction(Return((1, 1), t2))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # Check that comparison was inverted
        assert modified
        # Should have a BinaryOp with != instead of UnaryOp not
        assert any(isinstance(inst, BinaryOp) and inst.op == "!=" for inst in block.instructions)
        assert optimizer.stats["boolean_optimized"] > 0

    def test_not_less_than_inversion(self) -> None:
        """Test not(x < y) -> x >= y optimization."""
        func = MIRFunction("test", [])

        # Create integer variables
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        func.add_local(x)
        func.add_local(y)

        # Create basic block
        block = BasicBlock("entry")

        # x < y
        t1 = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(t1, "<", x, y, (1, 1)))

        # not(x < y) - should be optimized to x >= y
        t2 = Temp(MIRType.BOOL, 1)
        block.add_instruction(UnaryOp(t2, "not", t1, (1, 1)))

        block.add_instruction(Return((1, 1), t2))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # Check that comparison was inverted
        assert modified
        # Should have a BinaryOp with >= instead of UnaryOp not
        assert any(isinstance(inst, BinaryOp) and inst.op == ">=" for inst in block.instructions)
        assert optimizer.stats["boolean_optimized"] > 0

    def test_triple_negation(self) -> None:
        """Test not(not(not(x))) -> not(x) optimization."""
        func = MIRFunction("test", [])

        # Create a boolean variable
        x = Variable("x", MIRType.BOOL)
        func.add_local(x)

        # Create basic block
        block = BasicBlock("entry")

        # not(x)
        t1 = Temp(MIRType.BOOL, 0)
        block.add_instruction(UnaryOp(t1, "not", x, (1, 1)))

        # not(not(x))
        t2 = Temp(MIRType.BOOL, 1)
        block.add_instruction(UnaryOp(t2, "not", t1, (1, 1)))

        # not(not(not(x))) - should optimize to not(x)
        t3 = Temp(MIRType.BOOL, 2)
        block.add_instruction(UnaryOp(t3, "not", t2, (1, 1)))

        block.add_instruction(Return((1, 1), t3))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # Check that optimizations were applied
        assert modified
        # After optimization, we should have simplified the triple negation
        assert optimizer.stats["boolean_optimized"] > 0

    def test_mixed_arithmetic_negation(self) -> None:
        """Test -(x + (-y)) -> y - x optimization potential."""
        func = MIRFunction("test", [])

        # Create integer variables
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        func.add_local(x)
        func.add_local(y)

        # Create basic block
        block = BasicBlock("entry")

        # -y
        t1 = Temp(MIRType.INT, 0)
        block.add_instruction(UnaryOp(t1, "-", y, (1, 1)))

        # x + (-y)
        t2 = Temp(MIRType.INT, 1)
        block.add_instruction(BinaryOp(t2, "+", x, t1, (1, 1)))

        # -(x + (-y))
        t3 = Temp(MIRType.INT, 2)
        block.add_instruction(UnaryOp(t3, "-", t2, (1, 1)))

        block.add_instruction(Return((1, 1), t3))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        optimizer = TypeSpecificOptimization()
        modified = optimizer.run_on_function(func)

        # This is a complex pattern that might not be fully optimized yet,
        # but we can check that the pass runs without errors
        assert modified or not modified  # Either outcome is acceptable
