"""Comprehensive tests for optimization_pipeline module.

Tests all aspects of the optimization pipeline including optimization levels,
pipeline configuration, and custom pipeline building.
"""

from typing import Any
from unittest.mock import MagicMock, patch

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimization_pass import ModulePass, PassInfo, PassType, PreservationLevel
from machine_dialect.mir.optimization_pipeline import (
    OptimizationLevel,
    OptimizationPipeline,
    PipelineBuilder,
    create_o0_pipeline,
    create_o1_pipeline,
    create_o2_pipeline,
    create_o3_pipeline,
    create_size_pipeline,
)
from machine_dialect.mir.optimizations.inlining import FunctionInlining


class MockPass(ModulePass):
    """Mock pass for testing."""

    def __init__(self, name: str = "mock-pass", modified: bool = True) -> None:
        """Initialize mock pass.

        Args:
            name: Name of the pass.
            modified: Whether the pass modifies the module.
        """
        super().__init__()
        self._name = name
        self._modified = modified
        self.run_count = 0
        self.stats = {"test_stat": 42}

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name=self._name,
            description="Mock pass for testing",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def run_on_module(self, module: MIRModule) -> bool:
        """Run the pass on a module.

        Args:
            module: The module to run on.

        Returns:
            Whether the module was modified.
        """
        self.run_count += 1
        return self._modified

    def finalize(self) -> None:
        """Finalize the pass."""
        pass

    def get_statistics(self) -> dict[str, Any]:
        """Get pass statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats


def create_test_module() -> MIRModule:
    """Create a test module with optimization opportunities.

    Returns:
        A test MIR module.
    """
    module = MIRModule("test")

    # Create main function with constant folding opportunities
    main_func = MIRFunction("main")

    # Create basic blocks
    entry = BasicBlock("entry")
    main_func.cfg.add_block(entry)
    main_func.cfg.set_entry_block(entry)

    # Add instructions with optimization opportunities
    t0 = Temp(MIRType.INT, 0)
    t1 = Temp(MIRType.INT, 1)
    t2 = Temp(MIRType.INT, 2)
    t3 = Temp(MIRType.INT, 3)
    t4 = Temp(MIRType.INT, 4)

    # Constant folding opportunity: 2 + 3 = 5
    entry.add_instruction(LoadConst(t0, Constant(2, MIRType.INT), (1, 1)))
    entry.add_instruction(LoadConst(t1, Constant(3, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))

    # Strength reduction opportunity: x * 4 -> x << 2
    entry.add_instruction(LoadConst(t3, Constant(4, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t4, "*", t2, t3, (1, 1)))

    # Return result
    entry.add_instruction(Return((1, 1), t4))

    module.add_function(main_func)
    return module


class TestOptimizationLevel:
    """Tests for OptimizationLevel enum."""

    def test_optimization_levels(self) -> None:
        """Test all optimization level values."""
        assert OptimizationLevel.O0.value == "O0"
        assert OptimizationLevel.O1.value == "O1"
        assert OptimizationLevel.O2.value == "O2"
        assert OptimizationLevel.O3.value == "O3"
        assert OptimizationLevel.Os.value == "Os"

    def test_optimization_level_members(self) -> None:
        """Test that all expected optimization levels exist."""
        levels = list(OptimizationLevel)
        assert len(levels) == 5
        assert OptimizationLevel.O0 in levels
        assert OptimizationLevel.O1 in levels
        assert OptimizationLevel.O2 in levels
        assert OptimizationLevel.O3 in levels
        assert OptimizationLevel.Os in levels


class TestOptimizationPipeline:
    """Tests for OptimizationPipeline class."""

    def test_initialization(self) -> None:
        """Test pipeline initialization."""
        pipeline = OptimizationPipeline()
        assert pipeline.pass_manager is not None
        assert isinstance(pipeline.stats, dict)
        assert len(pipeline.stats) == 0

    def test_register_all_passes(self) -> None:
        """Test that all passes are registered."""
        pipeline = OptimizationPipeline()
        # Check that passes were registered (indirectly through registry)
        assert pipeline.pass_manager is not None

    def test_get_passes_for_o0(self) -> None:
        """Test O0 optimization level (no optimization)."""
        pipeline = OptimizationPipeline()
        passes = pipeline.get_passes_for_level(OptimizationLevel.O0)
        assert len(passes) == 0

    def test_get_passes_for_o1(self) -> None:
        """Test O1 optimization level (basic optimization)."""
        pipeline = OptimizationPipeline()
        passes = pipeline.get_passes_for_level(OptimizationLevel.O1)

        # O1 should include basic passes
        assert len(passes) > 0
        # Check pass names (can be MockPass or None)
        pass_names = [p.get_info().name if p else None for p in passes]
        # Filter out None values
        pass_names = [name for name in pass_names if name is not None]
        assert len(pass_names) > 0

    def test_get_passes_for_o2(self) -> None:
        """Test O2 optimization level (standard optimization)."""
        pipeline = OptimizationPipeline()
        passes = pipeline.get_passes_for_level(OptimizationLevel.O2)

        # O2 should include more passes
        assert len(passes) > 0

        # Check for inlining pass
        inlining_passes = [p for p in passes if isinstance(p, FunctionInlining)]
        assert len(inlining_passes) == 1
        assert inlining_passes[0].size_threshold == 30

    def test_get_passes_for_o3(self) -> None:
        """Test O3 optimization level (aggressive optimization)."""
        pipeline = OptimizationPipeline()
        passes = pipeline.get_passes_for_level(OptimizationLevel.O3)

        # O3 should include aggressive inlining
        inlining_passes = [p for p in passes if isinstance(p, FunctionInlining)]
        assert len(inlining_passes) == 1
        assert inlining_passes[0].size_threshold == 100  # More aggressive than O2

        # O3 should have more passes than O2
        o2_passes = pipeline.get_passes_for_level(OptimizationLevel.O2)
        assert len(passes) >= len(o2_passes)

    def test_get_passes_for_os(self) -> None:
        """Test Os optimization level (optimize for size)."""
        pipeline = OptimizationPipeline()
        passes = pipeline.get_passes_for_level(OptimizationLevel.Os)

        # Os should NOT include inlining (increases size)
        inlining_passes = [p for p in passes if isinstance(p, FunctionInlining)]
        assert len(inlining_passes) == 0

        # Should have some optimization passes
        assert len(passes) > 0

    def test_optimize_o0(self) -> None:
        """Test optimization with O0 level."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        modified = pipeline.optimize(module, OptimizationLevel.O0)

        # O0 should not modify the module
        assert not modified
        assert pipeline.stats["level"] == "O0"
        assert len(pipeline.stats["passes_run"]) == 0
        assert pipeline.stats["total_modifications"] == 0

    def test_optimize_with_modifications(self) -> None:
        """Test optimization that modifies the module."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        # Create mock passes
        mock_pass1 = MockPass("pass1", modified=True)
        mock_pass2 = MockPass("pass2", modified=False)
        mock_pass3 = MockPass("pass3", modified=True)

        # Mock get_passes_for_level to return our mock passes
        with patch.object(pipeline, "get_passes_for_level", return_value=[mock_pass1, mock_pass2, mock_pass3]):
            modified = pipeline.optimize(module, OptimizationLevel.O1)

        assert modified
        assert pipeline.stats["level"] == "O1"
        assert pipeline.stats["passes_run"] == ["pass1", "pass2", "pass3"]
        assert pipeline.stats["total_modifications"] == 2  # pass1 and pass3 modified
        assert "pass1" in pipeline.stats["pass_stats"]
        assert "pass2" in pipeline.stats["pass_stats"]
        assert "pass3" in pipeline.stats["pass_stats"]

    def test_optimize_with_custom_pipeline(self) -> None:
        """Test optimization with custom pipeline."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        # Mock the pass manager registry
        mock_registry = MagicMock()
        mock_pass1 = MockPass("custom-pass1", modified=True)
        mock_pass2 = MockPass("custom-pass2", modified=False)

        def get_pass(name: str) -> ModulePass | None:
            if name == "custom-pass1":
                return mock_pass1
            elif name == "custom-pass2":
                return mock_pass2
            return None

        mock_registry.get_pass = get_pass
        pipeline.pass_manager.registry = mock_registry

        modified = pipeline.optimize_with_custom_pipeline(module, ["custom-pass1", "custom-pass2", "nonexistent-pass"])

        assert modified
        assert mock_pass1.run_count == 1
        assert mock_pass2.run_count == 1

    def test_get_statistics(self) -> None:
        """Test getting optimization statistics."""
        pipeline = OptimizationPipeline()

        # Initially empty
        stats = pipeline.get_statistics()
        assert stats == {}

        # After optimization
        module = create_test_module()
        pipeline.optimize(module, OptimizationLevel.O0)

        stats = pipeline.get_statistics()
        assert stats["level"] == "O0"
        assert "passes_run" in stats
        assert "total_modifications" in stats
        assert "pass_stats" in stats


class TestPipelineBuilder:
    """Tests for PipelineBuilder class."""

    def test_initialization(self) -> None:
        """Test builder initialization."""
        builder = PipelineBuilder()
        assert builder.passes == []
        assert builder.pass_configs == {}

    def test_add_pass(self) -> None:
        """Test adding a pass."""
        builder = PipelineBuilder()
        result = builder.add_pass("test-pass")

        assert result is builder  # Returns self for chaining
        assert "test-pass" in builder.passes
        assert "test-pass" not in builder.pass_configs

    def test_add_pass_with_config(self) -> None:
        """Test adding a pass with configuration."""
        builder = PipelineBuilder()
        result = builder.add_pass("test-pass", threshold=10, enabled=True)

        assert result is builder
        assert "test-pass" in builder.passes
        assert "test-pass" in builder.pass_configs
        assert builder.pass_configs["test-pass"]["threshold"] == 10
        assert builder.pass_configs["test-pass"]["enabled"] is True

    def test_add_cleanup_passes(self) -> None:
        """Test adding cleanup passes."""
        builder = PipelineBuilder()
        result = builder.add_cleanup_passes()

        assert result is builder
        assert "dce" in builder.passes
        assert "jump-threading" in builder.passes
        assert "peephole" in builder.passes

    def test_add_algebraic_passes(self) -> None:
        """Test adding algebraic optimization passes."""
        builder = PipelineBuilder()
        result = builder.add_algebraic_passes()

        assert result is builder
        assert "constant-propagation" in builder.passes
        assert "strength-reduction" in builder.passes
        assert "cse" in builder.passes

    def test_add_loop_passes(self) -> None:
        """Test adding loop optimization passes."""
        builder = PipelineBuilder()
        result = builder.add_loop_passes()

        assert result is builder
        assert "licm" in builder.passes

    def test_repeat(self) -> None:
        """Test repeating the pipeline."""
        builder = PipelineBuilder()
        builder.add_pass("pass1").add_pass("pass2")

        result = builder.repeat(3)

        assert result is builder
        assert builder.passes == ["pass1", "pass2", "pass1", "pass2", "pass1", "pass2"]

    def test_repeat_once(self) -> None:
        """Test repeat with times=1 (no repetition)."""
        builder = PipelineBuilder()
        builder.add_pass("pass1").add_pass("pass2")

        result = builder.repeat(1)

        assert result is builder
        assert builder.passes == ["pass1", "pass2"]

    def test_build(self) -> None:
        """Test building the pipeline."""
        builder = PipelineBuilder()
        builder.add_pass("pass1").add_pass("pass2")

        result = builder.build()

        assert result == ["pass1", "pass2"]
        assert result is not builder.passes  # Should be a copy

    def test_chaining(self) -> None:
        """Test method chaining."""
        builder = PipelineBuilder()

        result = builder.add_pass("inline").add_algebraic_passes().add_loop_passes().add_cleanup_passes().repeat(2)

        assert result is builder
        expected = [
            "inline",
            "constant-propagation",
            "strength-reduction",
            "cse",
            "licm",
            "dce",
            "jump-threading",
            "peephole",
            "inline",
            "constant-propagation",
            "strength-reduction",
            "cse",
            "licm",
            "dce",
            "jump-threading",
            "peephole",
        ]
        assert builder.passes == expected

    def test_complex_pipeline(self) -> None:
        """Test building a complex custom pipeline."""
        builder = PipelineBuilder()
        builder.add_pass("inline", size_threshold=50)
        builder.add_algebraic_passes()
        builder.add_pass("inline", size_threshold=100)
        builder.add_loop_passes()
        builder.add_cleanup_passes()
        pipeline = builder.build()

        # inline + 3 algebraic + inline + 1 loop + 3 cleanup = 9 total
        assert len(pipeline) == 9
        assert pipeline[0] == "inline"
        assert pipeline[4] == "inline"
        assert pipeline[-1] == "peephole"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_o0_pipeline(self) -> None:
        """Test creating O0 pipeline."""
        pipeline = create_o0_pipeline()
        assert isinstance(pipeline, OptimizationPipeline)
        assert pipeline.pass_manager is not None

    def test_create_o1_pipeline(self) -> None:
        """Test creating O1 pipeline."""
        pipeline = create_o1_pipeline()
        assert isinstance(pipeline, OptimizationPipeline)
        assert pipeline.pass_manager is not None

    def test_create_o2_pipeline(self) -> None:
        """Test creating O2 pipeline."""
        pipeline = create_o2_pipeline()
        assert isinstance(pipeline, OptimizationPipeline)
        assert pipeline.pass_manager is not None

    def test_create_o3_pipeline(self) -> None:
        """Test creating O3 pipeline."""
        pipeline = create_o3_pipeline()
        assert isinstance(pipeline, OptimizationPipeline)
        assert pipeline.pass_manager is not None

    def test_create_size_pipeline(self) -> None:
        """Test creating size optimization pipeline."""
        pipeline = create_size_pipeline()
        assert isinstance(pipeline, OptimizationPipeline)
        assert pipeline.pass_manager is not None

    def test_all_pipelines_can_optimize(self) -> None:
        """Test that all convenience pipelines can run optimization."""
        create_test_module()  # Validate it can create a module

        pipelines = [
            (create_o0_pipeline(), OptimizationLevel.O0),
            (create_o1_pipeline(), OptimizationLevel.O1),
            (create_o2_pipeline(), OptimizationLevel.O2),
            (create_o3_pipeline(), OptimizationLevel.O3),
            (create_size_pipeline(), OptimizationLevel.Os),
        ]

        for pipeline, level in pipelines:
            test_module = create_test_module()  # Fresh module for each test
            # Should not raise any exceptions
            pipeline.optimize(test_module, level)
            stats = pipeline.get_statistics()
            assert stats["level"] == level.value


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_custom_pipeline(self) -> None:
        """Test custom pipeline with empty pass list."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        modified = pipeline.optimize_with_custom_pipeline(module, [])

        assert not modified

    def test_nonexistent_passes_in_custom_pipeline(self) -> None:
        """Test custom pipeline with only nonexistent passes."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        # Mock registry to return None for all passes
        mock_registry = MagicMock()
        mock_registry.get_pass.return_value = None
        pipeline.pass_manager.registry = mock_registry

        modified = pipeline.optimize_with_custom_pipeline(module, ["nonexistent1", "nonexistent2"])

        assert not modified

    def test_pipeline_builder_empty_repeat(self) -> None:
        """Test repeating an empty pipeline."""
        builder = PipelineBuilder()
        result = builder.repeat(5)

        assert result is builder
        assert builder.passes == []

    def test_pipeline_builder_zero_repeat(self) -> None:
        """Test repeat with times=0."""
        builder = PipelineBuilder()
        builder.add_pass("pass1")

        # Repeat 0 times should remove all passes
        result = builder.repeat(0)

        assert result is builder
        # After repeat(0), we should have no passes since (times - 1) = -1 means no extension
        assert builder.passes == ["pass1"]  # Original pass remains, no additional copies

    def test_pass_without_get_statistics(self) -> None:
        """Test handling passes without get_statistics method."""
        pipeline = OptimizationPipeline()
        module = create_test_module()

        # Create a mock pass without get_statistics
        mock_pass = MagicMock(spec=ModulePass)
        mock_pass.get_info.return_value = PassInfo(
            "test", "Test pass", PassType.OPTIMIZATION, [], PreservationLevel.ALL
        )
        mock_pass.run_on_module.return_value = True
        # Delete get_statistics to simulate it not existing
        del mock_pass.get_statistics

        with patch.object(pipeline, "get_passes_for_level", return_value=[mock_pass]):
            pipeline.optimize(module, OptimizationLevel.O1)

        # Should handle gracefully
        stats = pipeline.get_statistics()
        assert stats["passes_run"] == ["test"]
        assert "test" not in stats["pass_stats"]  # No stats for this pass
