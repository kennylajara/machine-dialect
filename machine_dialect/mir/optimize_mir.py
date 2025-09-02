"""MIR optimization pipeline integration.

This module provides the main entry point for optimizing MIR modules
using the pass management infrastructure.
"""

from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_config import (
    OptimizationConfig,
    OptimizationPipeline,
)
from machine_dialect.mir.optimizations import register_all_passes
from machine_dialect.mir.pass_manager import PassManager


def optimize_mir(
    module: MIRModule,
    optimization_level: int = 1,
    config: OptimizationConfig | None = None,
    debug: bool = False,
    custom_passes: list[str] | None = None,
) -> tuple[MIRModule, dict[str, dict[str, int]]]:
    """Optimize a MIR module using the optimization framework.

    Args:
        module: The MIR module to optimize.
        optimization_level: Optimization level (0-3).
        config: Optional custom optimization configuration.
        debug: Enable debug output.
        custom_passes: Optional list of custom passes to run instead of default pipeline.

    Returns:
        Tuple of (optimized module, pass statistics).
    """
    # Use provided config or create from level
    if config is None:
        config = OptimizationConfig.from_level(optimization_level)

    # Create pass manager
    pass_manager = PassManager()
    pass_manager.debug_mode = debug or config.debug_passes

    # Register all available passes
    register_all_passes(pass_manager)

    # Get optimization pipeline
    if custom_passes is not None:
        # Use custom passes if provided
        passes = custom_passes
    else:
        # Use default pipeline based on config
        passes = OptimizationPipeline.get_passes(config)

    if debug:
        print(f"Running optimization level {optimization_level}")
        print(f"Passes: {passes}")

    # Run optimization passes
    modified = pass_manager.run_passes(module, passes, optimization_level)

    if debug:
        print(f"Module modified: {modified}")

    # Get statistics
    stats = pass_manager.get_statistics()

    if debug and config.pass_statistics:
        print("\nOptimization Statistics:")
        for pass_name, pass_stats in stats.items():
            if pass_stats:
                print(f"  {pass_name}:")
                for stat_name, value in pass_stats.items():
                    print(f"    {stat_name}: {value}")

    return module, stats


def optimize_mir_simple(module: MIRModule, level: int = 1) -> MIRModule:
    """Simple interface for MIR optimization.

    Args:
        module: The MIR module to optimize.
        level: Optimization level (0-3).

    Returns:
        The optimized module.
    """
    optimized, _ = optimize_mir(module, level)
    return optimized
