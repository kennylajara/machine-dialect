"""Loop Invariant Code Motion (LICM) optimization pass.

This module implements LICM to hoist loop-invariant computations out of loops,
reducing redundant calculations and improving performance.
"""

from machine_dialect.mir.analyses.loop_analysis import Loop, LoopAnalysis
from machine_dialect.mir.analyses.use_def_chains import UseDefChains
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    MIRInstruction,
    Phi,
    Print,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_values import Constant, MIRValue, Variable
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)
from machine_dialect.mir.ssa_construction import DominanceInfo


class LoopInvariantCodeMotion(OptimizationPass):
    """Loop Invariant Code Motion optimization pass."""

    def __init__(self) -> None:
        """Initialize LICM pass."""
        super().__init__()
        self.loop_analysis: LoopAnalysis | None = None
        self.dominance: DominanceInfo | None = None
        self.use_def: UseDefChains | None = None
        self.stats = {"hoisted": 0, "loops_processed": 0}

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="licm",
            description="Hoist loop-invariant code out of loops",
            pass_type=PassType.OPTIMIZATION,
            requires=["loop-analysis", "dominance", "use-def-chains"],
            preserves=PreservationLevel.NONE,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run LICM on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        # Get required analyses
        loop_info = self.get_analysis("loop-analysis", function)
        self.dominance = self.get_analysis("dominance", function)
        self.use_def = self.get_analysis("use-def-chains", function)

        if not loop_info or not self.dominance or not self.use_def:
            return False

        transformer = MIRTransformer(function)
        modified = False

        # Process loops from innermost to outermost for better optimization
        loops = self._get_loops_in_order(loop_info.loops if hasattr(loop_info, "loops") else [])

        for loop in loops:
            if self._process_loop(loop, function, transformer):
                modified = True
                self.stats["loops_processed"] += 1

        return modified

    def _get_loops_in_order(self, loops: list[Loop]) -> list[Loop]:
        """Get loops ordered from innermost to outermost.

        Args:
            loops: List of loops.

        Returns:
            Ordered list of loops.
        """
        # Sort by depth (deeper loops first) to process inner loops before outer
        return sorted(loops, key=lambda loop: loop.depth, reverse=True)

    def _process_loop(self, loop: Loop, function: MIRFunction, transformer: MIRTransformer) -> bool:
        """Process a single loop for invariant code motion.

        Args:
            loop: The loop to process.
            function: The containing function.
            transformer: MIR transformer for modifications.

        Returns:
            True if modifications were made.
        """
        modified = False
        preheader = self._get_or_create_preheader(loop, function, transformer)

        if not preheader:
            return False

        # Find loop-invariant instructions
        invariant_instructions = self._find_invariant_instructions(loop, function)

        # Hoist invariant instructions to preheader
        for inst, block in invariant_instructions:
            if self._can_hoist(inst, block, loop, preheader):
                self._hoist_instruction(inst, block, preheader, transformer)
                self.stats["hoisted"] += 1
                modified = True

        return modified

    def _get_or_create_preheader(
        self, loop: Loop, function: MIRFunction, transformer: MIRTransformer
    ) -> BasicBlock | None:
        """Get or create a preheader block for a loop.

        A preheader is a single-entry block that dominates the loop header
        and is the only predecessor from outside the loop.

        Args:
            loop: The loop.
            function: The containing function.
            transformer: MIR transformer.

        Returns:
            The preheader block or None if creation failed.
        """
        header = loop.header

        # Find predecessors from outside the loop
        outside_preds = [pred for pred in header.predecessors if pred not in loop.blocks]

        if len(outside_preds) == 1:
            # Single outside predecessor could be the preheader if it only goes to header
            pred = outside_preds[0]
            if len(pred.successors) == 1:
                return pred

        # Need to create a new preheader
        preheader = BasicBlock("loop_preheader")
        transformer.function.cfg.add_block(preheader)

        # Redirect outside predecessors to preheader
        for pred in outside_preds:
            # Update the jump/branch instruction in predecessor
            for i, inst in enumerate(pred.instructions):
                if isinstance(inst, Jump) and inst.label == header.label:
                    source_loc = inst.source_location if hasattr(inst, "source_location") else (0, 0)
                    pred.instructions[i] = Jump(preheader.label, source_loc)
                elif isinstance(inst, ConditionalJump):
                    if inst.true_label == header.label:
                        inst.true_label = preheader.label
                    if inst.false_label == header.label:
                        inst.false_label = preheader.label

            # Update CFG edges
            if header in pred.successors:
                pred.successors.remove(header)
                pred.successors.append(preheader)
            if pred in header.predecessors:
                header.predecessors.remove(pred)
            preheader.predecessors.append(pred)

        # Add unconditional jump from preheader to header
        # TODO: Verify if (0, 0) is the right approach for synthetic instructions
        preheader.instructions.append(Jump(header.label, (0, 0)))
        preheader.successors.append(header)
        header.predecessors.append(preheader)

        return preheader

    def _find_invariant_instructions(
        self, loop: Loop, function: MIRFunction
    ) -> list[tuple[MIRInstruction, BasicBlock]]:
        """Find loop-invariant instructions.

        An instruction is loop-invariant if:
        1. All its operands are defined outside the loop or are loop-invariant
        2. It doesn't have side effects that depend on loop iteration

        Args:
            loop: The loop to analyze.
            function: The containing function.

        Returns:
            List of (instruction, block) pairs that are loop-invariant.
        """
        invariant: list[tuple[MIRInstruction, BasicBlock]] = []
        invariant_values: set[MIRValue] = set()

        # First, find all variables that are modified inside the loop
        modified_in_loop: set[str] = set()
        for block in loop.blocks:
            for inst in block.instructions:
                for def_val in inst.get_defs():
                    if isinstance(def_val, Variable):
                        modified_in_loop.add(def_val.name)

        # Function parameters are invariant if not modified in the loop
        # They are implicitly defined outside all loops
        for param in function.params:
            param_name = param.name if isinstance(param, Variable) else str(param)
            if param_name not in modified_in_loop:
                # Find the Variable object for this parameter
                # Look through loop instructions to find the Variable instance
                for block in loop.blocks:
                    for inst in block.instructions:
                        for use in inst.get_uses():
                            if isinstance(use, Variable) and use.name == param_name:
                                invariant_values.add(use)
                                break

        # Values defined outside the loop are invariant ONLY if not modified inside
        for block in function.cfg.blocks.values():
            if block not in loop.blocks:
                for inst in block.instructions:
                    for def_val in inst.get_defs():
                        # Only add if it's not a variable OR if it's a variable not modified in loop
                        if isinstance(def_val, Variable):
                            if def_val.name not in modified_in_loop:
                                invariant_values.add(def_val)
                        else:
                            # Temps and other values from outside are invariant
                            invariant_values.add(def_val)

        # Constants are always invariant
        for block in loop.blocks:
            for inst in block.instructions:
                for use in inst.get_uses():
                    if isinstance(use, Constant):
                        invariant_values.add(use)

        # Fixed-point iteration to find invariant instructions
        changed = True
        while changed:
            changed = False
            for block in loop.blocks:
                for inst in block.instructions:
                    # Skip if already marked as invariant
                    if any(inst is i for i, _ in invariant):
                        continue

                    # Check if instruction is invariant
                    if self._is_invariant_instruction(inst, invariant_values, loop):
                        invariant.append((inst, block))
                        invariant_values.update(inst.get_defs())
                        changed = True

        return invariant

    def _is_invariant_instruction(self, inst: MIRInstruction, invariant_values: set[MIRValue], loop: Loop) -> bool:
        """Check if an instruction is loop-invariant.

        Args:
            inst: The instruction to check.
            invariant_values: Set of known invariant values.
            loop: The containing loop.

        Returns:
            True if the instruction is loop-invariant.
        """
        # Control flow instructions are not invariant
        if isinstance(inst, ConditionalJump | Jump | Return | Phi):
            return False

        # Side-effect instructions need careful handling
        if isinstance(inst, Call | Print):
            # Conservative: don't hoist calls or prints
            return False

        # Check if instruction defines a variable that's modified in the loop
        # This is an additional safety check to prevent hoisting loop counters
        for def_val in inst.get_defs():
            if isinstance(def_val, Variable):
                # Check if this variable is modified elsewhere in the loop
                # If so, we can't hoist this instruction
                for block in loop.blocks:
                    for other_inst in block.instructions:
                        if other_inst is not inst:
                            for other_def in other_inst.get_defs():
                                if isinstance(other_def, Variable) and other_def.name == def_val.name:
                                    # This variable is modified elsewhere in loop, can't hoist
                                    return False

        # Check if all operands are invariant
        for operand in inst.get_uses():
            if operand not in invariant_values:
                return False

        # Safe arithmetic and data movement instructions
        if isinstance(inst, BinaryOp | UnaryOp | Copy | LoadConst | StoreVar):
            return True

        return False

    def _can_hoist(self, inst: MIRInstruction, block: BasicBlock, loop: Loop, preheader: BasicBlock) -> bool:
        """Check if an instruction can be safely hoisted.

        Args:
            inst: The instruction to hoist.
            block: The block containing the instruction.
            loop: The loop.
            preheader: The preheader block.

        Returns:
            True if the instruction can be hoisted.
        """
        # Check if the instruction will execute on every iteration
        # For now, we use a simple heuristic: hoist if the block is in the loop
        # and the instruction is safe to speculatively execute
        if not self.dominance:
            return False

        # Check if this block is guaranteed to execute when the loop is entered
        # The header always executes, and blocks dominated by the header that
        # don't have conditional predecessors within the loop are safe
        if block == loop.header:
            return True

        # For other blocks, check if they dominate the latch (back edge source)
        # This ensures they execute on every iteration that continues
        latch = loop.back_edge[0]  # Source of the back edge
        if not self.dominance.dominates(block, latch):
            # If it doesn't dominate the latch, it might not execute on every iteration
            # Be conservative and don't hoist
            return False

        # Don't hoist memory operations that might alias
        # (Conservative for now - could add alias analysis later)
        if isinstance(inst, StoreVar):
            # Check if any other instruction in the loop might read this variable
            var = inst.var
            for loop_block in loop.blocks:
                for loop_inst in loop_block.instructions:
                    if loop_inst is inst:
                        continue
                    # Check for potential aliasing
                    for use in loop_inst.get_uses():
                        if isinstance(use, Variable) and use.name == var.name:
                            return False

        return True

    def _hoist_instruction(
        self,
        inst: MIRInstruction,
        from_block: BasicBlock,
        to_block: BasicBlock,
        transformer: MIRTransformer,
    ) -> None:
        """Hoist an instruction from one block to another.

        Args:
            inst: The instruction to hoist.
            from_block: The source block.
            to_block: The destination block (preheader).
            transformer: MIR transformer.
        """
        # Remove from original block
        from_block.instructions.remove(inst)

        # Insert at the end of preheader (before the jump)
        if to_block.instructions and isinstance(to_block.instructions[-1], Jump):
            to_block.instructions.insert(-1, inst)
        else:
            to_block.instructions.append(inst)

        transformer.modified = True

    def finalize(self) -> None:
        """Finalize the pass after running.

        Cleans up any temporary state.
        """
        self.loop_analysis = None
        self.dominance = None
        self.use_def = None

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats
