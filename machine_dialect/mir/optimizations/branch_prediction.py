"""Branch prediction optimization pass.

This module uses profiling data to optimize branch layout and convert
predictable branches to more efficient code patterns.
"""

from dataclasses import dataclass

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    ConditionalJump,
    Jump,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import (
    ModulePass,
    PassInfo,
    PassType,
    PreservationLevel,
)
from machine_dialect.mir.profiling.profile_data import ProfileData


@dataclass
class BranchInfo:
    """Information about a branch for optimization.

    Attributes:
        block: The basic block containing the branch.
        instruction: The branch instruction.
        taken_probability: Probability of branch being taken.
        is_predictable: Whether branch is highly predictable.
        is_loop_header: Whether this is a loop header branch.
    """

    block: BasicBlock
    instruction: ConditionalJump
    taken_probability: float
    is_predictable: bool
    is_loop_header: bool = False


class BranchPredictionOptimization(ModulePass):
    """Branch prediction optimization pass.

    This pass uses profile data to:
    1. Reorder basic blocks for better branch prediction
    2. Convert highly predictable branches to conditional moves
    3. Add branch hints for the VM
    """

    def __init__(self, profile_data: ProfileData | None = None, predictability_threshold: float = 0.95) -> None:
        """Initialize branch prediction optimization.

        Args:
            profile_data: Optional profiling data with branch statistics.
            predictability_threshold: Threshold for considering branch predictable.
        """
        super().__init__()
        self.profile_data = profile_data
        self.predictability_threshold = predictability_threshold
        self.stats = {
            "branches_analyzed": 0,
            "blocks_reordered": 0,
            "branches_converted_to_select": 0,
            "branch_hints_added": 0,
        }

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="branch-prediction",
            description="Optimize branches using profile data",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def finalize(self) -> None:
        """Finalize the pass after running."""
        pass

    def run_on_module(self, module: MIRModule) -> bool:
        """Run branch prediction optimization on a module.

        Args:
            module: The module to optimize.

        Returns:
            True if the module was modified.
        """
        modified = False

        # Process each function
        for function in module.functions.values():
            if self._optimize_function_branches(function):
                modified = True

        return modified

    def _optimize_function_branches(self, function: MIRFunction) -> bool:
        """Optimize branches in a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        modified = False

        # Collect branch information
        branches = self._collect_branch_info(function)

        # Phase 1: Convert highly predictable branches to select instructions
        for branch_info in branches:
            if branch_info.is_predictable and self._can_convert_to_select(branch_info):
                if self._convert_to_select(branch_info):
                    self.stats["branches_converted_to_select"] += 1
                    modified = True

        # Phase 2: Reorder blocks for better branch prediction
        if self._reorder_blocks(function, branches):
            self.stats["blocks_reordered"] += 1
            modified = True

        # Phase 3: Add branch hints
        for branch_info in branches:
            if self._add_branch_hint(branch_info):
                self.stats["branch_hints_added"] += 1
                modified = True

        return modified

    def _collect_branch_info(self, function: MIRFunction) -> list[BranchInfo]:
        """Collect information about branches in a function.

        Args:
            function: The function to analyze.

        Returns:
            List of branch information.
        """
        branches = []

        for block_name, block in function.cfg.blocks.items():
            # Check if block ends with conditional jump
            if block.instructions:
                last_inst = block.instructions[-1]
                if isinstance(last_inst, ConditionalJump):
                    self.stats["branches_analyzed"] += 1

                    # Get profile data if available
                    taken_prob = 0.5  # Default to unpredictable
                    is_predictable = False

                    if self.profile_data:
                        # Look up branch profile
                        branch_key = f"{function.name}:{block_name}"
                        if branch_key in self.profile_data.branches:
                            branch_profile = self.profile_data.branches[branch_key]
                            taken_prob = branch_profile.taken_probability
                            is_predictable = branch_profile.predictable
                    else:
                        # Simple heuristic: backwards branches (loops) are likely taken
                        if last_inst.true_label < block_name:
                            taken_prob = 0.9
                            is_predictable = True

                    # Check if it's a loop header
                    is_loop_header = self._is_loop_header(function, block_name)

                    branches.append(
                        BranchInfo(
                            block=block,
                            instruction=last_inst,
                            taken_probability=taken_prob,
                            is_predictable=is_predictable
                            or (
                                taken_prob >= self.predictability_threshold
                                or taken_prob <= (1 - self.predictability_threshold)
                            ),
                            is_loop_header=is_loop_header,
                        )
                    )

        return branches

    def _is_loop_header(self, function: MIRFunction, block_name: str) -> bool:
        """Check if a block is a loop header.

        Args:
            function: The function containing the block.
            block_name: Name of the block to check.

        Returns:
            True if the block is a loop header.
        """
        # Simple heuristic: block has a back edge to itself
        block = function.cfg.blocks.get(block_name)
        if block and block.instructions:
            last_inst = block.instructions[-1]
            if isinstance(last_inst, ConditionalJump | Jump):
                # Check if it jumps back to itself or an earlier block
                targets = []
                if isinstance(last_inst, ConditionalJump):
                    targets = [last_inst.true_label]
                    if last_inst.false_label:
                        targets.append(last_inst.false_label)
                elif isinstance(last_inst, Jump):
                    targets = [last_inst.label]

                for target in targets:
                    if target <= block_name:  # Back edge
                        return True

        return False

    def _can_convert_to_select(self, branch_info: BranchInfo) -> bool:
        """Check if a branch can be converted to a select instruction.

        Args:
            branch_info: Information about the branch.

        Returns:
            True if conversion is possible.
        """
        # Don't convert loop headers (would break loop structure)
        if branch_info.is_loop_header:
            return False

        # Check if both targets are simple (single assignment followed by join)
        # This is a simplified check - real implementation would be more thorough

        # For now, only convert very simple patterns
        block = branch_info.block
        if len(block.instructions) < 2:
            return False

        # Look for pattern: compare, branch
        # Could be converted to: select

        return False  # Conservative for now

    def _convert_to_select(self, branch_info: BranchInfo) -> bool:
        """Convert a predictable branch to a select instruction.

        Args:
            branch_info: Information about the branch to convert.

        Returns:
            True if conversion was performed.
        """
        # This would convert patterns like:
        #   if (cond) { x = a; } else { x = b; }
        # To:
        #   x = select(cond, a, b)

        # For now, not implemented
        return False

    def _reorder_blocks(self, function: MIRFunction, branches: list[BranchInfo]) -> bool:
        """Reorder blocks to optimize branch prediction.

        Args:
            function: The function to reorder.
            branches: Branch information.

        Returns:
            True if blocks were reordered.
        """
        # Strategy: Place likely successors immediately after their predecessors
        # This makes the likely path fall-through (no taken branch)

        modified = False
        new_order: list[str] = []
        visited: set[str] = set()

        # Start with entry block
        entry = function.cfg.entry_block
        if not entry:
            return False

        # Build new order using likely paths
        work_list: list[str] = [entry.label]

        while work_list:
            current = work_list.pop(0)
            if current in visited:
                continue

            visited.add(current)
            new_order.append(current)

            # Find branch in this block
            block = function.cfg.blocks.get(current)
            if not block:
                continue

            # Find likely successor
            for branch_info in branches:
                if branch_info.block == block:
                    # Add likely target first (so it's next in layout)
                    if branch_info.taken_probability >= 0.5:
                        # Likely to take branch
                        if branch_info.instruction.true_label not in visited:
                            work_list.insert(0, branch_info.instruction.true_label)
                        if branch_info.instruction.false_label and branch_info.instruction.false_label not in visited:
                            work_list.append(branch_info.instruction.false_label)
                    else:
                        # Likely to fall through
                        if branch_info.instruction.false_label and branch_info.instruction.false_label not in visited:
                            work_list.insert(0, branch_info.instruction.false_label)
                        if branch_info.instruction.true_label not in visited:
                            work_list.append(branch_info.instruction.true_label)
                    break
            else:
                # No branch, add successors in order
                # (would need CFG successor information here)
                pass

        # Add any unvisited blocks
        for block_name in function.cfg.blocks:
            if block_name not in visited:
                new_order.append(block_name)

        # Check if order changed
        old_order = list(function.cfg.blocks.keys())
        if new_order != old_order:
            # Reorder the blocks dictionary
            # Note: In Python 3.7+, dict preserves insertion order
            new_blocks = {}
            for block_name in new_order:
                if block_name in function.cfg.blocks:
                    new_blocks[block_name] = function.cfg.blocks[block_name]
            function.cfg.blocks = new_blocks
            modified = True

        return modified

    def _add_branch_hint(self, branch_info: BranchInfo) -> bool:
        """Add branch prediction hint to instruction.

        Args:
            branch_info: Information about the branch.

        Returns:
            True if hint was added.
        """
        # Add hint as metadata on the instruction
        # The VM can use this to optimize branch prediction

        inst = branch_info.instruction

        # Add prediction hint attribute using type: ignore for dynamic attributes
        if not hasattr(inst, "prediction_hint"):
            if branch_info.taken_probability >= 0.5:
                inst.prediction_hint = "likely_taken"  # type: ignore[attr-defined]
            else:
                inst.prediction_hint = "likely_not_taken"  # type: ignore[attr-defined]

            # Also store the probability for more precise optimization
            inst.taken_probability = branch_info.taken_probability  # type: ignore[attr-defined]

            return True

        return False
