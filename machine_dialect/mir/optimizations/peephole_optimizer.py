"""Peephole optimizer for bytecode optimization.

This module implements pattern-based bytecode optimizations that look at
small windows of instructions to apply local optimizations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from machine_dialect.codegen.isa import Opcode
from machine_dialect.codegen.objects import Chunk


@dataclass
class OptimizationPattern:
    """Represents an optimization pattern.

    Attributes:
        name: Pattern name for debugging.
        pattern: Sequence of opcodes to match.
        replacement: Function to generate replacement bytecode.
        conditions: Additional conditions to check.
    """

    name: str
    pattern: list[Opcode | None]  # None matches any opcode
    replacement: Callable[[list[int], int, Any], list[int]]
    conditions: Callable[[list[int], int], bool] | None = None


class PeepholeOptimizer:
    """Performs peephole optimizations on bytecode."""

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self.patterns = self._create_patterns()
        self.stats = {
            "patterns_applied": 0,
            "bytes_saved": 0,
            "instructions_eliminated": 0,
        }

    def optimize_chunk(self, chunk: Chunk) -> Chunk:
        """Optimize a bytecode chunk.

        Args:
            chunk: The chunk to optimize.

        Returns:
            Optimized chunk.
        """
        # Create optimized bytecode
        optimized = []
        i = 0
        bytecode = list(chunk.bytecode)  # Convert bytearray to list

        while i < len(bytecode):
            # Try to match patterns
            matched = False
            for pattern in self.patterns:
                match_len = self._try_match_pattern(bytecode, i, pattern)
                if match_len > 0:
                    # Apply optimization
                    replacement = pattern.replacement(bytecode, i, chunk.constants)
                    optimized.extend(replacement)

                    # Track statistics
                    self.stats["patterns_applied"] += 1
                    self.stats["bytes_saved"] += match_len - len(replacement)

                    i += match_len
                    matched = True
                    break

            if not matched:
                # Copy instruction as-is
                opcode = bytecode[i]
                optimized.append(opcode)
                i += 1

                # Copy operands
                operand_size = self._get_operand_size(opcode)
                for _ in range(operand_size):
                    if i < len(bytecode):
                        optimized.append(bytecode[i])
                        i += 1

        # Create new chunk with optimized bytecode
        new_chunk = Chunk(chunk.name, chunk.chunk_type)
        new_chunk.bytecode = bytearray(optimized)  # Convert back to bytearray
        new_chunk.constants = chunk.constants
        new_chunk.num_locals = chunk.num_locals
        new_chunk.num_params = chunk.num_params

        return new_chunk

    def _create_patterns(self) -> list[OptimizationPattern]:
        """Create optimization patterns.

        Returns:
            List of optimization patterns.
        """
        patterns = []

        # Pattern: LOAD_CONST + LOAD_CONST + ADD → LOAD_CONST (folded)
        def fold_const_add(bytecode: list[int], pos: int, constants: Any) -> list[int]:
            # Extract constant indices
            idx1 = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            idx2 = bytecode[pos + 4] | (bytecode[pos + 5] << 8)

            # Get constant values
            val1 = constants.get(idx1)
            val2 = constants.get(idx2)

            # Compute folded value
            if isinstance(val1, int | float) and isinstance(val2, int | float):
                result = val1 + val2
                # Add new constant
                result_idx = constants.add(result)
                # Return single LOAD_CONST
                return [Opcode.LOAD_CONST, result_idx & 0xFF, (result_idx >> 8) & 0xFF]

            # Can't fold - return original
            return bytecode[pos : pos + 7]

        patterns.append(
            OptimizationPattern(
                name="const_add_folding",
                pattern=[Opcode.LOAD_CONST, None, None, Opcode.LOAD_CONST, None, None, Opcode.ADD],
                replacement=fold_const_add,
            )
        )

        # Pattern: LOAD_CONST + LOAD_CONST + SUB → LOAD_CONST (folded)
        def fold_const_sub(bytecode: list[int], pos: int, constants: Any) -> list[int]:
            idx1 = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            idx2 = bytecode[pos + 4] | (bytecode[pos + 5] << 8)
            val1 = constants.get(idx1)
            val2 = constants.get(idx2)

            if isinstance(val1, int | float) and isinstance(val2, int | float):
                result = val1 - val2
                result_idx = constants.add(result)
                return [Opcode.LOAD_CONST, result_idx & 0xFF, (result_idx >> 8) & 0xFF]

            return bytecode[pos : pos + 7]

        patterns.append(
            OptimizationPattern(
                name="const_sub_folding",
                pattern=[Opcode.LOAD_CONST, None, None, Opcode.LOAD_CONST, None, None, Opcode.SUB],
                replacement=fold_const_sub,
            )
        )

        # Pattern: LOAD_CONST + LOAD_CONST + MUL → LOAD_CONST (folded)
        def fold_const_mul(bytecode: list[int], pos: int, constants: Any) -> list[int]:
            idx1 = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            idx2 = bytecode[pos + 4] | (bytecode[pos + 5] << 8)
            val1 = constants.get(idx1)
            val2 = constants.get(idx2)

            if isinstance(val1, int | float) and isinstance(val2, int | float):
                result = val1 * val2
                result_idx = constants.add(result)
                return [Opcode.LOAD_CONST, result_idx & 0xFF, (result_idx >> 8) & 0xFF]

            return bytecode[pos : pos + 7]

        patterns.append(
            OptimizationPattern(
                name="const_mul_folding",
                pattern=[Opcode.LOAD_CONST, None, None, Opcode.LOAD_CONST, None, None, Opcode.MUL],
                replacement=fold_const_mul,
            )
        )

        # Pattern: JUMP to JUMP → direct JUMP
        def optimize_jump_chain(bytecode: list[int], pos: int, _constants: Any) -> list[int]:
            # Get first jump target
            offset1 = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            if offset1 >= 32768:
                offset1 = offset1 - 65536

            target1 = pos + 3 + offset1

            # Check if target is another jump
            if target1 < len(bytecode) - 2 and bytecode[target1] == Opcode.JUMP:
                # Get second jump target
                offset2 = bytecode[target1 + 1] | (bytecode[target1 + 2] << 8)
                if offset2 >= 32768:
                    offset2 = offset2 - 65536

                # Calculate combined offset
                final_target = target1 + 3 + offset2
                combined_offset = final_target - (pos + 3)

                # Convert to unsigned
                if combined_offset < 0:
                    combined_offset = (1 << 16) + combined_offset

                return [Opcode.JUMP, combined_offset & 0xFF, (combined_offset >> 8) & 0xFF]

            return bytecode[pos : pos + 3]

        patterns.append(
            OptimizationPattern(
                name="jump_threading",
                pattern=[Opcode.JUMP, None, None],
                replacement=optimize_jump_chain,
            )
        )

        # Pattern: STORE_LOCAL + LOAD_LOCAL (same slot) → DUP + STORE_LOCAL
        def optimize_store_load(bytecode: list[int], pos: int, _constants: Any) -> list[int]:
            slot1 = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            slot2 = bytecode[pos + 4] | (bytecode[pos + 5] << 8)

            if slot1 == slot2:
                # Replace with DUP + STORE_LOCAL
                return [Opcode.DUP, Opcode.STORE_LOCAL, bytecode[pos + 1], bytecode[pos + 2]]

            return bytecode[pos : pos + 6]

        patterns.append(
            OptimizationPattern(
                name="store_load_optimization",
                pattern=[Opcode.STORE_LOCAL, None, None, Opcode.LOAD_LOCAL, None, None],
                replacement=optimize_store_load,
            )
        )

        # Pattern: LOAD_CONST true + JUMP_IF_FALSE → remove both (dead code)
        def eliminate_dead_branch(bytecode: list[int], pos: int, constants: Any) -> list[int]:
            idx = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            val = constants.get(idx)

            if val is True:
                # True value never jumps on JUMP_IF_FALSE - eliminate both
                return []

            return bytecode[pos : pos + 6]

        patterns.append(
            OptimizationPattern(
                name="dead_branch_elimination",
                pattern=[Opcode.LOAD_CONST, None, None, Opcode.JUMP_IF_FALSE, None, None],
                replacement=eliminate_dead_branch,
            )
        )

        # Pattern: LOAD_CONST false + JUMP_IF_FALSE → JUMP (always jumps)
        def simplify_false_jump(bytecode: list[int], pos: int, constants: Any) -> list[int]:
            idx = bytecode[pos + 1] | (bytecode[pos + 2] << 8)
            val = constants.get(idx)

            if val is False:
                # False always jumps - convert to unconditional jump
                return [Opcode.JUMP, bytecode[pos + 4], bytecode[pos + 5]]

            return bytecode[pos : pos + 6]

        patterns.append(
            OptimizationPattern(
                name="false_jump_simplification",
                pattern=[Opcode.LOAD_CONST, None, None, Opcode.JUMP_IF_FALSE, None, None],
                replacement=simplify_false_jump,
            )
        )

        # Pattern: POP after non-side-effect operation → eliminate both
        def eliminate_unused_computation(bytecode: list[int], pos: int, _constants: Any) -> list[int]:
            opcode = bytecode[pos]

            # Check if operation has no side effects
            no_side_effect_ops = [
                Opcode.LOAD_CONST,
                Opcode.LOAD_LOCAL,
                Opcode.ADD,
                Opcode.SUB,
                Opcode.MUL,
                Opcode.DIV,
                Opcode.LT,
                Opcode.GT,
                Opcode.EQ,
                Opcode.NEQ,
                Opcode.NEG,
                Opcode.NOT,
            ]

            if opcode in no_side_effect_ops:
                # Skip the operation and the POP
                if opcode in [Opcode.LOAD_CONST, Opcode.LOAD_LOCAL]:
                    return []  # Eliminate LOAD + operands + POP
                else:
                    # For operations, we need to check if inputs are side-effect free too
                    # For now, just don't optimize these
                    pass

            return bytecode[pos : pos + self._get_instruction_size(bytecode, pos) + 1]

        # Note: This pattern is complex and needs more context, so we'll skip it for now

        return patterns

    def _try_match_pattern(self, bytecode: list[int], pos: int, pattern: OptimizationPattern) -> int:
        """Try to match a pattern at given position.

        Args:
            bytecode: The bytecode array.
            pos: Current position.
            pattern: Pattern to match.

        Returns:
            Length of match if successful, 0 otherwise.
        """
        pattern_bytes = pattern.pattern
        current_pos = pos

        for expected in pattern_bytes:
            if current_pos >= len(bytecode):
                return 0

            if expected is not None and bytecode[current_pos] != expected:
                return 0

            current_pos += 1

        # Check additional conditions if any
        if pattern.conditions and not pattern.conditions(bytecode, pos):
            return 0

        return current_pos - pos

    def _get_operand_size(self, opcode: int) -> int:
        """Get the operand size for an opcode.

        Args:
            opcode: The opcode.

        Returns:
            Number of operand bytes.
        """
        if opcode in [
            Opcode.LOAD_CONST,
            Opcode.LOAD_LOCAL,
            Opcode.STORE_LOCAL,
            Opcode.JUMP,
            Opcode.JUMP_IF_FALSE,
            Opcode.LOAD_GLOBAL,
            Opcode.STORE_GLOBAL,
            Opcode.LOAD_FUNCTION,
        ]:
            return 2  # 16-bit operand
        elif opcode == Opcode.CALL:
            return 1  # 8-bit argument count
        else:
            return 0  # No operands

    def _get_instruction_size(self, bytecode: list[int], pos: int) -> int:
        """Get total size of instruction at position.

        Args:
            bytecode: The bytecode array.
            pos: Position of instruction.

        Returns:
            Total size including operands.
        """
        if pos >= len(bytecode):
            return 0

        opcode = bytecode[pos]
        return 1 + self._get_operand_size(opcode)

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """Reset optimization statistics."""
        self.stats = {
            "patterns_applied": 0,
            "bytes_saved": 0,
            "instructions_eliminated": 0,
        }
