"""MIR optimization passes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from machine_dialect.mir.optimizations.algebraic_simplification import AlgebraicSimplification
from machine_dialect.mir.optimizations.branch_prediction import BranchPredictionOptimization
from machine_dialect.mir.optimizations.constant_propagation import ConstantPropagation
from machine_dialect.mir.optimizations.cse import CommonSubexpressionElimination
from machine_dialect.mir.optimizations.dce import DeadCodeElimination
from machine_dialect.mir.optimizations.inlining import FunctionInlining
from machine_dialect.mir.optimizations.jump_threading import JumpThreadingOptimizer, JumpThreadingPass
from machine_dialect.mir.optimizations.licm import LoopInvariantCodeMotion
from machine_dialect.mir.optimizations.loop_unrolling import LoopUnrolling

# from machine_dialect.mir.optimizations.peephole_optimizer import PeepholeOptimizer  # Disabled - needs update
from machine_dialect.mir.optimizations.strength_reduction import StrengthReduction
from machine_dialect.mir.optimizations.tail_call import TailCallOptimization
from machine_dialect.mir.optimizations.type_narrowing import TypeNarrowing
from machine_dialect.mir.optimizations.type_specialization import TypeSpecialization
from machine_dialect.mir.optimizations.type_specific import TypeSpecificOptimization

if TYPE_CHECKING:
    from machine_dialect.mir.pass_manager import PassManager

__all__ = [
    "AlgebraicSimplification",
    "BranchPredictionOptimization",
    "CommonSubexpressionElimination",
    "ConstantPropagation",
    "DeadCodeElimination",
    "FunctionInlining",
    "JumpThreadingOptimizer",
    "JumpThreadingPass",
    "LoopInvariantCodeMotion",
    "LoopUnrolling",
    # "PeepholeOptimizer",  # Disabled
    # "PeepholePass",  # Disabled
    "StrengthReduction",
    "TailCallOptimization",
    "TypeNarrowing",
    "TypeSpecialization",
    "TypeSpecificOptimization",
]


def register_all_passes(pass_manager: PassManager) -> None:
    """Register all optimization passes with the pass manager.

    Args:
        pass_manager: Pass manager to register with.
    """
    from machine_dialect.mir.analyses.alias_analysis import AliasAnalysis
    from machine_dialect.mir.analyses.dominance_analysis import DominanceAnalysis
    from machine_dialect.mir.analyses.escape_analysis import EscapeAnalysis
    from machine_dialect.mir.analyses.loop_analysis import LoopAnalysis
    from machine_dialect.mir.analyses.type_analysis import TypeAnalysis
    from machine_dialect.mir.analyses.use_def_chains import UseDefChainsAnalysis

    # Register analysis passes
    pass_manager.register_pass(DominanceAnalysis)
    pass_manager.register_pass(UseDefChainsAnalysis)
    pass_manager.register_pass(LoopAnalysis)
    pass_manager.register_pass(AliasAnalysis)
    pass_manager.register_pass(EscapeAnalysis)
    pass_manager.register_pass(TypeAnalysis)

    # Register optimization passes
    pass_manager.register_pass(TypeSpecificOptimization)  # Run early to benefit other passes
    pass_manager.register_pass(TypeNarrowing)  # Run after type-specific to narrow union types
    pass_manager.register_pass(ConstantPropagation)
    pass_manager.register_pass(CommonSubexpressionElimination)
    pass_manager.register_pass(DeadCodeElimination)
    pass_manager.register_pass(StrengthReduction)
    pass_manager.register_pass(AlgebraicSimplification)
    pass_manager.register_pass(TailCallOptimization)
    pass_manager.register_pass(TypeSpecialization)
    pass_manager.register_pass(FunctionInlining)
    pass_manager.register_pass(LoopInvariantCodeMotion)
    pass_manager.register_pass(LoopUnrolling)
    pass_manager.register_pass(BranchPredictionOptimization)
    pass_manager.register_pass(JumpThreadingPass)
    # pass_manager.register_pass(PeepholePass)  # Disabled - needs update for new opcodes
