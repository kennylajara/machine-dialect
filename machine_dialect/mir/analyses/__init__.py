"""MIR analysis passes."""

from machine_dialect.mir.analyses.alias_analysis import AliasAnalysis, AliasInfo
from machine_dialect.mir.analyses.dominance_analysis import DominanceAnalysis
from machine_dialect.mir.analyses.escape_analysis import EscapeAnalysis, EscapeInfo
from machine_dialect.mir.analyses.loop_analysis import Loop, LoopAnalysis, LoopInfo
from machine_dialect.mir.analyses.use_def_chains import UseDefChains, UseDefChainsAnalysis

__all__ = [
    "AliasAnalysis",
    "AliasInfo",
    "DominanceAnalysis",
    "EscapeAnalysis",
    "EscapeInfo",
    "Loop",
    "LoopAnalysis",
    "LoopInfo",
    "UseDefChains",
    "UseDefChainsAnalysis",
]
