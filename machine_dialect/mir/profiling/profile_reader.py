"""Profile reader for loading persisted profile data.

This module implements deserialization of profile data from disk
for use in profile-guided optimization.
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


class ProfileReader:
    """Reads profile data from disk in various formats."""

    def __init__(self) -> None:
        """Initialize the profile reader."""
        pass

    def read_json(self, filepath: Path | str) -> ProfileData:
        """Read profile data from JSON format.

        Args:
            filepath: Path to input file.

        Returns:
            Loaded profile data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Profile file not found: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        return self._dict_to_profile(data)

    def read_binary(self, filepath: Path | str) -> ProfileData:
        """Read profile data from binary format.

        Args:
            filepath: Path to input file.

        Returns:
            Loaded profile data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            pickle.UnpicklingError: If file is not valid pickle format.
        """
        import pickle

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Profile file not found: {filepath}")

        with open(filepath, "rb") as f:
            data = pickle.load(f)
            if not isinstance(data, ProfileData):
                raise ValueError(f"Invalid profile data type: {type(data)}")
            return data

    def read_auto(self, filepath: Path | str) -> ProfileData:
        """Automatically detect format and read profile data.

        Args:
            filepath: Path to input file.

        Returns:
            Loaded profile data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If format cannot be determined.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Profile file not found: {filepath}")

        # Try to detect format by extension
        if filepath.suffix == ".json":
            return self.read_json(filepath)
        elif filepath.suffix in [".pkl", ".pickle", ".bin"]:
            return self.read_binary(filepath)

        # Try to detect by content
        try:
            return self.read_json(filepath)
        except json.JSONDecodeError:
            try:
                return self.read_binary(filepath)
            except Exception as e:
                raise ValueError(f"Cannot determine profile format: {e}") from e

    def merge_profiles(self, filepaths: list[Path | str]) -> ProfileData:
        """Merge multiple profile files into one.

        Args:
            filepaths: List of profile file paths.

        Returns:
            Merged profile data.
        """
        if not filepaths:
            raise ValueError("No profile files provided")

        # Read first profile as base
        merged = self.read_auto(filepaths[0])

        # Merge remaining profiles
        for filepath in filepaths[1:]:
            profile = self.read_auto(filepath)
            merged.merge(profile)

        return merged

    def _dict_to_profile(self, data: dict[str, Any]) -> ProfileData:
        """Convert dictionary to profile data.

        Args:
            data: Dictionary representation.

        Returns:
            Profile data object.
        """
        profile = ProfileData(
            module_name=data.get("module_name", "default"),
            total_samples=data.get("total_samples", 0),
            metadata=data.get("metadata", {}),
        )

        # Load functions
        for name, func_data in data.get("functions", {}).items():
            profile.functions[name] = self._dict_to_function(func_data)

        # Load branches
        for loc, branch_data in data.get("branches", {}).items():
            profile.branches[loc] = self._dict_to_branch(branch_data)

        # Load loops
        for loc, loop_data in data.get("loops", {}).items():
            profile.loops[loc] = self._dict_to_loop(loop_data)

        # Load blocks
        for loc, block_data in data.get("blocks", {}).items():
            profile.blocks[loc] = self._dict_to_block(block_data)

        # Load indirect calls
        for loc, call_data in data.get("indirect_calls", {}).items():
            profile.indirect_calls[loc] = self._dict_to_indirect_call(call_data)

        return profile

    def _dict_to_function(self, data: dict[str, Any]) -> FunctionProfile:
        """Convert dictionary to function profile."""
        profile = FunctionProfile(
            name=data["name"],
            call_count=data.get("call_count", 0),
            total_cycles=data.get("total_cycles", 0),
            avg_cycles=data.get("avg_cycles", 0.0),
            call_sites=data.get("call_sites", {}),
            hot=data.get("hot", False),
            inline_benefit=data.get("inline_benefit", 0.0),
        )
        return profile

    def _dict_to_branch(self, data: dict[str, Any]) -> BranchProfile:
        """Convert dictionary to branch profile."""
        profile = BranchProfile(
            location=data["location"],
            taken_count=data.get("taken_count", 0),
            not_taken_count=data.get("not_taken_count", 0),
            taken_probability=data.get("taken_probability", 0.5),
            predictable=data.get("predictable", False),
        )
        return profile

    def _dict_to_loop(self, data: dict[str, Any]) -> LoopProfile:
        """Convert dictionary to loop profile."""
        min_iter_raw = data.get("min_iterations")
        min_iter: int = 2**31 - 1  # Use max int instead of infinity
        if min_iter_raw is not None:
            min_iter = int(min_iter_raw)

        profile = LoopProfile(
            location=data["location"],
            entry_count=data.get("entry_count", 0),
            total_iterations=data.get("total_iterations", 0),
            avg_iterations=data.get("avg_iterations", 0.0),
            max_iterations=data.get("max_iterations", 0),
            min_iterations=min_iter,
            hot=data.get("hot", False),
            unroll_benefit=data.get("unroll_benefit", 0.0),
        )
        return profile

    def _dict_to_block(self, data: dict[str, Any]) -> BasicBlockProfile:
        """Convert dictionary to basic block profile."""
        profile = BasicBlockProfile(
            location=data["location"],
            execution_count=data.get("execution_count", 0),
            instruction_count=data.get("instruction_count", 0),
            total_cycles=data.get("total_cycles", 0),
            avg_cycles=data.get("avg_cycles", 0.0),
            hot=data.get("hot", False),
        )
        return profile

    def _dict_to_indirect_call(self, data: dict[str, Any]) -> IndirectCallProfile:
        """Convert dictionary to indirect call profile."""
        profile = IndirectCallProfile(
            location=data["location"],
            targets=data.get("targets", {}),
            total_calls=data.get("total_calls", 0),
            most_common_target=data.get("most_common_target"),
            devirtualization_benefit=data.get("devirtualization_benefit", 0.0),
        )
        return profile

    def validate_profile(self, profile_data: ProfileData) -> list[str]:
        """Validate profile data for consistency.

        Args:
            profile_data: Profile data to validate.

        Returns:
            List of validation warnings/errors.
        """
        warnings = []

        # Check for empty profile
        if profile_data.total_samples == 0:
            warnings.append("Profile has no samples")

        # Check function consistency
        for name, func in profile_data.functions.items():
            if func.call_count == 0 and func.total_cycles > 0:
                warnings.append(f"Function {name} has cycles but no calls")
            if func.call_count > 0 and func.avg_cycles == 0:
                warnings.append(f"Function {name} has calls but no average cycles")

        # Check branch consistency
        for loc, branch in profile_data.branches.items():
            total = branch.taken_count + branch.not_taken_count
            if total == 0:
                warnings.append(f"Branch {loc} has no executions")
            elif abs(branch.taken_probability - (branch.taken_count / total)) > 0.01:
                warnings.append(f"Branch {loc} has inconsistent probability")

        # Check loop consistency
        for loc, loop in profile_data.loops.items():
            if loop.entry_count == 0 and loop.total_iterations > 0:
                warnings.append(f"Loop {loc} has iterations but no entries")
            if loop.max_iterations < loop.min_iterations:
                warnings.append(f"Loop {loc} has max < min iterations")

        return warnings
