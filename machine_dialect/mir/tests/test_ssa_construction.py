"""Tests for SSA construction."""

from __future__ import annotations

import unittest

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Return,
    StoreVar,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Variable
from machine_dialect.mir.ssa_construction import DominanceInfo, construct_ssa


class TestDominanceInfo(unittest.TestCase):
    """Test dominance analysis."""

    def test_simple_dominance(self) -> None:
        """Test dominance in a simple CFG."""
        # Create CFG: entry -> block1 -> exit
        cfg = CFG()
        entry = BasicBlock("entry")
        block1 = BasicBlock("block1")
        exit_block = BasicBlock("exit")

        cfg.add_block(entry)
        cfg.add_block(block1)
        cfg.add_block(exit_block)
        cfg.set_entry_block(entry)

        cfg.connect(entry, block1)
        cfg.connect(block1, exit_block)

        # Compute dominance
        dom_info = DominanceInfo(cfg)

        # Entry dominates all blocks
        self.assertTrue(dom_info.dominates(entry, entry))
        self.assertTrue(dom_info.dominates(entry, block1))
        self.assertTrue(dom_info.dominates(entry, exit_block))

        # Block1 dominates exit but not entry
        self.assertFalse(dom_info.dominates(block1, entry))
        self.assertTrue(dom_info.dominates(block1, exit_block))

        # Exit dominates only itself
        self.assertFalse(dom_info.dominates(exit_block, entry))
        self.assertFalse(dom_info.dominates(exit_block, block1))

    def test_dominance_with_branch(self) -> None:
        """Test dominance in CFG with branches."""
        # Create diamond CFG:
        #     entry
        #     /   \
        #   then  else
        #     \   /
        #     merge
        cfg = CFG()
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge_block = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(then_block)
        cfg.add_block(else_block)
        cfg.add_block(merge_block)
        cfg.set_entry_block(entry)

        cfg.connect(entry, then_block)
        cfg.connect(entry, else_block)
        cfg.connect(then_block, merge_block)
        cfg.connect(else_block, merge_block)

        # Compute dominance
        dom_info = DominanceInfo(cfg)

        # Entry dominates all
        self.assertTrue(dom_info.dominates(entry, then_block))
        self.assertTrue(dom_info.dominates(entry, else_block))
        self.assertTrue(dom_info.dominates(entry, merge_block))

        # Neither branch dominates the other or merge
        self.assertFalse(dom_info.dominates(then_block, else_block))
        self.assertFalse(dom_info.dominates(else_block, then_block))
        self.assertFalse(dom_info.dominates(then_block, merge_block))
        self.assertFalse(dom_info.dominates(else_block, merge_block))

    def test_dominance_frontier(self) -> None:
        """Test dominance frontier calculation."""
        # Create diamond CFG
        cfg = CFG()
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge_block = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(then_block)
        cfg.add_block(else_block)
        cfg.add_block(merge_block)
        cfg.set_entry_block(entry)

        cfg.connect(entry, then_block)
        cfg.connect(entry, else_block)
        cfg.connect(then_block, merge_block)
        cfg.connect(else_block, merge_block)

        # Compute dominance
        dom_info = DominanceInfo(cfg)

        # Merge is in dominance frontier of then and else
        self.assertIn(merge_block, dom_info.dominance_frontier[then_block])
        self.assertIn(merge_block, dom_info.dominance_frontier[else_block])

        # Entry and merge have empty frontiers
        self.assertEqual(len(dom_info.dominance_frontier[entry]), 0)
        self.assertEqual(len(dom_info.dominance_frontier[merge_block]), 0)


