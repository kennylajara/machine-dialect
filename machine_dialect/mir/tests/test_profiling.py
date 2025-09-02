"""Tests for profiling infrastructure."""

import tempfile
from pathlib import Path

from machine_dialect.mir.profiling import (
    BranchProfile,
    FunctionProfile,
    LoopProfile,
    ProfileCollector,
    ProfileData,
    ProfileReader,
    ProfileWriter,
)


class TestProfileData:
    """Test profile data structures."""

    def test_function_profile(self) -> None:
        """Test function profile creation and updates."""
        profile = FunctionProfile(name="test_func")
        assert profile.name == "test_func"
        assert profile.call_count == 0
        assert not profile.hot

        # Update with calls
        profile.call_count = 150
        profile.total_cycles = 15000
        profile.update_stats()

        assert profile.hot
        assert profile.avg_cycles == 100.0
        assert profile.inline_benefit > 0

    def test_branch_profile(self) -> None:
        """Test branch profile creation and updates."""
        profile = BranchProfile(location="func:block:1")
        assert profile.location == "func:block:1"
        assert not profile.predictable

        # Update with biased branch
        profile.taken_count = 95
        profile.not_taken_count = 5
        profile.update_stats()

        assert profile.predictable
        assert profile.taken_probability == 0.95

    def test_loop_profile(self) -> None:
        """Test loop profile creation and iteration tracking."""
        profile = LoopProfile(location="func:loop1")
        assert profile.location == "func:loop1"
        assert not profile.hot

        # Record iterations
        profile.record_iteration(10)
        profile.record_iteration(12)
        profile.record_iteration(8)

        assert profile.entry_count == 3
        assert profile.total_iterations == 30
        assert profile.avg_iterations == 10.0
        assert profile.max_iterations == 12
        assert profile.min_iterations == 8

    def test_profile_data_merge(self) -> None:
        """Test merging profile data."""
        profile1 = ProfileData(module_name="test")
        profile1.functions["func1"] = FunctionProfile(name="func1", call_count=10)
        profile1.branches["branch1"] = BranchProfile(location="branch1", taken_count=5, not_taken_count=3)

        profile2 = ProfileData(module_name="test")
        profile2.functions["func1"] = FunctionProfile(name="func1", call_count=5)
        profile2.functions["func2"] = FunctionProfile(name="func2", call_count=3)
        profile2.branches["branch1"] = BranchProfile(location="branch1", taken_count=2, not_taken_count=1)

        profile1.merge(profile2)

        assert profile1.functions["func1"].call_count == 15
        assert "func2" in profile1.functions
        assert profile1.branches["branch1"].taken_count == 7
        assert profile1.branches["branch1"].not_taken_count == 4

    def test_hot_function_detection(self) -> None:
        """Test detection of hot functions."""
        profile = ProfileData(module_name="test")
        profile.functions["cold"] = FunctionProfile(name="cold", call_count=10)
        profile.functions["hot"] = FunctionProfile(name="hot", call_count=200)
        profile.functions["hot"].update_stats()

        hot_funcs = profile.get_hot_functions(threshold=100)
        assert "hot" in hot_funcs
        assert "cold" not in hot_funcs


class TestProfileCollector:
    """Test profile collection functionality."""

    def test_collector_initialization(self) -> None:
        """Test collector initialization."""
        collector = ProfileCollector("test_module")
        assert collector.profile_data.module_name == "test_module"
        assert not collector.enabled
        assert collector.sampling_rate == 1

    def test_function_profiling(self) -> None:
        """Test function entry/exit profiling."""
        collector = ProfileCollector()
        collector.enable()

        # Enter and exit function
        collector.enter_function("test_func", "main:10")
        collector.exit_function("test_func")

        profile_data = collector.get_profile_data()
        assert "test_func" in profile_data.functions
        func_profile = profile_data.functions["test_func"]
        assert func_profile.call_count == 1
        assert "main:10" in func_profile.call_sites

    def test_branch_profiling(self) -> None:
        """Test branch profiling."""
        collector = ProfileCollector()
        collector.enable()

        # Record branch executions
        collector.record_branch("func:block:1", taken=True)
        collector.record_branch("func:block:1", taken=True)
        collector.record_branch("func:block:1", taken=False)

        profile_data = collector.get_profile_data()
        assert "func:block:1" in profile_data.branches
        branch_profile = profile_data.branches["func:block:1"]
        assert branch_profile.taken_count == 2
        assert branch_profile.not_taken_count == 1

    def test_loop_profiling(self) -> None:
        """Test loop profiling."""
        collector = ProfileCollector()
        collector.enable()

        # Profile a loop
        collector.enter_loop("func:loop1")
        for _ in range(5):
            collector.record_loop_iteration()
        collector.exit_loop("func:loop1")

        profile_data = collector.get_profile_data()
        assert "func:loop1" in profile_data.loops
        loop_profile = profile_data.loops["func:loop1"]
        assert loop_profile.entry_count == 1
        assert loop_profile.total_iterations == 5

    def test_sampling(self) -> None:
        """Test sampling rate functionality."""
        collector = ProfileCollector()
        collector.enable(sampling_rate=2)  # Sample every 2nd event

        # Only every 2nd function call should be recorded
        collector.enter_function("func1")
        collector.exit_function("func1")
        collector.enter_function("func2")
        collector.exit_function("func2")

        profile_data = collector.get_profile_data()
        # Due to sampling, only one function should be recorded
        assert len(profile_data.functions) == 1

    def test_hot_path_hints(self) -> None:
        """Test generation of optimization hints."""
        collector = ProfileCollector()
        collector.enable()

        # Create hot function
        for _ in range(200):
            collector.enter_function("hot_func")
            collector.exit_function("hot_func")

        # Create predictable branch
        for _ in range(100):
            collector.record_branch("predictable", taken=True)
        for _ in range(5):
            collector.record_branch("predictable", taken=False)

        hints = collector.get_hot_path_hints()
        assert "hot_func" in hints["hot_functions"]
        assert "predictable" in hints["predictable_branches"]


