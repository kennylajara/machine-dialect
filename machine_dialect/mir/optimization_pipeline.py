"""Optimization pipeline configuration for MIR.

This module defines optimization levels and pass pipelines for different
compilation scenarios.
"""

from enum import Enum
from typing import Any

from machine_dialect.mir.analyses.dominance_analysis import DominanceAnalysis
from machine_dialect.mir.analyses.loop_analysis import LoopAnalysis
from machine_dialect.mir.analyses.use_def_chains import UseDefChainsAnalysis
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import ModulePass, Pass
from machine_dialect.mir.optimizations.constant_propagation import ConstantPropagation
from machine_dialect.mir.optimizations.cse import CommonSubexpressionElimination
from machine_dialect.mir.optimizations.dce import DeadCodeElimination
from machine_dialect.mir.optimizations.inlining import FunctionInlining
from machine_dialect.mir.optimizations.jump_threading import JumpThreadingPass
from machine_dialect.mir.optimizations.licm import LoopInvariantCodeMotion

# from machine_dialect.mir.optimizations.peephole_optimizer import PeepholePass  # Disabled
from machine_dialect.mir.optimizations.strength_reduction import StrengthReduction
from machine_dialect.mir.pass_manager import PassManager


class OptimizationLevel(Enum):
    """Optimization levels for compilation."""

    O0 = "O0"  # No optimization
    O1 = "O1"  # Basic optimization
    O2 = "O2"  # Standard optimization
    O3 = "O3"  # Aggressive optimization
    Os = "Os"  # Optimize for size


