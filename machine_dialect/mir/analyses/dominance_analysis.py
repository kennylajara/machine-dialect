"""Dominance analysis for MIR.

This module provides a pass wrapper for dominance analysis.
"""

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.optimization_pass import (
    FunctionAnalysisPass,
    PassInfo,
    PassType,
    PreservationLevel,
)
from machine_dialect.mir.ssa_construction import DominanceInfo


class DominanceAnalysis(FunctionAnalysisPass):
    """Analysis pass that computes dominance information."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="dominance",
            description="Compute dominance information",
            pass_type=PassType.ANALYSIS,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def run_on_function(self, function: MIRFunction) -> DominanceInfo:
        """Compute dominance for a function.

        Args:
            function: The function to analyze.

        Returns:
            Dominance information.
        """
        return DominanceInfo(function.cfg)

    def finalize(self) -> None:
        """Finalize the analysis pass.

        Nothing to clean up for dominance analysis.
        """
        pass
