"""Optimization configuration for MIR passes.

This module defines optimization levels and pass configurations
for the MIR optimization pipeline.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class OptimizationConfig:
    """Configuration for optimization passes.

    Attributes:
        level: Optimization level (0-3).
        enable_inlining: Enable function inlining.
        inline_threshold: Maximum size for inlining.
        enable_loop_opts: Enable loop optimizations.
        unroll_threshold: Maximum iterations for unrolling.
        enable_aggressive_opts: Enable aggressive optimizations.
        debug_passes: Enable debug output from passes.
        pass_statistics: Collect pass statistics.
    """

    level: int = 1
    enable_inlining: bool = True
    inline_threshold: int = 50
    enable_loop_opts: bool = True
    unroll_threshold: int = 4
    enable_aggressive_opts: bool = False
    debug_passes: bool = False
    pass_statistics: bool = True

    @classmethod
    def from_level(cls, level: int) -> "OptimizationConfig":
        """Create configuration from optimization level.

        Args:
            level: Optimization level (0-3).

        Returns:
            Optimization configuration.
        """
        if level == 0:
            # No optimizations
            return cls(
                level=0,
                enable_inlining=False,
                enable_loop_opts=False,
                enable_aggressive_opts=False,
            )
        elif level == 1:
            # Basic optimizations
            return cls(
                level=1,
                enable_inlining=False,
                inline_threshold=25,
                enable_loop_opts=False,
                enable_aggressive_opts=False,
            )
        elif level == 2:
            # Standard optimizations
            return cls(
                level=2,
                enable_inlining=True,
                inline_threshold=50,
                enable_loop_opts=True,
                unroll_threshold=4,
                enable_aggressive_opts=False,
            )
        elif level >= 3:
            # Aggressive optimizations
            return cls(
                level=3,
                enable_inlining=True,
                inline_threshold=100,
                enable_loop_opts=True,
                unroll_threshold=8,
                enable_aggressive_opts=True,
            )
        else:
            raise ValueError(f"Invalid optimization level: {level}")


class OptimizationPipeline:
    """Defines optimization pass pipelines for different levels."""

    @staticmethod
    def get_passes(config: OptimizationConfig) -> list[str]:
        """Get list of passes for a configuration.

        Args:
            config: Optimization configuration.

        Returns:
            List of pass names to run.
        """
        if config.level == 0:
            # No optimizations, just validation
            return []

        passes = []

        # Analysis passes (always needed)
        passes.extend(
            [
                "use-def-chains",
            ]
        )

        if config.level >= 1:
            # Basic optimizations
            passes.extend(
                [
                    "constant-propagation",
                    "strength-reduction",
                    "dce",  # Dead code elimination
                ]
            )

        if config.level >= 2:
            # Standard optimizations
            passes.extend(
                [
                    "cse",  # Common subexpression elimination
                ]
            )

            if config.enable_loop_opts:
                passes.extend(
                    [
                        "dominance",  # Required for loop analysis (also available via DominanceInfo)
                        "loop-analysis",
                        "licm",  # Loop invariant code motion
                        "loop-unrolling",  # Unroll small loops
                    ]
                )

            # Run another DCE pass after other optimizations
            passes.append("dce")

        if config.level >= 3:
            # Aggressive optimizations
            if config.enable_aggressive_opts:
                # Advanced analyses
                passes.extend(
                    [
                        "alias-analysis",  # Alias analysis
                        "escape-analysis",  # Escape analysis for stack allocation
                    ]
                )
                # More aggressive versions of passes
                passes.append("constant-propagation")  # Run again
                passes.append("cse")  # Run again

            if config.enable_inlining:
                passes.append("inline")  # Function inlining

            # Final cleanup
            passes.extend(
                [
                    "strength-reduction",
                    "dce",
                ]
            )

        return passes

    @staticmethod
    def get_analysis_passes() -> list[str]:
        """Get list of available analysis passes.

        Note: This function provides a catalog of available passes but is not
        currently used in the optimization pipeline. The main entry point is
        get_passes() which selects passes based on optimization level.

        Returns:
            List of analysis pass names.
        """
        from machine_dialect.mir.optimization_pass import PassType
        from machine_dialect.mir.optimizations import register_all_passes
        from machine_dialect.mir.pass_manager import PassManager

        pm = PassManager()
        register_all_passes(pm)
        return pm.registry.list_passes(PassType.ANALYSIS)

    @staticmethod
    def get_optimization_passes() -> list[str]:
        """Get list of available optimization passes.

        Returns:
            List of optimization pass names.
        """
        from machine_dialect.mir.optimization_pass import PassType
        from machine_dialect.mir.optimizations import register_all_passes
        from machine_dialect.mir.pass_manager import PassManager

        pm = PassManager()
        register_all_passes(pm)
        return pm.registry.list_passes(PassType.OPTIMIZATION)

    @staticmethod
    def get_cleanup_passes() -> list[str]:
        """Get list of cleanup passes.

        Cleanup passes are lightweight optimizations safe to run at the end
        of the optimization pipeline. Passes can be both optimization and cleanup.

        Returns:
            List of cleanup pass names.
        """
        from machine_dialect.mir.optimization_pass import PassType
        from machine_dialect.mir.optimizations import register_all_passes
        from machine_dialect.mir.pass_manager import PassManager

        pm = PassManager()
        register_all_passes(pm)
        return pm.registry.list_passes(PassType.CLEANUP)


# Predefined configurations
NO_OPT_CONFIG = OptimizationConfig.from_level(0)
BASIC_OPT_CONFIG = OptimizationConfig.from_level(1)
STANDARD_OPT_CONFIG = OptimizationConfig.from_level(2)
AGGRESSIVE_OPT_CONFIG = OptimizationConfig.from_level(3)

# Default configuration
DEFAULT_CONFIG = BASIC_OPT_CONFIG
