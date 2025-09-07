"""Common Subexpression Elimination (CSE) optimization pass.

This module implements CSE at the MIR level, eliminating redundant
computations by reusing previously computed values.
"""

from dataclasses import dataclass
from typing import Any

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    Copy,
    LoadConst,
    MIRInstruction,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


@dataclass(frozen=True)
class Expression:
    """Represents an expression for CSE.

    Attributes:
        op: Operation type.
        operands: Tuple of operands.
    """

    op: str
    operands: tuple[Any, ...]

    def __hash__(self) -> int:
        """Hash the expression."""
        return hash((self.op, self.operands))


class AvailableExpressions:
    """Tracks available expressions in a block."""

    def __init__(self) -> None:
        """Initialize available expressions."""
        # Map from expression to the value containing it
        self.expressions: dict[Expression, MIRValue] = {}
        # Map from value to expressions it defines
        self.definitions: dict[MIRValue, set[Expression]] = {}

    def add(self, expr: Expression, value: MIRValue) -> None:
        """Add an available expression.

        Args:
            expr: The expression.
            value: The value containing the expression.
        """
        self.expressions[expr] = value
        if value not in self.definitions:
            self.definitions[value] = set()
        self.definitions[value].add(expr)

    def get(self, expr: Expression) -> MIRValue | None:
        """Get the value for an expression.

        Args:
            expr: The expression to look up.

        Returns:
            The value containing the expression or None.
        """
        return self.expressions.get(expr)

    def invalidate(self, value: MIRValue) -> None:
        """Invalidate expressions involving a value.

        Args:
            value: The value that changed.
        """
        # Remove expressions that use this value
        to_remove = []
        for expr in self.expressions:
            if value in expr.operands:
                to_remove.append(expr)

        for expr in to_remove:
            del self.expressions[expr]

        # Remove expressions defined by this value
        if value in self.definitions:
            for expr in self.definitions[value]:
                if expr in self.expressions:
                    del self.expressions[expr]
            del self.definitions[value]

    def copy(self) -> "AvailableExpressions":
        """Create a copy of available expressions.

        Returns:
            A copy of this available expressions set.
        """
        new = AvailableExpressions()
        new.expressions = self.expressions.copy()
        new.definitions = {k: v.copy() for k, v in self.definitions.items()}
        return new


