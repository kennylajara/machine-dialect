"""Profiling infrastructure for MIR optimization.

This module provides profile-guided optimization (PGO) support for the MIR
optimization framework, enabling data-driven optimization decisions based on
runtime behavior.
"""

from machine_dialect.mir.profiling.profile_collector import ProfileCollector
from machine_dialect.mir.profiling.profile_data import (
    BranchProfile,
    FunctionProfile,
    LoopProfile,
    ProfileData,
)
from machine_dialect.mir.profiling.profile_reader import ProfileReader
from machine_dialect.mir.profiling.profile_writer import ProfileWriter

__all__ = [
    "BranchProfile",
    "FunctionProfile",
    "LoopProfile",
    "ProfileCollector",
    "ProfileData",
    "ProfileReader",
    "ProfileWriter",
]
