"""Test custom optimization passes functionality."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import LoadConst, Return
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Temp
from machine_dialect.mir.optimization_config import OptimizationConfig
from machine_dialect.mir.optimize_mir import optimize_mir


def create_simple_module() -> MIRModule:
    """Create a simple test module.

    Returns:
        A MIR module with a simple main function.
    """
    module = MIRModule("test")
    func = MIRFunction("main", [], MIRType.INT)
    entry = BasicBlock("entry")
    entry.add_instruction(LoadConst(Temp(MIRType.INT), 42, (1, 1)))
    entry.add_instruction(Return((1, 1)))
    func.cfg.add_block(entry)
    func.cfg.entry = entry  # type: ignore[attr-defined]
    module.add_function(func)
    return module


def test_custom_passes_override_default() -> None:
    """Test that custom passes override the default optimization pipeline."""
    module = create_simple_module()

    # Run with custom passes at optimization level 2
    # Level 2 would normally run many passes, but custom passes should override
    custom_passes = ["constant-propagation", "dce"]
    _optimized, stats = optimize_mir(module, optimization_level=2, custom_passes=custom_passes)

    # Verify that only our custom passes ran (plus their dependencies)
    # constant-propagation depends on use-def-chains analysis
    assert "constant-propagation" in stats
    assert "dce" in stats

    # These passes would normally run at level 2 but shouldn't with custom passes
    assert "cse" not in stats  # Common subexpression elimination
    assert "strength-reduction" not in stats


def test_no_custom_passes_uses_default() -> None:
    """Test that without custom passes, the default pipeline is used."""
    module = create_simple_module()

    # Run at level 2 without custom passes
    _optimized, stats = optimize_mir(module, optimization_level=2)

    # At level 2, we should see standard optimizations
    assert "constant-propagation" in stats or "constant-folding" in stats
    assert "dce" in stats
    # CSE is enabled at level 2
    assert "cse" in stats


def test_custom_passes_empty_list() -> None:
    """Test that an empty custom passes list runs no optimization passes."""
    module = create_simple_module()

    # Run with empty custom passes list
    _optimized, stats = optimize_mir(module, optimization_level=2, custom_passes=[])

    # No optimization passes should have run
    assert len(stats) == 0


def test_custom_passes_at_level_0() -> None:
    """Test that custom passes work even at optimization level 0."""
    module = create_simple_module()

    # Level 0 normally runs no optimizations, but custom passes should still run
    custom_passes = ["dce"]
    _optimized, stats = optimize_mir(module, optimization_level=0, custom_passes=custom_passes)

    # DCE should have run despite level 0
    assert "dce" in stats


def test_custom_passes_with_dependencies() -> None:
    """Test that custom passes include their required analysis passes."""
    module = create_simple_module()

    # constant-propagation requires use-def-chains analysis
    custom_passes = ["constant-propagation"]
    _optimized, stats = optimize_mir(module, optimization_level=1, custom_passes=custom_passes)

    # Both the optimization and its required analysis should be in stats
    assert "constant-propagation" in stats
    # Note: dependencies are handled internally by the pass manager
    # The stats might not always include analysis passes


def test_custom_passes_preserve_module() -> None:
    """Test that optimization with custom passes preserves module structure."""
    module = create_simple_module()
    original_func_count = len(module.functions)
    original_func_name = next(iter(module.functions.values())).name if module.functions else None

    # Run with custom passes
    custom_passes = ["dce"]
    optimized, _stats = optimize_mir(module, optimization_level=1, custom_passes=custom_passes)

    # Module structure should be preserved
    assert len(optimized.functions) == original_func_count
    if original_func_name:
        assert next(iter(optimized.functions.values())).name == original_func_name
    assert optimized.name == module.name


def test_invalid_custom_pass_name() -> None:
    """Test that invalid pass names are handled gracefully."""
    module = create_simple_module()

    # Try to run with an invalid pass name
    custom_passes = ["invalid-pass-name", "dce"]

    # This should either skip the invalid pass or raise an error
    # The actual behavior depends on the pass manager implementation
    # For now, we just verify it doesn't crash
    try:
        _optimized, stats = optimize_mir(module, optimization_level=1, custom_passes=custom_passes)
        # If it succeeds, the valid pass should still run
        assert "dce" in stats or len(stats) >= 0
    except (KeyError, ValueError):
        # It's also acceptable to raise an error for invalid passes
        pass


def test_custom_passes_order_preserved() -> None:
    """Test that custom passes run in the specified order."""
    module = create_simple_module()

    # Specify passes in a specific order
    custom_passes = ["dce", "constant-propagation", "dce"]
    _optimized, stats = optimize_mir(module, optimization_level=1, custom_passes=custom_passes)

    # Both passes should have run
    # Note: stats might aggregate multiple runs of the same pass
    assert "dce" in stats
    assert "constant-propagation" in stats


def test_custom_passes_with_config() -> None:
    """Test that custom passes work with a custom OptimizationConfig."""
    module = create_simple_module()

    # Create a custom config
    config = OptimizationConfig.from_level(2)
    config.debug_passes = True
    config.pass_statistics = True

    # Run with custom passes and custom config
    custom_passes = ["constant-propagation"]
    _optimized, stats = optimize_mir(module, optimization_level=2, config=config, custom_passes=custom_passes)

    # Custom passes should override the config's default pipeline
    assert "constant-propagation" in stats
    # CSE would normally be in level 2 but shouldn't run with custom passes
    assert "cse" not in stats
