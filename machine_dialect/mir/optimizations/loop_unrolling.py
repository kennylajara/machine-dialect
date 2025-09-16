"""Loop unrolling optimization pass.

This module implements loop unrolling to reduce loop overhead and enable
further optimizations by duplicating the loop body multiple times.
"""

from copy import deepcopy

from machine_dialect.mir.analyses.loop_analysis import Loop
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Jump,
    MIRInstruction,
)
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_values import Constant, MIRValue
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class LoopUnrolling(OptimizationPass):
    """Unroll small loops to reduce overhead.

    Attributes:
        unroll_threshold: Maximum unroll factor for loops.
        max_body_size: Maximum number of instructions in loop body.
        stats: Dictionary tracking optimization statistics.
    """

    def __init__(self) -> None:
        """Initialize loop unrolling pass.

        Sets default unroll threshold to 4 and maximum body size to 20
        instructions. Initializes statistics tracking.
        """
        super().__init__()
        self.unroll_threshold = 4  # Default unroll factor
        self.max_body_size = 20  # Maximum instructions in loop body
        self.stats = {"unrolled": 0, "loops_processed": 0}

    def initialize(self) -> None:
        """Initialize the pass before running."""
        self.stats = {"unrolled": 0, "loops_processed": 0}

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            PassInfo object describing this optimization pass.
        """
        return PassInfo(
            name="loop-unrolling",
            description="Unroll small loops to reduce overhead",
            pass_type=PassType.OPTIMIZATION,
            requires=["loop-analysis", "dominance"],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run loop unrolling on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        # Get required analyses
        loop_info = self.get_analysis("loop-analysis", function)
        dominance = self.get_analysis("dominance", function)

        if not loop_info or not dominance:
            return False

        # Get unroll threshold from config if available
        if hasattr(self, "config") and self.config:
            self.unroll_threshold = self.config.unroll_threshold

        transformer = MIRTransformer(function)
        modified = False

        # Process loops from innermost to outermost
        loops = self._get_loops_in_order(loop_info.loops if hasattr(loop_info, "loops") else [])

        for loop in loops:
            if self._should_unroll(loop, function):
                if self._unroll_loop(loop, function, transformer):
                    modified = True
                    self.stats["unrolled"] += 1
            self.stats["loops_processed"] += 1

        return modified

    def _get_loops_in_order(self, loops: list[Loop]) -> list[Loop]:
        """Get loops ordered from innermost to outermost.

        Args:
            loops: List of loops to order.

        Returns:
            Loops sorted by depth in descending order.
        """
        return sorted(loops, key=lambda loop: loop.depth, reverse=True)

    def _should_unroll(self, loop: Loop, function: MIRFunction) -> bool:
        """Determine if a loop should be unrolled.

        Args:
            loop: The loop to check.
            function: The containing function.

        Returns:
            True if the loop should be unrolled.
        """
        # Check loop size
        total_instructions = sum(len(block.instructions) for block in loop.blocks)
        if total_instructions > self.max_body_size:
            return False

        # Try to determine iteration count
        iteration_count = self._get_iteration_count(loop, function)
        if iteration_count is None:
            return False

        # Only unroll if iteration count is reasonable
        return 2 <= iteration_count <= self.unroll_threshold * 2

    def _get_iteration_count(self, loop: Loop, function: MIRFunction) -> int | None:
        """Try to determine the iteration count of a loop.

        Args:
            loop: The loop to analyze.
            function: The containing function.

        Returns:
            Number of iterations if determinable, None otherwise.

        Note:
            Currently implements a simple heuristic that looks for
            patterns like 'i = 0; while i < N; i++' with constant bounds.
        """
        # Simple heuristic: look for loops with constant bounds
        # This is a simplified version - real implementation would be more sophisticated

        # Look for pattern: i = 0; while i < N; i++
        header = loop.header

        # Find the loop condition
        for inst in header.instructions:
            if isinstance(inst, ConditionalJump):
                # Check if we're comparing against a constant
                cond_inst = self._find_defining_instruction(inst.condition, header)
                if isinstance(cond_inst, BinaryOp) and cond_inst.op in ["<", "<=", ">", ">="]:
                    # Check if one operand is a constant
                    if isinstance(cond_inst.right, Constant) and isinstance(cond_inst.right.value, int):
                        # Simple case: comparing against constant
                        limit = cond_inst.right.value
                        # Assume starting from 0 for now
                        if cond_inst.op == "<":
                            return limit
                        elif cond_inst.op == "<=":
                            return limit + 1

        return None

    def _find_defining_instruction(self, value: MIRValue, block: BasicBlock) -> MIRInstruction | None:
        """Find the instruction that defines a value.

        Args:
            value: The value whose definition to find.
            block: The basic block to search in.

        Returns:
            The instruction that defines the value, or None if not found.
        """
        for inst in block.instructions:
            if value in inst.get_defs():
                return inst
        return None

    def _unroll_loop(self, loop: Loop, function: MIRFunction, transformer: MIRTransformer) -> bool:
        """Unroll a loop by the unroll factor.

        Args:
            loop: The loop to unroll.
            function: The containing function.
            transformer: MIR transformer for applying changes.

        Returns:
            True if the loop was successfully unrolled.

        Note:
            Implements partial unrolling by duplicating the loop body
            up to the unroll factor, limited to 4 iterations.
        """
        unroll_factor = min(self.unroll_threshold, 4)  # Limit unrolling

        # For simplicity, we'll implement partial unrolling
        # Duplicate the loop body N times

        # Find the loop body (excluding header)
        loop_body_blocks = [b for b in loop.blocks if b != loop.header]

        if not loop_body_blocks:
            return False

        # Create copies of the loop body
        new_blocks = []
        for i in range(1, unroll_factor):
            # Clone each body block
            for block in loop_body_blocks:
                new_block = self._clone_block(block, f"_unroll_{i}")
                new_blocks.append(new_block)
                function.cfg.add_block(new_block)

        # Connect the cloned blocks
        if new_blocks:
            # Update control flow
            self._connect_unrolled_blocks(loop, new_blocks, loop_body_blocks, unroll_factor)

            # Update loop increment
            self._update_loop_increment(loop, unroll_factor)

            transformer.modified = True
            return True

        return False

    def _clone_block(self, block: BasicBlock, suffix: str) -> BasicBlock:
        """Clone a basic block with a new label.

        Args:
            block: Basic block to clone.
            suffix: Suffix to append to the new block's label.

        Returns:
            New BasicBlock instance with cloned instructions.
        """
        new_label = block.label + suffix
        new_block = BasicBlock(new_label)

        # Clone instructions
        for inst in block.instructions:
            new_inst = self._clone_instruction(inst, suffix)
            new_block.instructions.append(new_inst)

        return new_block

    def _clone_instruction(self, inst: MIRInstruction, suffix: str) -> MIRInstruction:
        """Clone an instruction, updating labels.

        Args:
            inst: Instruction to clone.
            suffix: Suffix for updating labels.

        Returns:
            Deep copy of the instruction.

        Note:
            Currently preserves original jump targets. A more complete
            implementation would update these based on the suffix.
        """
        # Deep copy the instruction
        new_inst = deepcopy(inst)

        # Update jump targets
        if isinstance(new_inst, Jump):
            # Keep original target for now
            pass
        elif isinstance(new_inst, ConditionalJump):
            # Keep original targets for now
            pass

        return new_inst

    def _connect_unrolled_blocks(
        self,
        loop: Loop,
        new_blocks: list[BasicBlock],
        original_body: list[BasicBlock],
        unroll_factor: int,
    ) -> None:
        """Connect the unrolled blocks properly.

        Args:
            loop: The original loop.
            new_blocks: New unrolled blocks to connect.
            original_body: Original loop body blocks.
            unroll_factor: Number of times the loop was unrolled.

        Note:
            This is a simplified implementation that chains blocks
            sequentially. A complete implementation would handle
            complex control flow graphs.
        """
        # This is simplified - real implementation would handle complex CFGs
        # For now, we just chain the blocks sequentially

        # blocks_per_iteration = len(original_body)  # Not used currently

        # Connect original body to first unrolled copy
        if original_body and new_blocks:
            last_original = original_body[-1]
            first_new = new_blocks[0]

            # Update jump at end of original body
            if last_original.instructions:
                last_inst = last_original.instructions[-1]
                if isinstance(last_inst, Jump):
                    # Instead of jumping back to header, jump to unrolled copy
                    last_inst.label = first_new.label

        # Connect unrolled copies to each other
        for i in range(len(new_blocks) - 1):
            current_block = new_blocks[i]
            next_block = new_blocks[i + 1]

            if current_block.instructions:
                last_inst = current_block.instructions[-1]
                if isinstance(last_inst, Jump):
                    last_inst.label = next_block.label

    def _update_loop_increment(self, loop: Loop, unroll_factor: int) -> None:
        """Update the loop increment to account for unrolling.

        Args:
            loop: The loop whose increment to update.
            unroll_factor: Number of times the loop was unrolled.

        Note:
            Searches for increment patterns like 'i = i + 1' and
            updates them to increment by the unroll factor.
        """
        # Find and update the loop counter increment
        # This is simplified - real implementation would be more sophisticated

        for block in loop.blocks:
            for inst in block.instructions:
                # Look for increment pattern: i = i + 1
                if isinstance(inst, BinaryOp) and inst.op == "+":
                    if isinstance(inst.right, Constant) and inst.right.value == 1:
                        # Update to increment by unroll_factor
                        new_const = Constant(unroll_factor)
                        inst.right = new_const

    def finalize(self) -> None:
        """Finalize the pass.

        Currently performs no finalization actions.
        """
        pass

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats
