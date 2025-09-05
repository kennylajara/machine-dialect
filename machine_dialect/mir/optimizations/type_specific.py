"""Type-specific MIR optimization pass.

This module implements type-aware optimizations that leverage type information
from variable definitions to generate more efficient MIR code.
"""


from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Copy,
    LoadConst,
    MIRInstruction,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    FunctionPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class TypeSpecificOptimization(FunctionPass):
    """Type-specific optimization pass.

    This pass performs optimizations based on known type information:
    - Type-aware constant folding
    - Elimination of unnecessary type checks
    - Boolean short-circuit evaluation
    - Integer-specific optimizations
    - Float-specific optimizations

    Note: This is distinct from TypeSpecialization which creates
    specialized function versions. This pass optimizes within functions.
    """

    def __init__(self) -> None:
        """Initialize the type-specific optimization pass."""
        super().__init__()
        self.type_info: dict[str, MIRType | MIRUnionType] = {}
        self.stats = {
            "constant_folded": 0,
            "type_checks_eliminated": 0,
            "boolean_optimized": 0,
            "integer_optimized": 0,
            "float_optimized": 0,
            "instructions_removed": 0,
        }

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="type-specific-optimization",
            description="Optimize MIR based on known type information",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run type-specific optimizations on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        modified = False

        # First, collect type information from the function
        self._collect_type_info(function)

        # Then optimize each basic block
        for block in function.cfg.blocks.values():
            if self._optimize_block(block, function):
                modified = True

        return modified

    def _collect_type_info(self, function: MIRFunction) -> None:
        """Collect type information from function locals and parameters.

        Args:
            function: The function to analyze.
        """
        self.type_info.clear()

        # Collect parameter types
        for param in function.params:
            if param.type != MIRType.UNKNOWN:
                self.type_info[param.name] = param.type
            # Check for union type metadata (only if not None)
            if hasattr(param, "union_type") and param.union_type is not None:
                self.type_info[param.name] = param.union_type

        # Collect local variable types
        for local in function.locals.values():
            if local.type != MIRType.UNKNOWN:
                self.type_info[local.name] = local.type
            # Check for union type metadata (only if not None)
            if hasattr(local, "union_type") and local.union_type is not None:
                self.type_info[local.name] = local.union_type

    def _optimize_block(self, block: BasicBlock, function: MIRFunction) -> bool:
        """Optimize a basic block using type information.

        Args:
            block: The block to optimize.
            function: The containing function.

        Returns:
            True if the block was modified.
        """
        modified = False
        new_instructions = []

        for inst in block.instructions:
            optimized = self._optimize_instruction(inst, function)

            if optimized is None:
                # Instruction was eliminated
                self.stats["instructions_removed"] += 1
                modified = True
            elif optimized != inst:
                # Instruction was replaced
                new_instructions.append(optimized)
                modified = True
            else:
                # No change
                new_instructions.append(inst)

        if modified:
            block.instructions = new_instructions

        return modified

    def _optimize_instruction(self, inst: MIRInstruction, function: MIRFunction) -> MIRInstruction | None:
        """Optimize a single instruction based on type information.

        Args:
            inst: The instruction to optimize.
            function: The containing function.

        Returns:
            Optimized instruction, None if eliminated, or original if unchanged.
        """
        if isinstance(inst, BinaryOp):
            return self._optimize_binary_op(inst, function)
        elif isinstance(inst, UnaryOp):
            return self._optimize_unary_op(inst, function)

        return inst

    def _optimize_binary_op(self, inst: BinaryOp, function: MIRFunction) -> MIRInstruction:
        """Optimize binary operations based on operand types.

        Args:
            inst: The binary operation.
            function: The containing function.

        Returns:
            Optimized instruction or None.
        """
        left_type = self._get_value_type(inst.left)
        right_type = self._get_value_type(inst.right)

        # Type-specific constant folding
        if isinstance(inst.left, Constant) and isinstance(inst.right, Constant):
            result = self._fold_binary_constants(inst.op, inst.left, inst.right, left_type, right_type)
            if result is not None:
                self.stats["constant_folded"] += 1
                return LoadConst(inst.dest, result)

        # Comparison optimizations (type-independent)
        optimized = self._optimize_comparison(inst, left_type, right_type)
        if optimized and optimized != inst:
            return optimized

        # Integer-specific optimizations
        if left_type == MIRType.INT and right_type == MIRType.INT:
            optimized = self._optimize_integer_binary_op(inst)
            if optimized and optimized != inst:
                self.stats["integer_optimized"] += 1
                return optimized

        # Float-specific optimizations
        elif left_type == MIRType.FLOAT or right_type == MIRType.FLOAT:
            optimized = self._optimize_float_binary_op(inst)
            if optimized and optimized != inst:
                self.stats["float_optimized"] += 1
                return optimized

        # Boolean-specific optimizations
        elif inst.op in ("and", "or"):
            optimized = self._optimize_boolean_op(inst)
            if optimized and optimized != inst:
                self.stats["boolean_optimized"] += 1
                return optimized

        return inst

    def _optimize_unary_op(self, inst: UnaryOp, function: MIRFunction) -> MIRInstruction:
        """Optimize unary operations based on operand type.

        Args:
            inst: The unary operation.
            function: The containing function.

        Returns:
            Optimized instruction.
        """
        operand_type = self._get_value_type(inst.operand)

        # Constant folding
        if isinstance(inst.operand, Constant):
            result = self._fold_unary_constant(inst.op, inst.operand, operand_type)
            if result is not None:
                self.stats["constant_folded"] += 1
                return LoadConst(inst.dest, result)

        # Type-specific optimizations
        if inst.op == "-":
            if operand_type == MIRType.INT:
                # Integer negation optimizations
                pass  # Could add specific patterns
            elif operand_type == MIRType.FLOAT:
                # Float negation optimizations
                pass  # Could add specific patterns
        elif inst.op == "not":
            # Boolean NOT optimizations
            if isinstance(inst.operand, Variable):
                # Could optimize double negation patterns
                pass

        return inst

    def _fold_binary_constants(
        self,
        operator: str,
        left: Constant,
        right: Constant,
        left_type: MIRType,
        right_type: MIRType,
    ) -> Constant | None:
        """Fold binary operation on constants with type awareness.

        Args:
            operator: The operator.
            left: Left constant.
            right: Right constant.
            left_type: Type of left operand.
            right_type: Type of right operand.

        Returns:
            Folded constant or None if not foldable.
        """
        try:
            # Type-specific folding
            if left_type == MIRType.INT and right_type == MIRType.INT:
                # Integer arithmetic
                if operator == "+":
                    return Constant(left.value + right.value, MIRType.INT)
                elif operator == "-":
                    return Constant(left.value - right.value, MIRType.INT)
                elif operator == "*":
                    return Constant(left.value * right.value, MIRType.INT)
                elif operator == "/" and right.value != 0:
                    # Integer division
                    return Constant(left.value // right.value, MIRType.INT)
                elif operator == "%" and right.value != 0:
                    return Constant(left.value % right.value, MIRType.INT)
                elif operator == "**":
                    return Constant(left.value**right.value, MIRType.INT)
                # Comparisons
                elif operator == "==":
                    return Constant(left.value == right.value, MIRType.BOOL)
                elif operator == "!=":
                    return Constant(left.value != right.value, MIRType.BOOL)
                elif operator == "<":
                    return Constant(left.value < right.value, MIRType.BOOL)
                elif operator == "<=":
                    return Constant(left.value <= right.value, MIRType.BOOL)
                elif operator == ">":
                    return Constant(left.value > right.value, MIRType.BOOL)
                elif operator == ">=":
                    return Constant(left.value >= right.value, MIRType.BOOL)

            elif left_type == MIRType.FLOAT or right_type == MIRType.FLOAT:
                # Float arithmetic (promote integers if needed)
                left_val = float(left.value)
                right_val = float(right.value)

                if operator == "+":
                    return Constant(left_val + right_val, MIRType.FLOAT)
                elif operator == "-":
                    return Constant(left_val - right_val, MIRType.FLOAT)
                elif operator == "*":
                    return Constant(left_val * right_val, MIRType.FLOAT)
                elif operator == "/" and right_val != 0.0:
                    return Constant(left_val / right_val, MIRType.FLOAT)
                elif operator == "**":
                    return Constant(left_val**right_val, MIRType.FLOAT)
                # Comparisons
                elif operator == "==":
                    return Constant(left_val == right_val, MIRType.BOOL)
                elif operator == "!=":
                    return Constant(left_val != right_val, MIRType.BOOL)
                elif operator == "<":
                    return Constant(left_val < right_val, MIRType.BOOL)
                elif operator == "<=":
                    return Constant(left_val <= right_val, MIRType.BOOL)
                elif operator == ">":
                    return Constant(left_val > right_val, MIRType.BOOL)
                elif operator == ">=":
                    return Constant(left_val >= right_val, MIRType.BOOL)

            elif left_type == MIRType.BOOL and right_type == MIRType.BOOL:
                # Boolean operations
                if operator == "and":
                    return Constant(left.value and right.value, MIRType.BOOL)
                elif operator == "or":
                    return Constant(left.value or right.value, MIRType.BOOL)
                elif operator == "==":
                    return Constant(left.value == right.value, MIRType.BOOL)
                elif operator == "!=":
                    return Constant(left.value != right.value, MIRType.BOOL)

            elif left_type == MIRType.STRING and right_type == MIRType.STRING:
                # String operations
                if operator == "+":
                    return Constant(str(left.value) + str(right.value), MIRType.STRING)
                elif operator == "==":
                    return Constant(left.value == right.value, MIRType.BOOL)
                elif operator == "!=":
                    return Constant(left.value != right.value, MIRType.BOOL)

        except (ValueError, TypeError, ZeroDivisionError):
            # Can't fold - runtime error
            pass

        return None

    def _fold_unary_constant(self, operator: str, operand: Constant, operand_type: MIRType) -> Constant | None:
        """Fold unary operation on constant with type awareness.

        Args:
            operator: The operator.
            operand: The constant operand.
            operand_type: Type of operand.

        Returns:
            Folded constant or None if not foldable.
        """
        try:
            if operator == "-":
                if operand_type == MIRType.INT:
                    return Constant(-operand.value, MIRType.INT)
                elif operand_type == MIRType.FLOAT:
                    return Constant(-operand.value, MIRType.FLOAT)
            elif operator == "not":
                return Constant(not operand.value, MIRType.BOOL)
        except (ValueError, TypeError):
            pass

        return None

    def _optimize_integer_binary_op(self, inst: BinaryOp) -> MIRInstruction:
        """Apply integer-specific optimizations including strength reduction.

        Args:
            inst: The binary operation on integers.

        Returns:
            Optimized instruction.
        """
        # Strength reduction for power-of-2 operations
        if isinstance(inst.right, Constant):
            right_val = inst.right.value

            # Special case for multiply by 2 - use addition instead of shift
            if inst.op == "*" and right_val == 2:
                # x * 2 -> x + x (addition can be faster than multiplication)
                return BinaryOp(inst.dest, "+", inst.left, inst.left)

            # Check if value is a positive power of 2 for other operations
            elif right_val > 0 and (right_val & (right_val - 1)) == 0:
                shift_amount = right_val.bit_length() - 1

                if inst.op == "*" and right_val > 2:  # Skip 2, handled above
                    # x * (2^n) -> x << n
                    from machine_dialect.mir.mir_instructions import ShiftOp

                    return ShiftOp(inst.dest, inst.left, Constant(shift_amount, MIRType.INT), "<<")
                elif inst.op == "/":
                    # x / (2^n) -> x >> n (for positive x)
                    # Note: This is arithmetic right shift for signed integers
                    from machine_dialect.mir.mir_instructions import ShiftOp

                    return ShiftOp(inst.dest, inst.left, Constant(shift_amount, MIRType.INT), ">>")
                elif inst.op == "%":
                    # x % (2^n) -> x & ((2^n) - 1)
                    mask_val = right_val - 1
                    return BinaryOp(inst.dest, "&", inst.left, Constant(mask_val, MIRType.INT))

            # Other optimizations with right constant
            if inst.op == "+" and right_val == 0:
                # x + 0 -> x
                return Copy(inst.dest, inst.left)
            elif inst.op == "-" and right_val == 0:
                # x - 0 -> x
                return Copy(inst.dest, inst.left)
            elif inst.op == "*":
                if right_val == 0:
                    # x * 0 -> 0
                    return LoadConst(inst.dest, Constant(0, MIRType.INT))
                elif right_val == 1:
                    # x * 1 -> x
                    return Copy(inst.dest, inst.left)
                elif right_val == -1:
                    # x * -1 -> -x
                    return UnaryOp(inst.dest, "-", inst.left)
                elif right_val == 2:
                    # x * 2 -> x + x (addition can be faster than multiplication)
                    return BinaryOp(inst.dest, "+", inst.left, inst.left)
            elif inst.op == "/":
                if right_val == 1:
                    # x / 1 -> x
                    return Copy(inst.dest, inst.left)
                elif right_val == -1:
                    # x / -1 -> -x
                    return UnaryOp(inst.dest, "-", inst.left)

        # Optimizations with left constant
        if isinstance(inst.left, Constant):
            left_val = inst.left.value

            # Check if value is a positive power of 2
            if left_val > 0 and (left_val & (left_val - 1)) == 0 and inst.op == "*":
                shift_amount = left_val.bit_length() - 1
                # (2^n) * x -> x << n
                from machine_dialect.mir.mir_instructions import ShiftOp

                return ShiftOp(inst.dest, inst.right, Constant(shift_amount, MIRType.INT), "<<")

            if inst.op == "+" and left_val == 0:
                # 0 + x -> x
                return Copy(inst.dest, inst.right)
            elif inst.op == "*":
                if left_val == 0:
                    # 0 * x -> 0
                    return LoadConst(inst.dest, Constant(0, MIRType.INT))
                elif left_val == 1:
                    # 1 * x -> x
                    return Copy(inst.dest, inst.right)
                elif left_val == 2:
                    # 2 * x -> x + x
                    return BinaryOp(inst.dest, "+", inst.right, inst.right)

        # Self-operation optimizations
        if inst.left == inst.right:
            if inst.op == "-":
                # x - x -> 0
                return LoadConst(inst.dest, Constant(0, MIRType.INT))
            elif inst.op == "/":
                # x / x -> 1 (assuming x != 0, which should be checked at runtime)
                # Note: This optimization assumes no division by zero
                return LoadConst(inst.dest, Constant(1, MIRType.INT))
            elif inst.op == "%":
                # x % x -> 0
                return LoadConst(inst.dest, Constant(0, MIRType.INT))
            elif inst.op == "^":
                # x ^ x -> 0 (XOR)
                return LoadConst(inst.dest, Constant(0, MIRType.INT))
            elif inst.op == "&":
                # x & x -> x (AND)
                return Copy(inst.dest, inst.left)
            elif inst.op == "|":
                # x | x -> x (OR)
                return Copy(inst.dest, inst.left)

        return inst

    def _optimize_float_binary_op(self, inst: BinaryOp) -> MIRInstruction:
        """Apply float-specific optimizations.

        Args:
            inst: The binary operation involving floats.

        Returns:
            Optimized instruction.
        """
        # Similar to integer but being careful with float precision
        if isinstance(inst.right, Constant):
            right_val = inst.right.value

            if inst.op == "+" and right_val == 0.0:
                # x + 0.0 -> x
                return Copy(inst.dest, inst.left)
            elif inst.op == "-" and right_val == 0.0:
                # x - 0.0 -> x
                return Copy(inst.dest, inst.left)
            elif inst.op == "*":
                if right_val == 0.0:
                    # x * 0.0 -> 0.0
                    return LoadConst(inst.dest, Constant(0.0, MIRType.FLOAT))
                elif right_val == 1.0:
                    # x * 1.0 -> x
                    return Copy(inst.dest, inst.left)
            elif inst.op == "/" and right_val == 1.0:
                # x / 1.0 -> x
                return Copy(inst.dest, inst.left)

        return inst

    def _optimize_comparison(self, inst: BinaryOp, left_type: MIRType, right_type: MIRType) -> MIRInstruction:
        """Apply comparison-specific optimizations.

        Args:
            inst: The comparison operation.
            left_type: Type of left operand.
            right_type: Type of right operand.

        Returns:
            Optimized instruction.
        """
        # Self-comparison optimizations
        if inst.left == inst.right:
            if inst.op == "==":
                # x == x -> True (except for NaN, but we assume non-NaN)
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
            elif inst.op == "!=":
                # x != x -> False
                return LoadConst(inst.dest, Constant(False, MIRType.BOOL))
            elif inst.op == "<=":
                # x <= x -> True
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
            elif inst.op == ">=":
                # x >= x -> True
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
            elif inst.op == "<":
                # x < x -> False
                return LoadConst(inst.dest, Constant(False, MIRType.BOOL))
            elif inst.op == ">":
                # x > x -> False
                return LoadConst(inst.dest, Constant(False, MIRType.BOOL))

        return inst

    def _optimize_boolean_op(self, inst: BinaryOp) -> MIRInstruction:
        """Apply boolean-specific optimizations.

        Args:
            inst: The boolean operation.

        Returns:
            Optimized instruction.
        """
        # Idempotent operations
        if inst.left == inst.right:
            if inst.op == "and":
                # x and x -> x
                return Copy(inst.dest, inst.left)
            elif inst.op == "or":
                # x or x -> x
                return Copy(inst.dest, inst.left)

        # Short-circuit evaluation patterns
        if isinstance(inst.left, Constant):
            left_val = bool(inst.left.value)

            if inst.op == "and" and not left_val:
                # False and x -> False
                return LoadConst(inst.dest, Constant(False, MIRType.BOOL))
            elif inst.op == "or" and left_val:
                # True or x -> True
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL))

        if isinstance(inst.right, Constant):
            right_val = bool(inst.right.value)

            if inst.op == "and":
                if not right_val:
                    # x and False -> False
                    return LoadConst(inst.dest, Constant(False, MIRType.BOOL))
                else:
                    # x and True -> x
                    return Copy(inst.dest, inst.left)
            elif inst.op == "or":
                if right_val:
                    # x or True -> True
                    return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
                else:
                    # x or False -> x
                    return Copy(inst.dest, inst.left)

        return inst

    def _get_value_type(self, value: MIRValue) -> MIRType:
        """Get the type of a MIR value.

        Args:
            value: The value to get type for.

        Returns:
            The MIR type.
        """
        if isinstance(value, Constant):
            # Constants always have a concrete MIR type
            if isinstance(value.type, MIRUnionType):
                return MIRType.UNKNOWN
            return value.type
        elif isinstance(value, Variable):
            # Check our collected type info
            if value.name in self.type_info:
                type_info = self.type_info[value.name]
                if isinstance(type_info, MIRUnionType):
                    # For union types, check runtime type if available
                    if hasattr(value, "runtime_type"):
                        runtime_type = getattr(value, "runtime_type", MIRType.UNKNOWN)
                        if isinstance(runtime_type, MIRType):
                            return runtime_type
                    return MIRType.UNKNOWN
                # type_info here is guaranteed to be MIRType from our collection logic
                return type_info if isinstance(type_info, MIRType) else MIRType.UNKNOWN
            # Variable.type could be a union type from initialization
            if isinstance(value.type, MIRUnionType):
                return MIRType.UNKNOWN
            return value.type
        elif isinstance(value, Temp):
            # Temps should always have concrete types
            if isinstance(value.type, MIRUnionType):
                return MIRType.UNKNOWN
            return value.type

        return MIRType.UNKNOWN

    def finalize(self) -> None:
        """Finalize and report statistics."""
        if any(self.stats.values()):
            print("Type-specific optimization statistics:")
            for key, value in self.stats.items():
                if value > 0:
                    print(f"  {key}: {value}")
