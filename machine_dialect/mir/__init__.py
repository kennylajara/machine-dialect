"""Machine Dialect™ MIR (Medium-level Intermediate Representation).

This module provides a Three-Address Code (TAC) based intermediate representation
with Static Single Assignment (SSA) support for Machine Dialect™ compilation.

The MIR sits between the HIR (desugared AST) and the final code generation
targets (bytecode and LLVM IR).
"""

from .basic_block import CFG, BasicBlock
from .hir_to_mir import HIRToMIRLowering, lower_to_mir
from .mir_function import MIRFunction
from .mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    Label,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Phi,
    Return,
    StoreVar,
    UnaryOp,
)
from .mir_module import MIRModule
from .mir_types import MIRType
from .mir_values import Constant, FunctionRef, MIRValue, Temp, Variable
from .optimization_config import OptimizationConfig
from .optimization_pipeline import OptimizationLevel, OptimizationPipeline, PipelineBuilder
from .optimize_mir import optimize_mir, optimize_mir_simple
from .pass_manager import PassManager

__all__ = [
    "CFG",
    "BasicBlock",
    "BinaryOp",
    "Call",
    "ConditionalJump",
    "Constant",
    "Copy",
    "FunctionRef",
    "HIRToMIRLowering",
    "Jump",
    "Label",
    "LoadConst",
    "LoadVar",
    "MIRFunction",
    "MIRInstruction",
    "MIRModule",
    "MIRType",
    "MIRValue",
    "OptimizationConfig",
    "OptimizationLevel",
    "OptimizationPipeline",
    "PassManager",
    "Phi",
    "PipelineBuilder",
    "Return",
    "StoreVar",
    "Temp",
    "UnaryOp",
    "Variable",
    "lower_to_mir",
    "optimize_mir",
    "optimize_mir_simple",
]
