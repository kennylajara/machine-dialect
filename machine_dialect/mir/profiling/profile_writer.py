"""Profile writer for persisting profile data.

This module implements serialization of profile data to disk for
reuse across compilation sessions.
"""

import json
from pathlib import Path
from typing import Any

from machine_dialect.mir.profiling.profile_data import (
    BasicBlockProfile,
    BranchProfile,
    FunctionProfile,
    IndirectCallProfile,
    LoopProfile,
    ProfileData,
)


class ProfileWriter:
    """Writes profile data to disk in various formats."""

    def __init__(self) -> None:
        """Initialize the profile writer."""
        pass

    def write_json(self, profile_data: ProfileData, filepath: Path | str) -> None:
        """Write profile data to JSON format.

        Args:
            profile_data: Profile data to write.
            filepath: Path to output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert profile data to JSON-serializable format
        data = self._profile_to_dict(profile_data)

        # Write to file with pretty formatting
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def write_binary(self, profile_data: ProfileData, filepath: Path | str) -> None:
        """Write profile data to efficient binary format.

        Args:
            profile_data: Profile data to write.
            filepath: Path to output file.
        """
        import pickle

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use pickle for binary serialization
        with open(filepath, "wb") as f:
            pickle.dump(profile_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def write_summary(self, profile_data: ProfileData, filepath: Path | str) -> None:
        """Write human-readable profile summary.

        Args:
            profile_data: Profile data to summarize.
            filepath: Path to output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            # Write header
            f.write(f"Profile Summary for Module: {profile_data.module_name}\n")
            f.write("=" * 60 + "\n\n")

            # Write statistics
            summary = profile_data.get_summary()
            f.write(f"Total Samples: {summary['total_samples']}\n\n")

            # Function statistics
            f.write("Functions:\n")
            f.write(f"  Total: {summary['functions']['total']}\n")
            f.write(f"  Hot: {summary['functions']['hot']}\n\n")

            # Hot functions details
            if profile_data.functions:
                f.write("Hot Functions (Top 10):\n")
                sorted_funcs = sorted(profile_data.functions.values(), key=lambda x: x.call_count, reverse=True)[:10]
                for func in sorted_funcs:
                    f.write(f"  {func.name}:\n")
                    f.write(f"    Calls: {func.call_count}\n")
                    f.write(f"    Avg Cycles: {func.avg_cycles:.2f}\n")
                    if func.inline_benefit > 0:
                        f.write(f"    Inline Benefit: {func.inline_benefit:.2f}\n")
                f.write("\n")

            # Branch statistics
            f.write("Branches:\n")
            f.write(f"  Total: {summary['branches']['total']}\n")
            f.write(f"  Predictable: {summary['branches']['predictable']}\n\n")

            # Predictable branches details
            predictable = [b for b in profile_data.branches.values() if b.predictable]
            if predictable:
                f.write("Predictable Branches (Top 10):\n")
                for branch in predictable[:10]:
                    f.write(f"  {branch.location}:\n")
                    f.write(f"    Taken: {branch.taken_probability:.1%}\n")
                f.write("\n")

            # Loop statistics
            f.write("Loops:\n")
            f.write(f"  Total: {summary['loops']['total']}\n")
            f.write(f"  Hot: {summary['loops']['hot']}\n\n")

            # Hot loops details
            hot_loops = [loop for loop in profile_data.loops.values() if loop.hot]
            if hot_loops:
                f.write("Hot Loops (Top 10):\n")
                sorted_loops = sorted(hot_loops, key=lambda x: x.total_iterations, reverse=True)[:10]
                for loop in sorted_loops:
                    f.write(f"  {loop.location}:\n")
                    f.write(f"    Iterations: {loop.total_iterations}\n")
                    f.write(f"    Avg per Entry: {loop.avg_iterations:.2f}\n")
                    if loop.unroll_benefit > 0:
                        f.write(f"    Unroll Benefit: {loop.unroll_benefit:.2f}\n")
                f.write("\n")

            # Indirect call statistics
            f.write("Indirect Calls:\n")
            f.write(f"  Total: {summary['indirect_calls']['total']}\n")
            f.write(f"  Devirtualizable: {summary['indirect_calls']['devirtualizable']}\n\n")

            # Devirtualization opportunities
            devirt = [c for c in profile_data.indirect_calls.values() if c.devirtualization_benefit > 50]
            if devirt:
                f.write("Devirtualization Opportunities:\n")
                for call in devirt:
                    f.write(f"  {call.location}:\n")
                    f.write(f"    Target: {call.most_common_target}\n")
                    f.write(f"    Benefit: {call.devirtualization_benefit:.2f}\n")

    def _profile_to_dict(self, profile_data: ProfileData) -> dict[str, Any]:
        """Convert profile data to dictionary.

        Args:
            profile_data: Profile data to convert.

        Returns:
            Dictionary representation.
        """
        return {
            "module_name": profile_data.module_name,
            "total_samples": profile_data.total_samples,
            "metadata": profile_data.metadata,
            "functions": {name: self._function_to_dict(prof) for name, prof in profile_data.functions.items()},
            "branches": {loc: self._branch_to_dict(prof) for loc, prof in profile_data.branches.items()},
            "loops": {loc: self._loop_to_dict(prof) for loc, prof in profile_data.loops.items()},
            "blocks": {loc: self._block_to_dict(prof) for loc, prof in profile_data.blocks.items()},
            "indirect_calls": {
                loc: self._indirect_call_to_dict(prof) for loc, prof in profile_data.indirect_calls.items()
            },
        }

    def _function_to_dict(self, profile: FunctionProfile) -> dict[str, Any]:
        """Convert function profile to dictionary."""
        return {
            "name": profile.name,
            "call_count": profile.call_count,
            "total_cycles": profile.total_cycles,
            "avg_cycles": profile.avg_cycles,
            "call_sites": profile.call_sites,
            "hot": profile.hot,
            "inline_benefit": profile.inline_benefit,
        }

    def _branch_to_dict(self, profile: BranchProfile) -> dict[str, Any]:
        """Convert branch profile to dictionary."""
        return {
            "location": profile.location,
            "taken_count": profile.taken_count,
            "not_taken_count": profile.not_taken_count,
            "taken_probability": profile.taken_probability,
            "predictable": profile.predictable,
        }

    def _loop_to_dict(self, profile: LoopProfile) -> dict[str, Any]:
        """Convert loop profile to dictionary."""
        # Handle max int as None for JSON
        min_iter = profile.min_iterations
        if min_iter == 2**31 - 1:  # Max int sentinel value
            min_iter_value: int | None = None
        else:
            min_iter_value = min_iter

        return {
            "location": profile.location,
            "entry_count": profile.entry_count,
            "total_iterations": profile.total_iterations,
            "avg_iterations": profile.avg_iterations,
            "max_iterations": profile.max_iterations,
            "min_iterations": min_iter_value,
            "hot": profile.hot,
            "unroll_benefit": profile.unroll_benefit,
        }

    def _block_to_dict(self, profile: BasicBlockProfile) -> dict[str, Any]:
        """Convert basic block profile to dictionary."""
        return {
            "location": profile.location,
            "execution_count": profile.execution_count,
            "instruction_count": profile.instruction_count,
            "total_cycles": profile.total_cycles,
            "avg_cycles": profile.avg_cycles,
            "hot": profile.hot,
        }

    def _indirect_call_to_dict(self, profile: IndirectCallProfile) -> dict[str, Any]:
        """Convert indirect call profile to dictionary."""
        return {
            "location": profile.location,
            "targets": profile.targets,
            "total_calls": profile.total_calls,
            "most_common_target": profile.most_common_target,
            "devirtualization_benefit": profile.devirtualization_benefit,
        }
