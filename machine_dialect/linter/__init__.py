"""Machine Dialect™ Linter.

This module provides linting capabilities for Machine Dialect™ code,
including style checking, error detection, and code quality analysis.
"""

from .linter import Linter
from .violations import Violation, ViolationSeverity

__all__ = ["Linter", "Violation", "ViolationSeverity"]
