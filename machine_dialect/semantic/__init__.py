"""Semantic analysis for Machine Dialect.

This package provides semantic analysis capabilities including:
- Type checking and inference
- Variable usage validation
- Scope analysis
- Error reporting with helpful messages
"""

from machine_dialect.semantic.analyzer import SemanticAnalyzer, TypeInfo

__all__ = ["SemanticAnalyzer", "TypeInfo"]
