"""Virtual register allocation for MIR.

This module implements register allocation using linear scan algorithm.
"""

from dataclasses import dataclass

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import MIRInstruction
from machine_dialect.mir.mir_values import MIRValue, Temp, Variable


@dataclass
class LiveInterval:
    """Represents the live interval of a value.

    Attributes:
        value: The MIR value.
        start: Start position of the interval.
        end: End position of the interval.
        register: Allocated register/slot number.
    """

    value: MIRValue
    start: int
    end: int
    register: int | None = None


@dataclass
class RegisterAllocation:
    """Result of register allocation.

    Attributes:
        allocations: Mapping from MIR values to register numbers.
        spilled_values: Set of values that need to be spilled to memory.
        max_registers: Maximum number of registers used.
    """

    allocations: dict[MIRValue, int]
    spilled_values: set[MIRValue]
    max_registers: int


class RegisterAllocator:
    """Allocates virtual registers for MIR values using linear scan."""

    def __init__(self, function: MIRFunction, max_registers: int = 256) -> None:
        """Initialize the register allocator.

        Args:
            function: The MIR function to allocate registers for.
            max_registers: Maximum number of available registers.
        """
        self.function = function
        self.max_registers = max_registers
        self.live_intervals: list[LiveInterval] = []
        self.active_intervals: list[LiveInterval] = []
        self.free_registers: list[int] = list(range(max_registers))
        self.instruction_positions: dict[MIRInstruction, int] = {}
        self.spilled_values: set[MIRValue] = set()
        self.next_spill_slot = 0  # Track spill slot allocation

    def allocate(self) -> RegisterAllocation:
        """Perform register allocation.

        Returns:
            The register allocation result.
        """
        # Build instruction positions
        self._build_instruction_positions()

        # Compute live intervals
        self._compute_live_intervals()

        # Sort intervals by start position
        self.live_intervals.sort(key=lambda x: x.start)

        # Perform linear scan allocation
        allocations = self._linear_scan()

        # Calculate the actual number of registers used
        max_reg_used = 0
        for reg in allocations.values():
            if reg >= 0:  # Only count actual registers, not spill slots
                max_reg_used = max(max_reg_used, reg + 1)

        return RegisterAllocation(
            allocations=allocations, spilled_values=self.spilled_values, max_registers=max_reg_used
        )

    def _build_instruction_positions(self) -> None:
        """Build a mapping from instructions to positions."""
        position = 0
        for block in self.function.cfg.blocks.values():
            for inst in block.instructions:
                self.instruction_positions[inst] = position
                position += 1

    def _compute_live_intervals(self) -> None:
        """Compute live intervals for all values."""
        # Track first definition and last use for each value
        first_def: dict[MIRValue, int] = {}
        last_use: dict[MIRValue, int] = {}

        for block in self.function.cfg.blocks.values():
            for inst in block.instructions:
                position = self.instruction_positions[inst]

                # Process definitions
                for def_val in inst.get_defs():
                    if self._should_allocate(def_val):
                        if def_val not in first_def:
                            first_def[def_val] = position
                        last_use[def_val] = position  # Def is also a use

                # Process uses
                for use_val in inst.get_uses():
                    if self._should_allocate(use_val):
                        last_use[use_val] = position
                        if use_val not in first_def:
                            # Value used before defined (parameter or external)
                            first_def[use_val] = 0

        # Create intervals
        for value in first_def:
            interval = LiveInterval(value=value, start=first_def[value], end=last_use.get(value, first_def[value]))
            self.live_intervals.append(interval)

    def _should_allocate(self, value: MIRValue) -> bool:
        """Check if a value needs register allocation.

        Args:
            value: The value to check.

        Returns:
            True if the value needs a register.
        """
        # Allocate registers for temps and variables
        return isinstance(value, Temp | Variable)

    def _linear_scan(self) -> dict[MIRValue, int]:
        """Perform linear scan register allocation.

        Returns:
            Mapping from values to register numbers.
        """
        allocations: dict[MIRValue, int] = {}

        for interval in self.live_intervals:
            # Expire old intervals
            self._expire_old_intervals(interval.start)

            # Try to allocate a register
            if self.free_registers:
                # Allocate from free registers
                register = self.free_registers.pop(0)
                interval.register = register
                allocations[interval.value] = register
                self.active_intervals.append(interval)
                # Sort active intervals by end position
                self.active_intervals.sort(key=lambda x: x.end)
            else:
                # Need to spill - all registers are in use
                self._spill_at_interval(interval)
                if interval.register is not None:
                    # Got a register through spilling
                    allocations[interval.value] = interval.register
                    self.active_intervals.append(interval)
                    self.active_intervals.sort(key=lambda x: x.end)
                else:
                    # This interval was spilled to memory
                    self.spilled_values.add(interval.value)
                    # Assign a spill slot (using negative numbers for spill slots)
                    self.next_spill_slot += 1
                    allocations[interval.value] = -(self.max_registers + self.next_spill_slot)

        return allocations

    def _expire_old_intervals(self, current_position: int) -> None:
        """Expire intervals that are no longer live.

        Args:
            current_position: The current position in the program.
        """
        expired = []
        for interval in self.active_intervals:
            if interval.end >= current_position:
                break  # Sorted by end, so we can stop
            expired.append(interval)

        for interval in expired:
            self.active_intervals.remove(interval)
            if interval.register is not None and interval.register >= 0:
                self.free_registers.append(interval.register)
                self.free_registers.sort()

    def _spill_at_interval(self, interval: LiveInterval) -> None:
        """Spill a value when no registers are available.

        Args:
            interval: The interval that needs a register.
        """
        if not self.active_intervals:
            # No active intervals, must spill current
            self.spilled_values.add(interval.value)
            interval.register = None
            return

        # Find the interval with the furthest end point
        # (this is the last one since active_intervals is sorted by end)
        spill_candidate = self.active_intervals[-1]

        if spill_candidate.end > interval.end:
            # Spill the furthest interval and give its register to current
            self.active_intervals.remove(spill_candidate)
            interval.register = spill_candidate.register
            self.spilled_values.add(spill_candidate.value)
            spill_candidate.register = None
        else:
            # Current interval ends later, spill it instead
            self.spilled_values.add(interval.value)
            interval.register = None


