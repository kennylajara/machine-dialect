"""Compiler module for Machine Dialect™.

This module provides the main compilation infrastructure for Machine Dialect™,
organizing the compilation process into clear phases and providing a unified
interface for compilation.
"""

from machine_dialect.compiler.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.pipeline import CompilationPipeline

__all__ = [
    "CompilationContext",
    "CompilationPipeline",
    "Compiler",
    "CompilerConfig",
]
