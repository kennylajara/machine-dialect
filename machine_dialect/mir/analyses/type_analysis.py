"""Enhanced type analysis for MIR.

This module provides advanced type analysis capabilities including
type inference, type tracking, and generic type support.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    Copy,
    LoadConst,
    MIRInstruction,
    Phi,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    FunctionAnalysisPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class TypeConstraint(Enum):
    """Type constraints for generic types."""

    ANY = auto()  # No constraint
    NUMERIC = auto()  # Int or Float
    COMPARABLE = auto()  # Supports comparison
    CALLABLE = auto()  # Function type
    ITERABLE = auto()  # Can be iterated


@dataclass
class GenericType:
    """Generic type representation.

    Attributes:
        name: Type variable name (e.g., 'T', 'U').
        constraint: Optional constraint on the type.
        concrete_type: Concrete type when specialized.
    """

    name: str
    constraint: TypeConstraint = TypeConstraint.ANY
    concrete_type: MIRType | None = None

    def is_bound(self) -> bool:
        """Check if generic type is bound to concrete type.

        Returns:
            True if bound to a concrete type, False otherwise.
        """
        return self.concrete_type is not None

    def bind(self, mir_type: MIRType) -> bool:
        """Bind generic type to concrete type.

        Args:
            mir_type: The concrete type to bind to.

        Returns:
            True if binding succeeded, False if incompatible.
        """
        if self.is_bound():
            return self.concrete_type == mir_type

        # Check constraint compatibility
        if not self._satisfies_constraint(mir_type):
            return False

        self.concrete_type = mir_type
        return True

    def _satisfies_constraint(self, mir_type: MIRType) -> bool:
        """Check if type satisfies constraint.

        Args:
            mir_type: The type to check.

        Returns:
            True if constraint is satisfied.
        """
        if self.constraint == TypeConstraint.ANY:
            return True
        elif self.constraint == TypeConstraint.NUMERIC:
            return mir_type in (MIRType.INT, MIRType.FLOAT)
        elif self.constraint == TypeConstraint.COMPARABLE:
            return mir_type in (MIRType.INT, MIRType.FLOAT, MIRType.STRING)
        elif self.constraint == TypeConstraint.CALLABLE:
            return mir_type == MIRType.FUNCTION
        else:
            return True


@dataclass
class TypeInfo:
    """Extended type information for a value.

    Attributes:
        base_type: The base MIR type.
        is_generic: Whether this is a generic type.
        generic_type: Generic type information if applicable.
        nullable: Whether the value can be null/empty.
        constant_value: Known constant value if any.
    """

    base_type: MIRType | MIRUnionType
    is_generic: bool = False
    generic_type: GenericType | None = None
    nullable: bool = False
    constant_value: Any = None

    def get_concrete_type(self) -> MIRType | MIRUnionType:
        """Get the concrete type.

        Returns:
            The concrete MIR type, or base type if not generic/bound.
        """
        if self.is_generic and self.generic_type and self.generic_type.is_bound():
            concrete = self.generic_type.concrete_type
            if concrete is not None:
                return concrete
        return self.base_type


@dataclass
class TypeEnvironment:
    """Type environment for tracking value types.

    Attributes:
        types: Mapping from values to type information.
        generic_bindings: Current generic type bindings.
    """

    types: dict[MIRValue, TypeInfo] = field(default_factory=dict)
    generic_bindings: dict[str, GenericType] = field(default_factory=dict)

    def get_type(self, value: MIRValue) -> TypeInfo | None:
        """Get type information for a value.

        Args:
            value: The value to query.

        Returns:
            Type information if available, None otherwise.
        """
        return self.types.get(value)

    def set_type(self, value: MIRValue, type_info: TypeInfo) -> None:
        """Set type information for a value.

        Args:
            value: The value to set type for.
            type_info: The type information.
        """
        self.types[value] = type_info

    def merge(self, other: "TypeEnvironment") -> "TypeEnvironment":
        """Merge with another type environment.

        Args:
            other: The other environment to merge.

        Returns:
            New environment containing merged type information.
        """
        merged = TypeEnvironment()

        # Merge types, choosing more specific when possible
        for value in set(self.types.keys()) | set(other.types.keys()):
            if value in self.types and value in other.types:
                # Choose more specific type
                self_type = self.types[value]
                other_type = other.types[value]

                if self_type.base_type == MIRType.UNKNOWN:
                    merged.types[value] = other_type
                elif other_type.base_type == MIRType.UNKNOWN:
                    merged.types[value] = self_type
                else:
                    # Keep first if both are known
                    merged.types[value] = self_type
            elif value in self.types:
                merged.types[value] = self.types[value]
            else:
                merged.types[value] = other.types[value]

        # Merge generic bindings
        merged.generic_bindings.update(self.generic_bindings)
        merged.generic_bindings.update(other.generic_bindings)

        return merged


class TypeAnalysis(FunctionAnalysisPass):
    """Enhanced type analysis pass.

    This analysis provides detailed type information including
    generic types, nullability, and constant values.
    """

    def __init__(self) -> None:
        """Initialize type analysis."""
        super().__init__()
        self.environments: dict[str, TypeEnvironment] = {}

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass metadata including name, description, and dependencies.
        """
        return PassInfo(
            name="type-analysis",
            description="Enhanced type analysis with generics",
            pass_type=PassType.ANALYSIS,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def finalize(self) -> None:
        """Finalize the analysis.

        Note:
            Currently performs no finalization actions.
        """
        pass

    def run_on_function(self, function: MIRFunction) -> TypeEnvironment:
        """Run type analysis on a function.

        Args:
            function: The function to analyze.

        Returns:
            Type environment for the function.
        """
        self._analyze_function(function)
        return self.environments.get(function.name, TypeEnvironment())

    def get_analysis(self, function: MIRFunction) -> TypeEnvironment:
        """Get type analysis results for a function.

        Args:
            function: The function to analyze.

        Returns:
            Type environment for the function.
        """
        func_name = function.name

        if func_name not in self.environments or not self.is_valid():
            self._analyze_function(function)

        return self.environments.get(func_name, TypeEnvironment())

    def _analyze_function(self, function: MIRFunction) -> None:
        """Analyze types in a function.

        Args:
            function: The function to analyze.
        """
        env = TypeEnvironment()

        # Initialize parameter types
        for param in function.params:
            type_info = TypeInfo(base_type=param.type, nullable=param.type == MIRType.UNKNOWN)
            env.set_type(param, type_info)

        # Analyze each basic block
        for block in function.cfg.blocks.values():
            self._analyze_block(block, env)

        # Store the environment
        self.environments[function.name] = env
        self._valid = True

    def _analyze_block(self, block: BasicBlock, env: TypeEnvironment) -> None:
        """Analyze types in a basic block.

        Args:
            block: The block to analyze.
            env: Current type environment.
        """
        for inst in block.instructions:
            self._analyze_instruction(inst, env)

    def _analyze_instruction(self, inst: MIRInstruction, env: TypeEnvironment) -> None:
        """Analyze types for an instruction.

        Args:
            inst: The instruction to analyze.
            env: Current type environment.
        """
        if isinstance(inst, LoadConst):
            # Constant has known type and value
            type_info = TypeInfo(base_type=inst.constant.type, constant_value=inst.constant.value)
            env.set_type(inst.dest, type_info)

        elif isinstance(inst, Copy):
            # Copy propagates type
            source_type = env.get_type(inst.source)
            if source_type:
                env.set_type(inst.dest, source_type)

        elif isinstance(inst, BinaryOp):
            # Infer result type from operands
            left_type = self._get_value_type(inst.left, env)
            right_type = self._get_value_type(inst.right, env)

            result_type = self._infer_binary_op_type(inst.op, left_type, right_type)
            env.set_type(inst.dest, result_type)

        elif isinstance(inst, UnaryOp):
            # Infer result type from operand
            operand_type = self._get_value_type(inst.operand, env)
            result_type = self._infer_unary_op_type(inst.op, operand_type)
            env.set_type(inst.dest, result_type)

        elif isinstance(inst, Call):
            # For now, mark result as unknown
            # In future, could use function signatures
            if inst.dest:
                type_info = TypeInfo(base_type=MIRType.UNKNOWN)
                env.set_type(inst.dest, type_info)

        elif isinstance(inst, Phi):
            # Phi node merges types from sources
            source_types = [self._get_value_type(source, env) for source, _ in inst.incoming]

            # Find common type
            merged_type = self._merge_types(source_types)
            env.set_type(inst.dest, merged_type)

    def _get_value_type(self, value: MIRValue, env: TypeEnvironment) -> TypeInfo:
        """Get type info for a value.

        Args:
            value: The value to get type for.
            env: Current type environment.

        Returns:
            Type information from environment or inferred from value.
        """
        # Check environment first
        type_info = env.get_type(value)
        if type_info:
            return type_info

        # Fall back to basic type
        if isinstance(value, Constant):
            return TypeInfo(base_type=value.type, constant_value=value.value)
        elif isinstance(value, Variable):
            return TypeInfo(base_type=value.type)
        elif isinstance(value, Temp):
            return TypeInfo(base_type=value.type)
        else:
            return TypeInfo(base_type=MIRType.UNKNOWN)

    def _infer_binary_op_type(self, op: str, left: TypeInfo, right: TypeInfo) -> TypeInfo:
        """Infer result type of binary operation.

        Args:
            op: The operator.
            left: Left operand type.
            right: Right operand type.

        Returns:
            Result type information.
        """
        # Comparison operators return boolean
        if op in ("==", "!=", "<", ">", "<=", ">="):
            return TypeInfo(base_type=MIRType.BOOL)

        # Logical operators work on booleans
        if op in ("and", "or"):
            return TypeInfo(base_type=MIRType.BOOL)

        # Arithmetic operators
        if op in ("+", "-", "*", "/", "%", "^"):
            # If both are numeric, result is numeric
            if left.base_type in (MIRType.INT, MIRType.FLOAT):
                if right.base_type in (MIRType.INT, MIRType.FLOAT):
                    # Float dominates
                    if left.base_type == MIRType.FLOAT or right.base_type == MIRType.FLOAT:
                        return TypeInfo(base_type=MIRType.FLOAT)
                    else:
                        return TypeInfo(base_type=MIRType.INT)

            # String concatenation
            if op == "+" and left.base_type == MIRType.STRING:
                return TypeInfo(base_type=MIRType.STRING)

        # Default to unknown
        return TypeInfo(base_type=MIRType.UNKNOWN)

    def _infer_unary_op_type(self, op: str, operand: TypeInfo) -> TypeInfo:
        """Infer result type of unary operation.

        Args:
            op: The operator.
            operand: Operand type.

        Returns:
            Result type information.
        """
        if op == "-":
            # Negation preserves numeric type
            if operand.base_type in (MIRType.INT, MIRType.FLOAT):
                return TypeInfo(base_type=operand.base_type)
        elif op == "not":
            # Logical not returns boolean
            return TypeInfo(base_type=MIRType.BOOL)

        return TypeInfo(base_type=MIRType.UNKNOWN)

    def _merge_types(self, types: list[TypeInfo]) -> TypeInfo:
        """Merge multiple types into common type.

        Args:
            types: List of types to merge.

        Returns:
            Merged type information.
        """
        if not types:
            return TypeInfo(base_type=MIRType.UNKNOWN)

        # If all same type, return that
        base_types = [t.base_type for t in types]
        if len(set(base_types)) == 1:
            return types[0]

        # If mix of int and float, return float
        if set(base_types) <= {MIRType.INT, MIRType.FLOAT}:
            return TypeInfo(base_type=MIRType.FLOAT)

        # Otherwise unknown
        return TypeInfo(base_type=MIRType.UNKNOWN, nullable=True)
