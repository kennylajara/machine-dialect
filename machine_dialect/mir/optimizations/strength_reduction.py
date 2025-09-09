"""Strength reduction optimization pass.

This module implements strength reduction at the MIR level, replacing
expensive operations with cheaper equivalents.
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
from machine_dialect.mir.mir_values import Constant, MIRValue
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class StrengthReduction(OptimizationPass):
    """Strength reduction optimization pass."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="strength-reduction",
            description="Replace expensive operations with cheaper equivalents",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run strength reduction on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        transformer = MIRTransformer(function)

        for block in function.cfg.blocks.values():
            self._reduce_block(block, transformer)

        return transformer.modified

    def _reduce_block(self, block: BasicBlock, transformer: MIRTransformer) -> None:
        """Apply strength reduction to a block.

        Args:
            block: The block to optimize.
            transformer: MIR transformer.
        """
        for inst in list(block.instructions):
            if isinstance(inst, BinaryOp):
                self._reduce_binary_op(inst, block, transformer)
            elif isinstance(inst, UnaryOp):
                self._reduce_unary_op(inst, block, transformer)

    def _reduce_binary_op(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Apply strength reduction to a binary operation.

        Args:
            inst: Binary operation instruction.
            block: Containing block.
            transformer: MIR transformer.
        """
        # Check for multiplication by power of 2
        if inst.op == "*":
            # Check for x * 1 or 1 * x first (special cases)
            if self._is_one(inst.right) or self._is_one(inst.left):
                # Don't convert to shift, let algebraic simplifications handle it
                pass
            elif self._is_power_of_two_constant(inst.right):
                shift = self._get_power_of_two(inst.right)
                if shift is not None and shift > 0:  # Only optimize for shift > 0
                    # Replace multiplication with left shift
                    shift_const = Constant(shift, MIRType.INT)
                    new_inst = BinaryOp(inst.dest, "<<", inst.left, shift_const, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["multiply_to_shift"] = self.stats.get("multiply_to_shift", 0) + 1
                    return
            elif self._is_power_of_two_constant(inst.left):
                shift = self._get_power_of_two(inst.left)
                if shift is not None and shift > 0:  # Only optimize for shift > 0
                    # Replace multiplication with left shift (commutative)
                    shift_const = Constant(shift, MIRType.INT)
                    new_inst = BinaryOp(inst.dest, "<<", inst.right, shift_const, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["multiply_to_shift"] = self.stats.get("multiply_to_shift", 0) + 1
                    return

        # Check for division by power of 2
        elif inst.op in ["/", "//"]:
            # Check for x / 1 first (special case)
            if self._is_one(inst.right):
                # Don't convert to shift, let algebraic simplifications handle it
                pass
            elif self._is_power_of_two_constant(inst.right):
                shift = self._get_power_of_two(inst.right)
                if shift is not None and shift > 0:  # Only optimize for shift > 0
                    # Replace division with right shift (for integers)
                    shift_const = Constant(shift, MIRType.INT)
                    new_inst = BinaryOp(inst.dest, ">>", inst.left, shift_const, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["divide_to_shift"] = self.stats.get("divide_to_shift", 0) + 1
                    return

        # Check for modulo by power of 2
        elif inst.op == "%":
            if self._is_power_of_two_constant(inst.right):
                power = self._get_constant_value(inst.right)
                if power is not None and power > 0:
                    # Replace modulo with bitwise AND (n % power = n & (power - 1))
                    mask = Constant(power - 1, MIRType.INT)
                    new_inst = BinaryOp(inst.dest, "&", inst.left, mask, inst.source_location)
                    transformer.replace_instruction(block, inst, new_inst)
                    self.stats["modulo_to_and"] = self.stats.get("modulo_to_and", 0) + 1
                    return

        # Algebraic simplifications
        self._apply_algebraic_simplifications(inst, block, transformer)

    def _reduce_unary_op(
        self,
        inst: UnaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Apply strength reduction to a unary operation.

        Args:
            inst: Unary operation instruction.
            block: Containing block.
            transformer: MIR transformer.
        """
        # Double negation elimination
        if inst.op == "-":
            # Check if operand is result of another negation
            # This would require tracking def-use chains
            pass

        # Boolean not simplification
        elif inst.op == "not":
            # Check for not(not(x)) pattern
            pass

    def _apply_algebraic_simplifications(
        self,
        inst: BinaryOp,
        block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Apply algebraic simplifications to binary operations.

        Args:
            inst: Binary operation instruction.
            block: Containing block.
            transformer: MIR transformer.
        """
        new_inst: MIRInstruction
        # Identity operations
        if inst.op == "+":
            # x + 0 = x
            if self._is_zero(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            elif self._is_zero(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

        elif inst.op == "-":
            # x - 0 = x
            if self._is_zero(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x - x = 0
            elif self._values_equal(inst.left, inst.right):
                zero = Constant(0, MIRType.INT)
                new_inst = LoadConst(inst.dest, zero, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

        elif inst.op == "*":
            # x * 0 = 0
            if self._is_zero(inst.right) or self._is_zero(inst.left):
                zero = Constant(0, MIRType.INT)
                new_inst = LoadConst(inst.dest, zero, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x * 1 = x
            elif self._is_one(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            elif self._is_one(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x * -1 = -x
            elif self._is_negative_one(inst.right):
                new_inst = UnaryOp(inst.dest, "-", inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            elif self._is_negative_one(inst.left):
                new_inst = UnaryOp(inst.dest, "-", inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

        elif inst.op in ["/", "//"]:
            # x / 1 = x
            if self._is_one(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x / x = 1 (if x != 0)
            elif self._values_equal(inst.left, inst.right):
                one = Constant(1, MIRType.INT)
                new_inst = LoadConst(inst.dest, one, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

        # Boolean operations
        elif inst.op == "and":
            # x and False = False (check this first as it's stronger)
            if self._is_false(inst.right) or self._is_false(inst.left):
                false = Constant(False, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, false, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x and True = x
            elif self._is_true(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            elif self._is_true(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

        elif inst.op == "or":
            # x or True = True (check this first as it's stronger)
            if self._is_true(inst.right) or self._is_true(inst.left):
                true = Constant(True, MIRType.BOOL)
                new_inst = LoadConst(inst.dest, true, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            # x or False = x
            elif self._is_false(inst.right):
                new_inst = Copy(inst.dest, inst.left, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return
            elif self._is_false(inst.left):
                new_inst = Copy(inst.dest, inst.right, inst.source_location)
                transformer.replace_instruction(block, inst, new_inst)
                self.stats["algebraic_simplified"] = self.stats.get("algebraic_simplified", 0) + 1
                return

    def _is_power_of_two_constant(self, value: MIRValue) -> bool:
        """Check if a value is a constant power of 2.

        Args:
            value: Value to check.

        Returns:
            True if the value is a power of 2 constant.
        """
        if isinstance(value, Constant):
            val = value.value
            if isinstance(val, int) and val > 0:
                # Check if only one bit is set
                return (val & (val - 1)) == 0
        return False

    def _get_power_of_two(self, value: MIRValue) -> int | None:
        """Get the power of 2 exponent.

        Args:
            value: Power of 2 constant.

        Returns:
            The exponent or None.
        """
        if isinstance(value, Constant):
            val = value.value
            if isinstance(val, int) and val > 0 and (val & (val - 1)) == 0:
                # Count trailing zeros to get exponent
                exp = 0
                while val > 1:
                    val >>= 1
                    exp += 1
                return exp
        return None

    def _get_constant_value(self, value: MIRValue) -> int | float | bool | None:
        """Get constant value if it's a constant.

        Args:
            value: MIR value.

        Returns:
            The constant value or None.
        """
        if isinstance(value, Constant):
            val = value.value
            if isinstance(val, int | float | bool):
                return val
        return None

    def _is_zero(self, value: MIRValue) -> bool:
        """Check if value is zero.

        Args:
            value: Value to check.

        Returns:
            True if value is zero.
        """
        val = self._get_constant_value(value)
        return val == 0

    def _is_one(self, value: MIRValue) -> bool:
        """Check if value is one.

        Args:
            value: Value to check.

        Returns:
            True if value is one.
        """
        val = self._get_constant_value(value)
        return val == 1

    def _is_negative_one(self, value: MIRValue) -> bool:
        """Check if value is negative one.

        Args:
            value: Value to check.

        Returns:
            True if value is -1.
        """
        val = self._get_constant_value(value)
        return val == -1

    def _is_true(self, value: MIRValue) -> bool:
        """Check if value is boolean true.

        Args:
            value: Value to check.

        Returns:
            True if value is boolean true.
        """
        val = self._get_constant_value(value)
        return val is True

    def _is_false(self, value: MIRValue) -> bool:
        """Check if value is boolean false.

        Args:
            value: Value to check.

        Returns:
            True if value is boolean false.
        """
        val = self._get_constant_value(value)
        return val is False

    def _values_equal(self, v1: MIRValue, v2: MIRValue) -> bool:
        """Check if two values are equal.

        Args:
            v1: First value.
            v2: Second value.

        Returns:
            True if values are equal.
        """
        # Simple equality check - could be enhanced
        return v1 == v2

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
