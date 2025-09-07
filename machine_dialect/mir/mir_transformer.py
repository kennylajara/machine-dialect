"""MIR transformation utilities for optimization passes.

This module provides utilities for transforming MIR code, including
instruction manipulation, block operations, and SSA preservation.
"""

from collections.abc import Callable

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    ConditionalJump,
    Jump,
    Label,
    MIRInstruction,
    Phi,
    Return,
)
from machine_dialect.mir.mir_values import MIRValue


class MIRTransformer:
    """Utility class for transforming MIR code."""

    def __init__(self, function: MIRFunction) -> None:
        """Initialize the transformer.

        Args:
            function: Function to transform.
        """
        self.function = function
        self.modified = False

    def replace_instruction(
        self,
        block: BasicBlock,
        old_inst: MIRInstruction,
        new_inst: MIRInstruction,
    ) -> bool:
        """Replace an instruction in a block.

        Args:
            block: The block containing the instruction.
            old_inst: Instruction to replace.
            new_inst: Replacement instruction.

        Returns:
            True if replacement was successful.
        """
        try:
            index = block.instructions.index(old_inst)
            block.instructions[index] = new_inst
            self.modified = True
            return True
        except ValueError:
            # Check phi nodes
            try:
                index = block.phi_nodes.index(old_inst)  # type: ignore
                if isinstance(new_inst, Phi):
                    block.phi_nodes[index] = new_inst
                    self.modified = True
                    return True
            except (ValueError, TypeError):
                pass
        return False

    def remove_instruction(
        self,
        block: BasicBlock,
        inst: MIRInstruction,
    ) -> bool:
        """Remove an instruction from a block.

        Args:
            block: The block containing the instruction.
            inst: Instruction to remove.

        Returns:
            True if removal was successful.
        """
        try:
            block.instructions.remove(inst)
            self.modified = True
            return True
        except ValueError:
            # Check phi nodes
            try:
                block.phi_nodes.remove(inst)  # type: ignore
                self.modified = True
                return True
            except (ValueError, TypeError):
                pass
        return False

    def insert_instruction(
        self,
        block: BasicBlock,
        inst: MIRInstruction,
        position: int | None = None,
    ) -> None:
        """Insert an instruction into a block.

        Args:
            block: The block to insert into.
            inst: Instruction to insert.
            position: Position to insert at (None for end).
        """
        if isinstance(inst, Phi):
            block.phi_nodes.append(inst)
        else:
            if position is None:
                # Insert before terminator if present
                if block.get_terminator():
                    block.instructions.insert(-1, inst)
                else:
                    block.instructions.append(inst)
            else:
                block.instructions.insert(position, inst)
        self.modified = True

    def replace_uses(
        self,
        old_value: MIRValue,
        new_value: MIRValue,
        block: BasicBlock | None = None,
    ) -> int:
        """Replace all uses of a value.

        Args:
            old_value: Value to replace.
            new_value: Replacement value.
            block: Optional block to limit replacement to.

        Returns:
            Number of replacements made.
        """
        count = 0
        blocks = [block] if block else self.function.cfg.blocks.values()

        for b in blocks:
            # Process phi nodes
            for phi in b.phi_nodes:
                for i, (val, label) in enumerate(phi.incoming):
                    if val == old_value:
                        phi.incoming[i] = (new_value, label)
                        count += 1
                        self.modified = True

            # Process instructions
            for inst in b.instructions:
                inst.replace_use(old_value, new_value)
                # Check if replacement occurred
                if new_value in inst.get_uses():
                    count += 1
                    self.modified = True

        return count

    def remove_dead_instructions(self, block: BasicBlock) -> int:
        """Remove dead instructions from a block.

        Args:
            block: Block to clean.

        Returns:
            Number of instructions removed.
        """
        removed = 0
        to_remove = []

        for inst in block.instructions:
            # Skip side-effecting instructions
            if isinstance(inst, Return | Jump | ConditionalJump | Label):
                continue
            if hasattr(inst, "has_side_effects") and inst.has_side_effects():
                continue

            # Check if any definitions are used
            defs = inst.get_defs()
            if defs and all(self._is_dead_value(v) for v in defs):
                to_remove.append(inst)

        for inst in to_remove:
            self.remove_instruction(block, inst)
            removed += 1

        return removed

    def _is_dead_value(self, value: MIRValue) -> bool:
        """Check if a value is dead (unused).

        Args:
            value: Value to check.

        Returns:
            True if the value is dead.
        """
        # This is a simplified check - should use use-def chains
        for block in self.function.cfg.blocks.values():
            for phi in block.phi_nodes:
                if value in [v for v, _ in phi.incoming]:
                    return False
            for inst in block.instructions:
                if value in inst.get_uses():
                    return False
        return True

    def split_block(
        self,
        block: BasicBlock,
        split_point: int,
        new_label: str,
    ) -> BasicBlock:
        """Split a block at a given instruction index.

        Args:
            block: Block to split.
            split_point: Index to split at.
            new_label: Label for the new block.

        Returns:
            The new block containing instructions after split point.
        """
        # Create new block
        new_block = BasicBlock(new_label)

        # Move instructions after split point to new block
        new_block.instructions = block.instructions[split_point:]
        block.instructions = block.instructions[:split_point]

        # Update CFG edges
        # New block takes over original block's successors
        new_block.successors = block.successors.copy()
        for succ in new_block.successors:
            # Update predecessor
            idx = succ.predecessors.index(block)
            succ.predecessors[idx] = new_block

        # Original block now jumps to new block
        block.successors = [new_block]
        new_block.predecessors = [block]

        # Add jump instruction if needed
        if not block.get_terminator():
            block.add_instruction(Jump(new_label, (0, 0)))

        # Add new block to CFG
        self.function.cfg.add_block(new_block)
        self.modified = True

        return new_block

    def merge_blocks(self, pred: BasicBlock, succ: BasicBlock) -> bool:
        """Merge two blocks if possible.

        Args:
            pred: Predecessor block.
            succ: Successor block.

        Returns:
            True if merge was successful.
        """
        # Can only merge if pred has single successor and succ has single predecessor
        if len(pred.successors) != 1 or len(succ.predecessors) != 1:
            return False

        # Can't merge if succ has phi nodes
        if succ.phi_nodes:
            return False

        # Remove jump from pred if it exists
        if pred.get_terminator() and isinstance(pred.get_terminator(), Jump):
            pred.instructions.pop()

        # Move instructions from succ to pred
        pred.instructions.extend(succ.instructions)

        # Update CFG
        pred.successors = succ.successors
        for s in succ.successors:
            idx = s.predecessors.index(succ)
            s.predecessors[idx] = pred

        # Remove succ from CFG
        del self.function.cfg.blocks[succ.label]
        self.modified = True

        return True

    def eliminate_unreachable_blocks(self) -> int:
        """Remove unreachable blocks from the function.

        Returns:
            Number of blocks removed.
        """
        # Find reachable blocks via DFS
        reachable = set()
        worklist = []

        if self.function.cfg.entry_block:
            worklist.append(self.function.cfg.entry_block)

        while worklist:
            block = worklist.pop()
            if block in reachable:
                continue
            reachable.add(block)
            worklist.extend(block.successors)

        # Remove unreachable blocks
        removed = 0
        unreachable = [b for b in self.function.cfg.blocks.values() if b not in reachable]

        for block in unreachable:
            # Update predecessors' successor lists
            for pred in block.predecessors:
                pred.successors.remove(block)

            # Update successors' predecessor lists
            for succ in block.successors:
                succ.predecessors.remove(block)

            # Remove from CFG
            del self.function.cfg.blocks[block.label]
            removed += 1
            self.modified = True

        return removed

    def simplify_cfg(self) -> bool:
        """Simplify the control flow graph.

        Returns:
            True if any simplification was performed.
        """
        initial_modified = self.modified

        # Remove unreachable blocks
        self.eliminate_unreachable_blocks()

        # Merge blocks where possible
        changed = True
        while changed:
            changed = False
            for block in list(self.function.cfg.blocks.values()):
                if len(block.successors) == 1:
                    succ = block.successors[0]
                    if self.merge_blocks(block, succ):
                        changed = True
                        break

        # Remove empty blocks (except entry)
        for block in list(self.function.cfg.blocks.values()):
            if block != self.function.cfg.entry_block and not block.instructions and not block.phi_nodes:
                # Redirect predecessors to successors
                if len(block.successors) == 1:
                    succ = block.successors[0]
                    for pred in block.predecessors:
                        # Update pred's successors
                        idx = pred.successors.index(block)
                        pred.successors[idx] = succ
                        # Update succ's predecessors
                        idx = succ.predecessors.index(block)
                        succ.predecessors[idx] = pred
                        # Update jump targets
                        term = pred.get_terminator()
                        if isinstance(term, Jump) and term.label == block.label:
                            term.label = succ.label
                        elif isinstance(term, ConditionalJump):
                            if term.true_label == block.label:
                                term.true_label = succ.label
                            if term.false_label == block.label:
                                term.false_label = succ.label

                    del self.function.cfg.blocks[block.label]
                    self.modified = True

        return self.modified != initial_modified

    def apply_to_all_instructions(
        self,
        transform: Callable[[MIRInstruction], MIRInstruction | None],
    ) -> int:
        """Apply a transformation to all instructions.

        Args:
            transform: Function that transforms or removes instructions.

        Returns:
            Number of instructions modified.
        """
        count = 0

        for block in self.function.cfg.blocks.values():
            # Process instructions
            new_instructions = []
            for inst in block.instructions:
                result = transform(inst)
                if result is not None:
                    new_instructions.append(result)
                    if result != inst:
                        count += 1
                        self.modified = True
                else:
                    count += 1
                    self.modified = True

            block.instructions = new_instructions

        return count
