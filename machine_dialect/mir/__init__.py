"""Machine Dialect MIR (Medium-level Intermediate Representation).

This module provides a Three-Address Code (TAC) based intermediate representation
with Static Single Assignment (SSA) support for Machine Dialect compilation.

The MIR sits between the HIR (desugared AST) and the final code generation
targets (bytecode and LLVM IR).
"""

from .basic_block import CFG, BasicBlock
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

__all__ = [
    "BasicBlock",
    "BinaryOp",
    "CFG",
    "Call",
    "ConditionalJump",
    "Constant",
    "Copy",
    "FunctionRef",
    "Jump",
    "Label",
    "LoadConst",
    "LoadVar",
    "MIRFunction",
    "MIRInstruction",
    "MIRModule",
    "MIRType",
    "MIRValue",
    "Phi",
    "Return",
    "StoreVar",
    "Temp",
    "UnaryOp",
    "Variable",
]
