"""Constant propagation and folding optimization pass.

This module implements constant propagation at the MIR level, replacing
variable uses with constants and folding constant expressions.
"""

from typing import Any

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Phi,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class ConstantLattice:
    """Lattice for constant propagation analysis.

    Values can be:
    - TOP: Unknown/uninitialized
    - Constant value: Known constant
    - BOTTOM: Not a constant (conflicting values)
    """

    TOP = object()  # Unknown
    BOTTOM = object()  # Not constant

    def __init__(self) -> None:
        """Initialize the lattice."""
        self.values: dict[MIRValue, Any] = {}

    def get(self, value: MIRValue) -> Any:
        """Get the lattice value.

        Args:
            value: MIR value to query.

        Returns:
            Lattice value (TOP, BOTTOM, or constant).
        """
        return self.values.get(value, self.TOP)

    def set(self, value: MIRValue, lattice_val: Any) -> bool:
        """Set the lattice value.

        Args:
            value: MIR value to set.
            lattice_val: New lattice value.

        Returns:
            True if the value changed.
        """
        old = self.get(value)
        if old == lattice_val:
            return False

        if old == self.BOTTOM:
            return False  # Can't change from BOTTOM

        if lattice_val == self.TOP:
            return False  # Can't go back to TOP

        if old == self.TOP:
            self.values[value] = lattice_val
            return True

        # Both are constants - must be same or go to BOTTOM
        if old != lattice_val:
            self.values[value] = self.BOTTOM
            return True

        return False

    def is_constant(self, value: MIRValue) -> bool:
        """Check if a value is a known constant.

        Args:
            value: MIR value to check.

        Returns:
            True if the value is a known constant.
        """
        val = self.get(value)
        return bool(val != self.TOP and val != self.BOTTOM)

    def get_constant(self, value: MIRValue) -> Any:
        """Get the constant value.

        Args:
            value: MIR value to query.

        Returns:
            The constant value or None.
        """
        val = self.get(value)
        if val != self.TOP and val != self.BOTTOM:
            return val
        return None


