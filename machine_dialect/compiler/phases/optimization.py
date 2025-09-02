"""Optimization phase of compilation.

This module handles the optimization phase of compilation.
"""

from machine_dialect.compiler.context import CompilationContext
from machine_dialect.mir.mir_dumper import DumpVerbosity, MIRDumper
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimize_mir import optimize_mir
from machine_dialect.mir.profiling.profile_reader import ProfileReader
from machine_dialect.mir.reporting.optimization_reporter import OptimizationReporter


class OptimizationPhase:
    """Optimization phase."""

    def run(self, context: CompilationContext, mir_module: MIRModule) -> MIRModule:
        """Run optimization phase.

        Args:
            context: Compilation context.
            mir_module: MIR module to optimize.

        Returns:
            Optimized MIR module.
        """
        if not context.should_optimize():
            if context.config.verbose:
                print("Skipping optimization (level 0)")
            return mir_module

        if context.config.verbose:
            print(f"Running optimization level {context.config.optimization_level}...")

        # Load profile data if available
        profile_data = None
        if context.config.profile_path and context.config.profile_path.exists():
            reader = ProfileReader()
            profile_data = reader.read_from_file(str(context.config.profile_path))  # type: ignore[attr-defined]
            context.profile_data = profile_data
            if context.config.verbose:
                print(f"Loaded profile data from {context.config.profile_path}")

        # Create optimization reporter
        reporter = OptimizationReporter() if context.config.show_optimization_report else None
        context.optimization_reporter = reporter

        # Get optimization passes
        passes = context.config.get_optimization_passes()

        if context.config.verbose:
            print(f"Running passes: {', '.join(passes)}")

        # Create optimization config
        from machine_dialect.mir.optimization_config import OptimizationConfig

        opt_config = OptimizationConfig.from_level(int(context.config.optimization_level))

        # Apply custom pass list if provided
        custom_passes = None
        if context.config.pass_pipeline:
            custom_passes = passes

        # Run optimization
        optimized_module, stats = optimize_mir(
            mir_module,
            optimization_level=int(context.config.optimization_level),
            config=opt_config,
            debug=context.config.debug,
            custom_passes=custom_passes,
        )

        # Store stats in reporter if provided
        if reporter and stats:
            for pass_name, pass_stats in stats.items():
                reporter.start_pass(pass_name)
                reporter.end_pass(metrics=pass_stats)

        # Dump optimized MIR if requested
        if context.config.dump_mir:
            self._dump_mir(optimized_module, "optimized", context)

        # Show optimization report if requested
        if context.config.show_optimization_report and reporter:
            self._show_optimization_report(reporter)

        return optimized_module

    def _dump_mir(self, module: MIRModule, phase: str, context: CompilationContext) -> None:
        """Dump MIR representation.

        Args:
            module: MIR module to dump.
            phase: Phase name for labeling.
            context: Compilation context.
        """
        verbosity = DumpVerbosity.from_string(context.config.mir_dump_verbosity)
        dumper = MIRDumper(verbosity=verbosity, use_color=True)

        print(f"\n=== MIR ({phase}) ===")
        dumper.dump_module(module)

    def _show_optimization_report(self, reporter: OptimizationReporter) -> None:
        """Show optimization report.

        Args:
            reporter: Optimization reporter.
        """
        print("\n=== Optimization Report ===")
        print(reporter.generate_detailed_report())
