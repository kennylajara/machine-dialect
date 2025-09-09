"""Type narrowing optimization pass.

This module implements type narrowing based on runtime type checks,
allowing subsequent operations to use more specific type information.
"""

from dataclasses import dataclass
from typing import Any

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    LoadConst,
    MIRInstruction,
    TypeAssert,
    TypeCast,
    TypeCheck,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, MIRValue, Variable
from machine_dialect.mir.optimization_pass import (
    FunctionPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


@dataclass
class TypeConstraint:
    """Type constraint for a value at a program point.

    Attributes:
        value: The value being constrained.
        narrowed_type: The narrowed type after a check.
        valid_blocks: Set of blocks where this constraint is valid.
    """

    value: MIRValue
    narrowed_type: MIRType | MIRUnionType
    valid_blocks: set[Any]


class TypeNarrowing(FunctionPass):
    """Type narrowing optimization pass.

    This pass tracks type constraints from TypeCheck and TypeAssert
    instructions and propagates narrowed types through dominated blocks.
    """

    def __init__(self) -> None:
        """Initialize the type narrowing pass."""
        super().__init__()
        self.constraints: dict[MIRValue, TypeConstraint] = {}
        self.dominance_tree: dict[Any, set[Any]] = {}
        self.stats = {
            "types_narrowed": 0,
            "checks_eliminated": 0,
            "casts_eliminated": 0,
            "operations_specialized": 0,
        }

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="type-narrowing",
            description="Narrow types based on runtime type checks",
            pass_type=PassType.OPTIMIZATION,
            requires=["dominance"],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run type narrowing on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        modified = False

        # Build dominance tree
        self._build_dominance_tree(function)

        # First pass: collect type constraints from checks
        self._collect_type_constraints(function)

        # Second pass: apply narrowed types
        for block in function.cfg.blocks.values():
            if self._apply_type_narrowing(block, function):
                modified = True

        # Third pass: eliminate redundant checks
        for block in function.cfg.blocks.values():
            if self._eliminate_redundant_checks(block):
                modified = True

        return modified

    def _build_dominance_tree(self, function: MIRFunction) -> None:
        """Build dominance tree for the function.

        Simple approximation: a block dominates its successors in a
        straight-line path (no branches).

        Args:
            function: The function to analyze.
        """
        self.dominance_tree.clear()

        for block in function.cfg.blocks.values():
            dominated = set()

            # A block dominates itself
            dominated.add(block)

            # Find blocks dominated by this one
            # Simple heuristic: single successor with single predecessor
            current = block
            while len(current.successors) == 1:
                successor = current.successors[0]
                if len(successor.predecessors) == 1:
                    dominated.add(successor)
                    current = successor
                else:
                    break

            self.dominance_tree[block] = dominated

    def _collect_type_constraints(self, function: MIRFunction) -> None:
        """Collect type constraints from type checks.

        Args:
            function: The function to analyze.
        """
        self.constraints.clear()

        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, TypeCheck):
                    # TypeCheck creates a boolean result
                    # Track that after a successful check, the value has the checked type
                    self._add_constraint_from_check(inst, block, function)

                elif isinstance(inst, TypeAssert):
                    # TypeAssert guarantees the type after the assertion
                    self._add_constraint_from_assert(inst, block)

                elif isinstance(inst, ConditionalJump):
                    # Conditional jumps on type checks create constraints
                    self._add_constraint_from_branch(inst, block, function)

    def _add_constraint_from_check(self, inst: TypeCheck, block: BasicBlock, function: MIRFunction) -> None:
        """Add constraint from a TypeCheck instruction.

        Args:
            inst: TypeCheck instruction.
            block: Containing block.
            function: The containing function.
        """
        # Find where the check result is used
        for succ_block in block.successors:
            for succ_inst in succ_block.instructions:
                if isinstance(succ_inst, ConditionalJump) and succ_inst.condition == inst.dest:
                    # This check is used in a branch
                    # In the true branch, value has the checked type
                    if succ_inst.true_label:
                        true_block = self._find_block_by_label(function.cfg, succ_inst.true_label)
                        if true_block:
                            dominated = self.dominance_tree.get(true_block, set())
                            constraint = TypeConstraint(
                                value=inst.value, narrowed_type=inst.check_type, valid_blocks=dominated
                            )
                            self.constraints[inst.value] = constraint

    def _add_constraint_from_assert(self, inst: TypeAssert, block: BasicBlock) -> None:
        """Add constraint from a TypeAssert instruction.

        Args:
            inst: TypeAssert instruction.
            block: Containing block.
        """
        # After an assert, the value has the asserted type in dominated blocks
        dominated = self.dominance_tree.get(block, set())

        # Include successors in the constraint
        for succ in block.successors:
            succ_dominated = self.dominance_tree.get(succ, set())
            dominated = dominated.union(succ_dominated)

        constraint = TypeConstraint(value=inst.value, narrowed_type=inst.assert_type, valid_blocks=dominated)
        self.constraints[inst.value] = constraint

    def _add_constraint_from_branch(self, inst: ConditionalJump, block: BasicBlock, function: MIRFunction) -> None:
        """Add constraints from conditional branches on type checks.

        Args:
            inst: ConditionalJump instruction.
            block: Containing block.
            function: The containing function.
        """
        # Look for pattern: t = is_type(x, T); if t then ...
        for prev_inst in reversed(block.instructions):
            if isinstance(prev_inst, TypeCheck) and prev_inst.dest == inst.condition:
                # Found the type check
                if inst.true_label:
                    true_block = self._find_block_by_label(function.cfg, inst.true_label)
                    if true_block:
                        dominated = self.dominance_tree.get(true_block, set())
                        constraint = TypeConstraint(
                            value=prev_inst.value, narrowed_type=prev_inst.check_type, valid_blocks=dominated
                        )
                        self.constraints[prev_inst.value] = constraint
                break

    def _apply_type_narrowing(self, block: BasicBlock, function: MIRFunction) -> bool:
        """Apply narrowed types to operations in a block.

        Args:
            block: The block to optimize.
            function: The containing function.

        Returns:
            True if modifications were made.
        """
        modified = False
        new_instructions: list[MIRInstruction] = []

        for inst in block.instructions:
            optimized = self._optimize_with_narrowed_types(inst, block)

            if optimized != inst:
                new_instructions.append(optimized)
                self.stats["operations_specialized"] += 1
                modified = True
            else:
                new_instructions.append(inst)

        if modified:
            block.instructions = new_instructions

        return modified

    def _optimize_with_narrowed_types(self, inst: MIRInstruction, block: BasicBlock) -> MIRInstruction:
        """Optimize an instruction using narrowed type information.

        Args:
            inst: The instruction to optimize.
            block: The containing block.

        Returns:
            Optimized instruction or original.
        """
        if isinstance(inst, BinaryOp):
            # Check if operands have narrowed types
            left_type = self._get_narrowed_type(inst.left, block)
            right_type = self._get_narrowed_type(inst.right, block)

            # If both are known to be integers after narrowing, use integer operations
            if left_type == MIRType.INT and right_type == MIRType.INT:
                # Could mark this operation as integer-specific
                # For now, just track the optimization
                self.stats["types_narrowed"] += 1

        elif isinstance(inst, TypeCast):
            # Check if cast is unnecessary due to narrowing
            value_type = self._get_narrowed_type(inst.value, block)

            if value_type == inst.target_type:
                # Cast is redundant, replace with copy
                self.stats["casts_eliminated"] += 1
                return Copy(inst.dest, inst.value, inst.source_location)

        return inst

    def _eliminate_redundant_checks(self, block: BasicBlock) -> bool:
        """Eliminate redundant type checks.

        Args:
            block: The block to optimize.

        Returns:
            True if modifications were made.
        """
        modified = False
        new_instructions: list[MIRInstruction] = []

        for inst in block.instructions:
            if isinstance(inst, TypeCheck):
                # Check if we already know the type from a constraint
                narrowed_type = self._get_narrowed_type(inst.value, block)

                if narrowed_type == inst.check_type:
                    # Check will always succeed
                    new_inst = LoadConst(inst.dest, Constant(True, MIRType.BOOL), inst.source_location)
                    new_instructions.append(new_inst)
                    self.stats["checks_eliminated"] += 1
                    modified = True
                elif isinstance(narrowed_type, MIRType) and isinstance(inst.check_type, MIRType):
                    # Check if types are incompatible
                    if self._types_incompatible(narrowed_type, inst.check_type):
                        # Check will always fail
                        new_inst = LoadConst(inst.dest, Constant(False, MIRType.BOOL), inst.source_location)
                        new_instructions.append(new_inst)
                        self.stats["checks_eliminated"] += 1
                        modified = True
                    else:
                        new_instructions.append(inst)
                else:
                    new_instructions.append(inst)
            else:
                new_instructions.append(inst)

        if modified:
            block.instructions = new_instructions

        return modified

    def _get_narrowed_type(self, value: MIRValue, block: BasicBlock) -> MIRType | MIRUnionType | None:
        """Get the narrowed type of a value in a block.

        Args:
            value: The value to check.
            block: The current block.

        Returns:
            Narrowed type or None.
        """
        if isinstance(value, Constant):
            return value.type

        constraint = self.constraints.get(value)
        if constraint and block in constraint.valid_blocks:
            return constraint.narrowed_type

        # Check if value is a Variable with known type
        if isinstance(value, Variable):
            if isinstance(value.type, MIRUnionType):
                return None
            return value.type

        return None

    def _types_incompatible(self, type1: MIRType, type2: MIRType) -> bool:
        """Check if two types are incompatible.

        Args:
            type1: First type.
            type2: Second type.

        Returns:
            True if types are incompatible.
        """
        # Simple incompatibility check
        if type1 == type2:
            return False

        # Numeric types are somewhat compatible
        numeric_types = {MIRType.INT, MIRType.FLOAT}
        if type1 in numeric_types and type2 in numeric_types:
            return False

        # Otherwise, different types are incompatible
        return True

    def _find_block_by_label(self, cfg: CFG, label: str) -> BasicBlock | None:
        """Find a block by its label.

        Args:
            cfg: The CFG to search in.
            label: Block label.

        Returns:
            Block or None.
        """
        # Search through all blocks in the CFG
        for block in cfg.blocks.values():
            if hasattr(block, "label") and block.label == label:
                return block
        return None

    def finalize(self) -> None:
        """Finalize and report statistics."""
        if any(self.stats.values()):
            print("Type narrowing optimization statistics:")
            for key, value in self.stats.items():
                if value > 0:
                    print(f"  {key}: {value}")
