"""Compiler configuration module.

This module defines configuration options for the Machine Dialect™ compiler.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path


class OptimizationLevel(IntEnum):
    """Optimization level enumeration."""

    NONE = 0  # No optimizations
    BASIC = 1  # Basic optimizations (constant folding, DCE)
    STANDARD = 2  # Standard optimizations (default)
    AGGRESSIVE = 3  # Aggressive optimizations (inlining, specialization)


@dataclass
class CompilerConfig:
    """Compiler configuration settings.

    Attributes:
        optimization_level: Level of optimization to apply.
        dump_mir: Whether to dump MIR representation.
        dump_cfg: Path to export control flow graph.
        show_optimization_report: Whether to show optimization report.
        verbose: Enable verbose output.
        debug: Enable debug mode.
        profile_path: Path to profile data for PGO.
        mir_phase_only: Stop after MIR generation.
        output_path: Output file path.
        module_name: Name for the compiled module.
    """

    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    dump_mir: bool = False
    dump_cfg: Path | None = None
    show_optimization_report: bool = False
    verbose: bool = False
    debug: bool = False
    profile_path: Path | None = None
    mir_phase_only: bool = False
    output_path: Path | None = None
    module_name: str | None = None

    # MIR dumping options
    mir_dump_verbosity: str = "normal"
    mir_dump_phases: list[str] = field(default_factory=list)

    # Optimization pass configuration
    enabled_passes: list[str] | None = None
    disabled_passes: list[str] | None = None
    pass_pipeline: str | None = None  # Custom pass pipeline

    @classmethod
    def from_cli_options(
        cls,
        opt_level: str = "2",
        dump_mir: bool = False,
        show_cfg: str | None = None,
        opt_report: bool = False,
        verbose: bool = False,
        debug: bool = False,
        mir_phase: bool = False,
        output: str | None = None,
        module_name: str | None = None,
        **kwargs: object,
    ) -> "CompilerConfig":
        """Create config from CLI options.

        Args:
            opt_level: Optimization level string.
            dump_mir: Whether to dump MIR.
            show_cfg: Path for CFG export.
            opt_report: Whether to show optimization report.
            verbose: Enable verbose output.
            debug: Enable debug mode.
            mir_phase: Stop after MIR generation.
            output: Output file path.
            module_name: Module name.
            **kwargs: Additional options.

        Returns:
            Compiler configuration instance.
        """
        return cls(
            optimization_level=OptimizationLevel(int(opt_level)),
            dump_mir=dump_mir,
            dump_cfg=Path(show_cfg) if show_cfg else None,
            show_optimization_report=opt_report,
            verbose=verbose,
            debug=debug,
            mir_phase_only=mir_phase,
            output_path=Path(output) if output else None,
            module_name=module_name,
        )

    def get_optimization_passes(self) -> list[str]:
        """Get list of optimization passes to run based on level.

        Returns:
            List of optimization pass names.
        """
        if self.pass_pipeline:
            return self.pass_pipeline.split(",")

        passes = []

        if self.optimization_level >= OptimizationLevel.BASIC:
            passes.extend(
                [
                    "constant-folding",
                    "constant-propagation",
                    "dce",
                    "simplify-cfg",
                ]
            )

        if self.optimization_level >= OptimizationLevel.STANDARD:
            passes.extend(
                [
                    "cse",
                    "strength-reduction",
                    "algebraic-simplification",  # New pass
                    "licm",
                    "loop-unrolling",
                    "tail-call",
                ]
            )

        if self.optimization_level >= OptimizationLevel.AGGRESSIVE:
            passes.extend(
                [
                    "inlining",
                    "type-specialization",
                    "branch-prediction",
                    "escape-analysis",
                ]
            )

        # Filter based on enabled/disabled lists
        if self.enabled_passes:
            passes = [p for p in passes if p in self.enabled_passes]
        if self.disabled_passes:
            passes = [p for p in passes if p not in self.disabled_passes]

        return passes
