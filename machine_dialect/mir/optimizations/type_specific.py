"""Type-specific MIR optimization pass.

This module implements type-aware optimizations that leverage type information
from variable definitions to generate more efficient MIR code.
"""

from machine_dialect.mir.analyses.dominance_analysis import DominanceAnalysis
from machine_dialect.mir.analyses.use_def_chains import UseDefChains, UseDefChainsAnalysis
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.dataflow import DataFlowAnalysis, Range, TypeContext
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    LoadConst,
    MaxOp,
    MinOp,
    MIRInstruction,
    SaturatingAddOp,
    ShiftOp,
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


class TypeInference(DataFlowAnalysis[dict[MIRValue, TypeContext]]):
    """Type inference using dataflow analysis framework."""

    def initial_state(self) -> dict[MIRValue, TypeContext]:
        """Get initial type state."""
        return {}

    def transfer(self, inst: MIRInstruction, state: dict[MIRValue, TypeContext]) -> dict[MIRValue, TypeContext]:
        """Transfer function for type inference.

        Args:
            inst: The instruction to process.
            state: Input type state.

        Returns:
            Output type state after processing the instruction.
        """
        new_state = state.copy()

        # LoadConst establishes exact type and range
        if isinstance(inst, LoadConst):
            # Ensure we have a MIRType, not MIRUnionType
            base_type = inst.constant.type if not isinstance(inst.constant.type, MIRUnionType) else MIRType.UNKNOWN
            ctx = TypeContext(base_type=base_type, nullable=False, provenance="constant")
            # For numeric constants, set exact range
            if isinstance(inst.constant.value, int | float):
                ctx.range = Range(inst.constant.value, inst.constant.value)
            new_state[inst.dest] = ctx

        # BinaryOp propagates type information
        elif isinstance(inst, BinaryOp):
            left_ctx = state.get(inst.left)
            right_ctx = state.get(inst.right)

            # Determine result type
            if inst.op in ["==", "!=", "<", "<=", ">", ">=", "and", "or"]:
                result_type = MIRType.BOOL
                ctx = TypeContext(base_type=result_type, nullable=False)
            elif left_ctx and right_ctx:
                # Numeric operations
                if left_ctx.base_type == MIRType.FLOAT or right_ctx.base_type == MIRType.FLOAT:
                    result_type = MIRType.FLOAT
                else:
                    result_type = left_ctx.base_type
                ctx = TypeContext(base_type=result_type)

                # Compute range for arithmetic operations
                if inst.op == "+" and left_ctx.range and right_ctx.range:
                    if left_ctx.range.min is not None and right_ctx.range.min is not None:
                        new_min = left_ctx.range.min + right_ctx.range.min
                    else:
                        new_min = None
                    if left_ctx.range.max is not None and right_ctx.range.max is not None:
                        new_max = left_ctx.range.max + right_ctx.range.max
                    else:
                        new_max = None
                    ctx.range = Range(new_min, new_max)
                elif inst.op == "-" and left_ctx.range and right_ctx.range:
                    if left_ctx.range.min is not None and right_ctx.range.max is not None:
                        new_min = left_ctx.range.min - right_ctx.range.max
                    else:
                        new_min = None
                    if left_ctx.range.max is not None and right_ctx.range.min is not None:
                        new_max = left_ctx.range.max - right_ctx.range.min
                    else:
                        new_max = None
                    ctx.range = Range(new_min, new_max)
            else:
                ctx = TypeContext(base_type=MIRType.UNKNOWN)

            new_state[inst.dest] = ctx

        # Copy propagates type information
        elif isinstance(inst, Copy):
            if inst.source in state:
                new_state[inst.dest] = state[inst.source]

        # UnaryOp
        elif isinstance(inst, UnaryOp):
            operand_ctx = state.get(inst.operand)
            if operand_ctx:
                if inst.op == "not":
                    ctx = TypeContext(base_type=MIRType.BOOL, nullable=False)
                else:
                    ctx = TypeContext(base_type=operand_ctx.base_type)
                    # Negation flips range
                    if inst.op == "-" and operand_ctx.range:
                        ctx.range = Range(
                            -operand_ctx.range.max if operand_ctx.range.max is not None else None,
                            -operand_ctx.range.min if operand_ctx.range.min is not None else None,
                        )
                new_state[inst.dest] = ctx

        # New specialized instructions
        elif isinstance(inst, MinOp):
            left_ctx = state.get(inst.left)
            right_ctx = state.get(inst.right)
            if left_ctx and right_ctx:
                ctx = TypeContext(base_type=left_ctx.base_type)
                # Result range is constrained by both inputs
                if left_ctx.range and right_ctx.range:
                    new_min = (
                        min(left_ctx.range.min, right_ctx.range.min)
                        if left_ctx.range.min is not None and right_ctx.range.min is not None
                        else None
                    )
                    new_max = (
                        min(left_ctx.range.max, right_ctx.range.max)
                        if left_ctx.range.max is not None and right_ctx.range.max is not None
                        else None
                    )
                    ctx.range = Range(new_min, new_max)
                new_state[inst.dest] = ctx

        elif isinstance(inst, MaxOp):
            left_ctx = state.get(inst.left)
            right_ctx = state.get(inst.right)
            if left_ctx and right_ctx:
                ctx = TypeContext(base_type=left_ctx.base_type)
                # Result range is constrained by both inputs
                if left_ctx.range and right_ctx.range:
                    new_min = (
                        max(left_ctx.range.min, right_ctx.range.min)
                        if left_ctx.range.min is not None and right_ctx.range.min is not None
                        else None
                    )
                    new_max = (
                        max(left_ctx.range.max, right_ctx.range.max)
                        if left_ctx.range.max is not None and right_ctx.range.max is not None
                        else None
                    )
                    ctx.range = Range(new_min, new_max)
                new_state[inst.dest] = ctx

        return new_state

    def meet(self, states: list[dict[MIRValue, TypeContext]]) -> dict[MIRValue, TypeContext]:
        """Meet operation for type states.

        Args:
            states: Type states to join.

        Returns:
            The joined type state.
        """
        if not states:
            return {}

        result = states[0].copy()
        for state in states[1:]:
            for value, ctx in state.items():
                if value in result:
                    # Merge type contexts - union of ranges
                    existing = result[value]
                    if existing.range and ctx.range:
                        result[value].range = existing.range.union(ctx.range)
                else:
                    result[value] = ctx

        return result


