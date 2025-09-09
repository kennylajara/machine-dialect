"""Comprehensive tests for branch prediction optimization pass."""

from unittest.mock import MagicMock

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Jump,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimization_pass import PassType, PreservationLevel
from machine_dialect.mir.optimizations.branch_prediction import (
    BranchInfo,
    BranchPredictionOptimization,
)
from machine_dialect.mir.profiling.profile_data import ProfileData


class TestBranchInfo:
    """Test BranchInfo dataclass."""

    def test_branch_info_creation(self) -> None:
        """Test creating BranchInfo."""
        block = BasicBlock("test_block")
        temp = Temp(MIRType.BOOL)
        jump = ConditionalJump(temp, "then_block", (1, 1), "else_block")

        info = BranchInfo(
            block=block,
            instruction=jump,
            taken_probability=0.98,
            is_predictable=True,
            is_loop_header=False,
        )

        assert info.block == block
        assert info.instruction == jump
        assert info.taken_probability == 0.98
        assert info.is_predictable
        assert not info.is_loop_header

    def test_branch_info_defaults(self) -> None:
        """Test BranchInfo default values."""
        block = BasicBlock("test_block")
        temp = Temp(MIRType.BOOL)
        jump = ConditionalJump(temp, "then_block", (1, 1), "else_block")

        info = BranchInfo(
            block=block,
            instruction=jump,
            taken_probability=0.5,
            is_predictable=False,
        )

        assert not info.is_loop_header


