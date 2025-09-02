"""Profile collector for runtime profiling.

This module implements the profile collection mechanism that integrates
with the VM to gather runtime statistics for PGO.
"""

import time
from typing import Any

from machine_dialect.mir.profiling.profile_data import (
    BasicBlockProfile,
    BranchProfile,
    FunctionProfile,
    IndirectCallProfile,
    LoopProfile,
    ProfileData,
)


class ProfileCollector:
    """Collects runtime profile data during execution.

    This collector integrates with the VM to gather statistics about
    function calls, branches, loops, and basic blocks during program
    execution.
    """

    def __init__(self, module_name: str = "default") -> None:
        """Initialize the profile collector.

        Args:
            module_name: Name of the module being profiled.
        """
        self.profile_data = ProfileData(module_name=module_name)
        self.enabled = False
        self.sampling_rate = 1  # Sample every N events (1 = all events)
        self.sample_counter = 0

        # Stack for tracking function calls
        self.call_stack: list[tuple[str, float]] = []

        # Loop iteration tracking
        self.loop_stack: list[tuple[str, int]] = []

        # Current function context
        self.current_function: str | None = None
        self.current_block: str | None = None

    def enable(self, sampling_rate: int = 1) -> None:
        """Enable profile collection.

        Args:
            sampling_rate: Sample every N events (1 = all events).
        """
        self.enabled = True
        self.sampling_rate = max(1, sampling_rate)

    def disable(self) -> None:
        """Disable profile collection."""
        self.enabled = False

    def should_sample(self) -> bool:
        """Check if current event should be sampled.

        Returns:
            True if event should be sampled.
        """
        if not self.enabled:
            return False

        self.sample_counter += 1
        if self.sample_counter >= self.sampling_rate:
            self.sample_counter = 0
            return True
        return False

    def enter_function(self, function_name: str, call_site: str | None = None) -> None:
        """Record function entry.

        Args:
            function_name: Name of the function being entered.
            call_site: Location of the call site.
        """
        if not self.should_sample():
            return

        # Record entry time
        entry_time = time.perf_counter()
        self.call_stack.append((function_name, entry_time))

        # Update function profile
        if function_name not in self.profile_data.functions:
            self.profile_data.functions[function_name] = FunctionProfile(name=function_name)

        profile = self.profile_data.functions[function_name]
        profile.call_count += 1

        # Record call site if provided
        if call_site:
            profile.call_sites[call_site] = profile.call_sites.get(call_site, 0) + 1

        # Update context
        self.current_function = function_name
        self.profile_data.total_samples += 1

    def exit_function(self, function_name: str) -> None:
        """Record function exit.

        Args:
            function_name: Name of the function being exited.
        """
        if not self.enabled or not self.call_stack:
            return

        # Pop from call stack and calculate duration
        if self.call_stack and self.call_stack[-1][0] == function_name:
            _, entry_time = self.call_stack.pop()
            duration = time.perf_counter() - entry_time

            # Update function profile
            if function_name in self.profile_data.functions:
                profile = self.profile_data.functions[function_name]
                # Convert to cycles (approximate)
                cycles = int(duration * 1_000_000)  # Microseconds as proxy for cycles
                profile.total_cycles += cycles
                profile.update_stats()

        # Update context
        if self.call_stack:
            self.current_function = self.call_stack[-1][0]
        else:
            self.current_function = None

    def record_branch(self, location: str, taken: bool) -> None:
        """Record branch execution.

        Args:
            location: Branch location identifier.
            taken: Whether the branch was taken.
        """
        if not self.should_sample():
            return

        # Create or update branch profile
        if location not in self.profile_data.branches:
            self.profile_data.branches[location] = BranchProfile(location=location)

        profile = self.profile_data.branches[location]
        if taken:
            profile.taken_count += 1
        else:
            profile.not_taken_count += 1
        profile.update_stats()

        self.profile_data.total_samples += 1

    def enter_loop(self, loop_id: str) -> None:
        """Record loop entry.

        Args:
            loop_id: Loop identifier.
        """
        if not self.enabled:
            return

        # Push loop onto stack with iteration counter
        self.loop_stack.append((loop_id, 0))

    def record_loop_iteration(self) -> None:
        """Record a loop iteration."""
        if not self.enabled or not self.loop_stack:
            return

        # Increment iteration count for current loop
        loop_id, iterations = self.loop_stack[-1]
        self.loop_stack[-1] = (loop_id, iterations + 1)

    def exit_loop(self, loop_id: str) -> None:
        """Record loop exit.

        Args:
            loop_id: Loop identifier.
        """
        if not self.enabled or not self.loop_stack:
            return

        # Pop loop from stack and record iterations
        if self.loop_stack and self.loop_stack[-1][0] == loop_id:
            _, iterations = self.loop_stack.pop()

            # Only record if we sampled this loop
            if self.should_sample():
                if loop_id not in self.profile_data.loops:
                    self.profile_data.loops[loop_id] = LoopProfile(location=loop_id)

                profile = self.profile_data.loops[loop_id]
                profile.record_iteration(iterations)
                self.profile_data.total_samples += 1

    def enter_block(self, block_id: str) -> None:
        """Record basic block entry.

        Args:
            block_id: Block identifier.
        """
        if not self.should_sample():
            return

        # Create full block location
        if self.current_function:
            location = f"{self.current_function}:{block_id}"
        else:
            location = block_id

        # Create or update block profile
        if location not in self.profile_data.blocks:
            self.profile_data.blocks[location] = BasicBlockProfile(location=location)

        profile = self.profile_data.blocks[location]
        profile.execution_count += 1
        profile.update_stats()

        self.current_block = block_id
        self.profile_data.total_samples += 1

    def record_indirect_call(self, call_site: str, target: str) -> None:
        """Record an indirect call.

        Args:
            call_site: Location of the indirect call.
            target: Actual target function called.
        """
        if not self.should_sample():
            return

        # Create or update indirect call profile
        if call_site not in self.profile_data.indirect_calls:
            self.profile_data.indirect_calls[call_site] = IndirectCallProfile(location=call_site)

        profile = self.profile_data.indirect_calls[call_site]
        profile.record_call(target)
        self.profile_data.total_samples += 1

    def get_profile_data(self) -> ProfileData:
        """Get collected profile data.

        Returns:
            The collected profile data.
        """
        return self.profile_data

    def reset(self) -> None:
        """Reset all collected profile data."""
        module_name = self.profile_data.module_name
        self.profile_data = ProfileData(module_name=module_name)
        self.call_stack.clear()
        self.loop_stack.clear()
        self.current_function = None
        self.current_block = None
        self.sample_counter = 0

    def merge_profile(self, other_profile: ProfileData) -> None:
        """Merge another profile into this collector's data.

        Args:
            other_profile: Profile data to merge.
        """
        self.profile_data.merge(other_profile)

    def get_hot_path_hints(self) -> dict[str, Any]:
        """Get optimization hints based on hot paths.

        Returns:
            Dictionary of optimization hints.
        """
        hints: dict[str, Any] = {
            "hot_functions": self.profile_data.get_hot_functions(),
            "hot_loops": self.profile_data.get_hot_loops(),
            "predictable_branches": self.profile_data.get_predictable_branches(),
            "inline_candidates": [],
            "unroll_candidates": [],
            "devirtualize_candidates": [],
        }

        # Find inline candidates
        for name, func_profile in self.profile_data.functions.items():
            if func_profile.inline_benefit > 50:
                hints["inline_candidates"].append(
                    {
                        "function": name,
                        "benefit": func_profile.inline_benefit,
                        "call_count": func_profile.call_count,
                    }
                )

        # Find unroll candidates
        for loc, loop_profile in self.profile_data.loops.items():
            if loop_profile.unroll_benefit > 50:
                hints["unroll_candidates"].append(
                    {
                        "loop": loc,
                        "benefit": loop_profile.unroll_benefit,
                        "avg_iterations": loop_profile.avg_iterations,
                    }
                )

        # Find devirtualization candidates
        for loc, call_profile in self.profile_data.indirect_calls.items():
            if call_profile.devirtualization_benefit > 50:
                hints["devirtualize_candidates"].append(
                    {
                        "call_site": loc,
                        "target": call_profile.most_common_target,
                        "benefit": call_profile.devirtualization_benefit,
                    }
                )

        return hints
