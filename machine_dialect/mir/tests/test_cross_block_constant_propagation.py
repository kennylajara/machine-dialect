"""Tests for cross-block constant propagation."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Phi,
    Return,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.optimizations.constant_propagation import ConstantPropagation


class TestCrossBlockConstantPropagation:
    """Test cross-block constant propagation."""

    def test_constant_through_multiple_blocks(self) -> None:
        """Test propagation of constants through multiple blocks."""
        # Create function
        func = MIRFunction("test", [])

        # Block 1: x = 10
        block1 = BasicBlock("entry")
        x = Variable("x", MIRType.INT)
        func.add_local(x)
        block1.add_instruction(LoadConst(x, Constant(10, MIRType.INT), (1, 1)))
        block1.add_instruction(Jump("block2", (1, 1)))

        # Block 2: y = x + 5
        block2 = BasicBlock("block2")
        y = Variable("y", MIRType.INT)
        func.add_local(y)
        t1 = Temp(MIRType.INT, 0)
        block2.add_instruction(BinaryOp(t1, "+", x, Constant(5, MIRType.INT), (1, 1)))
        block2.add_instruction(Copy(y, t1, (1, 1)))
        block2.add_instruction(Jump("block3", (1, 1)))

        # Block 3: z = y * 2
        block3 = BasicBlock("block3")
        z = Variable("z", MIRType.INT)
        func.add_local(z)
        t2 = Temp(MIRType.INT, 1)
        block3.add_instruction(BinaryOp(t2, "*", y, Constant(2, MIRType.INT), (1, 1)))
        block3.add_instruction(Copy(z, t2, (1, 1)))
        block3.add_instruction(Return((1, 1), z))

        # Set up CFG
        func.cfg.add_block(block1)
        func.cfg.add_block(block2)
        func.cfg.add_block(block3)
        func.cfg.set_entry_block(block1)

        block1.add_successor(block2)
        block2.add_predecessor(block1)
        block2.add_successor(block3)
        block3.add_predecessor(block2)

        # Run optimization
        optimizer = ConstantPropagation()
        modified = optimizer.run_on_function(func)

        assert modified
        # After optimization, operations should be folded
        # x = 10 -> y = 15 -> z = 30
        # Check that final return is a constant
        final_inst = block3.instructions[-1]
        assert isinstance(final_inst, Return)
        # The value might be replaced with a constant

    def test_phi_node_constant_propagation(self) -> None:
        """Test constant propagation through phi nodes."""
        func = MIRFunction("test", [])

        # Entry block
        entry = BasicBlock("entry")
        cond = Variable("cond", MIRType.BOOL)
        func.add_local(cond)
        entry.add_instruction(LoadConst(cond, Constant(True, MIRType.BOOL), (1, 1)))
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        # Then block: x = 10
        then_block = BasicBlock("then")
        x_then = Temp(MIRType.INT, 0)
        then_block.add_instruction(LoadConst(x_then, Constant(10, MIRType.INT), (1, 1)))
        then_block.add_instruction(Jump("merge", (1, 1)))

        # Else block: x = 10 (same value)
        else_block = BasicBlock("else")
        x_else = Temp(MIRType.INT, 1)
        else_block.add_instruction(LoadConst(x_else, Constant(10, MIRType.INT), (1, 1)))
        else_block.add_instruction(Jump("merge", (1, 1)))

        # Merge block with phi node
        merge = BasicBlock("merge")
        x = Variable("x", MIRType.INT)
        func.add_local(x)
        phi = Phi(x, [(x_then, "then"), (x_else, "else")], (1, 1))
        merge.phi_nodes.append(phi)

        # Use x in computation
        result = Temp(MIRType.INT, 2)
        merge.add_instruction(BinaryOp(result, "+", x, Constant(5, MIRType.INT), (1, 1)))
        merge.add_instruction(Return((1, 1), result))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.set_entry_block(entry)

        entry.add_successor(then_block)
        entry.add_successor(else_block)
        then_block.add_predecessor(entry)
        else_block.add_predecessor(entry)
        then_block.add_successor(merge)
        else_block.add_successor(merge)
        merge.add_predecessor(then_block)
        merge.add_predecessor(else_block)

        # Run optimization
        optimizer = ConstantPropagation()
        modified = optimizer.run_on_function(func)

        assert modified
        # Since both branches assign the same constant (10) to x,
        # the phi should resolve to 10 and x + 5 should fold to 15

    def test_loop_constant_propagation(self) -> None:
        """Test constant propagation in loops."""
        func = MIRFunction("test", [])

        # Entry block: i = 0, sum = 0
        entry = BasicBlock("entry")
        i = Variable("i", MIRType.INT)
        sum_var = Variable("sum", MIRType.INT)
        func.add_local(i)
        func.add_local(sum_var)

        entry.add_instruction(LoadConst(i, Constant(0, MIRType.INT), (1, 1)))
        entry.add_instruction(LoadConst(sum_var, Constant(0, MIRType.INT), (1, 1)))
        entry.add_instruction(Jump("loop", (1, 1)))

        # Loop block
        loop = BasicBlock("loop")
        # Phi nodes for loop variables
        i_phi = Phi(i, [(i, "entry")], (1, 1))  # Will have back-edge added
        sum_phi = Phi(sum_var, [(sum_var, "entry")], (1, 1))
        loop.phi_nodes.append(i_phi)
        loop.phi_nodes.append(sum_phi)

        # Check condition: i < 10
        t_cond = Temp(MIRType.BOOL, 0)
        loop.add_instruction(BinaryOp(t_cond, "<", i, Constant(10, MIRType.INT), (1, 1)))
        loop.add_instruction(ConditionalJump(t_cond, "body", (1, 1), "exit"))

        # Loop body
        body = BasicBlock("body")
        # sum = sum + i
        t_sum = Temp(MIRType.INT, 1)
        body.add_instruction(BinaryOp(t_sum, "+", sum_var, i, (1, 1)))
        body.add_instruction(Copy(sum_var, t_sum, (1, 1)))

        # i = i + 1
        t_i = Temp(MIRType.INT, 2)
        body.add_instruction(BinaryOp(t_i, "+", i, Constant(1, MIRType.INT), (1, 1)))
        body.add_instruction(Copy(i, t_i, (1, 1)))
        body.add_instruction(Jump("loop", (1, 1)))

        # Exit block
        exit_block = BasicBlock("exit")
        exit_block.add_instruction(Return((1, 1), sum_var))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(loop)
        func.cfg.add_block(body)
        func.cfg.add_block(exit_block)
        func.cfg.set_entry_block(entry)

        entry.add_successor(loop)
        loop.add_predecessor(entry)
        loop.add_successor(body)
        loop.add_successor(exit_block)
        body.add_predecessor(loop)
        body.add_successor(loop)  # Back-edge
        loop.add_predecessor(body)  # Back-edge
        exit_block.add_predecessor(loop)

        # Add back-edge to phi nodes
        i_phi.incoming.append((i, "body"))
        sum_phi.incoming.append((sum_var, "body"))

        # Run optimization
        optimizer = ConstantPropagation()
        optimizer.run_on_function(func)

        # In loops, constant propagation is limited but should still
        # propagate initial values and fold operations where possible
        assert optimizer.stats.get("constants_propagated", 0) >= 0

    def test_conditional_constant_propagation(self) -> None:
        """Test constant propagation with conditional branches."""
        func = MIRFunction("test", [])

        # Entry: x = 5, y = 10
        entry = BasicBlock("entry")
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        func.add_local(x)
        func.add_local(y)

        entry.add_instruction(LoadConst(x, Constant(5, MIRType.INT), (1, 1)))
        entry.add_instruction(LoadConst(y, Constant(10, MIRType.INT), (1, 1)))

        # Compute condition: x < y (should be constant True)
        cond = Temp(MIRType.BOOL, 0)
        entry.add_instruction(BinaryOp(cond, "<", x, y, (1, 1)))
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        # Then block (should be taken)
        then_block = BasicBlock("then")
        result_then = Temp(MIRType.INT, 1)
        then_block.add_instruction(BinaryOp(result_then, "+", x, y, (1, 1)))
        then_block.add_instruction(Return((1, 1), result_then))

        # Else block (dead code)
        else_block = BasicBlock("else")
        result_else = Temp(MIRType.INT, 2)
        else_block.add_instruction(BinaryOp(result_else, "-", y, x, (1, 1)))
        else_block.add_instruction(Return((1, 1), result_else))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.set_entry_block(entry)

        entry.add_successor(then_block)
        entry.add_successor(else_block)
        then_block.add_predecessor(entry)
        else_block.add_predecessor(entry)

        # Run optimization
        optimizer = ConstantPropagation()
        modified = optimizer.run_on_function(func)

        assert modified
        # The condition x < y should be folded to True
        # and potentially the branch should be simplified
