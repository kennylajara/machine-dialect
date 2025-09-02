"""Loop analysis for MIR.

This module provides loop detection and characterization for
optimization passes like LICM and loop unrolling.
"""

from dataclasses import dataclass, field

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.optimization_pass import (
    FunctionAnalysisPass,
    PassInfo,
    PassType,
    PreservationLevel,
)
from machine_dialect.mir.ssa_construction import DominanceInfo


@dataclass
class Loop:
    """Represents a natural loop in the CFG.

    Attributes:
        header: Loop header block.
        back_edge: Back edge (latch -> header).
        blocks: Set of blocks in the loop.
        exits: Set of exit blocks from the loop.
        depth: Nesting depth (0 for outermost).
        parent: Parent loop if nested.
        children: Child loops if any.
    """

    header: BasicBlock
    back_edge: tuple[BasicBlock, BasicBlock]  # (from, to)
    blocks: set[BasicBlock]
    exits: set[BasicBlock]
    depth: int
    parent: "Loop | None" = None
    children: list["Loop"] = field(default_factory=list)

    def contains(self, block: BasicBlock) -> bool:
        """Check if a block is in this loop.

        Args:
            block: Block to check.

        Returns:
            True if block is in the loop.
        """
        return block in self.blocks

    def is_inner_loop(self) -> bool:
        """Check if this is an inner loop (no children).

        Returns:
            True if this is an inner loop.
        """
        return len(self.children) == 0


class LoopInfo:
    """Container for loop information in a function."""

    def __init__(self) -> None:
        """Initialize loop info."""
        self.loops: list[Loop] = []
        self.loop_map: dict[BasicBlock, Loop] = {}  # Header -> Loop
        self.block_to_loop: dict[BasicBlock, Loop] = {}  # Block -> Innermost loop

    def get_loop(self, header: BasicBlock) -> Loop | None:
        """Get loop by header block.

        Args:
            header: Loop header block.

        Returns:
            The loop or None.
        """
        return self.loop_map.get(header)

    def get_innermost_loop(self, block: BasicBlock) -> Loop | None:
        """Get the innermost loop containing a block.

        Args:
            block: The block.

        Returns:
            The innermost loop or None.
        """
        return self.block_to_loop.get(block)

    def get_loops_at_depth(self, depth: int) -> list[Loop]:
        """Get all loops at a specific depth.

        Args:
            depth: Nesting depth.

        Returns:
            List of loops at that depth.
        """
        return [loop for loop in self.loops if loop.depth == depth]

    def get_inner_loops(self) -> list[Loop]:
        """Get all inner loops.

        Returns:
            List of inner loops.
        """
        return [loop for loop in self.loops if loop.is_inner_loop()]


class LoopAnalysis(FunctionAnalysisPass):
    """Analysis pass that identifies loops in the CFG."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="loop-analysis",
            description="Identify and characterize loops",
            pass_type=PassType.ANALYSIS,
            requires=["dominance"],
            preserves=PreservationLevel.ALL,
        )

    def run_on_function(self, function: MIRFunction) -> LoopInfo:
        """Analyze loops in a function.

        Args:
            function: The function to analyze.

        Returns:
            Loop information.
        """
        loop_info = LoopInfo()

        # Get dominance information
        dominance = DominanceInfo(function.cfg)

        # Find back edges (edges where target dominates source)
        back_edges = self._find_back_edges(function, dominance)

        # Build natural loops from back edges
        for source, target in back_edges:
            loop = self._build_loop(source, target, dominance)
            loop_info.loops.append(loop)
            loop_info.loop_map[target] = loop

        # Determine loop nesting
        self._determine_nesting(loop_info)

        # Build block-to-loop mapping
        for loop in loop_info.loops:
            for block in loop.blocks:
                # Map to innermost loop
                if block not in loop_info.block_to_loop:
                    loop_info.block_to_loop[block] = loop
                else:
                    # Keep the innermost (highest depth)
                    if loop.depth > loop_info.block_to_loop[block].depth:
                        loop_info.block_to_loop[block] = loop

        return loop_info

    def _find_back_edges(
        self,
        function: MIRFunction,
        dominance: DominanceInfo,
    ) -> list[tuple[BasicBlock, BasicBlock]]:
        """Find back edges in the CFG.

        Args:
            function: The function.
            dominance: Dominance information.

        Returns:
            List of back edges (source, target).
        """
        back_edges = []

        for block in function.cfg.blocks.values():
            for succ in block.successors:
                # Check if successor dominates this block
                if dominance.dominates(succ, block):
                    back_edges.append((block, succ))

        return back_edges

    def _build_loop(
        self,
        latch: BasicBlock,
        header: BasicBlock,
        dominance: DominanceInfo,
    ) -> Loop:
        """Build a natural loop from a back edge.

        Args:
            latch: Latch block (source of back edge).
            header: Header block (target of back edge).
            dominance: Dominance information.

        Returns:
            The constructed loop.
        """
        # Natural loop consists of header and all blocks that can
        # reach latch without going through header
        loop_blocks = {header, latch}
        worklist = [latch]

        while worklist:
            block = worklist.pop()
            for pred in block.predecessors:
                if pred not in loop_blocks:
                    loop_blocks.add(pred)
                    worklist.append(pred)

        # Find exit blocks
        exits = set()
        for block in loop_blocks:
            for succ in block.successors:
                if succ not in loop_blocks:
                    exits.add(succ)

        return Loop(
            header=header,
            back_edge=(latch, header),
            blocks=loop_blocks,
            exits=exits,
            depth=0,  # Will be set later
        )

    def _determine_nesting(self, loop_info: LoopInfo) -> None:
        """Determine loop nesting relationships.

        Args:
            loop_info: Loop information to update.
        """
        # Sort loops by size (smaller loops are likely inner)
        loops = sorted(loop_info.loops, key=lambda loop: len(loop.blocks))

        # Determine parent-child relationships
        for i, inner in enumerate(loops):
            for outer in loops[i + 1 :]:
                # Check if inner is contained in outer
                if inner.header in outer.blocks and inner.blocks.issubset(outer.blocks):
                    if inner.parent is None:
                        inner.parent = outer
                        outer.children.append(inner)

        # Set depths
        for loop in loop_info.loops:
            if loop.parent is None:
                self._set_depth(loop, 0)

    def _set_depth(self, loop: Loop, depth: int) -> None:
        """Set loop depth recursively.

        Args:
            loop: The loop.
            depth: Depth to set.
        """
        loop.depth = depth
        for child in loop.children:
            self._set_depth(child, depth + 1)

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
