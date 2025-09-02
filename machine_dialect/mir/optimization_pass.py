"""Base classes and interfaces for MIR optimization and analysis passes.

This module provides the foundation for all optimization and analysis passes
in the MIR optimization framework.
"""

import abc
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_module import MIRModule


class PassType(Enum):
    """Type of pass."""

    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    CLEANUP = "cleanup"  # Cleanup passes that can run after optimizations
    UTILITY = "utility"


class PreservationLevel(Enum):
    """Level of preservation for analyses."""

    NONE = "none"  # Invalidates everything
    CFG = "cfg"  # Preserves CFG structure
    DOMINANCE = "dominance"  # Preserves dominance info
    ALL = "all"  # Preserves all analyses


@dataclass
class PassInfo:
    """Information about a pass.

    Attributes:
        name: Pass name.
        description: Pass description.
        pass_type: Type(s) of pass - can be single type or list of types.
        requires: List of required analysis passes.
        preserves: What analyses this pass preserves.
    """

    name: str
    description: str
    pass_type: PassType | list[PassType]
    requires: list[str]
    preserves: PreservationLevel


class Pass(ABC):
    """Base class for all passes."""

    def __init__(self) -> None:
        """Initialize the pass."""
        self.stats: dict[str, int] = {}
        self.debug_mode = False

    @abstractmethod
    def get_info(self) -> PassInfo:
        """Get information about this pass.

        Returns:
            Pass information.
        """
        pass

    def initialize(self) -> None:
        """Initialize the pass before running.

        Override this for pass-specific initialization.
        """
        self.stats.clear()

    @abc.abstractmethod
    def finalize(self) -> None:
        """Finalize the pass after running.

        Override this for pass-specific finalization.
        """

    def get_stats(self) -> dict[str, int]:
        """Get pass statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats.copy()


class ModulePass(Pass):
    """Base class for module-level passes."""

    @abstractmethod
    def run_on_module(self, module: MIRModule) -> bool:
        """Run the pass on a module.

        Args:
            module: The module to process.

        Returns:
            True if the module was modified.
        """
        pass


class FunctionPass(Pass):
    """Base class for function-level passes."""

    @abstractmethod
    def run_on_function(self, function: MIRFunction) -> bool:
        """Run the pass on a function.

        Args:
            function: The function to process.

        Returns:
            True if the function was modified.
        """
        pass

    def run_on_module(self, module: MIRModule) -> bool:
        """Run the pass on all functions in a module.

        Args:
            module: The module to process.

        Returns:
            True if any function was modified.
        """
        modified = False
        for function in module.functions.values():
            if self.run_on_function(function):
                modified = True
        return modified


class AnalysisPass(Pass):
    """Base class for analysis passes."""

    def __init__(self) -> None:
        """Initialize the analysis pass."""
        super().__init__()
        self._cache: dict[str, Any] = {}
        self._valid = False

    def invalidate(self) -> None:
        """Invalidate the analysis cache."""
        self._cache.clear()
        self._valid = False

    def is_valid(self) -> bool:
        """Check if the analysis is valid.

        Returns:
            True if the analysis is valid.
        """
        return self._valid


class ModuleAnalysisPass(AnalysisPass):
    """Base class for module-level analysis passes."""

    @abstractmethod
    def run_on_module(self, module: MIRModule) -> Any:
        """Run analysis on a module.

        Args:
            module: The module to analyze.

        Returns:
            Analysis results.
        """
        pass

    def get_analysis(self, module: MIRModule) -> Any:
        """Get cached analysis results or compute them.

        Args:
            module: The module to analyze.

        Returns:
            Analysis results.
        """
        if not self._valid:
            result = self.run_on_module(module)
            self._cache[module.name] = result
            self._valid = True
            return result
        return self._cache.get(module.name)


class FunctionAnalysisPass(AnalysisPass):
    """Base class for function-level analysis passes."""

    @abstractmethod
    def run_on_function(self, function: MIRFunction) -> Any:
        """Run analysis on a function.

        Args:
            function: The function to analyze.

        Returns:
            Analysis results.
        """
        pass

    def get_analysis(self, function: MIRFunction) -> Any:
        """Get cached analysis results or compute them.

        Args:
            function: The function to analyze.

        Returns:
            Analysis results.
        """
        if not self._valid or function.name not in self._cache:
            result = self.run_on_function(function)
            self._cache[function.name] = result
            self._valid = True
            return result
        return self._cache[function.name]


class OptimizationPass(FunctionPass):
    """Base class for optimization passes."""

    def __init__(self) -> None:
        """Initialize the optimization pass."""
        super().__init__()
        self.analysis_manager: Any = None  # Set by pass manager

    def get_analysis(self, analysis_name: str, function: MIRFunction) -> Any:
        """Get analysis results from the analysis manager.

        Args:
            analysis_name: Name of the analysis.
            function: The function to analyze.

        Returns:
            Analysis results.

        Raises:
            RuntimeError: If analysis manager is not set.
        """
        if self.analysis_manager is None:
            raise RuntimeError("Analysis manager not set")
        return self.analysis_manager.get_analysis(analysis_name, function)