class ConstantPropagation(OptimizationPass):
    """Constant propagation and folding optimization pass."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="constant-propagation",
            description="Propagate constants and fold constant expressions",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run constant propagation on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        # Perform constant propagation analysis
        lattice = self._analyze_constants(function)

        # Apply transformations based on analysis
        transformer = MIRTransformer(function)

        # Replace uses with constants
        for value, const_val in lattice.values.items():
            if const_val != ConstantLattice.TOP and const_val != ConstantLattice.BOTTOM:
                if isinstance(value, Variable | Temp):
                    # Create constant
                    const = Constant(const_val, self._infer_type(const_val))
                    count = transformer.replace_uses(value, const)
                    self.stats["constants_propagated"] = self.stats.get("constants_propagated", 0) + count

        # Fold constant expressions
        self._fold_constant_expressions(function, transformer)

        # Simplify control flow with known conditions
        self._simplify_control_flow(function, transformer, lattice)

        return transformer.modified

    def _analyze_constants(self, function: MIRFunction) -> ConstantLattice:
        """Analyze function to find constant values using iterative dataflow.

        This implements a worklist algorithm that converges to a fixed point,
        properly handling loops and cross-block propagation.

        Args:
            function: Function to analyze.

        Returns:
            Constant lattice with analysis results.
        """
        lattice = ConstantLattice()
        worklist = set()
        block_lattices: dict[Any, ConstantLattice] = {}

        # Initialize all blocks' local lattices
        for block in function.cfg.blocks.values():
            block_lattices[block] = ConstantLattice()
            worklist.add(block)

        # Fixed-point iteration
        iteration_count = 0
        max_iterations = 100  # Prevent infinite loops

        while worklist and iteration_count < max_iterations:
            iteration_count += 1
            block = worklist.pop()

            # Merge lattice values from predecessors
            changed = self._merge_predecessors(block, block_lattices, lattice)

            # Process phi nodes with proper meet operation
            for phi in block.phi_nodes:
                if self._process_phi(phi, block, block_lattices, lattice):
                    changed = True

            # Process instructions
            for inst in block.instructions:
                if self._process_instruction(inst, lattice):
                    changed = True

            # If this block changed, add successors to worklist
            if changed:
                worklist.update(block.successors)

        return lattice

    def _merge_predecessors(
        self, block: Any, block_lattices: dict[Any, ConstantLattice], lattice: ConstantLattice
    ) -> bool:
        """Merge lattice values from predecessor blocks.

        Args:
            block: Current block.
            block_lattices: Per-block lattice states.
            lattice: Global lattice.

        Returns:
            True if any values changed.
        """
        changed = False

        # For each predecessor, merge its output values
        for pred in block.predecessors:
            pred_lattice = block_lattices.get(pred)
            if pred_lattice:
                for value, const_val in pred_lattice.values.items():
                    if lattice.set(value, const_val):
                        changed = True

        return changed

    def _process_phi(
        self, phi: Phi, block: Any, block_lattices: dict[Any, ConstantLattice], lattice: ConstantLattice
    ) -> bool:
        """Process phi node with improved cross-block analysis.

        Args:
            phi: Phi node to process.
            block: Current block.
            block_lattices: Per-block lattice states.
            lattice: Constant lattice.

        Returns:
            True if the phi's value changed.
        """
        # Collect all incoming values with proper lattice meet
        result = ConstantLattice.TOP
        all_same = True
        first_val = None

        for value, pred_block in phi.incoming:
            if isinstance(value, Constant):
                val = value.value
            else:
                # Look up value from predecessor's lattice
                pred_lattice = block_lattices.get(pred_block, lattice)
                val = pred_lattice.get(value) if pred_lattice else lattice.get(value)

            if val == ConstantLattice.BOTTOM:
                result = ConstantLattice.BOTTOM
                break
            elif val != ConstantLattice.TOP:
                if first_val is None:
                    first_val = val
                elif first_val != val:
                    all_same = False
                    result = ConstantLattice.BOTTOM
                    break

        # If all values are the same constant, propagate it
        if all_same and first_val is not None:
            result = first_val

        if result != ConstantLattice.TOP:
            return lattice.set(phi.dest, result)
        return False

    def _process_instruction(self, inst: MIRInstruction, lattice: ConstantLattice) -> bool:
        """Process instruction with change tracking.

        Args:
            inst: Instruction to process.
            lattice: Constant lattice.

        Returns:
            True if any value changed.
        """
        changed = False

        if isinstance(inst, LoadConst):
            # LoadConst defines a constant
            if lattice.set(inst.dest, inst.constant.value):
                changed = True

        elif isinstance(inst, Copy):
            # Copy propagates constants
            if isinstance(inst.source, Constant):
                if lattice.set(inst.dest, inst.source.value):
                    changed = True
            elif isinstance(inst.source, Variable | Temp):
                val = lattice.get(inst.source)
                if val != ConstantLattice.TOP:
                    if lattice.set(inst.dest, val):
                        changed = True

        elif isinstance(inst, StoreVar):
            # Store propagates constants to variables
            if isinstance(inst.source, Constant):
                if lattice.set(inst.var, inst.source.value):
                    changed = True
            elif isinstance(inst.source, Variable | Temp):
                val = lattice.get(inst.source)
                if val != ConstantLattice.TOP:
                    if lattice.set(inst.var, val):
                        changed = True

        elif isinstance(inst, LoadVar):
            # Load from variable
            val = lattice.get(inst.var)
            if val != ConstantLattice.TOP:
                if lattice.set(inst.dest, val):
                    changed = True

        elif isinstance(inst, BinaryOp):
            # Try to fold binary operations
            left_val = self._get_value(inst.left, lattice)
            right_val = self._get_value(inst.right, lattice)

            if left_val is not None and right_val is not None:
                result = self._fold_binary_op(inst.op, left_val, right_val)
                if result is not None:
                    if lattice.set(inst.dest, result):
                        changed = True

        elif isinstance(inst, UnaryOp):
            # Try to fold unary operations
            operand_val = self._get_value(inst.operand, lattice)

            if operand_val is not None:
                result = self._fold_unary_op(inst.op, operand_val)
                if result is not None:
                    if lattice.set(inst.dest, result):
                        changed = True

        return changed

    def _process_binary_op(self, inst: BinaryOp, lattice: ConstantLattice) -> None:
        """Process a binary operation for constant folding.

        Args:
            inst: Binary operation instruction.
            lattice: Constant lattice.
        """
        # Get operand values
        left_val = self._get_value(inst.left, lattice)
        right_val = self._get_value(inst.right, lattice)

        if left_val is None or right_val is None:
            return

        # Try to fold the operation
        result = self._fold_binary_op(inst.op, left_val, right_val)
        if result is not None:
            lattice.set(inst.dest, result)

    def _process_unary_op(self, inst: UnaryOp, lattice: ConstantLattice) -> None:
        """Process a unary operation for constant folding.

        Args:
            inst: Unary operation instruction.
            lattice: Constant lattice.
        """
        # Get operand value
        operand_val = self._get_value(inst.operand, lattice)

        if operand_val is None:
            return

        # Try to fold the operation
        result = self._fold_unary_op(inst.op, operand_val)
        if result is not None:
            lattice.set(inst.dest, result)

    def _get_value(self, value: MIRValue, lattice: ConstantLattice) -> Any:
        """Get the constant value of a MIR value.

        Args:
            value: MIR value to evaluate.
            lattice: Constant lattice.

        Returns:
            The constant value or None.
        """
        if isinstance(value, Constant):
            return value.value
        elif isinstance(value, Variable | Temp):
            val = lattice.get(value)
            if val != ConstantLattice.TOP and val != ConstantLattice.BOTTOM:
                return val
        return None

    def _fold_binary_op(self, op: str, left: Any, right: Any) -> Any:
        """Fold a binary operation with constant operands.

        Args:
            op: Operation string.
            left: Left operand value.
            right: Right operand value.

        Returns:
            The folded result or None.
        """
        try:
            # Arithmetic operations
            if op == "+":
                # Handle string concatenation and numeric addition
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                if right != 0:
                    # Integer division for integers
                    if isinstance(left, int) and isinstance(right, int):
                        return left // right
                    return left / right
            elif op == "//":
                if right != 0:
                    return left // right
            elif op == "%":
                if right != 0:
                    return left % right
            elif op == "**":
                return left**right

            # Comparison operations
            elif op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == ">":
                return left > right
            elif op == ">=":
                return left >= right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "===":  # Strict equality
                return left is right
            elif op == "!==":  # Strict inequality
                return left is not right

            # Logical operations
            elif op == "and":
                return left and right
            elif op == "or":
                return left or right

            # Bitwise operations
            elif op == "&":
                if isinstance(left, int) and isinstance(right, int):
                    return left & right
            elif op == "|":
                if isinstance(left, int) and isinstance(right, int):
                    return left | right
            elif op == "^":
                if isinstance(left, int) and isinstance(right, int):
                    return left ^ right
            elif op == "<<":
                if isinstance(left, int) and isinstance(right, int):
                    return left << right
            elif op == ">>":
                if isinstance(left, int) and isinstance(right, int):
                    return left >> right

            # String operations
            elif op == "in":
                return left in right
            elif op == "not in":
                return left not in right

        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            pass
        return None

    def _fold_unary_op(self, op: str, operand: Any) -> Any:
        """Fold a unary operation with constant operand.

        Args:
            op: Operation string.
            operand: Operand value.

        Returns:
            The folded result or None.
        """
        try:
            if op == "-":
                return -operand
            elif op == "not":
                return not operand
            elif op == "+":
                return +operand
            elif op == "~":  # Bitwise NOT
                if isinstance(operand, int):
                    return ~operand
            elif op == "abs":
                return abs(operand)
            elif op == "len":
                if hasattr(operand, "__len__"):
                    return len(operand)
        except (TypeError, ValueError):
            pass
        return None

    def _fold_constant_expressions(
        self,
        function: MIRFunction,
        transformer: MIRTransformer,
    ) -> None:
        """Fold constant expressions in the function.

        Args:
            function: Function to optimize.
            transformer: MIR transformer.
        """
        for block in function.cfg.blocks.values():
            for inst in list(block.instructions):
                if isinstance(inst, BinaryOp):
                    # Try to fold binary operation
                    left_val = self._get_constant_value(inst.left)
                    right_val = self._get_constant_value(inst.right)

                    if left_val is not None and right_val is not None:
                        result = self._fold_binary_op(inst.op, left_val, right_val)
                        if result is not None:
                            # Replace with LoadConst
                            const = Constant(result, self._infer_type(result))
                            new_inst = LoadConst(inst.dest, const, inst.source_location)
                            transformer.replace_instruction(block, inst, new_inst)
                            self.stats["expressions_folded"] = self.stats.get("expressions_folded", 0) + 1

                elif isinstance(inst, UnaryOp):
                    # Try to fold unary operation
                    operand_val = self._get_constant_value(inst.operand)

                    if operand_val is not None:
                        result = self._fold_unary_op(inst.op, operand_val)
                        if result is not None:
                            # Replace with LoadConst
                            const = Constant(result, self._infer_type(result))
                            new_inst = LoadConst(inst.dest, const, inst.source_location)
                            transformer.replace_instruction(block, inst, new_inst)
                            self.stats["expressions_folded"] = self.stats.get("expressions_folded", 0) + 1

    def _simplify_control_flow(
        self,
        function: MIRFunction,
        transformer: MIRTransformer,
        lattice: ConstantLattice,
    ) -> None:
        """Simplify control flow with known conditions.

        Args:
            function: Function to optimize.
            transformer: MIR transformer.
            lattice: Constant lattice.
        """
        for block in list(function.cfg.blocks.values()):
            term = block.get_terminator()
            if isinstance(term, ConditionalJump):
                # Check if condition is constant
                cond_val = self._get_value(term.condition, lattice)
                if cond_val is not None:
                    # Replace with unconditional jump
                    if cond_val:
                        new_jump = Jump(term.true_label, term.source_location)
                    elif term.false_label is not None:
                        new_jump = Jump(term.false_label, term.source_location)
                    else:
                        continue  # Can't simplify without false label

                    transformer.replace_instruction(block, term, new_jump)
                    self.stats["branches_simplified"] = self.stats.get("branches_simplified", 0) + 1

    def _get_constant_value(self, value: MIRValue) -> Any:
        """Get the constant value if it's a constant.

        Args:
            value: MIR value.

        Returns:
            Constant value or None.
        """
        if isinstance(value, Constant):
            return value.value
        return None

    def _infer_type(self, value: Any) -> MIRType:
        """Infer MIR type from a Python value.

        Args:
            value: Python value.

        Returns:
            Inferred MIR type.
        """
        if isinstance(value, bool):
            return MIRType.BOOL
        elif isinstance(value, int):
            return MIRType.INT
        elif isinstance(value, float):
            return MIRType.FLOAT
        elif isinstance(value, str):
            return MIRType.STRING
        elif value is None:
            return MIRType.EMPTY
        else:
            return MIRType.UNKNOWN

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
