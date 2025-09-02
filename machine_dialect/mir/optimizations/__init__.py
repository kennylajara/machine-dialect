"""MIR bytecode optimization passes."""

from machine_dialect.mir.optimizations.jump_threading import JumpThreadingOptimizer
from machine_dialect.mir.optimizations.peephole_optimizer import PeepholeOptimizer

__all__ = ["PeepholeOptimizer", "JumpThreadingOptimizer"]
