"""Profile data structures for PGO.

This module defines the data structures used to store and manipulate
runtime profile information for profile-guided optimization.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProfileType(Enum):
    """Types of profile data collected."""

    FUNCTION_CALL = "function_call"
    BRANCH = "branch"
    LOOP = "loop"
    BASIC_BLOCK = "basic_block"
    INDIRECT_CALL = "indirect_call"


@dataclass
class FunctionProfile:
    """Profile data for a function.

    Attributes:
        name: Function name.
        call_count: Number of times the function was called.
        total_cycles: Total execution cycles (or time).
        avg_cycles: Average execution cycles per call.
        call_sites: Map of call site locations to call counts.
        hot: Whether this is a hot function.
        inline_benefit: Estimated benefit of inlining.
    """

    name: str
    call_count: int = 0
    total_cycles: int = 0
    avg_cycles: float = 0.0
    call_sites: dict[str, int] = field(default_factory=dict)
    hot: bool = False
    inline_benefit: float = 0.0

    def update_stats(self) -> None:
        """Update derived statistics."""
        if self.call_count > 0:
            self.avg_cycles = self.total_cycles / self.call_count
            # Mark as hot if called frequently or takes significant time
            self.hot = self.call_count > 100 or self.total_cycles > 10000
            # Calculate inline benefit based on call frequency and size
            self.inline_benefit = min(self.call_count * 0.1, 100.0)

    def merge(self, other: "FunctionProfile") -> None:
        """Merge another function profile into this one.

        Args:
            other: Profile to merge.
        """
        self.call_count += other.call_count
        self.total_cycles += other.total_cycles
        for site, count in other.call_sites.items():
            self.call_sites[site] = self.call_sites.get(site, 0) + count
        self.update_stats()


@dataclass
class BranchProfile:
    """Profile data for a branch instruction.

    Attributes:
        location: Branch location (function:block:instruction).
        taken_count: Number of times branch was taken.
        not_taken_count: Number of times branch was not taken.
        taken_probability: Probability of branch being taken.
        predictable: Whether branch is predictable.
    """

    location: str
    taken_count: int = 0
    not_taken_count: int = 0
    taken_probability: float = 0.5
    predictable: bool = False

    def update_stats(self) -> None:
        """Update derived statistics."""
        total = self.taken_count + self.not_taken_count
        if total > 0:
            self.taken_probability = self.taken_count / total
            # Branch is predictable if heavily biased
            self.predictable = self.taken_probability > 0.9 or self.taken_probability < 0.1

    def merge(self, other: "BranchProfile") -> None:
        """Merge another branch profile into this one.

        Args:
            other: Profile to merge.
        """
        self.taken_count += other.taken_count
        self.not_taken_count += other.not_taken_count
        self.update_stats()


@dataclass
class LoopProfile:
    """Profile data for a loop.

    Attributes:
        location: Loop location (function:loop_id).
        entry_count: Number of times loop was entered.
        total_iterations: Total iterations across all entries.
        avg_iterations: Average iterations per entry.
        max_iterations: Maximum iterations observed.
        min_iterations: Minimum iterations observed.
        hot: Whether this is a hot loop.
        unroll_benefit: Estimated benefit of unrolling.
    """

    location: str
    entry_count: int = 0
    total_iterations: int = 0
    avg_iterations: float = 0.0
    max_iterations: int = 0
    min_iterations: int = 2**31 - 1  # Use max int instead of infinity
    hot: bool = False
    unroll_benefit: float = 0.0

    def update_stats(self) -> None:
        """Update derived statistics."""
        if self.entry_count > 0:
            self.avg_iterations = self.total_iterations / self.entry_count
            # Mark as hot if executed frequently
            self.hot = self.total_iterations > 1000
            # Calculate unroll benefit for small, predictable loops
            if self.avg_iterations < 10 and self.max_iterations < 20:
                self.unroll_benefit = min(self.avg_iterations * 10, 100.0)

    def record_iteration(self, iterations: int) -> None:
        """Record a loop execution.

        Args:
            iterations: Number of iterations in this execution.
        """
        self.entry_count += 1
        self.total_iterations += iterations
        self.max_iterations = max(self.max_iterations, iterations)
        self.min_iterations = min(self.min_iterations, iterations)
        self.update_stats()

    def merge(self, other: "LoopProfile") -> None:
        """Merge another loop profile into this one.

        Args:
            other: Profile to merge.
        """
        self.entry_count += other.entry_count
        self.total_iterations += other.total_iterations
        self.max_iterations = max(self.max_iterations, other.max_iterations)
        self.min_iterations = min(self.min_iterations, other.min_iterations)
        self.update_stats()


@dataclass
class BasicBlockProfile:
    """Profile data for a basic block.

    Attributes:
        location: Block location (function:block_id).
        execution_count: Number of times block was executed.
        instruction_count: Number of instructions in block.
        total_cycles: Total execution cycles.
        avg_cycles: Average cycles per execution.
        hot: Whether this is a hot block.
    """

    location: str
    execution_count: int = 0
    instruction_count: int = 0
    total_cycles: int = 0
    avg_cycles: float = 0.0
    hot: bool = False

    def update_stats(self) -> None:
        """Update derived statistics."""
        if self.execution_count > 0:
            self.avg_cycles = self.total_cycles / self.execution_count
            # Mark as hot if executed frequently
            self.hot = self.execution_count > 100

    def merge(self, other: "BasicBlockProfile") -> None:
        """Merge another block profile into this one.

        Args:
            other: Profile to merge.
        """
        self.execution_count += other.execution_count
        self.total_cycles += other.total_cycles
        self.instruction_count = max(self.instruction_count, other.instruction_count)
        self.update_stats()


@dataclass
class IndirectCallProfile:
    """Profile data for indirect calls.

    Attributes:
        location: Call site location.
        targets: Map of target functions to call counts.
        total_calls: Total number of calls.
        most_common_target: Most frequently called target.
        devirtualization_benefit: Benefit of devirtualizing.
    """

    location: str
    targets: dict[str, int] = field(default_factory=dict)
    total_calls: int = 0
    most_common_target: str | None = None
    devirtualization_benefit: float = 0.0

    def record_call(self, target: str) -> None:
        """Record an indirect call.

        Args:
            target: Target function name.
        """
        self.targets[target] = self.targets.get(target, 0) + 1
        self.total_calls += 1
        self.update_stats()

    def update_stats(self) -> None:
        """Update derived statistics."""
        if self.targets:
            # Find most common target
            self.most_common_target = max(self.targets, key=self.targets.get)  # type: ignore
            # Calculate devirtualization benefit
            if self.most_common_target:
                freq = self.targets[self.most_common_target] / self.total_calls
                if freq > 0.8:  # If one target dominates
                    self.devirtualization_benefit = freq * 100

    def merge(self, other: "IndirectCallProfile") -> None:
        """Merge another indirect call profile.

        Args:
            other: Profile to merge.
        """
        for target, count in other.targets.items():
            self.targets[target] = self.targets.get(target, 0) + count
        self.total_calls += other.total_calls
        self.update_stats()


@dataclass
class ProfileData:
    """Complete profile data for a module.

    Attributes:
        module_name: Name of the profiled module.
        functions: Function profile data.
        branches: Branch profile data.
        loops: Loop profile data.
        blocks: Basic block profile data.
        indirect_calls: Indirect call profile data.
        total_samples: Total number of profile samples.
        metadata: Additional metadata.
    """

    module_name: str
    functions: dict[str, FunctionProfile] = field(default_factory=dict)
    branches: dict[str, BranchProfile] = field(default_factory=dict)
    loops: dict[str, LoopProfile] = field(default_factory=dict)
    blocks: dict[str, BasicBlockProfile] = field(default_factory=dict)
    indirect_calls: dict[str, IndirectCallProfile] = field(default_factory=dict)
    total_samples: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_hot_functions(self, threshold: int = 100) -> list[str]:
        """Get list of hot functions.

        Args:
            threshold: Minimum call count to be considered hot.

        Returns:
            List of hot function names.
        """
        return [name for name, profile in self.functions.items() if profile.call_count >= threshold or profile.hot]

    def get_hot_loops(self) -> list[str]:
        """Get list of hot loops.

        Returns:
            List of hot loop locations.
        """
        return [loc for loc, profile in self.loops.items() if profile.hot]

    def get_predictable_branches(self) -> list[str]:
        """Get list of predictable branches.

        Returns:
            List of predictable branch locations.
        """
        return [loc for loc, profile in self.branches.items() if profile.predictable]

    def merge(self, other: "ProfileData") -> None:
        """Merge another profile data into this one.

        Args:
            other: Profile data to merge.
        """
        # Merge functions
        for name, func_profile in other.functions.items():
            if name in self.functions:
                self.functions[name].merge(func_profile)
            else:
                self.functions[name] = func_profile

        # Merge branches
        for loc, branch_profile in other.branches.items():
            if loc in self.branches:
                self.branches[loc].merge(branch_profile)
            else:
                self.branches[loc] = branch_profile

        # Merge loops
        for loc, loop_profile in other.loops.items():
            if loc in self.loops:
                self.loops[loc].merge(loop_profile)
            else:
                self.loops[loc] = loop_profile

        # Merge blocks
        for loc, block_profile in other.blocks.items():
            if loc in self.blocks:
                self.blocks[loc].merge(block_profile)
            else:
                self.blocks[loc] = block_profile

        # Merge indirect calls
        for loc, call_profile in other.indirect_calls.items():
            if loc in self.indirect_calls:
                self.indirect_calls[loc].merge(call_profile)
            else:
                self.indirect_calls[loc] = call_profile

        self.total_samples += other.total_samples

    def get_summary(self) -> dict[str, Any]:
        """Get profile summary statistics.

        Returns:
            Dictionary of summary statistics.
        """
        return {
            "module": self.module_name,
            "total_samples": self.total_samples,
            "functions": {
                "total": len(self.functions),
                "hot": len(self.get_hot_functions()),
            },
            "branches": {
                "total": len(self.branches),
                "predictable": len(self.get_predictable_branches()),
            },
            "loops": {"total": len(self.loops), "hot": len(self.get_hot_loops())},
            "blocks": {
                "total": len(self.blocks),
                "hot": sum(1 for b in self.blocks.values() if b.hot),
            },
            "indirect_calls": {
                "total": len(self.indirect_calls),
                "devirtualizable": sum(1 for c in self.indirect_calls.values() if c.devirtualization_benefit > 50),
            },
        }