class LifetimeAnalyzer:
    """Analyzes the lifetime of temporaries for optimization."""

    def __init__(self, function: MIRFunction) -> None:
        """Initialize the lifetime analyzer.

        Args:
            function: The function to analyze.
        """
        self.function = function
        self.lifetimes: dict[MIRValue, tuple[int, int]] = {}

    def analyze(self) -> dict[MIRValue, tuple[int, int]]:
        """Analyze lifetimes of all values.

        Returns:
            Mapping from values to (first_use, last_use) positions.
        """
        position = 0

        for block in self.function.cfg.blocks.values():
            for inst in block.instructions:
                # Track definitions
                for def_val in inst.get_defs():
                    if isinstance(def_val, Temp | Variable):
                        if def_val not in self.lifetimes:
                            self.lifetimes[def_val] = (position, position)
                        else:
                            start, _ = self.lifetimes[def_val]
                            self.lifetimes[def_val] = (start, position)

                # Track uses
                for use_val in inst.get_uses():
                    if isinstance(use_val, Temp | Variable):
                        if use_val not in self.lifetimes:
                            self.lifetimes[use_val] = (position, position)
                        else:
                            start, _ = self.lifetimes[use_val]
                            self.lifetimes[use_val] = (start, position)

                position += 1

        return self.lifetimes

    def find_reusable_slots(self) -> list[set[MIRValue]]:
        """Find sets of values that can share the same stack slot.

        Returns:
            List of sets where each set contains values that can share a slot.
        """
        reusable_groups: list[set[MIRValue]] = []

        # Sort values by start of lifetime
        sorted_values = sorted(self.lifetimes.items(), key=lambda x: x[1][0])

        for value, (start, end) in sorted_values:
            # Find a group where this value doesn't overlap with any member
            placed = False
            for group in reusable_groups:
                can_share = True
                for other in group:
                    other_start, other_end = self.lifetimes[other]
                    # Check for overlap
                    if not (end < other_start or start > other_end):
                        can_share = False
                        break

                if can_share:
                    group.add(value)
                    placed = True
                    break

            if not placed:
                # Create a new group
                reusable_groups.append({value})

        return reusable_groups
