"""Dead code elimination optimization pass.

This module implements dead code elimination (DCE) at the MIR level,
removing instructions and blocks that have no effect on program output.
"""

from machine_dialect.mir.analyses.use_def_chains import UseDefChains
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    Call,
    ConditionalJump,
    Jump,
    MIRInstruction,
    Print,
    Return,
    Scope,
    StoreVar,
)
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_values import Temp, Variable
from machine_dialect.mir.optimization_pass import (
    OptimizationPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class DeadCodeElimination(OptimizationPass):
    """Dead code elimination optimization pass."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="dce",
            description="Eliminate dead code and unreachable blocks",
            pass_type=[PassType.OPTIMIZATION, PassType.CLEANUP],
            requires=["use-def-chains"],
            preserves=PreservationLevel.CFG,
        )

    def run_on_function(self, function: MIRFunction) -> bool:
        """Run dead code elimination on a function.

        Args:
            function: The function to optimize.

        Returns:
            True if the function was modified.
        """
        transformer = MIRTransformer(function)

        # Get use-def chains
        use_def_chains: UseDefChains = self.get_analysis("use-def-chains", function)

        # Phase 1: Remove dead instructions
        dead_instructions = self._find_dead_instructions(function, use_def_chains)
        for block, inst in dead_instructions:
            transformer.remove_instruction(block, inst)
            self.stats["dead_instructions_removed"] = self.stats.get("dead_instructions_removed", 0) + 1

        # Phase 2: Remove dead stores
        dead_stores = self._find_dead_stores(function, use_def_chains)
        for block, inst in dead_stores:
            # When removing a StoreVar, replace uses of the variable with the source value
            if isinstance(inst, StoreVar):
                # Replace all uses of the variable with the source value
                transformer.replace_uses(inst.var, inst.source)
            transformer.remove_instruction(block, inst)
            self.stats["dead_stores_removed"] = self.stats.get("dead_stores_removed", 0) + 1

        # Phase 3: Remove unreachable blocks
        num_unreachable = transformer.eliminate_unreachable_blocks()
        self.stats["unreachable_blocks_removed"] = num_unreachable

        # Phase 4: Simplify control flow
        transformer.simplify_cfg()

        return transformer.modified

    def _find_dead_instructions(
        self,
        function: MIRFunction,
        use_def_chains: UseDefChains,
    ) -> list[tuple[BasicBlock, MIRInstruction]]:
        """Find dead instructions that can be removed.

        Args:
            function: The function to analyze.
            use_def_chains: Use-def chain information.

        Returns:
            List of (block, instruction) pairs to remove.
        """
        dead = []

        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                # Skip instructions with side effects
                if self._has_side_effects(inst):
                    continue

                # Check if all values defined by this instruction are dead
                defs = inst.get_defs()
                if not defs:
                    continue

                all_dead = True
                for value in defs:
                    if isinstance(value, Temp | Variable):
                        if not use_def_chains.is_dead(value):
                            all_dead = False
                            break

                if all_dead:
                    dead.append((block, inst))

        return dead

    def _find_dead_stores(
        self,
        function: MIRFunction,
        use_def_chains: UseDefChains,
    ) -> list[tuple[BasicBlock, MIRInstruction]]:
        """Find dead store instructions.

        Args:
            function: The function to analyze.
            use_def_chains: Use-def chain information.

        Returns:
            List of (block, instruction) pairs to remove.
        """
        dead_stores = []

        for block in function.cfg.blocks.values():
            # Track last store to each variable in the block
            last_stores: dict[Variable, MIRInstruction] = {}

            for inst in block.instructions:
                if isinstance(inst, StoreVar):
                    # Check if there's a previous store to the same variable
                    if inst.var in last_stores:
                        # Previous store might be dead if not used between stores
                        prev_store = last_stores[inst.var]
                        if self._is_dead_store(
                            prev_store,
                            inst,
                            block,
                            use_def_chains,
                        ):
                            dead_stores.append((block, prev_store))

                    last_stores[inst.var] = inst

            # Check if final stores are dead (no uses after block)
            for _var, store in last_stores.items():
                if self._is_store_dead_at_end(store, block, use_def_chains):
                    dead_stores.append((block, store))

        return dead_stores

    def _is_dead_store(
        self,
        store1: MIRInstruction,
        store2: MIRInstruction,
        block: BasicBlock,
        use_def_chains: UseDefChains,
    ) -> bool:
        """Check if store1 is dead because of store2.

        Args:
            store1: First store instruction.
            store2: Second store instruction.
            block: Containing block.
            use_def_chains: Use-def chain information.

        Returns:
            True if store1 is dead.
        """
        # Find instructions between the two stores
        idx1 = block.instructions.index(store1)
        idx2 = block.instructions.index(store2)

        if idx1 >= idx2:
            return False

        # Check if variable is used between the stores
        if isinstance(store1, StoreVar):
            var = store1.var
            for i in range(idx1 + 1, idx2):
                inst = block.instructions[i]
                if var in inst.get_uses():
                    return False

        return True

    def _is_store_dead_at_end(
        self,
        store: MIRInstruction,
        block: BasicBlock,
        use_def_chains: UseDefChains,
    ) -> bool:
        """Check if a store at the end of a block is dead.

        Args:
            store: Store instruction.
            block: Containing block.
            use_def_chains: Use-def chain information.

        Returns:
            True if the store is dead.
        """
        if not isinstance(store, StoreVar):
            return False

        # Check if variable is used after this block
        var = store.var

        # Check uses in successor blocks
        visited = set()
        worklist = list(block.successors)

        while worklist:
            succ = worklist.pop()
            if succ in visited:
                continue
            visited.add(succ)

            # Check phi nodes
            for phi in succ.phi_nodes:
                for val, pred_label in phi.incoming:
                    if val == var and pred_label == block.label:
                        return False

            # Check instructions
            for inst in succ.instructions:
                if var in inst.get_uses():
                    return False
                # If we see another store to the same variable, we're done
                if isinstance(inst, StoreVar) and inst.var == var:
                    break
            else:
                # No store found, check successors
                worklist.extend(succ.successors)

        return True

    def _has_side_effects(self, inst: MIRInstruction) -> bool:
        """Check if an instruction has side effects.

        Args:
            inst: Instruction to check.

        Returns:
            True if the instruction has side effects.
        """
        # Control flow instructions
        if isinstance(inst, Jump | ConditionalJump | Return):
            return True

        # I/O operations
        if isinstance(inst, Print):
            return True

        # Function calls (conservative - assume all calls have side effects)
        if isinstance(inst, Call):
            return True

        # Memory operations
        if isinstance(inst, StoreVar):
            return True

        # Assertions and scopes
        if isinstance(inst, Assert | Scope):
            return True

        return False

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
