"""Generic dataflow analysis framework for MIR.

This module provides a generic framework for implementing dataflow analyses
on the MIR, replacing ad-hoc analysis implementations with a uniform approach.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import MIRInstruction
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import MIRValue


@runtime_checkable
class Comparable(Protocol):
    """Protocol for comparable types."""

    def __lt__(self, other: Any) -> bool: ...

    def __le__(self, other: Any) -> bool: ...

    def __gt__(self, other: Any) -> bool: ...

    def __ge__(self, other: Any) -> bool: ...

    def __eq__(self, other: Any) -> bool: ...


# TypeVar for types that support ordering
T = TypeVar("T")
# Unconstrained type variable for DataFlowAnalysis
U = TypeVar("U")

# For now, we'll make Range non-generic for numeric types specifically
NumericValue = int | float


class Direction(Enum):
    """Direction of dataflow analysis."""

    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass
class Range:
    """Value range with support for strided and modular arithmetic.

    This replaces the simple tuple-based ranges with a rich representation
    that can express more complex constraints.

    Attributes:
        min: Minimum value (None for unbounded).
        max: Maximum value (None for unbounded).
        stride: Step size for values (e.g., all even numbers).
        modulo: Modular constraint (e.g., x % 4 == 0).
    """

    min: NumericValue | None = None
    max: NumericValue | None = None
    stride: NumericValue | None = None
    modulo: NumericValue | None = None

    def is_constant(self) -> bool:
        """Check if this range represents a single constant value."""
        return self.min is not None and self.min == self.max

    def contains(self, value: NumericValue) -> bool:
        """Check if a value is within this range.

        Args:
            value: The value to check.

        Returns:
            True if the value is in the range.
        """
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value > self.max:
            return False
        if self.stride is not None and self.min is not None:
            diff = value - self.min
            if diff % self.stride != 0:
                return False
        if self.modulo is not None:
            if value % self.modulo != 0:
                return False
        return True

    def intersect(self, other: "Range") -> "Range":
        """Compute intersection of two ranges.

        Args:
            other: The other range.

        Returns:
            The intersection range.
        """
        new_min = self.min
        if other.min is not None:
            new_min = other.min if new_min is None else max(new_min, other.min)

        new_max = self.max
        if other.max is not None:
            new_max = other.max if new_max is None else min(new_max, other.max)

        # Handle stride - use GCD for intersection
        new_stride = self.stride
        if other.stride is not None:
            if new_stride is None:
                new_stride = other.stride
            else:
                # Simplified - in reality would need GCD
                new_stride = max(new_stride, other.stride)

        # Handle modulo - use LCM for intersection
        new_modulo = self.modulo
        if other.modulo is not None:
            if new_modulo is None:
                new_modulo = other.modulo
            else:
                # Simplified - in reality would need LCM
                new_modulo = max(new_modulo, other.modulo)

        return Range(new_min, new_max, new_stride, new_modulo)

    def union(self, other: "Range") -> "Range":
        """Compute union of two ranges.

        Args:
            other: The other range.

        Returns:
            The union range.
        """
        new_min = self.min
        if other.min is not None:
            new_min = other.min if new_min is None else min(new_min, other.min)

        new_max = self.max
        if other.max is not None:
            new_max = other.max if new_max is None else max(new_max, other.max)

        # Union loses stride and modulo constraints unless they match
        new_stride = self.stride if self.stride == other.stride else None
        new_modulo = self.modulo if self.modulo == other.modulo else None

        return Range(new_min, new_max, new_stride, new_modulo)


@dataclass
class TypeContext:
    """Rich type context with refinements and constraints.

    This replaces the simple type dictionary with a comprehensive
    representation of type information.

    Attributes:
        base_type: The base MIR type.
        range: Value range for numeric types.
        nullable: Whether the value can be null/empty.
        refinements: Per-block type refinements.
        provenance: Source of type information.
    """

    base_type: MIRType
    range: Range | None = None
    nullable: bool = True
    refinements: dict[BasicBlock, MIRType] = field(default_factory=dict)
    provenance: str | None = None

    def refine_for_block(self, block: BasicBlock, refined_type: MIRType) -> None:
        """Add a type refinement for a specific block.

        Args:
            block: The block where the refinement applies.
            refined_type: The refined type in that block.
        """
        self.refinements[block] = refined_type

    def get_type_for_block(self, block: BasicBlock) -> MIRType:
        """Get the type for a specific block.

        Args:
            block: The block to query.

        Returns:
            The refined type for that block, or base type.
        """
        return self.refinements.get(block, self.base_type)


class DataFlowAnalysis(Generic[U], ABC):
    """Generic dataflow analysis framework.

    This provides a uniform way to implement dataflow analyses,
    replacing ad-hoc implementations throughout the codebase.
    """

    def __init__(self, direction: Direction = Direction.FORWARD) -> None:
        """Initialize the dataflow analysis.

        Args:
            direction: Direction of analysis (forward or backward).
        """
        self.direction = direction
        self.state: dict[BasicBlock, U] = {}
        self.entry_state: U | None = None
        self.exit_state: U | None = None

    @abstractmethod
    def initial_state(self) -> U:
        """Get the initial state for the analysis.

        Returns:
            The initial state.
        """
        pass

    @abstractmethod
    def transfer(self, inst: MIRInstruction, state: U) -> U:
        """Transfer function for an instruction.

        Args:
            inst: The instruction to process.
            state: The input state.

        Returns:
            The output state after the instruction.
        """
        pass

    @abstractmethod
    def meet(self, states: list[U]) -> U:
        """Meet operation for joining states.

        Args:
            states: States to join.

        Returns:
            The joined state.
        """
        pass

    def analyze(self, function: MIRFunction) -> dict[BasicBlock, U]:
        """Run the dataflow analysis on a function.

        Args:
            function: The function to analyze.

        Returns:
            Mapping from blocks to their computed states.
        """
        # Initialize all blocks with initial state
        for block in function.cfg.blocks.values():
            self.state[block] = self.initial_state()

        # Set entry/exit state
        if function.cfg.entry_block:
            self.entry_state = self.initial_state()
            self.state[function.cfg.entry_block] = self.entry_state

        # Iterate until fixpoint
        changed = True
        iteration = 0
        max_iterations = 100  # Prevent infinite loops

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            # Process blocks in appropriate order
            blocks = list(function.cfg.blocks.values())
            if self.direction == Direction.BACKWARD:
                blocks.reverse()

            for block in blocks:
                old_state = self.state[block]

                # Compute input state from predecessors/successors
                if self.direction == Direction.FORWARD:
                    pred_states = [self.state[pred] for pred in block.predecessors]
                    if pred_states:
                        input_state = self.meet(pred_states)
                    else:
                        input_state = self.initial_state()
                else:
                    succ_states = [self.state[succ] for succ in block.successors]
                    if succ_states:
                        input_state = self.meet(succ_states)
                    else:
                        input_state = self.initial_state()

                # Apply transfer function to all instructions
                current_state = input_state
                instructions = block.instructions
                if self.direction == Direction.BACKWARD:
                    instructions = list(reversed(instructions))

                for inst in instructions:
                    current_state = self.transfer(inst, current_state)

                # Update block state
                if current_state != old_state:
                    self.state[block] = current_state
                    changed = True

        return self.state


class TypePropagation(DataFlowAnalysis[dict[MIRValue, TypeContext]]):
    """Type propagation as a proper dataflow analysis.

    This replaces the ad-hoc type propagation in TypeSpecificOptimization.
    """

    def initial_state(self) -> dict[MIRValue, TypeContext]:
        """Get initial type state."""
        return {}

    def transfer(self, inst: MIRInstruction, state: dict[MIRValue, TypeContext]) -> dict[MIRValue, TypeContext]:
        """Transfer function for type propagation.

        Args:
            inst: The instruction to process.
            state: The input type state.

        Returns:
            The output type state.
        """
        new_state = state.copy()

        # This would be extended with actual type propagation logic
        # For now, just a placeholder
        for def_val in inst.get_defs():
            # Infer type from instruction
            new_state[def_val] = TypeContext(MIRType.UNKNOWN)

        return new_state

    def meet(self, states: list[dict[MIRValue, TypeContext]]) -> dict[MIRValue, TypeContext]:
        """Meet operation for type states.

        Args:
            states: Type states to join.

        Returns:
            The joined type state.
        """
        if not states:
            return {}

        result = states[0].copy()
        for state in states[1:]:
            # Merge type contexts
            for value, ctx in state.items():
                if value in result:
                    # Merge contexts - for now just keep first
                    # In reality would compute least upper bound
                    pass
                else:
                    result[value] = ctx

        return result


class RangeAnalysis(DataFlowAnalysis[dict[MIRValue, Range]]):
    """Range analysis as a proper dataflow analysis.

    This replaces the ad-hoc range tracking in TypeSpecificOptimization.
    """

    def initial_state(self) -> dict[MIRValue, Range]:
        """Get initial range state."""
        return {}

    def transfer(self, inst: MIRInstruction, state: dict[MIRValue, Range]) -> dict[MIRValue, Range]:
        """Transfer function for range analysis.

        Args:
            inst: The instruction to process.
            state: The input range state.

        Returns:
            The output range state.
        """
        new_state = state.copy()

        # This would be extended with actual range propagation logic
        # For now, just a placeholder
        from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst

        if isinstance(inst, LoadConst):
            # Constant has exact range
            if isinstance(inst.constant.value, int):
                new_state[inst.dest] = Range(inst.constant.value, inst.constant.value)
        elif isinstance(inst, BinaryOp):
            # Compute range from operands
            left_range = state.get(inst.left)
            right_range = state.get(inst.right)

            if left_range and right_range and inst.op == "+":
                # Addition of ranges
                if left_range.min is not None and right_range.min is not None:
                    new_min = left_range.min + right_range.min
                else:
                    new_min = None

                if left_range.max is not None and right_range.max is not None:
                    new_max = left_range.max + right_range.max
                else:
                    new_max = None

                new_state[inst.dest] = Range(new_min, new_max)

        return new_state

    def meet(self, states: list[dict[MIRValue, Range]]) -> dict[MIRValue, Range]:
        """Meet operation for range states.

        Args:
            states: Range states to join.

        Returns:
            The joined range state.
        """
        if not states:
            return {}

        result = states[0].copy()
        for state in states[1:]:
            # Merge ranges
            for value, range_val in state.items():
                if value in result:
                    # Union of ranges
                    result[value] = result[value].union(range_val)
                else:
                    result[value] = range_val

        return result