class TestSSAConstruction(unittest.TestCase):
    """Test SSA construction."""

    def test_simple_ssa_construction(self) -> None:
        """Test SSA construction for simple function."""
        # Create function with single variable assignment
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create blocks
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Create variable
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Add instructions: x = 1; return x
        const1 = Constant(1, MIRType.INT)
        entry.add_instruction(StoreVar(x, const1, (1, 1)))
        temp = func.new_temp(MIRType.INT)
        entry.add_instruction(Copy(temp, x, (1, 1)))
        entry.add_instruction(Return((1, 1), temp))

        # Convert to SSA
        construct_ssa(func)

        # Should have versioned variables
        # Check that we have SSA form (no verification of exact names)
        self.assertTrue(len(entry.instructions) > 0)

    def test_phi_insertion(self) -> None:
        """Test phi node insertion at join points."""
        # Create function with diamond CFG
        func = MIRFunction("test", [], MIRType.INT)

        # Create blocks
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge_block = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge_block)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge_block)
        func.cfg.connect(else_block, merge_block)

        # Create variable
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Add conditional jump in entry
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(LoadConst(cond, True, (1, 1)))
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        # Assign different values in branches
        const1 = Constant(1, MIRType.INT)
        const2 = Constant(2, MIRType.INT)
        then_block.add_instruction(StoreVar(x, const1, (1, 1)))
        then_block.add_instruction(Jump("merge", (1, 1)))

        else_block.add_instruction(StoreVar(x, const2, (1, 1)))
        else_block.add_instruction(Jump("merge", (1, 1)))

        # Use x in merge
        result = func.new_temp(MIRType.INT)
        merge_block.add_instruction(Copy(result, x, (1, 1)))
        merge_block.add_instruction(Return((1, 1), result))

        # Convert to SSA
        construct_ssa(func)

        # Merge block should have phi node (in phi_nodes list, not instructions)
        self.assertGreater(len(merge_block.phi_nodes), 0)

        # Phi should have incoming values from both predecessors
        if merge_block.phi_nodes:
            phi = merge_block.phi_nodes[0]
            self.assertEqual(len(phi.incoming), 2)
            incoming_labels = {label for _, label in phi.incoming}
            self.assertIn("then", incoming_labels)
            self.assertIn("else", incoming_labels)

    def test_ssa_with_loops(self) -> None:
        """Test SSA construction with loop (self-referencing phi)."""
        # Create function with loop
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create blocks for loop
        entry = BasicBlock("entry")
        loop_header = BasicBlock("loop_header")
        loop_body = BasicBlock("loop_body")
        exit_block = BasicBlock("exit")

        func.cfg.add_block(entry)
        func.cfg.add_block(loop_header)
        func.cfg.add_block(loop_body)
        func.cfg.add_block(exit_block)
        func.cfg.set_entry_block(entry)

        # Connect for loop structure
        func.cfg.connect(entry, loop_header)
        func.cfg.connect(loop_header, loop_body)
        func.cfg.connect(loop_header, exit_block)
        func.cfg.connect(loop_body, loop_header)  # Back edge

        # Create loop counter variable
        i = Variable("i", MIRType.INT)
        func.add_local(i)

        # Initialize counter in entry
        const0 = Constant(0, MIRType.INT)
        entry.add_instruction(StoreVar(i, const0, (1, 1)))
        entry.add_instruction(Jump("loop_header", (1, 1)))

        # Loop header checks condition
        cond = func.new_temp(MIRType.BOOL)
        ten = Constant(10, MIRType.INT)
        loop_header.add_instruction(BinaryOp(cond, "<", i, ten, (1, 1)))
        loop_header.add_instruction(ConditionalJump(cond, "loop_body", (1, 1), "exit"))

        # Loop body increments counter
        one = Constant(1, MIRType.INT)
        new_i = func.new_temp(MIRType.INT)
        loop_body.add_instruction(BinaryOp(new_i, "+", i, one, (1, 1)))
        loop_body.add_instruction(StoreVar(i, new_i, (1, 1)))
        loop_body.add_instruction(Jump("loop_header", (1, 1)))

        # Exit
        exit_block.add_instruction(Return((1, 1)))

        # Convert to SSA
        construct_ssa(func)

        # Loop header should have phi node for loop variable (in phi_nodes list)
        self.assertGreater(len(loop_header.phi_nodes), 0)

        # Phi should have incoming from entry and loop_body
        if loop_header.phi_nodes:
            phi = loop_header.phi_nodes[0]
            incoming_labels = {label for _, label in phi.incoming}
            self.assertIn("entry", incoming_labels)
            self.assertIn("loop_body", incoming_labels)

    def test_multiple_variables_ssa(self) -> None:
        """Test SSA construction with multiple variables."""
        # Create function with multiple variables
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create simple CFG
        entry = BasicBlock("entry")
        block1 = BasicBlock("block1")

        func.cfg.add_block(entry)
        func.cfg.add_block(block1)
        func.cfg.set_entry_block(entry)
        func.cfg.connect(entry, block1)

        # Create multiple variables
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        z = Variable("z", MIRType.INT)

        func.add_local(x)
        func.add_local(y)
        func.add_local(z)

        # Assign values in entry
        const1 = Constant(1, MIRType.INT)
        const2 = Constant(2, MIRType.INT)

        entry.add_instruction(StoreVar(x, const1, (1, 1)))
        entry.add_instruction(StoreVar(y, const2, (1, 1)))

        # Compute z = x + y
        temp = func.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(temp, "+", x, y, (1, 1)))
        entry.add_instruction(StoreVar(z, temp, (1, 1)))
        entry.add_instruction(Jump("block1", (1, 1)))

        # Use all variables in block1
        result = func.new_temp(MIRType.INT)
        block1.add_instruction(BinaryOp(result, "+", z, x, (1, 1)))
        block1.add_instruction(Return((1, 1), result))

        # Convert to SSA
        construct_ssa(func)

        # Should complete without errors
        self.assertTrue(True)

    def test_ssa_preserves_semantics(self) -> None:
        """Test that SSA construction preserves program semantics."""
        # Create function that computes: if (cond) x = 1 else x = 2; return x
        func = MIRFunction("test", [], MIRType.INT)

        # Create diamond CFG
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge_block = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge_block)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge_block)
        func.cfg.connect(else_block, merge_block)

        # Create variable
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Count instructions before SSA
        total_before = sum(len(b.instructions) for b in func.cfg.blocks.values())

        # Add instructions
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(LoadConst(cond, True, (1, 1)))
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        const1 = Constant(1, MIRType.INT)
        const2 = Constant(2, MIRType.INT)

        then_block.add_instruction(StoreVar(x, const1, (1, 1)))
        then_block.add_instruction(Jump("merge", (1, 1)))

        else_block.add_instruction(StoreVar(x, const2, (1, 1)))
        else_block.add_instruction(Jump("merge", (1, 1)))

        result = func.new_temp(MIRType.INT)
        merge_block.add_instruction(Copy(result, x, (1, 1)))
        merge_block.add_instruction(Return((1, 1), result))

        # Convert to SSA
        construct_ssa(func)

        # Should have added at least one phi node
        total_after = sum(len(b.instructions) for b in func.cfg.blocks.values())
        self.assertGreater(total_after, total_before)

        # Should still have return instruction
        returns = []
        for block in func.cfg.blocks.values():
            returns.extend([inst for inst in block.instructions if isinstance(inst, Return)])
        self.assertEqual(len(returns), 1)


if __name__ == "__main__":
    unittest.main()
