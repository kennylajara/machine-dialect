"""Pass manager for orchestrating optimization and analysis passes.

This module implements the pass management infrastructure for scheduling,
executing, and managing dependencies between passes.
"""

from collections import defaultdict
from typing import Any

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import (
    AnalysisPass,
    FunctionAnalysisPass,
    FunctionPass,
    ModuleAnalysisPass,
    ModulePass,
    OptimizationPass,
    Pass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class PassRegistry:
    """Registry for available passes."""

    def __init__(self) -> None:
        """Initialize the pass registry."""
        self._passes: dict[str, type[Pass]] = {}
        self._pass_info: dict[str, PassInfo] = {}

    def register(self, pass_class: type[Pass]) -> None:
        """Register a pass.

        Args:
            pass_class: The pass class to register.
        """
        instance = pass_class()
        info = instance.get_info()
        self._passes[info.name] = pass_class
        self._pass_info[info.name] = info

    def get_pass(self, name: str) -> Pass | None:
        """Get a pass instance by name.

        Args:
            name: Pass name.

        Returns:
            Pass instance or None.
        """
        pass_class = self._passes.get(name)
        if pass_class:
            return pass_class()
        return None

    def get_info(self, name: str) -> PassInfo | None:
        """Get pass information by name.

        Args:
            name: Pass name.

        Returns:
            Pass information or None.
        """
        return self._pass_info.get(name)

    def list_passes(self, pass_type: PassType | None = None) -> list[str]:
        """List available passes.

        Args:
            pass_type: Optional filter by pass type.

        Returns:
            List of pass names.
        """
        if pass_type is None:
            return list(self._passes.keys())

        result = []
        for name, info in self._pass_info.items():
            # Handle both single PassType and list of PassTypes
            if isinstance(info.pass_type, list):
                if pass_type in info.pass_type:
                    result.append(name)
            elif info.pass_type == pass_type:
                result.append(name)
        return result


class AnalysisManager:
    """Manager for analysis passes and their results."""

    def __init__(self) -> None:
        """Initialize the analysis manager."""
        self._analyses: dict[str, AnalysisPass] = {}
        self._dependencies: dict[str, set[str]] = defaultdict(set)

    def register_analysis(self, name: str, analysis: AnalysisPass) -> None:
        """Register an analysis pass.

        Args:
            name: Analysis name.
            analysis: Analysis pass instance.
        """
        self._analyses[name] = analysis

    def get_analysis(
        self,
        name: str,
        target: MIRModule | MIRFunction,
    ) -> Any:
        """Get analysis results.

        Args:
            name: Analysis name.
            target: Module or function to analyze.

        Returns:
            Analysis results.

        Raises:
            KeyError: If analysis not found.
        """
        if name not in self._analyses:
            raise KeyError(f"Analysis '{name}' not found")

        analysis = self._analyses[name]

        if isinstance(analysis, ModuleAnalysisPass) and isinstance(target, MIRModule):
            return analysis.get_analysis(target)
        elif isinstance(analysis, FunctionAnalysisPass) and isinstance(
            target,
            MIRFunction,
        ):
            return analysis.get_analysis(target)
        else:
            raise TypeError("Incompatible analysis and target types")

    def invalidate(self, names: list[str] | None = None) -> None:
        """Invalidate analyses.

        Args:
            names: Specific analyses to invalidate, or None for all.
        """
        if names is None:
            for analysis in self._analyses.values():
                analysis.invalidate()
        else:
            for name in names:
                if name in self._analyses:
                    self._analyses[name].invalidate()
                    # Invalidate dependent analyses
                    for dep_name, deps in self._dependencies.items():
                        if name in deps and dep_name in self._analyses:
                            self._analyses[dep_name].invalidate()

    def preserve_analyses(self, level: PreservationLevel) -> None:
        """Preserve analyses based on preservation level.

        Args:
            level: Preservation level.
        """
        if level == PreservationLevel.NONE:
            self.invalidate()
        elif level == PreservationLevel.CFG:
            # Invalidate analyses that depend on CFG changes
            to_invalidate = []
            for name, analysis in self._analyses.items():
                info = analysis.get_info()
                if "cfg" not in info.requires:
                    to_invalidate.append(name)
            self.invalidate(to_invalidate)
        elif level == PreservationLevel.DOMINANCE:
            # Invalidate analyses that depend on dominance
            to_invalidate = []
            for name, analysis in self._analyses.items():
                info = analysis.get_info()
                if "dominance" not in info.requires:
                    to_invalidate.append(name)
            self.invalidate(to_invalidate)
        # PreservationLevel.ALL preserves everything


class PassScheduler:
    """Schedules passes based on dependencies and optimization level."""

    def __init__(self, registry: PassRegistry) -> None:
        """Initialize the pass scheduler.

        Args:
            registry: Pass registry.
        """
        self.registry = registry

    def schedule_passes(
        self,
        pass_names: list[str],
        optimization_level: int = 1,
    ) -> list[str]:
        """Schedule passes in optimal order.

        Args:
            pass_names: Requested passes.
            optimization_level: Optimization level (0-3).

        Returns:
            Ordered list of passes to run.
        """
        # Build dependency graph
        dependencies: dict[str, set[str]] = {}
        for name in pass_names:
            info = self.registry.get_info(name)
            if info:
                dependencies[name] = set(info.requires)

        # Topological sort with cycle detection
        scheduled = []
        visited = set()
        visiting = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Circular dependency detected involving {name}")

            visiting.add(name)

            # Visit dependencies first
            for dep in dependencies.get(name, set()):
                if dep not in pass_names:
                    # Add required dependency
                    pass_names.append(dep)
                    dep_info = self.registry.get_info(dep)
                    if dep_info:
                        dependencies[dep] = set(dep_info.requires)
                visit(dep)

            visiting.remove(name)
            visited.add(name)
            scheduled.append(name)

        for name in pass_names:
            visit(name)

        # Apply optimization level heuristics
        if optimization_level == 0:
            # No optimizations
            scheduled = [
                n for n in scheduled if (info := self.registry.get_info(n)) and info.pass_type != PassType.OPTIMIZATION
            ]
        elif optimization_level >= 2:
            # Add aggressive optimizations
            # Could add more passes based on level
            pass

        return scheduled


class PassManager:
    """Main pass manager for running optimization pipelines."""

    def __init__(self) -> None:
        """Initialize the pass manager."""
        self.registry = PassRegistry()
        self.analysis_manager = AnalysisManager()
        self.scheduler = PassScheduler(self.registry)
        self.stats: dict[str, dict[str, int]] = {}
        self.debug_mode = False

    def register_pass(self, pass_class: type[Pass]) -> None:
        """Register a pass with the manager.

        Args:
            pass_class: Pass class to register.
        """
        self.registry.register(pass_class)

    def run_passes(
        self,
        module: MIRModule,
        pass_names: list[str],
        optimization_level: int = 1,
    ) -> bool:
        """Run a sequence of passes on a module.

        Args:
            module: Module to optimize.
            pass_names: List of pass names to run.
            optimization_level: Optimization level (0-3).

        Returns:
            True if the module was modified.
        """
        # Schedule passes
        scheduled = self.scheduler.schedule_passes(pass_names, optimization_level)

        if self.debug_mode:
            print(f"Scheduled passes: {scheduled}")

        modified = False
        for pass_name in scheduled:
            pass_instance = self.registry.get_pass(pass_name)
            if not pass_instance:
                print(f"Warning: Pass '{pass_name}' not found")
                continue

            # Set up analysis manager for optimization passes
            if isinstance(pass_instance, OptimizationPass):
                pass_instance.analysis_manager = self.analysis_manager

            # Initialize pass
            pass_instance.initialize()
            pass_instance.debug_mode = self.debug_mode

            # Run pass
            pass_info = pass_instance.get_info()
            if pass_info.pass_type == PassType.ANALYSIS:
                # Register analysis
                if isinstance(pass_instance, AnalysisPass):
                    self.analysis_manager.register_analysis(
                        pass_name,
                        pass_instance,
                    )
                    # Run analysis to populate cache
                    if isinstance(pass_instance, ModuleAnalysisPass):
                        pass_instance.run_on_module(module)
                    elif isinstance(pass_instance, FunctionAnalysisPass):
                        for function in module.functions.values():
                            pass_instance.run_on_function(function)
            else:
                # Run optimization/utility pass
                if isinstance(pass_instance, ModulePass):
                    if pass_instance.run_on_module(module):
                        modified = True
                elif isinstance(pass_instance, FunctionPass):
                    if pass_instance.run_on_module(module):
                        modified = True

                # Handle analysis preservation
                self.analysis_manager.preserve_analyses(pass_info.preserves)

            # Finalize pass
            pass_instance.finalize()

            # Collect statistics
            self.stats[pass_name] = pass_instance.get_stats()

            if self.debug_mode and self.stats[pass_name]:
                print(f"  {pass_name}: {self.stats[pass_name]}")

        return modified

    def run_function_pass(
        self,
        function: MIRFunction,
        pass_name: str,
    ) -> bool:
        """Run a single function pass.

        Args:
            function: Function to optimize.
            pass_name: Pass name.

        Returns:
            True if the function was modified.
        """
        pass_instance = self.registry.get_pass(pass_name)
        if not pass_instance or not isinstance(pass_instance, FunctionPass):
            return False

        pass_instance.initialize()
        modified = pass_instance.run_on_function(function)
        pass_instance.finalize()

        return modified

    def get_statistics(self) -> dict[str, dict[str, int]]:
        """Get statistics from all passes.

        Returns:
            Dictionary of pass statistics.
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """Reset all statistics."""
        self.stats.clear()
