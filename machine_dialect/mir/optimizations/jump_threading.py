"""Advanced jump threading optimizations for bytecode.

This module implements sophisticated jump threading optimizations that
follow chains of jumps and eliminate redundant control flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from machine_dialect.codegen.isa import Opcode
from machine_dialect.codegen.objects import Chunk
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import ModulePass, PassInfo, PassType, PreservationLevel


@dataclass
class BasicBlock:
    """Represents a basic block in control flow graph.

    Attributes:
        start: Start index in bytecode.
        end: End index in bytecode (exclusive).
        successors: List of successor block indices.
        predecessors: List of predecessor block indices.
        is_dead: Whether this block is unreachable.
    """

    start: int
    end: int
    successors: list[int]
    predecessors: list[int]
    is_dead: bool = False


class JumpThreadingOptimizer:
    """Performs advanced jump threading optimizations."""

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self.blocks: list[BasicBlock] = []
        self.block_map: dict[int, int] = {}  # bytecode index -> block index
        self.jump_targets: dict[int, int] = {}  # jump instruction -> target
        self.stats = {
            "jumps_threaded": 0,
            "blocks_eliminated": 0,
            "jumps_simplified": 0,
            "blocks_merged": 0,
        }

    def optimize(self, chunk: Chunk) -> Chunk:
        """Optimize jumps in a bytecode chunk.

        Args:
            chunk: The chunk to optimize.

        Returns:
            Optimized chunk.
        """
        bytecode = list(chunk.bytecode)

        # Build control flow graph
        self._build_cfg(bytecode)

        # Apply optimizations
        bytecode = self._thread_jumps(bytecode)
        bytecode = self._eliminate_dead_blocks(bytecode)
        bytecode = self._merge_blocks(bytecode)
        bytecode = self._simplify_conditional_jumps(bytecode, chunk.constants.constants())

        # Create optimized chunk
        new_chunk = Chunk(chunk.name, chunk.chunk_type)
        new_chunk.bytecode = bytearray(bytecode)
        new_chunk.constants = chunk.constants
        new_chunk.num_locals = chunk.num_locals
        new_chunk.num_params = chunk.num_params

        return new_chunk

    def _build_cfg(self, bytecode: list[int]) -> None:
        """Build control flow graph from bytecode.

        Args:
            bytecode: The bytecode to analyze.
        """
        self.blocks = []
        self.block_map = {}
        self.jump_targets = {}

        # First pass: identify jump targets and block boundaries
        jump_targets = set()
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]

            if opcode in [Opcode.JUMP, Opcode.JUMP_IF_FALSE]:
                # Get jump target
                if i + 2 < len(bytecode):
                    target = (bytecode[i + 1] << 8) | bytecode[i + 2]
                    jump_targets.add(target)
                    self.jump_targets[i] = target
                i += 3
            elif opcode == Opcode.RETURN:
                # Return ends a block
                i += 1
            else:
                i += self._get_instruction_size(opcode)

        # Second pass: create basic blocks
        block_start = 0
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]

            # Check if this is a jump target (start of new block)
            if i in jump_targets and i != block_start:
                # End current block
                self.blocks.append(BasicBlock(block_start, i, [], []))
                block_start = i

            # Check if this instruction ends a block
            is_terminator = opcode in [
                Opcode.JUMP,
                Opcode.JUMP_IF_FALSE,
                Opcode.RETURN,
            ]

            i += self._get_instruction_size(opcode)

            if is_terminator and i < len(bytecode):
                # End current block
                self.blocks.append(BasicBlock(block_start, i, [], []))
                block_start = i

        # Add final block if needed
        if block_start < len(bytecode):
            self.blocks.append(BasicBlock(block_start, len(bytecode), [], []))

        # Build block map
        for idx, block in enumerate(self.blocks):
            for pc in range(block.start, block.end):
                self.block_map[pc] = idx

        # Connect blocks (build successor/predecessor relationships)
        for idx, block in enumerate(self.blocks):
            if block.end > 0 and block.end - 3 >= block.start:
                last_pc = block.end - 3
                if last_pc in self.jump_targets:
                    target = self.jump_targets[last_pc]
                    if target in self.block_map:
                        target_block = self.block_map[target]
                        block.successors.append(target_block)
                        self.blocks[target_block].predecessors.append(idx)

                # Check for fall-through
                last_opcode: int | None = bytecode[last_pc] if last_pc < len(bytecode) else None
                if last_opcode not in [Opcode.JUMP, Opcode.RETURN] and idx + 1 < len(self.blocks):
                    block.successors.append(idx + 1)
                    self.blocks[idx + 1].predecessors.append(idx)

    def _thread_jumps(self, bytecode: list[int]) -> list[int]:
        """Thread jumps through chains of unconditional jumps.

        Args:
            bytecode: The bytecode to optimize.

        Returns:
            Optimized bytecode.
        """
        result = bytecode.copy()
        changed = True

        while changed:
            changed = False
            i = 0
            while i < len(result):
                opcode = result[i]

                if opcode in [Opcode.JUMP, Opcode.JUMP_IF_FALSE]:
                    if i + 2 < len(result):
                        target = (result[i + 1] << 8) | result[i + 2]

                        # Follow chain of jumps
                        final_target = self._follow_jump_chain(result, target)

                        if final_target != target:
                            # Update jump target
                            result[i + 1] = (final_target >> 8) & 0xFF
                            result[i + 2] = final_target & 0xFF
                            self.stats["jumps_threaded"] += 1
                            changed = True

                    i += 3
                else:
                    i += self._get_instruction_size(opcode)

        return result

    def _follow_jump_chain(self, bytecode: list[int], target: int, max_depth: int = 10) -> int:
        """Follow a chain of unconditional jumps to find final target.

        Args:
            bytecode: The bytecode.
            target: Initial jump target.
            max_depth: Maximum chain depth to follow.

        Returns:
            Final jump target.
        """
        visited = set()
        current = target
        depth = 0

        while depth < max_depth and current not in visited and current < len(bytecode):
            visited.add(current)

            # Check if target is an unconditional jump
            if current + 2 < len(bytecode) and bytecode[current] == Opcode.JUMP:
                # Get next target
                next_target = (bytecode[current + 1] << 8) | bytecode[current + 2]

                # Check if we're jumping to the next instruction (can eliminate)
                if next_target == current + 3:
                    return current + 3

                current = next_target
                depth += 1
            else:
                break

        return current

    def _eliminate_dead_blocks(self, bytecode: list[int]) -> list[int]:
        """Eliminate unreachable blocks.

        Args:
            bytecode: The bytecode.

        Returns:
            Bytecode with dead blocks replaced by NOPs.
        """
        # Mark reachable blocks (starting from block 0)
        reachable = set()
        worklist = [0]

        while worklist:
            block_idx = worklist.pop()
            if block_idx in reachable or block_idx >= len(self.blocks):
                continue

            reachable.add(block_idx)
            worklist.extend(self.blocks[block_idx].successors)

        # Replace unreachable blocks with NOPs
        result = bytecode.copy()
        for idx, block in enumerate(self.blocks):
            if idx not in reachable:
                # Replace block with NOPs
                for i in range(block.start, block.end):
                    result[i] = Opcode.POP
                self.stats["blocks_eliminated"] += 1
                block.is_dead = True

        return result

    def _merge_blocks(self, bytecode: list[int]) -> list[int]:
        """Merge blocks that can be combined.

        Args:
            bytecode: The bytecode.

        Returns:
            Optimized bytecode.
        """
        result = bytecode.copy()

        for block in self.blocks:
            if block.is_dead:
                continue

            # Check if this block has a single successor that has a single predecessor
            if len(block.successors) == 1:
                succ_idx = block.successors[0]
                if succ_idx < len(self.blocks):
                    succ_block = self.blocks[succ_idx]
                    if len(succ_block.predecessors) == 1 and not succ_block.is_dead:
                        # Check if the blocks are adjacent and the first ends with a jump
                        if block.end == succ_block.start and block.end >= 3:
                            last_opcode = result[block.end - 3]
                            if last_opcode == Opcode.JUMP:
                                # Remove the jump
                                for i in range(block.end - 3, block.end):
                                    result[i] = Opcode.POP
                                self.stats["blocks_merged"] += 1

        return result

    def _simplify_conditional_jumps(self, bytecode: list[int], constants: list[Any]) -> list[int]:
        """Simplify conditional jumps with constant conditions.

        Args:
            bytecode: The bytecode.
            constants: Constant pool.

        Returns:
            Optimized bytecode.
        """
        result = bytecode.copy()
        i = 0

        while i < len(result):
            opcode = result[i]

            # Check for constant load followed by conditional jump
            if opcode == Opcode.LOAD_CONST and i + 3 < len(result):
                const_idx = (result[i + 1] << 8) | result[i + 2]
                next_opcode = result[i + 3]

                if const_idx < len(constants):
                    const_value = constants[const_idx]

                    if next_opcode == Opcode.JUMP_IF_FALSE and i + 5 < len(result):
                        if not const_value:
                            # Always jump - replace with unconditional jump
                            result[i] = Opcode.JUMP
                            result[i + 1] = result[i + 4]
                            result[i + 2] = result[i + 5]
                            result[i + 3] = Opcode.POP
                            result[i + 4] = Opcode.POP
                            result[i + 5] = Opcode.POP
                        else:
                            # Never jump - remove both instructions
                            for j in range(i, i + 6):
                                result[j] = Opcode.POP
                        self.stats["jumps_simplified"] += 1
                        i += 6
                        continue

                    # Note: JUMP_IF_TRUE doesn't exist in current ISA

            i += self._get_instruction_size(opcode)

        return result

    def _get_instruction_size(self, opcode: int) -> int:
        """Get the size of an instruction including operands.

        Args:
            opcode: The opcode.

        Returns:
            Size in bytes.
        """
        # Instructions with 2-byte operands
        if opcode in [
            Opcode.LOAD_CONST,
            Opcode.LOAD_LOCAL,
            Opcode.STORE_LOCAL,
            Opcode.LOAD_GLOBAL,
            Opcode.STORE_GLOBAL,
            Opcode.JUMP,
            Opcode.JUMP_IF_FALSE,
            Opcode.LOAD_FUNCTION,
        ]:
            return 3

        # Instructions with 1-byte operands
        if opcode == Opcode.CALL:
            return 2

        # Instructions with no operands
        return 1

    def get_stats(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats


class JumpThreadingPass(ModulePass):
    """Jump threading optimization pass wrapper for MIR Pass interface."""

    def __init__(self) -> None:
        """Initialize the pass."""
        super().__init__()
        self.optimizer = JumpThreadingOptimizer()

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="jump-threading",
            description="Thread jumps and eliminate redundant control flow",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.NONE,
        )

    def run_on_module(self, module: MIRModule) -> bool:
        """Run jump threading on a module.

        Note: This is a bytecode-level optimization, not MIR-level.
        It would typically run after MIR->bytecode generation.

        Args:
            module: The module to optimize.

        Returns:
            False as this is a bytecode-level optimization.
        """
        # This pass operates on bytecode, not MIR
        # It's here for compatibility with the pass manager
        return False

    def finalize(self) -> None:
        """Finalize the pass."""
        pass

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.optimizer.get_stats().copy()
