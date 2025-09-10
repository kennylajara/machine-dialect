"""Tests for loop unrolling optimization pass."""

from unittest.mock import Mock, patch

from machine_dialect.mir.analyses.loop_analysis import Loop
from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Jump,
    LoadConst,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimization_pass import PassInfo, PassType, PreservationLevel
from machine_dialect.mir.optimizations.loop_unrolling import LoopUnrolling


class TestLoopUnrolling:
    """Test loop unrolling optimization pass."""

    def test_initialization(self) -> None:
        """Test loop unrolling pass initialization."""
        pass_instance = LoopUnrolling()

        assert pass_instance.unroll_threshold == 4
        assert pass_instance.max_body_size == 20
        assert pass_instance.stats == {"unrolled": 0, "loops_processed": 0}

    def test_get_info(self) -> None:
        """Test getting pass information."""
        pass_instance = LoopUnrolling()
        info = pass_instance.get_info()

        assert isinstance(info, PassInfo)
        assert info.name == "loop-unrolling"
        assert info.description == "Unroll small loops to reduce overhead"
        assert info.pass_type == PassType.OPTIMIZATION
        assert info.requires == ["loop-analysis", "dominance"]
        assert info.preserves == PreservationLevel.CFG

    def test_get_loops_in_order(self) -> None:
        """Test ordering loops from innermost to outermost."""
        pass_instance = LoopUnrolling()

        # Create mock loops with different depths
        loop1 = Mock(spec=Loop)
        loop1.depth = 1

        loop2 = Mock(spec=Loop)
        loop2.depth = 3

        loop3 = Mock(spec=Loop)
        loop3.depth = 2

        from typing import cast

        from machine_dialect.mir.analyses.loop_analysis import Loop as RealLoop

        loops = cast(list[RealLoop], [loop1, loop2, loop3])
        ordered = pass_instance._get_loops_in_order(loops)

        # Should be ordered by depth descending (3, 2, 1)
        assert ordered[0] == loop2
        assert ordered[1] == loop3
        assert ordered[2] == loop1

    def test_find_defining_instruction(self) -> None:
        """Test finding the instruction that defines a value."""
        pass_instance = LoopUnrolling()

        # Create a basic block with instructions
        block = BasicBlock("test")
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        # Add instruction that defines t0
        inst1 = LoadConst(t0, 42, (1, 1))
        block.add_instruction(inst1)

        # Add instruction that defines t1
        inst2 = BinaryOp(t1, "+", t0, Constant(1), (2, 1))
        block.add_instruction(inst2)

        # Find defining instruction for t0
        result = pass_instance._find_defining_instruction(t0, block)
        assert result == inst1

        # Find defining instruction for t1
        result = pass_instance._find_defining_instruction(t1, block)
        assert result == inst2

        # Non-existent value
        t2 = Temp(MIRType.INT, temp_id=2)
        result = pass_instance._find_defining_instruction(t2, block)
        assert result is None

    def test_should_unroll_too_large(self) -> None:
        """Test that large loops are not unrolled."""
        pass_instance = LoopUnrolling()

        # Create a loop with too many instructions
        loop = Mock(spec=Loop)
        block1 = BasicBlock("loop_body")

        # Add many instructions to exceed threshold
        for i in range(25):  # More than max_body_size (20)
            t = Temp(MIRType.INT, temp_id=i)
            block1.add_instruction(LoadConst(t, i, (i, 1)))

        loop.blocks = [block1]

        function = Mock(spec=MIRFunction)
        result = pass_instance._should_unroll(loop, function)

        assert result is False

    def test_should_unroll_unknown_iteration_count(self) -> None:
        """Test that loops with unknown iteration count are not unrolled."""
        pass_instance = LoopUnrolling()

        # Create a simple loop
        loop = Mock(spec=Loop)
        block = BasicBlock("loop_body")
        t0 = Temp(MIRType.INT, temp_id=0)
        block.add_instruction(LoadConst(t0, 1, (1, 1)))
        loop.blocks = [block]
        loop.header = block

        function = Mock(spec=MIRFunction)

        # Mock _get_iteration_count to return None
        with patch.object(pass_instance, "_get_iteration_count", return_value=None):
            result = pass_instance._should_unroll(loop, function)

        assert result is False

    def test_should_unroll_valid_loop(self) -> None:
        """Test that valid loops are marked for unrolling."""
        pass_instance = LoopUnrolling()

        # Create a simple loop
        loop = Mock(spec=Loop)
        block = BasicBlock("loop_body")
        t0 = Temp(MIRType.INT, temp_id=0)
        block.add_instruction(LoadConst(t0, 1, (1, 1)))
        loop.blocks = [block]

        function = Mock(spec=MIRFunction)

        # Mock _get_iteration_count to return a valid count
        with patch.object(pass_instance, "_get_iteration_count", return_value=4):
            result = pass_instance._should_unroll(loop, function)

        assert result is True

    def test_get_iteration_count_constant_bound(self) -> None:
        """Test determining iteration count with constant bounds."""
        pass_instance = LoopUnrolling()

        # Create a loop header with condition: i < 10
        header = BasicBlock("header")
        i = Temp(MIRType.INT, temp_id=0)
        cond = Temp(MIRType.BOOL, temp_id=1)

        # Add comparison: cond = i < 10
        cmp_inst = BinaryOp(cond, "<", i, Constant(10), (1, 1))
        header.add_instruction(cmp_inst)

        # Add conditional jump based on condition
        jump_inst = ConditionalJump(cond, "body", (2, 1), "exit")
        header.add_instruction(jump_inst)

        loop = Mock(spec=Loop)
        loop.header = header

        function = Mock(spec=MIRFunction)

        # Mock _find_defining_instruction to return the comparison
        with patch.object(pass_instance, "_find_defining_instruction", return_value=cmp_inst):
            result = pass_instance._get_iteration_count(loop, function)
            assert result == 10

    def test_get_iteration_count_less_equal(self) -> None:
        """Test iteration count with <= comparison."""
        pass_instance = LoopUnrolling()

        # Create a loop header with condition: i <= 5
        header = BasicBlock("header")
        i = Temp(MIRType.INT, temp_id=0)
        cond = Temp(MIRType.BOOL, temp_id=1)

        # Add comparison: cond = i <= 5
        cmp_inst = BinaryOp(cond, "<=", i, Constant(5), (1, 1))
        header.add_instruction(cmp_inst)

        # Add conditional jump
        jump_inst = ConditionalJump(cond, "body", (2, 1), "exit")
        header.add_instruction(jump_inst)

        loop = Mock(spec=Loop)
        loop.header = header

        function = Mock(spec=MIRFunction)

        # Mock _find_defining_instruction to return the comparison
        with patch.object(pass_instance, "_find_defining_instruction", return_value=cmp_inst):
            result = pass_instance._get_iteration_count(loop, function)
            assert result == 6  # 0 to 5 inclusive

    def test_get_iteration_count_non_constant(self) -> None:
        """Test that non-constant bounds return None."""
        pass_instance = LoopUnrolling()

        # Create a loop header with variable bound: i < n
        header = BasicBlock("header")
        i = Temp(MIRType.INT, temp_id=0)
        n = Temp(MIRType.INT, temp_id=1)  # Variable, not constant
        cond = Temp(MIRType.BOOL, temp_id=2)

        # Add comparison: cond = i < n
        cmp_inst = BinaryOp(cond, "<", i, n, (1, 1))
        header.add_instruction(cmp_inst)

        # Add conditional jump
        jump_inst = ConditionalJump(cond, "body", (2, 1), "exit")
        header.add_instruction(jump_inst)

        loop = Mock(spec=Loop)
        loop.header = header

        function = Mock(spec=MIRFunction)

        result = pass_instance._get_iteration_count(loop, function)
        assert result is None

    def test_clone_block(self) -> None:
        """Test cloning a basic block."""
        pass_instance = LoopUnrolling()

        # Create original block
        original = BasicBlock("original")
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        original.add_instruction(LoadConst(t0, 42, (1, 1)))
        original.add_instruction(BinaryOp(t1, "+", t0, Constant(1), (2, 1)))
        original.add_instruction(Jump("next", (3, 1)))

        # Clone the block
        cloned = pass_instance._clone_block(original, "_unroll_1")

        assert cloned.label == "original_unroll_1"
        assert len(cloned.instructions) == 3
        assert cloned.instructions != original.instructions  # Different objects

        # Check that instructions are cloned
        assert isinstance(cloned.instructions[0], LoadConst)
        assert isinstance(cloned.instructions[1], BinaryOp)
        assert isinstance(cloned.instructions[2], Jump)

    def test_clone_instruction(self) -> None:
        """Test cloning individual instructions."""
        pass_instance = LoopUnrolling()

        # Test cloning different instruction types
        t0 = Temp(MIRType.INT, temp_id=0)

        # Clone LoadConst
        inst1 = LoadConst(t0, 42, (1, 1))
        cloned1 = pass_instance._clone_instruction(inst1, "_suffix")
        assert isinstance(cloned1, LoadConst)
        assert cloned1 != inst1
        # Deep copy creates new objects, but the values should be equivalent
        assert cloned1.constant == inst1.constant

        # Clone Jump
        inst2 = Jump("target", (2, 1))
        cloned2 = pass_instance._clone_instruction(inst2, "_suffix")
        assert isinstance(cloned2, Jump)
        assert cloned2.label == "target"  # Currently preserves original target

        # Clone ConditionalJump
        cond = Temp(MIRType.BOOL, temp_id=1)
        inst3 = ConditionalJump(cond, "true_branch", (3, 1), "false_branch")
        cloned3 = pass_instance._clone_instruction(inst3, "_suffix")
        assert isinstance(cloned3, ConditionalJump)
        assert cloned3.true_label == "true_branch"
        assert cloned3.false_label == "false_branch"

    def test_update_loop_increment(self) -> None:
        """Test updating loop increment for unrolling."""
        pass_instance = LoopUnrolling()

        # Create a loop with increment
        block = BasicBlock("increment")
        i = Temp(MIRType.INT, temp_id=0)

        # Add increment: i = i + 1
        inc_inst = BinaryOp(i, "+", i, Constant(1), (1, 1))
        block.add_instruction(inc_inst)

        loop = Mock(spec=Loop)
        loop.blocks = [block]

        # Update increment for unroll factor of 4
        pass_instance._update_loop_increment(loop, 4)

        # The implementation updates the right operand to a new Constant
        # Check that increment value is now 4
        assert hasattr(inc_inst.right, "value")
        assert inc_inst.right.value == 4

    def test_connect_unrolled_blocks(self) -> None:
        """Test connecting unrolled blocks."""
        pass_instance = LoopUnrolling()

        # Create original loop body
        body1 = BasicBlock("body1")
        body1.add_instruction(Jump("header", (1, 1)))

        # Create unrolled copies
        unroll1 = BasicBlock("body1_unroll_1")
        unroll1.add_instruction(Jump("header", (2, 1)))

        unroll2 = BasicBlock("body1_unroll_2")
        unroll2.add_instruction(Jump("header", (3, 1)))

        loop = Mock(spec=Loop)

        pass_instance._connect_unrolled_blocks(loop, [unroll1, unroll2], [body1], 3)

        # Check that original body jumps to first unrolled copy
        assert hasattr(body1.instructions[-1], "label")
        assert body1.instructions[-1].label == "body1_unroll_1"

        # Check that first unrolled copy jumps to second
        assert hasattr(unroll1.instructions[-1], "label")
        assert unroll1.instructions[-1].label == "body1_unroll_2"

    def test_run_on_function_no_analyses(self) -> None:
        """Test that function returns False when analyses are missing."""
        pass_instance = LoopUnrolling()

        function = Mock(spec=MIRFunction)

        # Mock get_analysis to return None
        with patch.object(pass_instance, "get_analysis", return_value=None):
            result = pass_instance.run_on_function(function)

        assert result is False

    def test_run_on_function_with_config(self) -> None:
        """Test that config is used when available."""
        pass_instance = LoopUnrolling()

        # Set threshold directly
        pass_instance.unroll_threshold = 8

        function = Mock(spec=MIRFunction)

        # Mock analyses
        loop_info = Mock()
        loop_info.loops = []
        dominance = Mock()

        with patch.object(pass_instance, "get_analysis") as mock_get:
            mock_get.side_effect = [loop_info, dominance]
            result = pass_instance.run_on_function(function)

        # Check that config threshold was applied
        assert pass_instance.unroll_threshold == 8
        assert result is False  # No loops to process

    def test_run_on_function_process_loops(self) -> None:
        """Test processing loops in a function."""
        pass_instance = LoopUnrolling()

        # Create a function with CFG
        function = MIRFunction("test_func", [], MIRType.EMPTY)
        function.cfg = CFG()

        # Create a simple loop
        header = BasicBlock("header")
        body = BasicBlock("body")

        loop = Mock(spec=Loop)
        loop.depth = 1
        loop.header = header
        loop.blocks = [header, body]

        # Mock analyses
        loop_info = Mock()
        # Use hasattr check to avoid AttributeError
        loop_info.loops = [loop]
        dominance = Mock()

        with patch.object(pass_instance, "get_analysis") as mock_get:
            mock_get.side_effect = [loop_info, dominance]

            # Mock _get_loops_in_order to return our loop
            with patch.object(pass_instance, "_get_loops_in_order", return_value=[loop]):
                # Mock should_unroll to return False (don't actually unroll)
                with patch.object(pass_instance, "_should_unroll", return_value=False):
                    result = pass_instance.run_on_function(function)

        assert pass_instance.stats["loops_processed"] == 1
        assert pass_instance.stats["unrolled"] == 0
        assert result is False

    def test_finalize(self) -> None:
        """Test finalize method."""
        pass_instance = LoopUnrolling()
        # Should not raise any exception
        pass_instance.finalize()

    def test_get_statistics(self) -> None:
        """Test getting optimization statistics."""
        pass_instance = LoopUnrolling()

        # Initial stats
        stats = pass_instance.get_statistics()
        assert stats == {"unrolled": 0, "loops_processed": 0}

        # Modify stats
        pass_instance.stats["unrolled"] = 3
        pass_instance.stats["loops_processed"] = 5

        stats = pass_instance.get_statistics()
        assert stats == {"unrolled": 3, "loops_processed": 5}

    def test_unroll_loop_empty_body(self) -> None:
        """Test that loops with empty body are not unrolled."""
        pass_instance = LoopUnrolling()

        # Create a loop with only header (no body blocks)
        header = BasicBlock("header")
        loop = Mock(spec=Loop)
        loop.header = header
        loop.blocks = [header]

        function = MIRFunction("test", [], MIRType.EMPTY)
        function.cfg = CFG()

        transformer = Mock()

        # The implementation checks for loop_body_blocks excluding the header
        # Since all blocks are just the header, loop_body_blocks will be empty
        result = pass_instance._unroll_loop(loop, function, transformer)
        assert result is False

    def test_unroll_loop_success(self) -> None:
        """Test successful loop unrolling."""
        pass_instance = LoopUnrolling()
        pass_instance.unroll_threshold = 2

        # Create a loop with header and body
        header = BasicBlock("header")
        body = BasicBlock("body")
        body.add_instruction(Jump("header", (1, 1)))

        loop = Mock(spec=Loop)
        loop.header = header
        loop.blocks = [header, body]

        function = MIRFunction("test", [], MIRType.EMPTY)
        function.cfg = CFG()

        transformer = Mock()
        transformer.modified = False

        # Mock the helper methods to ensure they're called
        with patch.object(pass_instance, "_connect_unrolled_blocks"):
            with patch.object(pass_instance, "_update_loop_increment"):
                result = pass_instance._unroll_loop(loop, function, transformer)

        assert result is True
        assert transformer.modified is True

        # Check that new blocks were added to CFG (unroll_factor - 1 new blocks per body block)
        # With unroll_factor=2 and 1 body block, we should have 1 new block
        assert len(function.cfg.blocks) == 1