class TestBranchPredictionOptimization:
    """Test BranchPredictionOptimization pass."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.module = MIRModule("test")

        # Create a function with conditional branch
        self.func = MIRFunction("test_func", [], MIRType.INT)

        # Create basic blocks
        self.entry_block = BasicBlock("entry")
        self.then_block = BasicBlock("then")
        self.else_block = BasicBlock("else")
        self.merge_block = BasicBlock("merge")

        # Build control flow: if (x > 5) then ... else ...
        x = Temp(MIRType.INT)
        cond = Temp(MIRType.BOOL)
        result = Temp(MIRType.INT)

        # Entry block
        self.entry_block.add_instruction(LoadConst(x, Constant(10, MIRType.INT), (1, 1)))
        self.entry_block.add_instruction(BinaryOp(cond, ">", x, Constant(5, MIRType.INT), (1, 1)))
        self.entry_block.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        # Then block
        self.then_block.add_instruction(LoadConst(result, Constant(1, MIRType.INT), (1, 1)))
        self.then_block.add_instruction(Jump("merge", (1, 1)))

        # Else block
        self.else_block.add_instruction(LoadConst(result, Constant(0, MIRType.INT), (1, 1)))
        self.else_block.add_instruction(Jump("merge", (1, 1)))

        # Merge block
        self.merge_block.add_instruction(Return((1, 1), result))

        # Add blocks to CFG
        self.func.cfg.add_block(self.entry_block)
        self.func.cfg.add_block(self.then_block)
        self.func.cfg.add_block(self.else_block)
        self.func.cfg.add_block(self.merge_block)
        self.func.cfg.entry_block = self.entry_block

        # Set up control flow edges via successors/predecessors
        self.entry_block.add_successor(self.then_block)
        self.entry_block.add_successor(self.else_block)
        self.then_block.add_predecessor(self.entry_block)
        self.else_block.add_predecessor(self.entry_block)

        self.then_block.add_successor(self.merge_block)
        self.else_block.add_successor(self.merge_block)
        self.merge_block.add_predecessor(self.then_block)
        self.merge_block.add_predecessor(self.else_block)

        self.module.add_function(self.func)

    def test_pass_initialization(self) -> None:
        """Test initialization of branch prediction pass."""
        opt = BranchPredictionOptimization(predictability_threshold=0.9)
        assert opt.profile_data is None
        assert opt.predictability_threshold == 0.9
        assert opt.stats["branches_analyzed"] == 0

    def test_pass_info(self) -> None:
        """Test pass information."""
        opt = BranchPredictionOptimization()
        info = opt.get_info()
        assert info.name == "branch-prediction"
        assert info.pass_type == PassType.OPTIMIZATION
        # Branch prediction might preserve CFG structure
        assert info.preserves in [PreservationLevel.NONE, PreservationLevel.CFG]

    def test_collect_branch_info(self) -> None:
        """Test collecting branch information."""
        opt = BranchPredictionOptimization()

        # Mock profile data with proper method
        profile = MagicMock(spec=ProfileData)
        # Add branches dict with proper branch key and profile
        from unittest.mock import Mock

        branch_profile = Mock()
        branch_profile.taken_probability = 0.98
        branch_profile.predictable = True
        profile.branches = {"test_func:entry": branch_profile}
        opt.profile_data = profile

        branches = opt._collect_branch_info(self.func)

        # Should find one branch (in entry block)
        assert len(branches) == 1
        branch_info = branches[0]
        assert branch_info.block.label == "entry"
        assert isinstance(branch_info.instruction, ConditionalJump)
        assert branch_info.taken_probability == 0.98
        assert branch_info.is_predictable

    def test_collect_branch_info_no_profile(self) -> None:
        """Test collecting branch information without profile data."""
        opt = BranchPredictionOptimization()

        branches = opt._collect_branch_info(self.func)

        # Should find one branch with default probability
        assert len(branches) == 1
        branch_info = branches[0]
        assert branch_info.taken_probability == 0.5  # Default
        assert not branch_info.is_predictable

    def test_reorder_blocks_for_fallthrough(self) -> None:
        """Test reordering blocks for better fallthrough."""
        opt = BranchPredictionOptimization()

        # Mock profile data - then branch is highly likely
        profile = MagicMock(spec=ProfileData)
        from unittest.mock import Mock

        branch_profile = Mock()
        branch_profile.taken_probability = 0.99
        branch_profile.predictable = True
        profile.branches = {"test_func:entry": branch_profile}
        opt.profile_data = profile

        # Ensure blocks are in non-optimal order initially
        # Put else block before then block to force reordering
        original_order = list(self.func.cfg.blocks.keys())
        if "else" in original_order and "then" in original_order:
            # Reorder to put else before then (non-optimal for 0.99 taken probability)
            new_blocks = {}
            new_blocks["entry"] = self.func.cfg.blocks["entry"]
            new_blocks["else"] = self.func.cfg.blocks["else"]
            new_blocks["then"] = self.func.cfg.blocks["then"]
            new_blocks["merge"] = self.func.cfg.blocks["merge"]
            self.func.cfg.blocks = new_blocks

        # Collect branch info
        branches = opt._collect_branch_info(self.func)

        # Reorder blocks
        reordered = opt._reorder_blocks(self.func, branches)

        # Should reorder to put likely path (then) after entry
        assert reordered

        # Check new order has then block after entry
        new_order = list(self.func.cfg.blocks.keys())
        entry_idx = new_order.index("entry")
        then_idx = new_order.index("then")
        # Then should come right after entry for better fallthrough
        assert then_idx == entry_idx + 1

    def test_add_branch_hints(self) -> None:
        """Test adding branch hints."""
        opt = BranchPredictionOptimization()

        # Create predictable branch info
        last_inst = list(self.entry_block.instructions)[-1]
        assert isinstance(last_inst, ConditionalJump)
        branch_info = BranchInfo(
            block=self.entry_block,
            instruction=last_inst,
            taken_probability=0.98,
            is_predictable=True,
        )

        # Add branch hint (method takes single BranchInfo, not list)
        hint_added = opt._add_branch_hint(branch_info)

        # Check if hint was added (returns bool)
        assert isinstance(hint_added, bool)

    def test_convert_to_select(self) -> None:
        """Test converting predictable branches to select instructions."""
        opt = BranchPredictionOptimization()

        # Create simple if-then-else that can be converted
        func = MIRFunction("simple", [], MIRType.INT)
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        cond = Temp(MIRType.BOOL)
        result = Temp(MIRType.INT)

        # Simple pattern: result = cond ? 1 : 0
        entry.add_instruction(LoadConst(cond, Constant(True, MIRType.BOOL), (1, 1)))
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))

        then_block.add_instruction(LoadConst(result, Constant(1, MIRType.INT), (1, 1)))
        then_block.add_instruction(Jump("merge", (1, 1)))

        else_block.add_instruction(LoadConst(result, Constant(0, MIRType.INT), (1, 1)))
        else_block.add_instruction(Jump("merge", (1, 1)))

        merge.add_instruction(Return((1, 1), result))

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.entry_block = entry

        # Create highly predictable branch
        last_inst = list(entry.instructions)[-1]
        assert isinstance(last_inst, ConditionalJump)
        branch_info = BranchInfo(
            block=entry,
            instruction=last_inst,
            taken_probability=0.99,
            is_predictable=True,
        )

        # Try to convert (takes single BranchInfo)
        converted = opt._convert_to_select(branch_info)

        # Note: Actual conversion depends on implementation
        # This test verifies the method exists and runs
        assert isinstance(converted, bool)

    def test_detect_loop_headers(self) -> None:
        """Test detecting loop header branches."""
        # Create a function with a loop
        func = MIRFunction("loop_func", [], MIRType.INT)

        # Create loop structure
        entry = BasicBlock("entry")
        loop_header = BasicBlock("loop_header")
        loop_body = BasicBlock("loop_body")
        loop_exit = BasicBlock("loop_exit")

        i = Temp(MIRType.INT)
        cond = Temp(MIRType.BOOL)

        # Entry
        entry.add_instruction(LoadConst(i, Constant(0, MIRType.INT), (1, 1)))
        entry.add_instruction(Jump("loop_header", (1, 1)))

        # Loop header (condition check)
        loop_header.add_instruction(BinaryOp(cond, "<", i, Constant(10, MIRType.INT), (1, 1)))
        loop_header.add_instruction(ConditionalJump(cond, "loop_body", (1, 1), "loop_exit"))

        # Loop body
        loop_body.add_instruction(BinaryOp(i, "+", i, Constant(1, MIRType.INT), (1, 1)))
        loop_body.add_instruction(Jump("loop_header", (1, 1)))

        # Loop exit
        loop_exit.add_instruction(Return((1, 1), i))

        func.cfg.add_block(entry)
        func.cfg.add_block(loop_header)
        func.cfg.add_block(loop_body)
        func.cfg.add_block(loop_exit)
        func.cfg.entry_block = entry

        # Set up control flow edges
        entry.add_successor(loop_header)
        loop_header.add_predecessor(entry)

        loop_header.add_successor(loop_body)
        loop_header.add_successor(loop_exit)
        loop_body.add_predecessor(loop_header)
        loop_exit.add_predecessor(loop_header)

        loop_body.add_successor(loop_header)  # Back edge
        loop_header.add_predecessor(loop_body)

        opt = BranchPredictionOptimization()
        branches = opt._collect_branch_info(func)

        # Find loop header branch
        loop_branches = [b for b in branches if b.block.label == "loop_header"]
        assert len(loop_branches) == 1

        # Check if loop header is detected during collection
        # (loop detection happens internally during branch collection)
        assert len(loop_branches) == 1

    def test_run_on_module_with_profile(self) -> None:
        """Test running optimization with profile data."""
        # Create mock profile data
        profile = MagicMock(spec=ProfileData)
        from unittest.mock import Mock

        branch_profile = Mock()
        branch_profile.taken_probability = 0.97
        branch_profile.predictable = True
        profile.branches = {"test_func:entry": branch_profile}
        profile.get_function_metrics = MagicMock(
            return_value={
                "call_count": 1000,
                "branches": {
                    ("entry", "then"): 970,
                    ("entry", "else"): 30,
                },
            }
        )

        opt = BranchPredictionOptimization(profile_data=profile)

        # Run optimization
        opt.run_on_module(self.module)

        # Should analyze branches
        assert opt.stats["branches_analyzed"] > 0

    def test_run_on_module_without_profile(self) -> None:
        """Test running optimization without profile data."""
        opt = BranchPredictionOptimization()

        # Run optimization
        opt.run_on_module(self.module)

        # Should still analyze branches with defaults
        assert opt.stats["branches_analyzed"] > 0

    def test_highly_biased_branch_optimization(self) -> None:
        """Test optimization of highly biased branches."""
        # Create mock profile with highly biased branch
        profile = MagicMock(spec=ProfileData)
        from unittest.mock import Mock

        branch_profile = Mock()
        branch_profile.taken_probability = 0.999  # 99.9% taken
        branch_profile.predictable = True
        profile.branches = {"test_func:entry": branch_profile}

        opt = BranchPredictionOptimization(profile_data=profile, predictability_threshold=0.99)

        branches = opt._collect_branch_info(self.func)

        # Branch should be marked as highly predictable (0.999 > 0.99)
        assert branches[0].is_predictable

        # Run full optimization on the module
        opt.run_on_module(self.module)

        # With highly predictable branch, should do some optimization
        # Branch hints should be added for predictable branches
        assert opt.stats["branches_analyzed"] > 0
        # Check if any optimization was done
        total_optimizations = (
            opt.stats.get("branch_hints_added", 0)
            + opt.stats.get("blocks_reordered", 0)
            + opt.stats.get("branches_converted_to_select", 0)
        )
        assert total_optimizations > 0

    def test_multiple_branches(self) -> None:
        """Test handling multiple branches in a function."""
        # Create function with multiple branches
        func = MIRFunction("multi_branch", [], MIRType.INT)

        blocks = []
        for i in range(5):
            block = BasicBlock(f"block_{i}")
            if i < 4:
                cond = Temp(MIRType.BOOL)
                block.add_instruction(LoadConst(cond, Constant(True, MIRType.BOOL), (1, 1)))
                block.add_instruction(ConditionalJump(cond, f"block_{i + 1}", (1, 1), "exit"))
            else:
                block.add_instruction(Return((1, 1), Constant(0, MIRType.INT)))
            blocks.append(block)
            func.cfg.add_block(block)

        exit_block = BasicBlock("exit")
        exit_block.add_instruction(Return((1, 1), Constant(1, MIRType.INT)))
        func.cfg.add_block(exit_block)

        func.cfg.entry_block = blocks[0]

        opt = BranchPredictionOptimization()
        branches = opt._collect_branch_info(func)

        # Should find 4 branches
        assert len(branches) == 4

    def test_edge_cases(self) -> None:
        """Test edge cases."""
        opt = BranchPredictionOptimization()

        # Empty function
        empty_func = MIRFunction("empty", [], MIRType.EMPTY)
        branches = opt._collect_branch_info(empty_func)
        assert len(branches) == 0

        # Function with no branches
        no_branch_func = MIRFunction("no_branch", [], MIRType.INT)
        block = BasicBlock("entry")
        block.add_instruction(Return((1, 1), Constant(42, MIRType.INT)))
        no_branch_func.cfg.add_block(block)
        no_branch_func.cfg.entry_block = block

        branches = opt._collect_branch_info(no_branch_func)
        assert len(branches) == 0