class TypeSpecificOptimization(FunctionPass):
    """Type-specific optimization pass using modern dataflow framework.

    This pass performs optimizations based on known type information:
    - Type-aware constant folding with rich metadata
    - Range-based optimizations
    - Pattern-based transformations
    - Cross-block type propagation
    - Advanced algebraic simplifications
    """

    def __init__(self) -> None:
        """Initialize the type-specific optimization pass."""
        super().__init__()
        self.type_analysis = TypeInference()
        self.type_contexts: dict[BasicBlock, dict[MIRValue, TypeContext]] = {}
        self.use_def_chains: UseDefChains | None = None
        self.dominance_info: DominanceInfo | None = None
        self.stats = {
            "constant_folded": 0,
            "range_optimized": 0,
            "patterns_matched": 0,
            "cross_block_optimized": 0,
            "specialized_instructions": 0,
            "strength_reduced": 0,
            "dead_code_eliminated": 0,
            "boolean_optimized": 0,
            "type_checks_eliminated": 0,
            "integer_optimized": 0,
            "float_optimized": 0,
            "string_optimized": 0,
            "instructions_removed": 0,
        }

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="type-specific-optimization",
            description="Optimize MIR using type information and dataflow analysis",
            pass_type=PassType.OPTIMIZATION,
            requires=["use-def-chains", "dominance"],
            preserves=PreservationLevel.CFG,
        )

    def finalize(self) -> None:
        """Finalize the pass after running."""
        pass

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run type-specific optimizations on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        modified = False

        # Run type inference using dataflow framework
        block_type_contexts = self.type_analysis.analyze(function)
        # Store for cross-block access
        self.type_contexts = block_type_contexts

        # Get use-def chains and dominance info
        use_def_analysis = UseDefChainsAnalysis()
        self.use_def_chains = use_def_analysis.run_on_function(function)

        dom_analysis = DominanceAnalysis()
        self.dominance_info = dom_analysis.run_on_function(function)

        # Optimize each block
        for block in function.cfg.blocks.values():
            block_modified = self._optimize_block(block)
            if block_modified:
                modified = True

        # Cross-block optimizations
        if self._optimize_cross_block(function):
            modified = True

        return modified

    def _optimize_block(self, block: BasicBlock) -> bool:
        """Optimize a basic block.

        Args:
            block: The block to optimize.

        Returns:
            True if the block was modified.
        """
        modified = False
        new_instructions = []

        # Get block-specific type contexts
        block_types = self.type_contexts.get(block, {})

        for inst in block.instructions:
            optimized = self._optimize_instruction(inst, block_types)

            if optimized != inst:
                modified = True
                if optimized is not None:
                    # Update metadata on optimized instruction
                    if hasattr(inst, "dest") and inst.dest in block_types:
                        ctx = block_types[inst.dest]
                        optimized.result_type = ctx.base_type
                        if hasattr(inst.dest, "known_range"):
                            inst.dest.known_range = ctx.range
                    new_instructions.append(optimized)
                else:
                    self.stats["dead_code_eliminated"] += 1
            else:
                new_instructions.append(inst)

        if modified:
            block.instructions = new_instructions

        return modified

    def _optimize_instruction(
        self, inst: MIRInstruction, type_contexts: dict[MIRValue, TypeContext]
    ) -> MIRInstruction | None:
        """Optimize a single instruction.

        Args:
            inst: The instruction to optimize.
            type_contexts: Type contexts for values.

        Returns:
            Optimized instruction or None if eliminated.
        """
        # Constant folding with type awareness
        if isinstance(inst, BinaryOp):
            # Boolean short-circuit optimizations
            if inst.op == "and":
                # False and x => False
                if isinstance(inst.left, Constant) and inst.left.value is False:
                    self.stats["boolean_optimized"] += 1
                    return LoadConst(inst.dest, Constant(False, MIRType.BOOL), inst.source_location)
                # x and False => False
                if isinstance(inst.right, Constant) and inst.right.value is False:
                    self.stats["boolean_optimized"] += 1
                    return LoadConst(inst.dest, Constant(False, MIRType.BOOL), inst.source_location)
                # True and x => x
                if isinstance(inst.left, Constant) and inst.left.value is True:
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, inst.right, inst.source_location)
                # x and True => x
                if isinstance(inst.right, Constant) and inst.right.value is True:
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, inst.left, inst.source_location)
                # x and x => x (idempotent)
                if inst.left == inst.right:
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, inst.left, inst.source_location)
            elif inst.op == "or":
                # True or x => True
                if isinstance(inst.left, Constant) and inst.left.value is True:
                    self.stats["boolean_optimized"] += 1
                    return LoadConst(inst.dest, Constant(True, MIRType.BOOL), inst.source_location)
                # x or True => True
                if isinstance(inst.right, Constant) and inst.right.value is True:
                    self.stats["boolean_optimized"] += 1
                    return LoadConst(inst.dest, Constant(True, MIRType.BOOL), inst.source_location)
                # False or x => x
                if isinstance(inst.left, Constant) and inst.left.value is False:
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, inst.right, inst.source_location)
                # x or False => x
                if isinstance(inst.right, Constant) and inst.right.value is False:
                    self.stats["boolean_optimized"] += 1
                    return Copy(inst.dest, inst.left, inst.source_location)

            # Try constant folding
            if isinstance(inst.left, Constant) and isinstance(inst.right, Constant):
                folded = self._fold_binary_constant(inst.op, inst.left, inst.right)
                if folded:
                    self.stats["constant_folded"] += 1
                    return LoadConst(inst.dest, folded, inst.source_location)

            # Pattern-based optimizations
            pattern_opt = self._optimize_patterns(inst, type_contexts)
            if pattern_opt and pattern_opt != inst:
                self.stats["patterns_matched"] += 1
                return pattern_opt

            # Range-based optimizations
            range_opt = self._optimize_with_ranges(inst, type_contexts)
            if range_opt and range_opt != inst:
                self.stats["range_optimized"] += 1
                return range_opt

            # Strength reduction
            strength_opt = self._apply_strength_reduction(inst)
            if strength_opt and strength_opt != inst:
                self.stats["strength_reduced"] += 1
                # Check if this is also an integer optimization
                if isinstance(inst.left, Constant | Variable | Temp) or isinstance(
                    inst.right, Constant | Variable | Temp
                ):
                    left_ctx = type_contexts.get(inst.left)
                    right_ctx = type_contexts.get(inst.right)
                    if (left_ctx and left_ctx.base_type == MIRType.INT) or (
                        right_ctx and right_ctx.base_type == MIRType.INT
                    ):
                        self.stats["integer_optimized"] += 1
                    elif isinstance(inst.left, Constant) and inst.left.type == MIRType.INT:
                        self.stats["integer_optimized"] += 1
                    elif isinstance(inst.right, Constant) and inst.right.type == MIRType.INT:
                        self.stats["integer_optimized"] += 1
                return strength_opt

            # Self-equality optimization (x == x => True)
            if inst.op == "==" and inst.left == inst.right:
                self.stats["boolean_optimized"] += 1
                return LoadConst(inst.dest, Constant(True, MIRType.BOOL), inst.source_location)

        elif isinstance(inst, UnaryOp):
            # Double negation elimination
            if inst.op == "not":
                # Check if operand is result of another not operation
                if self.use_def_chains:
                    def_inst = self.use_def_chains.get_definition(inst.operand)
                    if isinstance(def_inst, UnaryOp) and def_inst.op == "not":
                        # not(not(x)) -> x
                        self.stats["boolean_optimized"] += 1
                        return Copy(inst.dest, def_inst.operand, inst.source_location)
                    # Check for comparison inversion: not(x op y) -> x inv_op y
                    elif isinstance(def_inst, BinaryOp):
                        inverted_op = self._invert_comparison(def_inst.op)
                        if inverted_op:
                            self.stats["boolean_optimized"] += 1
                            return BinaryOp(inst.dest, inverted_op, def_inst.left, def_inst.right, inst.source_location)
            elif inst.op == "-":
                # Check for double negation: -(-x) -> x
                if self.use_def_chains:
                    def_inst = self.use_def_chains.get_definition(inst.operand)
                    if isinstance(def_inst, UnaryOp) and def_inst.op == "-":
                        # -(-x) -> x
                        self.stats["integer_optimized"] += 1
                        return Copy(inst.dest, def_inst.operand, inst.source_location)

            # Constant folding
            if isinstance(inst.operand, Constant):
                folded = self._fold_unary_constant(inst.op, inst.operand)
                if folded:
                    self.stats["constant_folded"] += 1
                    return LoadConst(inst.dest, folded, inst.source_location)

        elif isinstance(inst, ConditionalJump):
            # Optimize conditional jumps with known conditions
            if isinstance(inst.condition, Constant):
                if inst.condition.value:
                    # Always true - convert to unconditional jump
                    from machine_dialect.mir.mir_instructions import Jump

                    self.stats["constant_folded"] += 1
                    if inst.true_label:
                        # TODO: Verify if using inst.source_location is correct for optimization-generated instructions
                        return Jump(inst.true_label, inst.source_location)
                else:
                    # Always false - convert to jump to false label
                    from machine_dialect.mir.mir_instructions import Jump

                    self.stats["constant_folded"] += 1
                    if inst.false_label:
                        # TODO: Verify if using inst.source_location is correct for optimization-generated instructions
                        return Jump(inst.false_label, inst.source_location)

        return inst

    def _optimize_patterns(self, inst: BinaryOp, type_contexts: dict[MIRValue, TypeContext]) -> MIRInstruction | None:
        """Apply pattern-based optimizations.

        Args:
            inst: The binary operation.
            type_contexts: Type contexts.

        Returns:
            Optimized instruction or None.
        """
        # Bit manipulation patterns
        if inst.op == "&" and self.use_def_chains:
            # Pattern: x & (x - 1) - clears the lowest set bit
            # Check if right operand is x - 1
            right_def = self.use_def_chains.get_definition(inst.right)
            if isinstance(right_def, BinaryOp) and right_def.op == "-":
                if right_def.left == inst.left and isinstance(right_def.right, Constant) and right_def.right.value == 1:
                    # Found x & (x - 1) pattern
                    # This could be replaced with a PopCountOp or specialized instruction
                    # For now, just mark that we found it
                    self.stats["patterns_matched"] += 1
                    # Could optimize to a specialized instruction here
                    return inst
            # Check if left operand is x - 1 (commutative)
            left_def = self.use_def_chains.get_definition(inst.left)
            if isinstance(left_def, BinaryOp) and left_def.op == "-":
                if left_def.left == inst.right and isinstance(left_def.right, Constant) and left_def.right.value == 1:
                    # Found (x - 1) & x pattern
                    self.stats["patterns_matched"] += 1
                    return inst

        # Min/max pattern detection
        # Pattern: (a < b) ? a : b => min(a, b)
        # Pattern: (a > b) ? a : b => max(a, b)

        # For now, convert comparisons that will be used in select patterns
        if inst.op in ["<", ">", "<=", ">="] and self.use_def_chains:
            # Check if this comparison is used in a conditional
            uses = self.use_def_chains.get_uses(inst.dest)
            for use in uses:
                if isinstance(use, ConditionalJump):
                    # Could potentially be converted to min/max
                    # This would require more complex pattern matching
                    pass

        # Saturating arithmetic patterns
        # Pattern: min(a + b, MAX_INT) => saturating_add(a, b)
        if inst.op == "+" and self._is_saturating_pattern(inst, type_contexts):
            self.stats["specialized_instructions"] += 1
            # SaturatingAddOp doesn't take source_location - it's an optimization-generated instruction
            return SaturatingAddOp(inst.dest, inst.left, inst.right)

        # Identity operations
        if self._is_identity_operation(inst):
            return Copy(inst.dest, inst.left if inst.op in ["+", "-", "*", "/"] else inst.right, inst.source_location)

        return inst

    def _optimize_with_ranges(
        self, inst: BinaryOp, type_contexts: dict[MIRValue, TypeContext]
    ) -> MIRInstruction | None:
        """Optimize using range information.

        Args:
            inst: The binary operation.
            type_contexts: Type contexts with ranges.

        Returns:
            Optimized instruction or None.
        """
        left_ctx = type_contexts.get(inst.left)
        right_ctx = type_contexts.get(inst.right)

        if not left_ctx or not right_ctx:
            return inst

        # Range-based comparison optimization
        if inst.op in ["<", "<=", ">", ">="]:
            if left_ctx.range and right_ctx.range:
                # Check if comparison result is statically known
                if inst.op == "<" and left_ctx.range.max is not None and right_ctx.range.min is not None:
                    if left_ctx.range.max < right_ctx.range.min:
                        # Always true
                        return LoadConst(inst.dest, Constant(True, MIRType.BOOL), inst.source_location)
                    elif left_ctx.range.min is not None and right_ctx.range.max is not None:
                        if left_ctx.range.min >= right_ctx.range.max:
                            # Always false
                            return LoadConst(inst.dest, Constant(False, MIRType.BOOL), inst.source_location)

        # Division by power of 2 optimization
        if inst.op == "/" and right_ctx.range and right_ctx.range.is_constant():
            val = right_ctx.range.min
            if isinstance(val, int) and val > 0 and (val & (val - 1)) == 0:
                # Power of 2 - use shift
                shift_amount = val.bit_length() - 1
                return ShiftOp(inst.dest, inst.left, Constant(shift_amount, MIRType.INT), ">>", inst.source_location)

        return inst

    def _apply_strength_reduction(self, inst: BinaryOp) -> MIRInstruction | None:
        """Apply strength reduction optimizations.

        Args:
            inst: The binary operation.

        Returns:
            Reduced instruction or original.
        """
        # Check for power-of-2 optimizations with right constant
        if isinstance(inst.right, Constant):
            val = inst.right.value
            if isinstance(val, int):
                # Multiplication optimizations
                if inst.op == "*":
                    if val == 0:
                        return LoadConst(inst.dest, Constant(0, MIRType.INT), inst.source_location)
                    elif val == 1:
                        return Copy(inst.dest, inst.left, inst.source_location)
                    elif val == 2:
                        return BinaryOp(inst.dest, "+", inst.left, inst.left, inst.source_location)
                    elif val == -1:
                        return UnaryOp(inst.dest, "-", inst.left, inst.source_location)
                    elif val > 2 and (val & (val - 1)) == 0:
                        # Power of 2 - use shift
                        shift_amount = val.bit_length() - 1
                        return ShiftOp(
                            inst.dest, inst.left, Constant(shift_amount, MIRType.INT), "<<", inst.source_location
                        )

                # Division by power of 2
                elif inst.op == "/" and val > 0 and (val & (val - 1)) == 0:
                    shift_amount = val.bit_length() - 1
                    return ShiftOp(
                        inst.dest, inst.left, Constant(shift_amount, MIRType.INT), ">>", inst.source_location
                    )

                # Modulo by power of 2
                elif inst.op == "%" and val > 0 and (val & (val - 1)) == 0:
                    mask_val = val - 1
                    return BinaryOp(inst.dest, "&", inst.left, Constant(mask_val, MIRType.INT), inst.source_location)

                # Power optimizations
                elif inst.op == "**":
                    if val == 0:
                        # x ** 0 -> 1
                        return LoadConst(inst.dest, Constant(1, MIRType.INT), inst.source_location)
                    elif val == 1:
                        # x ** 1 -> x
                        return Copy(inst.dest, inst.left, inst.source_location)
                    elif val == 2:
                        # x ** 2 -> x * x
                        return BinaryOp(inst.dest, "*", inst.left, inst.left, inst.source_location)

        # Self operations
        if inst.left == inst.right:
            if inst.op == "-":
                return LoadConst(inst.dest, Constant(0, MIRType.INT), inst.source_location)
            elif inst.op == "/" and inst.left != Constant(0, MIRType.INT):
                return LoadConst(inst.dest, Constant(1, MIRType.INT), inst.source_location)
            elif inst.op == "^":  # XOR
                return LoadConst(inst.dest, Constant(0, MIRType.INT), inst.source_location)
            elif inst.op == "%":  # x % x => 0
                return LoadConst(inst.dest, Constant(0, MIRType.INT), inst.source_location)

        return inst

    def _optimize_cross_block(self, function: MIRFunction) -> bool:
        """Perform cross-block optimizations.

        Args:
            function: The function to optimize.

        Returns:
            True if modified.
        """
        modified = False

        # Use dominance information for more aggressive optimizations
        if not self.dominance_info:
            return False

        for block in function.cfg.blocks.values():
            # Find values that are constant along all paths to this block
            for inst in block.instructions:
                if isinstance(inst, BinaryOp):
                    # Check if operands have consistent values from dominators
                    if self._has_consistent_value_from_dominators(inst.left, block):
                        # Can optimize based on dominator information
                        self.stats["cross_block_optimized"] += 1
                        modified = True

        return modified

    def _has_consistent_value_from_dominators(self, value: MIRValue, block: BasicBlock) -> bool:
        """Check if a value has consistent type/range from dominators.

        Args:
            value: The value to check.
            block: The current block.

        Returns:
            True if value is consistent.
        """
        if not self.dominance_info or not self.use_def_chains:
            return False

        # Get definition of value
        def_inst = self.use_def_chains.get_definition(value)
        if not def_inst:
            return False

        # Check if definition dominates this block
        def_block = self._find_block_for_instruction(def_inst)
        if def_block and self.dominance_info.dominates(def_block, block):
            return True

        return False

    def _find_block_for_instruction(self, inst: MIRInstruction) -> BasicBlock | None:
        """Find which block contains an instruction.

        Args:
            inst: The instruction to find.

        Returns:
            The containing block or None.
        """
        # This would need access to the function's CFG
        # For now, return None
        return None

    def _is_saturating_pattern(self, inst: BinaryOp, type_contexts: dict[MIRValue, TypeContext]) -> bool:
        """Check if this is a saturating arithmetic pattern.

        Args:
            inst: The instruction.
            type_contexts: Type contexts.

        Returns:
            True if saturating pattern.
        """
        # Simple heuristic for now
        if inst.op != "+":
            return False

        # Check if result is used in a min operation with a constant
        if self.use_def_chains:
            uses = self.use_def_chains.get_uses(inst.dest)
            for use in uses:
                if isinstance(use, MinOp):
                    return True

        return False

    def _is_identity_operation(self, inst: BinaryOp) -> bool:
        """Check if this is an identity operation.

        Args:
            inst: The binary operation.

        Returns:
            True if identity operation.
        """
        if isinstance(inst.right, Constant):
            val = inst.right.value
            if inst.op == "+" and val == 0:
                return True
            elif inst.op == "-" and val == 0:
                return True
            elif inst.op == "*" and val == 1:
                return True
            elif inst.op == "/" and val == 1:
                return True

        if isinstance(inst.left, Constant):
            val = inst.left.value
            if inst.op == "+" and val == 0:
                return True
            elif inst.op == "*" and val == 1:
                return True

        return False

    def _fold_binary_constant(self, op: str, left: Constant, right: Constant) -> Constant | None:
        """Fold binary operation on constants.

        Args:
            op: The operator.
            left: Left constant.
            right: Right constant.

        Returns:
            Folded constant or None.
        """
        try:
            left_val = left.value
            right_val = right.value

            # Integer operations
            if left.type == MIRType.INT and right.type == MIRType.INT:
                if op == "+":
                    return Constant(left_val + right_val, MIRType.INT)
                elif op == "-":
                    return Constant(left_val - right_val, MIRType.INT)
                elif op == "*":
                    return Constant(left_val * right_val, MIRType.INT)
                elif op == "/" and right_val != 0:
                    return Constant(left_val // right_val, MIRType.INT)
                elif op == "%" and right_val != 0:
                    return Constant(left_val % right_val, MIRType.INT)
                elif op == "**":
                    return Constant(left_val**right_val, MIRType.INT)
                elif op == "&":
                    return Constant(left_val & right_val, MIRType.INT)
                elif op == "|":
                    return Constant(left_val | right_val, MIRType.INT)
                elif op == "^":
                    return Constant(left_val ^ right_val, MIRType.INT)
                elif op == "<<":
                    return Constant(left_val << right_val, MIRType.INT)
                elif op == ">>":
                    return Constant(left_val >> right_val, MIRType.INT)
                # Comparisons
                elif op == "==":
                    return Constant(left_val == right_val, MIRType.BOOL)
                elif op == "!=":
                    return Constant(left_val != right_val, MIRType.BOOL)
                elif op == "<":
                    return Constant(left_val < right_val, MIRType.BOOL)
                elif op == "<=":
                    return Constant(left_val <= right_val, MIRType.BOOL)
                elif op == ">":
                    return Constant(left_val > right_val, MIRType.BOOL)
                elif op == ">=":
                    return Constant(left_val >= right_val, MIRType.BOOL)

            # Float operations
            elif left.type == MIRType.FLOAT or right.type == MIRType.FLOAT:
                left_val = float(left_val)
                right_val = float(right_val)

                if op == "+":
                    return Constant(left_val + right_val, MIRType.FLOAT)
                elif op == "-":
                    return Constant(left_val - right_val, MIRType.FLOAT)
                elif op == "*":
                    return Constant(left_val * right_val, MIRType.FLOAT)
                elif op == "/" and right_val != 0.0:
                    return Constant(left_val / right_val, MIRType.FLOAT)
                elif op == "**":
                    return Constant(left_val**right_val, MIRType.FLOAT)
                # Comparisons
                elif op == "==":
                    return Constant(left_val == right_val, MIRType.BOOL)
                elif op == "!=":
                    return Constant(left_val != right_val, MIRType.BOOL)
                elif op == "<":
                    return Constant(left_val < right_val, MIRType.BOOL)
                elif op == "<=":
                    return Constant(left_val <= right_val, MIRType.BOOL)
                elif op == ">":
                    return Constant(left_val > right_val, MIRType.BOOL)
                elif op == ">=":
                    return Constant(left_val >= right_val, MIRType.BOOL)

            # Boolean operations
            elif left.type == MIRType.BOOL and right.type == MIRType.BOOL:
                if op == "and":
                    return Constant(left_val and right_val, MIRType.BOOL)
                elif op == "or":
                    return Constant(left_val or right_val, MIRType.BOOL)
                elif op == "==":
                    return Constant(left_val == right_val, MIRType.BOOL)
                elif op == "!=":
                    return Constant(left_val != right_val, MIRType.BOOL)

            # String operations
            elif left.type == MIRType.STRING and right.type == MIRType.STRING:
                if op == "+":
                    return Constant(str(left_val) + str(right_val), MIRType.STRING)
                elif op == "==":
                    return Constant(left_val == right_val, MIRType.BOOL)
                elif op == "!=":
                    return Constant(left_val != right_val, MIRType.BOOL)

        except (ValueError, TypeError, ZeroDivisionError):
            pass

        return None

    def _invert_comparison(self, op: str) -> str | None:
        """Get the inverted comparison operator.

        Args:
            op: The comparison operator.

        Returns:
            The inverted operator or None if not a comparison.
        """
        inversions = {
            "==": "!=",
            "!=": "==",
            "<": ">=",
            "<=": ">",
            ">": "<=",
            ">=": "<",
        }
        return inversions.get(op)

    def _fold_unary_constant(self, op: str, operand: Constant) -> Constant | None:
        """Fold unary operation on constant.

        Args:
            op: The operator.
            operand: The operand.

        Returns:
            Folded constant or None.
        """
        try:
            if op == "-":
                if operand.type == MIRType.INT:
                    return Constant(-operand.value, MIRType.INT)
                elif operand.type == MIRType.FLOAT:
                    return Constant(-operand.value, MIRType.FLOAT)
            elif op == "not":
                return Constant(not operand.value, MIRType.BOOL)
            elif op == "~" and operand.type == MIRType.INT:
                return Constant(~operand.value, MIRType.INT)
        except (ValueError, TypeError):
            pass

        return None