class OptimizationPipeline:
    """Manages optimization pipelines for different optimization levels."""

    def __init__(self) -> None:
        """Initialize the optimization pipeline.

        Creates a pass manager and registers all available optimization
        and analysis passes.
        """
        self.pass_manager = PassManager()
        self._register_all_passes()
        self.stats: dict[str, Any] = {}

    def _register_all_passes(self) -> None:
        """Register all available passes with the pass manager.

        Registers both analysis passes (dominance, loop, use-def chains)
        and optimization passes (constant propagation, DCE, CSE, etc.).
        """
        # Register analysis passes
        self.pass_manager.register_pass(DominanceAnalysis)
        self.pass_manager.register_pass(LoopAnalysis)
        self.pass_manager.register_pass(UseDefChainsAnalysis)

        # Register optimization passes
        self.pass_manager.register_pass(ConstantPropagation)
        self.pass_manager.register_pass(DeadCodeElimination)
        self.pass_manager.register_pass(CommonSubexpressionElimination)
        self.pass_manager.register_pass(StrengthReduction)
        self.pass_manager.register_pass(JumpThreadingPass)
        # self.pass_manager.register_pass(PeepholePass)  # Disabled
        self.pass_manager.register_pass(LoopInvariantCodeMotion)
        self.pass_manager.register_pass(FunctionInlining)

    def get_passes_for_level(self, level: OptimizationLevel) -> list[Pass]:
        """Get the list of passes for an optimization level.

        Args:
            level: The optimization level.

        Returns:
            List of pass instances to run.
        """
        passes: list[Pass] = []

        if level == OptimizationLevel.O0:
            # No optimization
            return passes

        elif level == OptimizationLevel.O1:
            # Basic optimization
            # Focus on simple, fast optimizations
            o1_passes = [
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("strength-reduction"),
                self.pass_manager.registry.get_pass("dce"),
                self.pass_manager.registry.get_pass("peephole"),
            ]
            passes.extend([p for p in o1_passes if p is not None])

        elif level == OptimizationLevel.O2:
            # Standard optimization
            # Add more expensive optimizations
            o2_passes: list[Pass | None] = [
                # First pass: basic cleanup
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("strength-reduction"),
                self.pass_manager.registry.get_pass("dce"),
                # Inlining (small functions only)
                FunctionInlining(size_threshold=30),
                # After inlining, more opportunities
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("cse"),
                self.pass_manager.registry.get_pass("licm"),
                self.pass_manager.registry.get_pass("dce"),
                # Final cleanup
                self.pass_manager.registry.get_pass("jump-threading"),
                self.pass_manager.registry.get_pass("peephole"),
            ]
            passes.extend([p for p in o2_passes if p is not None])

        elif level == OptimizationLevel.O3:
            # Aggressive optimization
            # More aggressive thresholds and multiple iterations
            o3_passes: list[Pass | None] = [
                # First pass: aggressive inlining
                FunctionInlining(size_threshold=100),
                # Full optimization suite
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("strength-reduction"),
                self.pass_manager.registry.get_pass("cse"),
                self.pass_manager.registry.get_pass("licm"),
                self.pass_manager.registry.get_pass("dce"),
                # Second iteration after first round
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("cse"),
                self.pass_manager.registry.get_pass("dce"),
                # Control flow optimization
                self.pass_manager.registry.get_pass("jump-threading"),
                self.pass_manager.registry.get_pass("peephole"),
                # Final DCE to clean up
                self.pass_manager.registry.get_pass("dce"),
            ]
            passes.extend([p for p in o3_passes if p is not None])

        elif level == OptimizationLevel.Os:
            # Optimize for size
            # Focus on reducing code size
            os_passes = [
                # No inlining (increases size)
                self.pass_manager.registry.get_pass("constant-propagation"),
                self.pass_manager.registry.get_pass("cse"),  # Reduces duplicate code
                self.pass_manager.registry.get_pass("dce"),  # Removes dead code
                self.pass_manager.registry.get_pass("jump-threading"),  # Simplifies control flow
                self.pass_manager.registry.get_pass("peephole"),
            ]
            passes.extend([p for p in os_passes if p is not None])

        # Already filtered out None passes
        return passes

    def optimize(self, module: MIRModule, level: OptimizationLevel = OptimizationLevel.O2) -> bool:
        """Run optimization pipeline on a module.

        Args:
            module: The module to optimize.
            level: The optimization level.

        Returns:
            True if the module was modified.
        """
        passes = self.get_passes_for_level(level)
        modified = False

        # Reset statistics
        self.stats = {
            "level": level.value,
            "passes_run": [],
            "total_modifications": 0,
            "pass_stats": {},
        }

        for pass_instance in passes:
            pass_info = pass_instance.get_info()
            pass_name = pass_info.name

            # Run the pass
            pass_modified = False
            if isinstance(pass_instance, ModulePass):
                pass_modified = pass_instance.run_on_module(module)

            # Track statistics
            self.stats["passes_run"].append(pass_name)
            if pass_modified:
                modified = True
                self.stats["total_modifications"] += 1

            # Get pass-specific statistics if available
            if hasattr(pass_instance, "get_statistics"):
                self.stats["pass_stats"][pass_name] = pass_instance.get_statistics()

        return modified

    def optimize_with_custom_pipeline(self, module: MIRModule, pass_names: list[str]) -> bool:
        """Run a custom optimization pipeline.

        Args:
            module: The module to optimize.
            pass_names: List of pass names to run in order.

        Returns:
            True if the module was modified.
        """
        modified = False

        for pass_name in pass_names:
            pass_instance = self.pass_manager.registry.get_pass(pass_name)
            if pass_instance:
                if isinstance(pass_instance, ModulePass):
                    if pass_instance.run_on_module(module):
                        modified = True

        return modified

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics from the last optimization run.

        Returns:
            Dictionary containing optimization level, passes run,
            total modifications made, and per-pass statistics.
        """
        return self.stats


class PipelineBuilder:
    """Builder for creating custom optimization pipelines."""

    def __init__(self) -> None:
        """Initialize the pipeline builder.

        Creates an empty pipeline ready for pass configuration.
        """
        self.passes: list[str] = []
        self.pass_configs: dict[str, dict[str, Any]] = {}

    def add_pass(self, pass_name: str, **config: Any) -> "PipelineBuilder":
        """Add a pass to the pipeline.

        Args:
            pass_name: Name of the pass.
            **config: Configuration for the pass.

        Returns:
            Self for chaining.
        """
        self.passes.append(pass_name)
        if config:
            self.pass_configs[pass_name] = config
        return self

    def add_cleanup_passes(self) -> "PipelineBuilder":
        """Add standard cleanup passes.

        Returns:
            Self for chaining.
        """
        self.passes.extend(["dce", "jump-threading", "peephole"])
        return self

    def add_algebraic_passes(self) -> "PipelineBuilder":
        """Add algebraic optimization passes.

        Returns:
            Self for chaining.
        """
        self.passes.extend(["constant-propagation", "strength-reduction", "cse"])
        return self

    def add_loop_passes(self) -> "PipelineBuilder":
        """Add loop optimization passes.

        Returns:
            Self for chaining.
        """
        self.passes.append("licm")
        return self

    def repeat(self, times: int = 2) -> "PipelineBuilder":
        """Repeat the current pipeline multiple times.

        Args:
            times: Number of times to repeat.

        Returns:
            Self for chaining.
        """
        current_passes = self.passes.copy()
        for _ in range(times - 1):
            self.passes.extend(current_passes)
        return self

    def build(self) -> list[str]:
        """Build the pipeline.

        Returns:
            List of pass names.
        """
        return self.passes.copy()


# Convenience functions
def create_o0_pipeline() -> OptimizationPipeline:
    """Create a pipeline with no optimization.

    Returns:
        Pipeline configured for O0 (no optimization passes).
    """
    pipeline = OptimizationPipeline()
    return pipeline


def create_o1_pipeline() -> OptimizationPipeline:
    """Create a pipeline with basic optimization.

    Returns:
        Pipeline configured for O1 (fast, simple optimizations).
    """
    pipeline = OptimizationPipeline()
    return pipeline


def create_o2_pipeline() -> OptimizationPipeline:
    """Create a pipeline with standard optimization.

    Returns:
        Pipeline configured for O2 (balanced performance/compile time).
    """
    pipeline = OptimizationPipeline()
    return pipeline


def create_o3_pipeline() -> OptimizationPipeline:
    """Create a pipeline with aggressive optimization.

    Returns:
        Pipeline configured for O3 (maximum performance optimization).
    """
    pipeline = OptimizationPipeline()
    return pipeline


def create_size_pipeline() -> OptimizationPipeline:
    """Create a pipeline optimized for code size.

    Returns:
        Pipeline configured for Os (minimize code size).
    """
    pipeline = OptimizationPipeline()
    return pipeline
