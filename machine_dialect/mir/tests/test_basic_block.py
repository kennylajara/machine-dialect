"""Tests for MIR basic blocks and CFG."""

import unittest

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Jump,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Temp


class TestBasicBlock(unittest.TestCase):
    """Test basic block functionality."""

    def test_basic_block_creation(self) -> None:
        """Test creating basic blocks."""
        block = BasicBlock("entry")
        self.assertEqual(block.label, "entry")
        self.assertEqual(block.instructions, [])
        self.assertEqual(block.phi_nodes, [])
        self.assertEqual(block.predecessors, [])
        self.assertEqual(block.successors, [])

    def test_is_terminated(self) -> None:
        """Test checking if block is terminated."""
        block = BasicBlock("bb1")
        t0 = Temp(MIRType.INT, temp_id=0)

        # Empty block is not terminated
        self.assertFalse(block.is_terminated())

        # Block with non-terminator is not terminated
        block.add_instruction(LoadConst(t0, 42, (1, 1)))
        self.assertFalse(block.is_terminated())

        # Block with terminator is terminated
        block.add_instruction(Return((1, 1), t0))
        self.assertTrue(block.is_terminated())

    def test_get_terminator(self) -> None:
        """Test getting block terminator."""
        block = BasicBlock("bb1")
        t0 = Temp(MIRType.INT, temp_id=0)

        # No terminator initially
        self.assertIsNone(block.get_terminator())

        # Add instructions
        block.add_instruction(LoadConst(t0, 5, (1, 1)))
        self.assertIsNone(block.get_terminator())

        # Add terminator
        ret = Return((1, 1), t0)
        block.add_instruction(ret)
        self.assertEqual(block.get_terminator(), ret)

    def test_terminator_types(self) -> None:
        """Test different terminator types."""
        # Test Jump
        block1 = BasicBlock("bb1")
        jump = Jump("bb2", (1, 1))
        block1.add_instruction(jump)
        self.assertTrue(block1.is_terminated())

        # Test ConditionalJump
        block2 = BasicBlock("bb2")
        t0 = Temp(MIRType.BOOL, temp_id=0)
        cjump = ConditionalJump(t0, "then", (1, 1), "else")
        block2.add_instruction(cjump)
        self.assertTrue(block2.is_terminated())

        # Test Return
        block3 = BasicBlock("bb3")
        ret = Return((1, 1))
        block3.add_instruction(ret)
        self.assertTrue(block3.is_terminated())

    def test_connect_blocks(self) -> None:
        """Test connecting blocks as predecessors/successors."""
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        bb2 = BasicBlock("bb2")

        entry.add_successor(bb1)
        entry.add_successor(bb2)

        self.assertEqual(entry.successors, [bb1, bb2])
        self.assertEqual(bb1.predecessors, [entry])
        self.assertEqual(bb2.predecessors, [entry])

    def test_block_string_representation(self) -> None:
        """Test string representation of blocks."""
        block = BasicBlock("loop_body")
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        block.add_instruction(LoadConst(t0, 1, (1, 1)))
        block.add_instruction(BinaryOp(t1, "+", t0, t0, (1, 1)))
        block.add_instruction(Jump("loop_body", (1, 1)))

        expected = """loop_body:
  t0 = 1
  t1 = t0 + t0
  goto loop_body"""

        self.assertEqual(str(block), expected)


