"""Type-specific MIR optimization pass.

This module implements type-aware optimizations that leverage type information
from variable definitions to generate more efficient MIR code.
"""


from machine_dialect.mir.analyses.dominance_analysis import DominanceAnalysis
from machine_dialect.mir.analyses.use_def_chains import UseDefChains, UseDefChainsAnalysis
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
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
from machine_dialect.mir.ssa_construction import DominanceInfo


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
        self.def_map: dict[MIRValue, MIRInstruction] = {}  # Maps values to their defining instructions
        self.use_def_chains: UseDefChains | None = None  # Use-def chain analysis
        self.dominance_info: DominanceInfo | None = None  # Dominance information
        self.value_ranges: dict[MIRValue, tuple[int | float | None, int | float | None]] = {}  # Value range tracking
        self.stats = {
            "constant_folded": 0,
            "type_checks_eliminated": 0,
            "boolean_optimized": 0,
            "integer_optimized": 0,
            "float_optimized": 0,
            "string_optimized": 0,
            "instructions_removed": 0,
            "patterns_matched": 0,
            "cross_block_optimized": 0,
            "range_optimized": 0,
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
            requires=["use-def-chains", "dominance"],
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

        # Get analysis results if available
        self._get_analysis_results(function)

        # First, collect type information from the function
        self._collect_type_info(function)

        # Build def-use chains for pattern detection
        self._build_def_map(function)

        # Initialize value range analysis
        self._initialize_value_ranges(function)

        # Perform cross-block type propagation
        if self._propagate_types_across_blocks(function):
            modified = True

        # Then optimize each basic block
        for block in function.cfg.blocks.values():
            if self._optimize_block(block, function):
                modified = True

        # Perform cross-block optimizations
        if self._optimize_across_blocks(function):
            modified = True

        return modified

    def _build_def_map(self, function: MIRFunction) -> None:
        """Build a map from values to their defining instructions.

        Args:
            function: The function to analyze.
        """
        self.def_map.clear()

        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                # Record all definitions
                for def_val in inst.get_defs():
                    self.def_map[def_val] = inst

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
        # First try advanced pattern detection
        pattern_result = self._detect_advanced_patterns(inst, function)
        if pattern_result and pattern_result != inst:
            return pattern_result

        left_type = self._get_value_type(inst.left)
        right_type = self._get_value_type(inst.right)

        # Type-specific constant folding
        if isinstance(inst.left, Constant) and isinstance(inst.right, Constant):
            result = self._fold_binary_constants(inst.op, inst.left, inst.right, left_type, right_type)
            if result is not None:
                self.stats["constant_folded"] += 1
                return LoadConst(inst.dest, result)

        # Try range-based optimization
        range_result = self._optimize_with_range_info(inst)
        if range_result:
            return range_result

        # Comparison optimizations (type-independent)
        optimized = self._optimize_comparison(inst, left_type, right_type)
        if optimized and optimized != inst:
            return optimized

        # Integer-specific optimizations
        if left_type == MIRType.INT and right_type == MIRType.INT:
            optimized = self._optimize_integer_binary_op(inst)
            if optimized and optimized != inst:
                self.stats["integer_optimized"] += 1
                # Update value ranges based on operation
                self._update_range_from_operation(inst, optimized)
                return optimized

        # Float-specific optimizations
        elif left_type == MIRType.FLOAT or right_type == MIRType.FLOAT:
            optimized = self._optimize_float_binary_op(inst)
            if optimized and optimized != inst:
                self.stats["float_optimized"] += 1
                return optimized

        # String-specific optimizations
        elif left_type == MIRType.STRING or right_type == MIRType.STRING:
            optimized = self._optimize_string_binary_op(inst)
            if optimized and optimized != inst:
                self.stats["string_optimized"] += 1
                return optimized

        # Boolean-specific optimizations
        elif inst.op in ("and", "or"):
            optimized = self._optimize_boolean_op(inst)
            if optimized and optimized != inst:
                self.stats["boolean_optimized"] += 1
                return optimized

        # Apply more complex algebraic optimizations
        algebraic_result = self._apply_complex_algebraic_optimizations(inst)
        if algebraic_result and algebraic_result != inst:
            return algebraic_result

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
                # Check for negation of negation: -(-x) -> x
                if isinstance(inst.operand, Temp):
                    defining_inst = self.def_map.get(inst.operand)
                    if defining_inst and isinstance(defining_inst, UnaryOp) and defining_inst.op == "-":
                        # Found double negation
                        return Copy(inst.dest, defining_inst.operand)
            elif operand_type == MIRType.FLOAT:
                # Float negation optimizations
                # Check for negation of negation: -(-x) -> x
                if isinstance(inst.operand, Temp):
                    defining_inst = self.def_map.get(inst.operand)
                    if defining_inst and isinstance(defining_inst, UnaryOp) and defining_inst.op == "-":
                        # Found double negation
                        return Copy(inst.dest, defining_inst.operand)
        elif inst.op == "not":
            # Boolean NOT optimizations
            # Check for double negation: not(not(x)) -> x
            if isinstance(inst.operand, Temp) or isinstance(inst.operand, Variable):
                # Look for the instruction that defines this operand
                defining_inst = self.def_map.get(inst.operand)
                if defining_inst and isinstance(defining_inst, UnaryOp) and defining_inst.op == "not":
                    # Found double negation: not(not(x)) -> x
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, defining_inst.operand)

            # Check for NOT of comparison: not(x == y) -> x != y
            if isinstance(inst.operand, Temp):
                defining_inst = self.def_map.get(inst.operand)
                if defining_inst and isinstance(defining_inst, BinaryOp):
                    # Invert comparison operators
                    inverted_ops = {
                        "==": "!=",
                        "!=": "==",
                        "<": ">=",
                        "<=": ">",
                        ">": "<=",
                        ">=": "<",
                    }
                    if defining_inst.op in inverted_ops:
                        # not(x op y) -> x inverted_op y
                        self.stats["boolean_optimized"] += 1
                        return BinaryOp(
                            inst.dest, inverted_ops[defining_inst.op], defining_inst.left, defining_inst.right
                        )
        elif inst.op == "abs":
            # Absolute value optimizations
            if operand_type == MIRType.INT or operand_type == MIRType.FLOAT:
                # abs(constant) can be folded
                if isinstance(inst.operand, Constant):
                    result = abs(inst.operand.value)
                    return LoadConst(inst.dest, Constant(result, operand_type))

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

    def _optimize_string_binary_op(self, inst: BinaryOp) -> MIRInstruction:
        """Apply string-specific optimizations.

        Args:
            inst: The binary operation involving strings.

        Returns:
            Optimized instruction.
        """
        # String concatenation optimizations
        if inst.op == "+":
            # Empty string concatenation
            if isinstance(inst.left, Constant) and inst.left.value == "":
                # "" + x -> x
                return Copy(inst.dest, inst.right)
            elif isinstance(inst.right, Constant) and inst.right.value == "":
                # x + "" -> x
                return Copy(inst.dest, inst.left)

            # Constant string concatenation is handled by constant folding

        # String comparison optimizations
        elif inst.op == "==":
            # Comparing with empty string
            if isinstance(inst.right, Constant) and inst.right.value == "":
                # TODO: x == "" can be optimized to checking length
                #  This would need a Length instruction, so we leave it for now
                pass

            # Same string comparison
            if inst.left == inst.right:
                # x == x -> True
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL))

        elif inst.op == "!=":
            # Same string comparison
            if inst.left == inst.right:
                # x != x -> False
                return LoadConst(inst.dest, Constant(False, MIRType.BOOL))

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

        # Optimize comparisons with boolean constants
        if left_type == MIRType.BOOL or right_type == MIRType.BOOL:
            if inst.op == "==":
                # x == true -> x
                if isinstance(inst.right, Constant) and inst.right.value is True:
                    return Copy(inst.dest, inst.left)
                # x == false -> not x
                elif isinstance(inst.right, Constant) and inst.right.value is False:
                    return UnaryOp(inst.dest, "not", inst.left)
                # true == x -> x
                elif isinstance(inst.left, Constant) and inst.left.value is True:
                    return Copy(inst.dest, inst.right)
                # false == x -> not x
                elif isinstance(inst.left, Constant) and inst.left.value is False:
                    return UnaryOp(inst.dest, "not", inst.right)
            elif inst.op == "!=":
                # x != true -> not x
                if isinstance(inst.right, Constant) and inst.right.value is True:
                    return UnaryOp(inst.dest, "not", inst.left)
                # x != false -> x
                elif isinstance(inst.right, Constant) and inst.right.value is False:
                    return Copy(inst.dest, inst.left)
                # true != x -> not x
                elif isinstance(inst.left, Constant) and inst.left.value is True:
                    return UnaryOp(inst.dest, "not", inst.right)
                # false != x -> x
                elif isinstance(inst.left, Constant) and inst.left.value is False:
                    return Copy(inst.dest, inst.right)

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

    def _get_analysis_results(self, function: MIRFunction) -> None:
        """Get analysis results from the pass manager.

        Args:
            function: The function being optimized.
        """
        # Try to get use-def chains from pass manager
        if hasattr(function, "_pass_results"):
            results = getattr(function, "_pass_results", {})
            if "use-def-chains" in results:
                self.use_def_chains = results["use-def-chains"]
            if "dominance" in results:
                self.dominance_info = results["dominance"]

        # Fall back to running analyses if not available
        if self.use_def_chains is None:
            analysis = UseDefChainsAnalysis()
            self.use_def_chains = analysis.run_on_function(function)

        if self.dominance_info is None:
            dom_analysis = DominanceAnalysis()
            self.dominance_info = dom_analysis.run_on_function(function)

    def _initialize_value_ranges(self, function: MIRFunction) -> None:
        """Initialize value range tracking for integer variables.

        Args:
            function: The function to analyze.
        """
        self.value_ranges.clear()

        # Initialize ranges for parameters and locals
        for param in function.params:
            if param.type == MIRType.INT:
                # Default range for integers (unbounded)
                self.value_ranges[param] = (None, None)

        for local in function.locals.values():
            if local.type == MIRType.INT:
                self.value_ranges[local] = (None, None)

    def _propagate_types_across_blocks(self, function: MIRFunction) -> bool:
        """Propagate type information across basic blocks.

        Uses dominance information to safely propagate types.

        Args:
            function: The function to optimize.

        Returns:
            True if any types were refined.
        """
        if self.dominance_info is None:
            return False

        modified = False

        # Track type refinements from conditional branches
        type_refinements: dict[BasicBlock, dict[MIRValue, MIRType]] = {}

        for block in function.cfg.blocks.values():
            # Check for type checks in conditional jumps
            terminator = block.get_terminator()
            if terminator and isinstance(terminator, ConditionalJump):
                # Look for patterns like: if (typeof x == "int")
                cond_val = terminator.condition

                # If condition comes from a comparison, analyze it
                if isinstance(cond_val, Temp) and self.use_def_chains:
                    defining_inst = self.use_def_chains.get_definition(cond_val)
                    if isinstance(defining_inst, BinaryOp) and defining_inst.op == "==":
                        # Check for type check patterns
                        refined_type = self._extract_type_check(defining_inst)
                        if refined_type:
                            var, type_val = refined_type
                            # Record refinement for true branch
                            if terminator.true_label:
                                # Find the actual block for the label
                                true_block = function.cfg.get_block(terminator.true_label)
                                if true_block and true_block not in type_refinements:
                                    type_refinements[true_block] = {}
                                if true_block:
                                    type_refinements[true_block][var] = type_val
                                    self.stats["cross_block_optimized"] += 1
                                    modified = True

        # Apply type refinements to dominated blocks
        for refined_block, refinements in type_refinements.items():
            # Get dominated blocks if dominance info supports it
            if hasattr(self.dominance_info, "get_dominated_blocks"):
                for _dominated in self.dominance_info.get_dominated_blocks(refined_block):
                    for ref_var, ref_type in refinements.items():
                        if isinstance(ref_var, Variable) and ref_var.name in self.type_info:
                            # Refine type for this block
                            self.type_info[ref_var.name] = ref_type
            else:
                # Fall back to just applying to the target block
                for ref_var, ref_type in refinements.items():
                    if isinstance(ref_var, Variable) and ref_var.name in self.type_info:
                        self.type_info[ref_var.name] = ref_type

        return modified

    def _optimize_across_blocks(self, function: MIRFunction) -> bool:
        """Perform optimizations that span multiple blocks.

        Args:
            function: The function to optimize.

        Returns:
            True if modifications were made.
        """
        modified = False

        # Look for common patterns across blocks
        if self.use_def_chains:
            # Optimize min/max patterns
            if self._optimize_min_max_patterns(function):
                modified = True

            # Optimize loop patterns
            if self._optimize_loop_patterns(function):
                modified = True

        return modified

    def _extract_type_check(self, inst: BinaryOp) -> tuple[MIRValue, MIRType] | None:
        """Extract type check information from a comparison.

        Args:
            inst: The comparison instruction.

        Returns:
            Tuple of (variable, type) if this is a type check, None otherwise.
        """
        # Pattern: typeof(x) == "int"
        # This would need runtime type checking instructions, so we skip for now
        # TODO: Implement when we have type checking instructions
        return None

    def _optimize_min_max_patterns(self, function: MIRFunction) -> bool:
        """Optimize min/max patterns to use specialized instructions.

        Args:
            function: The function to optimize.

        Returns:
            True if patterns were found and optimized.
        """
        modified = False

        # Pattern: x > y ? x : y  ->  max(x, y)
        # Pattern: x < y ? x : y  ->  min(x, y)
        # This requires conditional move or select instructions
        # TODO: Implement when we have select/conditional move instructions

        return modified

    def _optimize_loop_patterns(self, function: MIRFunction) -> bool:
        """Optimize common loop patterns.

        Args:
            function: The function to optimize.

        Returns:
            True if loop patterns were optimized.
        """
        modified = False

        # Detect and optimize loop induction variables
        # TODO: Implement loop analysis first

        return modified

    def _detect_advanced_patterns(self, inst: MIRInstruction, function: MIRFunction) -> MIRInstruction | None:
        """Detect and optimize advanced patterns.

        Args:
            inst: The instruction to analyze.
            function: The containing function.

        Returns:
            Optimized instruction or None if no pattern matched.
        """
        if not self.use_def_chains:
            return None

        # Pattern: Bit counting operations
        if isinstance(inst, BinaryOp):
            # Pattern: x & (x - 1) - check if power of 2
            if inst.op == "&":
                if isinstance(inst.right, Temp):
                    right_def = self.use_def_chains.get_definition(inst.right)
                    if isinstance(right_def, BinaryOp) and right_def.op == "-":
                        if right_def.left == inst.left and isinstance(right_def.right, Constant):
                            if right_def.right.value == 1:
                                # This is the x & (x - 1) pattern
                                # Used to clear the lowest set bit
                                self.stats["patterns_matched"] += 1
                                # Could optimize to a specialized instruction
                                return inst

        # Pattern: Absolute value
        # x < 0 ? -x : x  ->  abs(x)
        # This requires conditional move, skip for now

        # Pattern: Saturating arithmetic
        # min(max(x + y, MIN), MAX)  ->  saturating_add(x, y)
        # Requires min/max support first

        return None

    def _update_value_range(self, value: MIRValue, min_val: int | float | None, max_val: int | float | None) -> None:
        """Update the value range for a value.

        Args:
            value: The value to update.
            min_val: Minimum value or None for unbounded.
            max_val: Maximum value or None for unbounded.
        """
        if value in self.value_ranges:
            old_min, old_max = self.value_ranges[value]
            # Tighten the range
            if min_val is not None and (old_min is None or min_val > old_min):
                old_min = min_val
            if max_val is not None and (old_max is None or max_val < old_max):
                old_max = max_val
            self.value_ranges[value] = (old_min, old_max)
        else:
            self.value_ranges[value] = (min_val, max_val)

    def _update_range_from_operation(self, original: BinaryOp, optimized: MIRInstruction) -> None:
        """Update value ranges based on an optimized operation.

        Args:
            original: The original binary operation.
            optimized: The optimized instruction.
        """
        # If we optimized to a constant, update the range
        if isinstance(optimized, LoadConst) and optimized.dest in self.value_ranges:
            if isinstance(optimized.constant.value, int):
                val = optimized.constant.value
                self.value_ranges[optimized.dest] = (val, val)
        # If we optimized to a copy, propagate range
        elif isinstance(optimized, Copy):
            if optimized.source in self.value_ranges:
                self.value_ranges[optimized.dest] = self.value_ranges[optimized.source]

    def _apply_complex_algebraic_optimizations(self, inst: BinaryOp) -> MIRInstruction | None:
        """Apply more complex algebraic optimizations.

        Args:
            inst: The binary operation.

        Returns:
            Optimized instruction or None.
        """
        # Distributive law: (a + b) * c -> a*c + b*c (when beneficial)
        if inst.op == "*" and self.use_def_chains:
            # Check if left operand is an addition
            if isinstance(inst.left, Temp):
                left_def = self.use_def_chains.get_definition(inst.left)
                if isinstance(left_def, BinaryOp) and left_def.op == "+":
                    # Check if distribution would enable constant folding
                    if isinstance(inst.right, Constant):
                        if isinstance(left_def.left, Constant) or isinstance(left_def.right, Constant):
                            # Would enable partial constant folding
                            # TODO: Actually implement the distribution
                            self.stats["patterns_matched"] += 1

        # Associativity: (a + b) + c -> a + (b + c) if b and c are constants
        if inst.op in ["+", "*"] and self.use_def_chains:
            if isinstance(inst.left, Temp) and isinstance(inst.right, Constant):
                left_def = self.use_def_chains.get_definition(inst.left)
                if isinstance(left_def, BinaryOp) and left_def.op == inst.op:
                    if isinstance(left_def.right, Constant):
                        # Can fold the two constants together
                        # TODO: Actually implement the reassociation
                        self.stats["patterns_matched"] += 1

        # DeMorgan's laws: not(a and b) -> (not a) or (not b)
        # This is handled in unary op optimization

        # Power optimizations
        if inst.op == "**":
            if isinstance(inst.right, Constant):
                exp = inst.right.value
                if exp == 2:
                    # x**2 -> x * x
                    return BinaryOp(inst.dest, "*", inst.left, inst.left)
                elif exp == 0.5:
                    # x**0.5 -> sqrt(x)
                    # Would need sqrt instruction
                    pass
                elif exp == 0:
                    # x**0 -> 1
                    result_type = self._get_value_type(inst.left)
                    if result_type == MIRType.INT:
                        return LoadConst(inst.dest, Constant(1, MIRType.INT))
                    else:
                        return LoadConst(inst.dest, Constant(1.0, MIRType.FLOAT))
                elif exp == 1:
                    # x**1 -> x
                    return Copy(inst.dest, inst.left)

        return None

    def _optimize_with_range_info(self, inst: BinaryOp) -> MIRInstruction | None:
        """Optimize using value range information.

        Args:
            inst: The instruction to optimize.

        Returns:
            Optimized instruction or None.
        """
        # Use range information to optimize comparisons
        if inst.op in ["<", "<=", ">", ">=", "==", "!="]:
            left_range = self.value_ranges.get(inst.left)
            right_range = self.value_ranges.get(inst.right)

            if left_range and right_range:
                left_min, left_max = left_range
                right_min, right_max = right_range

                # Check if comparison result is known from ranges
                if left_max is not None and right_min is not None:
                    if inst.op == "<" and left_max < right_min:
                        # Always true
                        self.stats["range_optimized"] += 1
                        return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
                    elif inst.op == ">=" and left_max < right_min:
                        # Always false
                        self.stats["range_optimized"] += 1
                        return LoadConst(inst.dest, Constant(False, MIRType.BOOL))

                if left_min is not None and right_max is not None:
                    if inst.op == ">" and left_min > right_max:
                        # Always true
                        self.stats["range_optimized"] += 1
                        return LoadConst(inst.dest, Constant(True, MIRType.BOOL))
                    elif inst.op == "<=" and left_min > right_max:
                        # Always false
                        self.stats["range_optimized"] += 1
                        return LoadConst(inst.dest, Constant(False, MIRType.BOOL))

        return None

    def finalize(self) -> None:
        """Finalize and report statistics."""
        if any(self.stats.values()):
            print("Type-specific optimization statistics:")
            for key, value in self.stats.items():
                if value > 0:
                    print(f"  {key}: {value}")