class CommonSubexpressionElimination(OptimizationPass):
    """Common subexpression elimination optimization pass."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="cse",
            description="Eliminate common subexpressions",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run CSE on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        transformer = MIRTransformer(function)

        # Perform local CSE within each block
        for block in function.cfg.blocks.values():
            self._local_cse(block, transformer)

        # Perform global CSE across blocks
        self._global_cse(function, transformer)

        return transformer.modified

    def _local_cse(self, block: BasicBlock, transformer: MIRTransformer) -> None:
        """Perform local CSE within a block.

        Args:
            block: The block to optimize.
            transformer: MIR transformer.
        """
        available = AvailableExpressions()

        for inst in list(block.instructions):
            # Check if this instruction computes an expression
            expr = self._get_expression(inst)

            if expr:
                # Check if expression is already available
                existing = available.get(expr)
                if existing and existing != self._get_result(inst):
                    # Replace with copy of existing value
                    result = self._get_result(inst)
                    if result:
                        new_inst = Copy(result, existing, inst.source_location)
                        transformer.replace_instruction(block, inst, new_inst)
                        self.stats["local_cse_eliminated"] = self.stats.get("local_cse_eliminated", 0) + 1
                else:
                    # Add expression to available set
                    result = self._get_result(inst)
                    if result:
                        available.add(expr, result)

            # Update available expressions based on side effects
            self._update_available(inst, available)

    def _global_cse(self, function: MIRFunction, transformer: MIRTransformer) -> None:
        """Perform global CSE across blocks.

        Args:
            function: The function to optimize.
            transformer: MIR transformer.
        """
        # Compute available expressions at entry of each block
        block_available: dict[BasicBlock, AvailableExpressions] = {}

        # Initialize with empty sets
        for block in function.cfg.blocks.values():
            block_available[block] = AvailableExpressions()

        # Iterate until fixed point
        changed = True
        while changed:
            changed = False

            for block in function.cfg.blocks.values():
                # Compute available at entry as intersection of predecessors
                if block.predecessors:
                    # Start with copy of first predecessor
                    if block.predecessors[0] in block_available:
                        new_available = self._intersect_available(
                            [block_available.get(p, AvailableExpressions()) for p in block.predecessors]
                        )
                    else:
                        new_available = AvailableExpressions()
                else:
                    new_available = AvailableExpressions()

                # Check if changed
                if self._available_changed(block_available[block], new_available):
                    block_available[block] = new_available
                    changed = True

                # Compute available at exit
                available = new_available.copy()
                for inst in block.instructions:
                    expr = self._get_expression(inst)
                    if expr:
                        result = self._get_result(inst)
                        if result:
                            available.add(expr, result)
                    self._update_available(inst, available)

        # Apply CSE based on available expressions
        for block in function.cfg.blocks.values():
            available = block_available[block].copy()

            for inst in list(block.instructions):
                expr = self._get_expression(inst)

                if expr:
                    existing = available.get(expr)
                    if existing and existing != self._get_result(inst):
                        # Replace with copy
                        result = self._get_result(inst)
                        if result:
                            source_loc = inst.source_location if hasattr(inst, "source_location") else (0, 0)
                            new_inst = Copy(result, existing, source_loc)
                            transformer.replace_instruction(block, inst, new_inst)
                            self.stats["global_cse_eliminated"] = self.stats.get("global_cse_eliminated", 0) + 1
                    else:
                        result = self._get_result(inst)
                        if result:
                            available.add(expr, result)

                self._update_available(inst, available)

    def _get_expression(self, inst: MIRInstruction) -> Expression | None:
        """Extract expression from an instruction.

        Args:
            inst: The instruction.

        Returns:
            The expression or None.
        """
        if isinstance(inst, BinaryOp):
            # Normalize commutative operations
            if inst.op in ["+", "*", "==", "!=", "and", "or"]:
                # Sort operands for commutative ops
                operands = tuple(sorted([self._normalize_value(inst.left), self._normalize_value(inst.right)], key=str))
            else:
                operands = (self._normalize_value(inst.left), self._normalize_value(inst.right))
            return Expression(f"binary_{inst.op}", operands)

        elif isinstance(inst, UnaryOp):
            return Expression(f"unary_{inst.op}", (self._normalize_value(inst.operand),))

        elif isinstance(inst, LoadConst):
            # Constants are their own expressions
            return Expression("const", (inst.constant.value, inst.constant.type))

        return None

    def _normalize_value(self, value: MIRValue) -> Any:
        """Normalize a value for expression comparison.

        Args:
            value: The value to normalize.

        Returns:
            Normalized representation.
        """
        if isinstance(value, Constant):
            return ("const", value.value, value.type)
        elif isinstance(value, Variable):
            return ("var", value.name)
        elif isinstance(value, Temp):
            return ("temp", value.id)
        else:
            return str(value)

    def _get_result(self, inst: MIRInstruction) -> MIRValue | None:
        """Get the result value of an instruction.

        Args:
            inst: The instruction.

        Returns:
            The result value or None.
        """
        defs = inst.get_defs()
        if defs and len(defs) == 1:
            return defs[0]
        return None

    def _update_available(
        self,
        inst: MIRInstruction,
        available: AvailableExpressions,
    ) -> None:
        """Update available expressions after an instruction.

        Args:
            inst: The instruction.
            available: Available expressions to update.
        """
        # Invalidate expressions if instruction has side effects
        if isinstance(inst, StoreVar):
            # Invalidate expressions using this variable
            available.invalidate(inst.var)
        elif isinstance(inst, Call):
            # Conservative: invalidate all expressions with variables
            # (calls might modify globals or have other side effects)
            for value in list(available.definitions.keys()):
                if isinstance(value, Variable):
                    available.invalidate(value)

    def _intersect_available(
        self,
        sets: list[AvailableExpressions],
    ) -> AvailableExpressions:
        """Compute intersection of available expression sets.

        Args:
            sets: List of available expression sets.

        Returns:
            The intersection.
        """
        if not sets:
            return AvailableExpressions()

        # Start with first set
        result = AvailableExpressions()
        if not sets[0].expressions:
            return result

        # Find expressions available in all sets
        for expr, value in sets[0].expressions.items():
            available_in_all = True
            for s in sets[1:]:
                if expr not in s.expressions:
                    available_in_all = False
                    break
                # Check if same value
                if s.expressions[expr] != value:
                    available_in_all = False
                    break

            if available_in_all:
                result.add(expr, value)

        return result

    def _available_changed(
        self,
        old: AvailableExpressions,
        new: AvailableExpressions,
    ) -> bool:
        """Check if available expressions changed.

        Args:
            old: Old available expressions.
            new: New available expressions.

        Returns:
            True if changed.
        """
        if len(old.expressions) != len(new.expressions):
            return True

        for expr, value in old.expressions.items():
            if expr not in new.expressions or new.expressions[expr] != value:
                return True

        return False

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