class TestCFG(unittest.TestCase):
    """Test control flow graph functionality."""

    def test_cfg_creation(self) -> None:
        """Test creating CFG."""
        cfg = CFG()
        self.assertEqual(cfg.blocks, {})
        self.assertIsNone(cfg.entry_block)
        self.assertIsNone(cfg.exit_block)

    def test_add_block(self) -> None:
        """Test adding blocks to CFG."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")

        cfg.add_block(entry)
        cfg.add_block(bb1)

        self.assertEqual(len(cfg.blocks), 2)
        self.assertEqual(cfg.blocks["entry"], entry)
        self.assertEqual(cfg.blocks["bb1"], bb1)

    def test_set_entry_block(self) -> None:
        """Test setting entry block."""
        cfg = CFG()
        entry = BasicBlock("entry")

        cfg.add_block(entry)
        cfg.set_entry_block(entry)

        self.assertEqual(cfg.entry_block, entry)

    def test_connect_blocks(self) -> None:
        """Test connecting blocks in CFG."""
        cfg = CFG()
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(then_block)
        cfg.add_block(else_block)
        cfg.add_block(merge)

        cfg.connect(entry, then_block)
        cfg.connect(entry, else_block)
        cfg.connect(then_block, merge)
        cfg.connect(else_block, merge)

        self.assertEqual(entry.successors, [then_block, else_block])
        self.assertEqual(then_block.predecessors, [entry])
        self.assertEqual(else_block.predecessors, [entry])
        self.assertEqual(merge.predecessors, [then_block, else_block])

    def test_get_block(self) -> None:
        """Test getting block by label."""
        cfg = CFG()
        bb1 = BasicBlock("bb1")
        cfg.add_block(bb1)

        self.assertEqual(cfg.get_block("bb1"), bb1)
        self.assertIsNone(cfg.get_block("nonexistent"))

    def test_get_predecessors(self) -> None:
        """Test getting block predecessors."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        bb2 = BasicBlock("bb2")
        merge = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(bb1)
        cfg.add_block(bb2)
        cfg.add_block(merge)

        cfg.connect(entry, bb1)
        cfg.connect(entry, bb2)
        cfg.connect(bb1, merge)
        cfg.connect(bb2, merge)

        self.assertEqual(cfg.get_predecessors(entry), [])
        self.assertEqual(cfg.get_predecessors(bb1), [entry])
        self.assertEqual(cfg.get_predecessors(merge), [bb1, bb2])

    def test_get_successors(self) -> None:
        """Test getting block successors."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        bb2 = BasicBlock("bb2")

        cfg.add_block(entry)
        cfg.add_block(bb1)
        cfg.add_block(bb2)

        cfg.connect(entry, bb1)
        cfg.connect(entry, bb2)

        self.assertEqual(cfg.get_successors(entry), [bb1, bb2])
        self.assertEqual(cfg.get_successors(bb1), [])
        self.assertEqual(cfg.get_successors(bb2), [])

    def test_compute_dominance_simple(self) -> None:
        """Test dominance computation on simple CFG."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        bb2 = BasicBlock("bb2")

        cfg.add_block(entry)
        cfg.add_block(bb1)
        cfg.add_block(bb2)
        cfg.set_entry_block(entry)

        cfg.connect(entry, bb1)
        cfg.connect(bb1, bb2)

        cfg.compute_dominance()

        # Entry dominates all blocks
        self.assertIn(entry, cfg.dominators[entry])
        self.assertIn(entry, cfg.dominators[bb1])
        self.assertIn(entry, cfg.dominators[bb2])

        # bb1 dominates bb2
        self.assertIn(bb1, cfg.dominators[bb2])

        # Each block dominates itself
        self.assertIn(bb1, cfg.dominators[bb1])
        self.assertIn(bb2, cfg.dominators[bb2])

    def test_compute_dominance_with_branch(self) -> None:
        """Test dominance with branching."""
        cfg = CFG()
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(then_block)
        cfg.add_block(else_block)
        cfg.add_block(merge)
        cfg.set_entry_block(entry)

        cfg.connect(entry, then_block)
        cfg.connect(entry, else_block)
        cfg.connect(then_block, merge)
        cfg.connect(else_block, merge)

        cfg.compute_dominance()

        # Entry dominates all
        for block in [entry, then_block, else_block, merge]:
            self.assertIn(entry, cfg.dominators[block])

        # Neither then nor else dominates merge (both paths lead to merge)
        self.assertNotIn(then_block, cfg.dominators[merge])
        self.assertNotIn(else_block, cfg.dominators[merge])

        # Then doesn't dominate else and vice versa
        self.assertNotIn(then_block, cfg.dominators[else_block])
        self.assertNotIn(else_block, cfg.dominators[then_block])

    def test_compute_dominance_frontiers(self) -> None:
        """Test dominance frontier computation."""
        cfg = CFG()
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        cfg.add_block(entry)
        cfg.add_block(then_block)
        cfg.add_block(else_block)
        cfg.add_block(merge)
        cfg.set_entry_block(entry)

        cfg.connect(entry, then_block)
        cfg.connect(entry, else_block)
        cfg.connect(then_block, merge)
        cfg.connect(else_block, merge)

        cfg.compute_dominance()
        cfg.compute_dominance_frontiers()

        # Merge is in the dominance frontier of then and else
        self.assertIn(merge, cfg.dominance_frontiers.get(then_block, []))
        self.assertIn(merge, cfg.dominance_frontiers.get(else_block, []))

        # Entry and merge should have empty frontiers in this case
        self.assertEqual(cfg.dominance_frontiers.get(entry, []), [])
        self.assertEqual(cfg.dominance_frontiers.get(merge, []), [])

    def test_topological_sort(self) -> None:
        """Test topological sorting of blocks."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        bb2 = BasicBlock("bb2")
        bb3 = BasicBlock("bb3")

        cfg.add_block(entry)
        cfg.add_block(bb1)
        cfg.add_block(bb2)
        cfg.add_block(bb3)
        cfg.set_entry_block(entry)

        cfg.connect(entry, bb1)
        cfg.connect(entry, bb2)
        cfg.connect(bb1, bb3)
        cfg.connect(bb2, bb3)

        sorted_blocks = cfg.topological_sort()

        # Entry should be first
        self.assertEqual(sorted_blocks[0], entry)

        # bb3 should be last (after both bb1 and bb2)
        self.assertEqual(sorted_blocks[-1], bb3)

        # bb1 and bb2 should be between entry and bb3
        bb1_index = sorted_blocks.index(bb1)
        bb2_index = sorted_blocks.index(bb2)
        bb3_index = sorted_blocks.index(bb3)
        self.assertLess(bb1_index, bb3_index)
        self.assertLess(bb2_index, bb3_index)

    def test_cfg_string_representation(self) -> None:
        """Test string representation of CFG."""
        cfg = CFG()
        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")

        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 1, (1, 1)))
        entry.add_instruction(Jump("bb1", (1, 1)))

        bb1.add_instruction(Return((1, 1), t0))

        cfg.add_block(entry)
        cfg.add_block(bb1)
        cfg.set_entry_block(entry)
        cfg.connect(entry, bb1)

        result = str(cfg)
        self.assertIn("entry:", result)
        self.assertIn("bb1:", result)
        self.assertIn("t0 = 1", result)
        self.assertIn("return t0", result)


class TestCFGWithLoops(unittest.TestCase):
    """Test CFG with loop structures."""

    def test_loop_dominance(self) -> None:
        """Test dominance in CFG with loops."""
        cfg = CFG()
        entry = BasicBlock("entry")
        loop_header = BasicBlock("loop_header")
        loop_body = BasicBlock("loop_body")
        exit_block = BasicBlock("exit")

        cfg.add_block(entry)
        cfg.add_block(loop_header)
        cfg.add_block(loop_body)
        cfg.add_block(exit_block)
        cfg.set_entry_block(entry)

        # Create loop structure
        cfg.connect(entry, loop_header)
        cfg.connect(loop_header, loop_body)
        cfg.connect(loop_body, loop_header)  # Back edge
        cfg.connect(loop_header, exit_block)

        cfg.compute_dominance()

        # Entry dominates all
        self.assertIn(entry, cfg.dominators[loop_header])
        self.assertIn(entry, cfg.dominators[loop_body])
        self.assertIn(entry, cfg.dominators[exit_block])

        # Loop header dominates body and exit
        self.assertIn(loop_header, cfg.dominators[loop_body])
        self.assertIn(loop_header, cfg.dominators[exit_block])

    def test_loop_dominance_frontiers(self) -> None:
        """Test dominance frontiers in loops."""
        cfg = CFG()
        entry = BasicBlock("entry")
        loop_header = BasicBlock("loop_header")
        loop_body = BasicBlock("loop_body")
        exit_block = BasicBlock("exit")

        cfg.add_block(entry)
        cfg.add_block(loop_header)
        cfg.add_block(loop_body)
        cfg.add_block(exit_block)
        cfg.set_entry_block(entry)

        cfg.connect(entry, loop_header)
        cfg.connect(loop_header, loop_body)
        cfg.connect(loop_body, loop_header)  # Back edge
        cfg.connect(loop_header, exit_block)

        cfg.compute_dominance()
        cfg.compute_dominance_frontiers()

        # Loop header is in the dominance frontier of loop body
        # (because of the back edge)
        self.assertIn(loop_header, cfg.dominance_frontiers.get(loop_body, []))


if __name__ == "__main__":
    unittest.main()