class TestProfilePersistence:
    """Test profile reading and writing."""

    def test_json_roundtrip(self) -> None:
        """Test JSON serialization and deserialization."""
        # Create profile data
        profile = ProfileData(module_name="test")
        profile.functions["func1"] = FunctionProfile(name="func1", call_count=100, total_cycles=1000)
        profile.branches["branch1"] = BranchProfile(location="branch1", taken_count=75, not_taken_count=25)
        profile.loops["loop1"] = LoopProfile(location="loop1", entry_count=10)

        # Write and read
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = Path(f.name)

        try:
            writer = ProfileWriter()
            writer.write_json(profile, filepath)

            reader = ProfileReader()
            loaded = reader.read_json(filepath)

            # Verify data
            assert loaded.module_name == "test"
            assert "func1" in loaded.functions
            assert loaded.functions["func1"].call_count == 100
            assert "branch1" in loaded.branches
            assert loaded.branches["branch1"].taken_count == 75
            assert "loop1" in loaded.loops
            assert loaded.loops["loop1"].entry_count == 10
        finally:
            filepath.unlink()

    def test_binary_roundtrip(self) -> None:
        """Test binary serialization and deserialization."""
        # Create profile data
        profile = ProfileData(module_name="test")
        profile.functions["func1"] = FunctionProfile(name="func1", call_count=50)
        profile.total_samples = 1000

        # Write and read
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            filepath = Path(f.name)

        try:
            writer = ProfileWriter()
            writer.write_binary(profile, filepath)

            reader = ProfileReader()
            loaded = reader.read_binary(filepath)

            # Verify data
            assert loaded.module_name == "test"
            assert loaded.total_samples == 1000
            assert loaded.functions["func1"].call_count == 50
        finally:
            filepath.unlink()

    def test_auto_format_detection(self) -> None:
        """Test automatic format detection."""
        profile = ProfileData(module_name="test")
        profile.functions["func1"] = FunctionProfile(name="func1")

        reader = ProfileReader()
        writer = ProfileWriter()

        # Test JSON detection
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            json_path = Path(f.name)

        try:
            writer.write_json(profile, json_path)
            loaded = reader.read_auto(json_path)
            assert loaded.module_name == "test"
        finally:
            json_path.unlink()

        # Test binary detection
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pkl_path = Path(f.name)

        try:
            writer.write_binary(profile, pkl_path)
            loaded = reader.read_auto(pkl_path)
            assert loaded.module_name == "test"
        finally:
            pkl_path.unlink()

    def test_profile_merging(self) -> None:
        """Test merging multiple profile files."""
        # Create profiles
        profile1 = ProfileData(module_name="test")
        profile1.functions["func1"] = FunctionProfile(name="func1", call_count=10)

        profile2 = ProfileData(module_name="test")
        profile2.functions["func1"] = FunctionProfile(name="func1", call_count=5)
        profile2.functions["func2"] = FunctionProfile(name="func2", call_count=3)

        # Write profiles
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "profile1.json"
            path2 = Path(tmpdir) / "profile2.json"

            writer = ProfileWriter()
            writer.write_json(profile1, path1)
            writer.write_json(profile2, path2)

            # Merge profiles
            reader = ProfileReader()
            merged = reader.merge_profiles([path1, path2])

            assert merged.functions["func1"].call_count == 15
            assert merged.functions["func2"].call_count == 3

    def test_summary_generation(self) -> None:
        """Test human-readable summary generation."""
        profile = ProfileData(module_name="test")

        # Add hot function
        hot_func = FunctionProfile(name="hot_func", call_count=1000, total_cycles=100000)
        hot_func.update_stats()
        profile.functions["hot_func"] = hot_func

        # Add predictable branch
        branch = BranchProfile(location="branch1", taken_count=95, not_taken_count=5)
        branch.update_stats()
        profile.branches["branch1"] = branch

        # Write summary
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            filepath = Path(f.name)

        try:
            writer = ProfileWriter()
            writer.write_summary(profile, filepath)

            # Verify summary content
            content = filepath.read_text()
            assert "test" in content
            assert "hot_func" in content
            assert "branch1" in content
            assert "95.0%" in content or "Taken: 0.95" in content
        finally:
            filepath.unlink()

    def test_validation(self) -> None:
        """Test profile data validation."""
        reader = ProfileReader()

        # Valid profile
        valid_profile = ProfileData(module_name="test")
        valid_profile.functions["func1"] = FunctionProfile(name="func1", call_count=10, total_cycles=100)
        valid_profile.functions["func1"].update_stats()
        valid_profile.total_samples = 10  # Add samples to make it valid

        warnings = reader.validate_profile(valid_profile)
        assert len(warnings) == 0

        # Invalid profile - cycles without calls
        invalid_profile = ProfileData(module_name="test")
        invalid_profile.functions["func1"] = FunctionProfile(name="func1", call_count=0, total_cycles=100)
        invalid_profile.total_samples = 1  # Add samples but still invalid

        warnings = reader.validate_profile(invalid_profile)
        assert len(warnings) > 0
        assert "cycles but no calls" in warnings[0]
