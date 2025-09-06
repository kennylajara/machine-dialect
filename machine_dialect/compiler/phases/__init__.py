"""Compilation phases module.

This module contains individual compilation phases that make up the
compilation pipeline.
"""

from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.compiler.phases.optimization import OptimizationPhase
from machine_dialect.compiler.phases.parsing import ParsingPhase

__all__ = [
    "CodeGenerationPhase",
    "HIRGenerationPhase",
    "MIRGenerationPhase",
    "OptimizationPhase",
    "ParsingPhase",
]
