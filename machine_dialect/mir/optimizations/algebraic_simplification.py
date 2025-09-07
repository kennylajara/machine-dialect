"""Advanced algebraic simplification optimization pass.

This module implements advanced algebraic simplifications at the MIR level,
applying mathematical identities and algebraic laws to simplify expressions.
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
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class AlgebraicSimplification(OptimizationPass):
    """Advanced algebraic simplification optimization pass."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="algebraic-simplification",
            description="Apply advanced algebraic simplifications and mathematical identities",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run algebraic simplification on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        transformer = MIRTransformer(function)

        for block in function.cfg.blocks.values():
            self._simplify_block(block, transformer)

        return transformer.modified

    def _simplify_block(self, block: BasicBlock, transformer: MIRTransformer) -> None:
        """Apply algebraic simplifications to a block.

        Args:
            block: The block to optimize.
            transformer: MIR transformer.
        """
        for inst in list(block.instructions):
            if isinstance(inst, BinaryOp):
                self._simplify_binary_op(inst, block, transformer)
            elif isinstance(inst, UnaryOp):
                self._simplify_unary_op(inst, block, transformer)

    def _simplify_binary_op(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Apply algebraic simplifications to a binary operation.

        Args:
            inst: Binary operation instruction.
            block: Containing block.
            transformer: MIR transformer.
        """
        # Comparison simplifications
        if inst.op in ["==", "!=", "<", ">", "<=", ">="]:
            if self._simplify_comparison(inst, block, transformer):
                return

        # Bitwise operation simplifications
        if inst.op in ["&", "|", "^", "<<", ">>"]:
            if self._simplify_bitwise(inst, block, transformer):
                return

        # Power operation simplifications
        if inst.op == "**":
            if self._simplify_power(inst, block, transformer):
                return

        # Modulo simplifications
        if inst.op == "%":
            if self._simplify_modulo(inst, block, transformer):
                return

        # Division simplifications
        if inst.op in ["/", "//"]:
            if self._simplify_division(inst, block, transformer):
                return

        # Advanced arithmetic simplifications
        if inst.op in ["+", "-", "*", "/"]:
            if self._simplify_advanced_arithmetic(inst, block, transformer):
                return

        # Complex pattern matching
        if self._simplify_complex_patterns(inst, block, transformer):
            return

    def _simplify_unary_op(
        self,
        inst: UnaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Apply algebraic simplifications to a unary operation.

        Args:
            inst: Unary operation instruction.
            block: Containing block.
            transformer: MIR transformer.
        """
        # Double negation elimination: -(-x) = x
        if inst.op == "-":
            # Check if operand is result of another negation
            # This requires def-use chain analysis
            defining_inst = self._get_defining_instruction(inst.operand, block)
            if isinstance(defining_inst, UnaryOp) and defining_inst.op == "-":
                new_inst = Copy(inst.dest, defining_inst.operand, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["double_negation_eliminated"] = self.stats.get("double_negation_eliminated", 0) + 1
                return

        # Boolean not simplification: not(not(x)) = x
        elif inst.op == "not":
            defining_inst = self._get_defining_instruction(inst.operand, block)
            if isinstance(defining_inst, UnaryOp) and defining_inst.op == "not":
                new_inst = Copy(inst.dest, defining_inst.operand, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["double_not_eliminated"] = self.stats.get("double_not_eliminated", 0) + 1
                return

    def _simplify_comparison(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Simplify comparison operations.

        Args:
            inst: Comparison instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        # x == x → true, x != x → false
        if self._values_equal(inst.left, inst.right):
            if inst.op == "==":
                true_const = Constant(True, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, true_const, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["comparison_simplified"] = self.stats.get("comparison_simplified", 0) + 1
                return True
            elif inst.op == "!=":
                false_const = Constant(False, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, false_const, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["comparison_simplified"] = self.stats.get("comparison_simplified", 0) + 1
                return True
            elif inst.op in ["<", ">"]:
                # x < x → false, x > x → false
                false_const = Constant(False, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, false_const, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["comparison_simplified"] = self.stats.get("comparison_simplified", 0) + 1
                return True
            elif inst.op in ["<=", ">="]:
                # x <= x → true, x >= x → true
                true_const = Constant(True, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, true_const, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["comparison_simplified"] = self.stats.get("comparison_simplified", 0) + 1
                return True

        return False

    def _simplify_bitwise(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Simplify bitwise operations.

        Args:
            inst: Bitwise operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        new_inst: MIRInstruction

        # x & 0 → 0
        if inst.op == "&":
            if self._is_zero(inst.right) or self._is_zero(inst.left):
                zero = Constant(0, MIRType.INT)
                new_inst = LoadConst(inst.dest, zero, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            # x & x → x
            elif self._values_equal(inst.left, inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            # x & ~0 → x (all ones)
            elif self._is_all_ones(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            elif self._is_all_ones(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True

        # x | 0 → x
        elif inst.op == "|":
            if self._is_zero(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            elif self._is_zero(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            # x | x → x
            elif self._values_equal(inst.left, inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            # x | ~0 → ~0 (all ones)
            elif self._is_all_ones(inst.right) or self._is_all_ones(inst.left):
                all_ones = Constant(-1, MIRType.INT)
                new_inst = LoadConst(inst.dest, all_ones, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True

        # x ^ 0 → x
        elif inst.op == "^":
            if self._is_zero(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            elif self._is_zero(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True
            # x ^ x → 0
            elif self._values_equal(inst.left, inst.right):
                zero = Constant(0, MIRType.INT)
                new_inst = LoadConst(inst.dest, zero, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["bitwise_simplified"] = self.stats.get("bitwise_simplified", 0) + 1
                return True

        # x << 0 → x, x >> 0 → x
        elif inst.op in ["<<", ">>"]:
            if self._is_zero(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["shift_simplified"] = self.stats.get("shift_simplified", 0) + 1
                return True

        return False

    def _simplify_power(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Simplify power operations.

        Args:
            inst: Power operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        new_inst: MIRInstruction

        # x ** 0 → 1
        if self._is_zero(inst.right):
            one = Constant(1, MIRType.INT)
            new_inst = LoadConst(inst.dest, one, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["power_simplified"] = self.stats.get("power_simplified", 0) + 1
            return True

        # x ** 1 → x
        elif self._is_one(inst.right):
            new_inst = Copy(inst.dest, inst.left, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["power_simplified"] = self.stats.get("power_simplified", 0) + 1
            return True

        # x ** 2 → x * x (more efficient)
        elif self._is_constant_value(inst.right, 2):
            new_inst = BinaryOp(inst.dest, "*", inst.left, inst.left, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["power_to_multiply"] = self.stats.get("power_to_multiply", 0) + 1
            return True

        # 0 ** x → 0 (for x > 0)
        elif self._is_zero(inst.left):
            zero = Constant(0, MIRType.INT)
            new_inst = LoadConst(inst.dest, zero, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["power_simplified"] = self.stats.get("power_simplified", 0) + 1
            return True

        # 1 ** x → 1
        elif self._is_one(inst.left):
            one = Constant(1, MIRType.INT)
            new_inst = LoadConst(inst.dest, one, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["power_simplified"] = self.stats.get("power_simplified", 0) + 1
            return True

        return False

    def _simplify_modulo(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Simplify modulo operations.

        Args:
            inst: Modulo operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        new_inst: MIRInstruction

        # x % 1 → 0
        if self._is_one(inst.right):
            zero = Constant(0, MIRType.INT)
            new_inst = LoadConst(inst.dest, zero, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["modulo_simplified"] = self.stats.get("modulo_simplified", 0) + 1
            return True

        # x % x → 0 (assuming x != 0)
        elif self._values_equal(inst.left, inst.right):
            zero = Constant(0, MIRType.INT)
            new_inst = LoadConst(inst.dest, zero, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["modulo_simplified"] = self.stats.get("modulo_simplified", 0) + 1
            return True

        # 0 % x → 0
        elif self._is_zero(inst.left):
            zero = Constant(0, MIRType.INT)
            new_inst = LoadConst(inst.dest, zero, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["modulo_simplified"] = self.stats.get("modulo_simplified", 0) + 1
            return True

        return False

    def _simplify_division(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Simplify division operations.

        Args:
            inst: Division operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        new_inst: MIRInstruction

        # x / 1 → x
        if self._is_one(inst.right):
            new_inst = Copy(inst.dest, inst.left, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["division_simplified"] = self.stats.get("division_simplified", 0) + 1
            return True

        # x / x → 1 (assuming x != 0)
        elif self._values_equal(inst.left, inst.right):
            one = Constant(1, inst.dest.type if hasattr(inst.dest, "type") else MIRType.INT)
            new_inst = LoadConst(inst.dest, one, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["division_simplified"] = self.stats.get("division_simplified", 0) + 1
            return True

        # 0 / x → 0 (assuming x != 0)
        elif self._is_zero(inst.left):
            zero = Constant(0, inst.dest.type if hasattr(inst.dest, "type") else MIRType.INT)
            new_inst = LoadConst(inst.dest, zero, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["division_simplified"] = self.stats.get("division_simplified", 0) + 1
            return True

        # x / -1 → -x
        elif self._is_constant_value(inst.right, -1):
            new_inst = UnaryOp(inst.dest, "-", inst.left, inst.source_location)
            transformer.replace_instruction(block, inst, new_inst)
            self.stats["division_simplified"] = self.stats.get("division_simplified", 0) + 1
            return True

        return False

    def _simplify_complex_patterns(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Apply complex pattern matching across instructions.

        Args:
            inst: Binary operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        # Pattern: (a + b) - b → a
        if inst.op == "-":
            left_def = self._get_defining_instruction(inst.left, block)
            if isinstance(left_def, BinaryOp) and left_def.op == "+":
                if self._values_equal(left_def.right, inst.right):
                    new_inst = Copy(inst.dest, left_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True
                elif self._values_equal(left_def.left, inst.right):
                    new_inst = Copy(inst.dest, left_def.right, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

            # Pattern: (a - b) - c → a - (b + c) when b and c are constants
            if isinstance(left_def, BinaryOp) and left_def.op == "-":
                if isinstance(left_def.right, Constant) and isinstance(inst.right, Constant):
                    new_const_val = left_def.right.value + inst.right.value
                    new_const = Constant(new_const_val, inst.right.type)
                    binary_inst: MIRInstruction = BinaryOp(
                        inst.dest, "-", left_def.left, new_const, inst.source_location
                    )
                    transformer.replace_instruction(block, inst, binary_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

        # Pattern: (a - b) + b → a
        elif inst.op == "+":
            left_def = self._get_defining_instruction(inst.left, block)
            if isinstance(left_def, BinaryOp) and left_def.op == "-":
                if self._values_equal(left_def.right, inst.right):
                    new_inst = Copy(inst.dest, left_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

            # Check right side: b + (a - b) → a
            right_def = self._get_defining_instruction(inst.right, block)
            if isinstance(right_def, BinaryOp) and right_def.op == "-":
                if self._values_equal(right_def.right, inst.left):
                    copy_inst: MIRInstruction = Copy(inst.dest, right_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, copy_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

        # Pattern: (a * b) / b → a
        elif inst.op in ["/", "//"]:
            left_def = self._get_defining_instruction(inst.left, block)
            if isinstance(left_def, BinaryOp) and left_def.op == "*":
                if self._values_equal(left_def.right, inst.right):
                    new_inst = Copy(inst.dest, left_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True
                elif self._values_equal(left_def.left, inst.right):
                    new_inst = Copy(inst.dest, left_def.right, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

        # Pattern: (a / b) * b → a
        elif inst.op == "*":
            left_def = self._get_defining_instruction(inst.left, block)
            if isinstance(left_def, BinaryOp) and left_def.op in ["/", "//"]:
                if self._values_equal(left_def.right, inst.right):
                    new_inst = Copy(inst.dest, left_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

            # Check right side: b * (a / b) → a
            right_def = self._get_defining_instruction(inst.right, block)
            if isinstance(right_def, BinaryOp) and right_def.op in ["/", "//"]:
                if self._values_equal(right_def.right, inst.left):
                    new_inst = Copy(inst.dest, right_def.left, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
                    return True

        # Pattern: 0 - x → -x
        if inst.op == "-" and self._is_zero(inst.left):
            unary_inst: MIRInstruction = UnaryOp(inst.dest, "-", inst.right, inst.source_location)
            transformer.replace_instruction(block, inst, unary_inst)
            self.stats["complex_pattern_matched"] = self.stats.get("complex_pattern_matched", 0) + 1
            return True

        return False

    def _simplify_advanced_arithmetic(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Apply advanced arithmetic simplifications.

        Args:
            inst: Arithmetic operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if simplified.
        """
        # Check for associativity opportunities
        # (a + b) + c where b and c are constants → a + (b + c)
        if inst.op in ["+", "*"]:
            left_def = self._get_defining_instruction(inst.left, block)
            if (
                isinstance(left_def, BinaryOp)
                and left_def.op == inst.op
                and isinstance(inst.right, Constant)
                and isinstance(left_def.right, Constant)
            ):
                # Compute (b op c)
                if inst.op == "+":
                    new_const_val = left_def.right.value + inst.right.value
                else:  # "*"
                    new_const_val = left_def.right.value * inst.right.value

                new_const = Constant(new_const_val, inst.right.type)
                new_inst = BinaryOp(inst.dest, inst.op, left_def.left, new_const, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["associativity_applied"] = self.stats.get("associativity_applied", 0) + 1
                return True

            # Also check right side for commutativity: c + (a + b) → (c + b) + a when b and c are constants
            right_def = self._get_defining_instruction(inst.right, block)
            if (
                isinstance(right_def, BinaryOp)
                and right_def.op == inst.op
                and isinstance(inst.left, Constant)
                and isinstance(right_def.right, Constant)
            ):
                # Compute (c op b)
                if inst.op == "+":
                    new_const_val = inst.left.value + right_def.right.value
                else:  # "*"
                    new_const_val = inst.left.value * right_def.right.value

                new_const = Constant(new_const_val, inst.left.type)
                new_inst = BinaryOp(inst.dest, inst.op, new_const, right_def.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["associativity_applied"] = self.stats.get("associativity_applied", 0) + 1
                return True

        # Check for subtraction associativity: (a - b) - c → a - (b + c) when b and c are constants
        # This is already handled in _simplify_complex_patterns

        # Apply De Morgan's laws for bitwise operations
        if self._apply_demorgan_laws(inst, block, transformer):
            return True

        return False

    def _apply_demorgan_laws(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> bool:
        """Apply De Morgan's laws for bitwise operations.

        Args:
            inst: Binary operation instruction.
            block: Containing block.
            transformer: MIR transformer.

        Returns:
            True if transformed.
        """
        # De Morgan's Law: ~(a & b) = ~a | ~b
        # De Morgan's Law: ~(a | b) = ~a & ~b
        # We look for patterns where the result of AND/OR is negated

        # For now, we'll skip this as it requires tracking how the result is used
        # This would be better implemented with a pattern matching framework

        return False

    def _get_defining_instruction(
        self,
        value: MIRValue,
        block: BasicBlock,
    ) -> MIRInstruction | None:
        """Get the instruction that defines a value.

        Args:
            value: The value to find definition for.
            block: The block to search in.

        Returns:
            Defining instruction or None.
        """
        if not isinstance(value, Temp):
            return None

        # Search backward in the block for the defining instruction
        for inst in reversed(block.instructions):
            if hasattr(inst, "dest") and inst.dest == value:
                return inst

        return None

    def _is_zero(self, value: MIRValue) -> bool:
        """Check if value is zero.

        Args:
            value: Value to check.

        Returns:
            True if value is zero.
        """
        return isinstance(value, Constant) and value.value == 0

    def _is_one(self, value: MIRValue) -> bool:
        """Check if value is one.

        Args:
            value: Value to check.

        Returns:
            True if value is one.
        """
        return isinstance(value, Constant) and value.value == 1

    def _is_all_ones(self, value: MIRValue) -> bool:
        """Check if value is all ones (-1 for signed integers).

        Args:
            value: Value to check.

        Returns:
            True if value is all ones.
        """
        return isinstance(value, Constant) and value.value == -1

    def _is_constant_value(self, value: MIRValue, expected: int | float) -> bool:
        """Check if value is a specific constant.

        Args:
            value: Value to check.
            expected: Expected constant value.

        Returns:
            True if value matches expected.
        """
        return isinstance(value, Constant) and value.value == expected

    def _values_equal(self, v1: MIRValue, v2: MIRValue) -> bool:
        """Check if two values are equal.

        Args:
            v1: First value.
            v2: Second value.

        Returns:
            True if values are equal.
        """
        # Simple equality check
        return v1 == v2

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
