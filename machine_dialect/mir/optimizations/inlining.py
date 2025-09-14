"""Function inlining optimization pass.

This module implements function inlining to eliminate call overhead and
enable further optimizations by exposing more code to analysis.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Call,
    ConditionalJump,
    Copy,
    Jump,
    MIRInstruction,
    Phi,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_transformer import MIRTransformer
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import FunctionRef, MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    ModulePass,
    PassInfo,
    PassType,
    PreservationLevel,
)


@dataclass
class InliningCost:
    """Cost model for inlining decisions.

    Attributes:
        instruction_count: Number of instructions in the function.
        call_site_benefit: Benefit from inlining at this call site.
        size_threshold: Maximum size for inlining.
        depth: Current inlining depth (to prevent infinite recursion).
    """

    instruction_count: int
    call_site_benefit: float
    size_threshold: int
    depth: int

    def should_inline(self) -> bool:
        """Determine if function should be inlined.

        Returns:
            True if inlining is beneficial.
        """
        # Don't inline if too deep (prevent infinite recursion)
        if self.depth > 3:
            return False

        # Don't inline very large functions
        if self.instruction_count > self.size_threshold:
            return False

        # Inline small functions (always beneficial)
        if self.instruction_count <= 5:
            return True

        # Use cost-benefit analysis for medium functions
        # Higher benefit for functions that enable optimizations
        cost = self.instruction_count * 1.0
        benefit = self.call_site_benefit

        # Inline if benefit outweighs cost
        return benefit > cost


class FunctionInlining(ModulePass):
    """Function inlining optimization pass."""

    def __init__(self, size_threshold: int = 50) -> None:
        """Initialize inlining pass.

        Args:
            size_threshold: Maximum function size to consider for inlining.
        """
        super().__init__()
        self.size_threshold = size_threshold
        self.stats = {"inlined": 0, "call_sites_processed": 0}
        self.inlining_depth: dict[str, int] = defaultdict(int)

    def initialize(self) -> None:
        """Initialize the pass before running."""
        super().initialize()
        # Re-initialize stats after base class clears them
        self.stats = {"inlined": 0, "call_sites_processed": 0}
        self.inlining_depth = defaultdict(int)

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="inline",
            description="Inline function calls",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.NONE,
        )

    def run_on_module(self, module: MIRModule) -> bool:
        """Run inlining on a module.

        Args:
            module: The module to optimize.

        Returns:
            True if the module was modified.
        """
        modified = False

        # Process each function
        for _, function in module.functions.items():
            if self._inline_calls_in_function(function, module):
                modified = True

        return modified

    def _inline_calls_in_function(self, function: MIRFunction, module: MIRModule) -> bool:
        """Inline calls within a function.

        Args:
            function: The function to process.
            module: The containing module.

        Returns:
            True if modifications were made.
        """
        modified = False
        transformer = MIRTransformer(function)

        # Keep inlining until no more opportunities
        # This handles the case where inlining creates new opportunities
        changed = True
        while changed:
            changed = False

            # Find all call sites fresh each iteration
            call_sites = self._find_call_sites(function)

            for call_inst, block in call_sites:
                self.stats["call_sites_processed"] += 1

                # Get the called function
                if not isinstance(call_inst.func, FunctionRef):
                    continue

                callee_name = call_inst.func.name
                if callee_name not in module.functions:
                    continue

                callee = module.functions[callee_name]

                # Check if we should inline
                cost = self._calculate_inlining_cost(callee, call_inst, self.inlining_depth[callee_name])
                if not cost.should_inline():
                    continue

                # Don't inline recursive functions directly
                if callee_name == function.name:
                    continue

                # Verify the call is still in the block (it might have been removed by previous inlining)
                if call_inst not in block.instructions:
                    continue

                # Perform inlining
                self.inlining_depth[callee_name] += 1
                if self._inline_call(call_inst, block, callee, function, transformer):
                    modified = True
                    changed = True
                    self.stats["inlined"] += 1
                    # Break inner loop to re-find call sites
                    break
                self.inlining_depth[callee_name] -= 1

        return modified

    def _find_call_sites(self, function: MIRFunction) -> list[tuple[Call, BasicBlock]]:
        """Find all call instructions in a function.

        Args:
            function: The function to search.

        Returns:
            List of (call instruction, containing block) pairs.
        """
        call_sites = []
        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, Call):
                    call_sites.append((inst, block))
        return call_sites

    def _calculate_inlining_cost(self, callee: MIRFunction, call_inst: Call, depth: int) -> InliningCost:
        """Calculate the cost of inlining a function.

        Args:
            callee: The function to inline.
            call_inst: The call instruction.
            depth: Current inlining depth.

        Returns:
            Inlining cost information.
        """
        # Count instructions in callee
        instruction_count = sum(len(block.instructions) for block in callee.cfg.blocks.values())

        # Calculate call site benefit
        # Higher benefit if:
        # - Arguments are constants (enables constant propagation)
        # - Function is called in a loop (amortizes inlining cost)
        # - Function has single return (simpler CFG merge)
        benefit = 10.0  # Base benefit from removing call overhead

        # Bonus for constant arguments
        from machine_dialect.mir.mir_values import Constant

        const_args = sum(1 for arg in call_inst.args if isinstance(arg, Constant))
        benefit += const_args * 5.0

        # Bonus for simple functions (single block)
        if len(callee.cfg.blocks) == 1:
            benefit += 10.0

        # Penalty for multiple returns (complex CFG)
        return_count = sum(
            1 for block in callee.cfg.blocks.values() for inst in block.instructions if isinstance(inst, Return)
        )
        if return_count > 1:
            benefit -= (return_count - 1) * 5.0

        return InliningCost(
            instruction_count=instruction_count,
            call_site_benefit=benefit,
            size_threshold=self.size_threshold,
            depth=depth,
        )

    def _inline_call(
        self,
        call_inst: Call,
        call_block: BasicBlock,
        callee: MIRFunction,
        caller: MIRFunction,
        transformer: MIRTransformer,
    ) -> bool:
        """Inline a function call.

        Args:
            call_inst: The call instruction to inline.
            call_block: The block containing the call.
            callee: The function to inline.
            caller: The calling function.
            transformer: MIR transformer.

        Returns:
            True if inlining succeeded.
        """
        # Create value mapping for parameters -> arguments
        value_map: dict[MIRValue, MIRValue] = {}
        # Get parameter names from the callee function
        # The params might be strings or Variables
        param_names: list[str] = []
        if hasattr(callee, "params") and callee.params:
            if isinstance(callee.params[0], str):
                param_names = callee.params  # type: ignore
            else:
                # Extract names from Variable objects
                for p in callee.params:
                    if isinstance(p, Variable):
                        param_names.append(p.name)
                    else:
                        param_names.append(str(p))

        for param_name, arg in zip(param_names, call_inst.args, strict=True):
            param_var = Variable(param_name, MIRType.INT)  # Assume INT for now
            value_map[param_var] = arg

        # Clone the callee's CFG
        _cloned_blocks, entry_block, return_blocks = self._clone_function_body(callee, caller, value_map, transformer)

        # Split the call block at the call instruction
        call_idx = call_block.instructions.index(call_inst)
        pre_call = call_block.instructions[:call_idx]
        post_call = call_block.instructions[call_idx + 1 :]

        # Create continuation block for code after the call
        cont_block = BasicBlock(f"{call_block.label}_cont")
        caller.cfg.add_block(cont_block)
        cont_block.instructions = post_call
        cont_block.successors = call_block.successors.copy()

        # Update predecessors of original successors
        for succ in call_block.successors:
            succ.predecessors.remove(call_block)
            succ.predecessors.append(cont_block)

        # Modify call block to jump to inlined entry
        call_block.instructions = [*pre_call, Jump(entry_block.label, call_inst.source_location)]
        call_block.successors = [entry_block]
        entry_block.predecessors.append(call_block)

        # Handle returns from inlined function
        if call_inst.dest:
            # If the call has a destination, we need to merge return values
            return_value_var = call_inst.dest
            for ret_block in return_blocks:
                # Replace return with assignment and jump to continuation
                ret_inst = ret_block.instructions[-1]
                assert isinstance(ret_inst, Return)
                if ret_inst.value:
                    ret_block.instructions[-1] = Copy(return_value_var, ret_inst.value, ret_inst.source_location)
                    ret_block.instructions.append(Jump(cont_block.label, ret_inst.source_location))
                else:
                    ret_block.instructions[-1] = Jump(cont_block.label, ret_inst.source_location)
                ret_block.successors = [cont_block]
                cont_block.predecessors.append(ret_block)
        else:
            # No return value - just jump to continuation
            for ret_block in return_blocks:
                ret_inst = ret_block.instructions[-1]
                source_loc = ret_inst.source_location if hasattr(ret_inst, "source_location") else (0, 0)
                ret_block.instructions[-1] = Jump(cont_block.label, source_loc)
                ret_block.successors = [cont_block]
                cont_block.predecessors.append(ret_block)

        transformer.modified = True
        return True

    def _clone_function_body(
        self,
        callee: MIRFunction,
        caller: MIRFunction,
        value_map: dict[MIRValue, MIRValue],
        transformer: MIRTransformer,
    ) -> tuple[dict[str, BasicBlock], BasicBlock, list[BasicBlock]]:
        """Clone a function's body for inlining.

        Args:
            callee: The function to clone.
            caller: The calling function.
            value_map: Mapping from callee values to caller values.
            transformer: MIR transformer.

        Returns:
            Tuple of (cloned blocks dict, entry block, return blocks list).
        """
        # Create a mapping for blocks
        block_map: dict[BasicBlock, BasicBlock] = {}
        cloned_blocks: dict[str, BasicBlock] = {}

        # First pass: create all blocks
        for old_block in callee.cfg.blocks.values():
            new_label = f"inlined_{callee.name}_{old_block.label}"
            new_block = BasicBlock(new_label)
            caller.cfg.add_block(new_block)
            block_map[old_block] = new_block
            cloned_blocks[new_label] = new_block

        # Map entry block - if not set, assume first block or "entry" label
        if callee.cfg.entry_block:
            entry_block = block_map[callee.cfg.entry_block]
        else:
            # Try to find entry block by label
            entry_block = None
            for old_block in callee.cfg.blocks.values():
                if old_block.label == "entry":
                    entry_block = block_map[old_block]
                    break
            if not entry_block and block_map:
                # Use first block as entry
                entry_block = next(iter(block_map.values()))
            if not entry_block:
                # Create a dummy entry block if empty
                entry_block = BasicBlock("inline_entry")

        assert entry_block is not None, "Entry block must be set"

        # Generate unique temps for the inlined function
        temp_counter = caller._next_temp_id

        def map_value(value: MIRValue) -> MIRValue:
            """Map a value from callee to caller."""
            if value in value_map:
                return value_map[value]
            if isinstance(value, Temp):
                # Create new temp with unique ID
                nonlocal temp_counter
                new_temp = Temp(value.type, temp_counter)
                temp_counter += 1
                caller._next_temp_id = temp_counter
                value_map[value] = new_temp
                return new_temp
            # Constants and other values remain unchanged
            return value

        # Second pass: clone instructions and update CFG
        return_blocks = []
        for old_block, new_block in block_map.items():
            # Clone instructions
            for inst in old_block.instructions:
                cloned_inst = self._clone_instruction(inst, map_value, block_map)
                new_block.instructions.append(cloned_inst)

                # Track return blocks
                if isinstance(cloned_inst, Return):
                    return_blocks.append(new_block)

            # Update successors/predecessors
            for succ in old_block.successors:
                new_succ = block_map[succ]
                new_block.successors.append(new_succ)
                new_succ.predecessors.append(new_block)

        return cloned_blocks, entry_block, return_blocks

    def _clone_instruction(
        self,
        inst: MIRInstruction,
        map_value: Any,
        block_map: dict[BasicBlock, BasicBlock],
    ) -> MIRInstruction:
        """Clone an instruction with value remapping.

        Args:
            inst: The instruction to clone.
            map_value: Function to map values.
            block_map: Mapping from old blocks to new blocks.

        Returns:
            Cloned instruction.
        """
        # Import here to avoid circular dependency
        from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst, Print, StoreVar, UnaryOp

        # Handle each instruction type
        if isinstance(inst, BinaryOp):
            return BinaryOp(
                map_value(inst.dest),
                inst.op,
                map_value(inst.left),
                map_value(inst.right),
                inst.source_location,
            )
        elif isinstance(inst, UnaryOp):
            return UnaryOp(
                map_value(inst.dest),
                inst.op,
                map_value(inst.operand),
                inst.source_location,
            )
        elif isinstance(inst, Copy):
            return Copy(
                map_value(inst.dest),
                map_value(inst.source),
                inst.source_location,
            )
        elif isinstance(inst, LoadConst):
            return LoadConst(
                map_value(inst.dest),
                inst.constant.value if hasattr(inst.constant, "value") else inst.constant,  # Use the constant value
                inst.source_location,
            )
        elif isinstance(inst, StoreVar):
            return StoreVar(
                inst.var,  # Variable names stay the same
                map_value(inst.source),
                inst.source_location,
            )
        elif isinstance(inst, Call):
            return Call(
                map_value(inst.dest) if inst.dest else None,
                inst.func,
                [map_value(arg) for arg in inst.args],
                inst.source_location,
            )
        elif isinstance(inst, Return):
            return Return(
                inst.source_location,
                map_value(inst.value) if inst.value else None,
            )
        elif isinstance(inst, ConditionalJump):
            # Find the blocks that correspond to the labels
            true_block = None
            false_block = None
            for old_b, new_b in block_map.items():
                if old_b.label == inst.true_label:
                    true_block = new_b
                if inst.false_label and old_b.label == inst.false_label:
                    false_block = new_b
            return ConditionalJump(
                map_value(inst.condition),
                true_block.label if true_block else inst.true_label,
                inst.source_location,
                false_block.label if false_block else inst.false_label,
            )
        elif isinstance(inst, Jump):
            # Find the block that corresponds to the label
            target_block = None
            for old_b, new_b in block_map.items():
                if old_b.label == inst.label:
                    target_block = new_b
                    break
            return Jump(
                target_block.label if target_block else inst.label,
                inst.source_location,
            )
        elif isinstance(inst, Phi):
            new_incoming = []
            for value, label in inst.incoming:
                # Find the new label for this block
                new_label = label
                for old_b, new_b in block_map.items():
                    if old_b.label == label:
                        new_label = new_b.label
                        break
                new_incoming.append((map_value(value), new_label))
            return Phi(map_value(inst.dest), new_incoming, inst.source_location)
        elif isinstance(inst, Print):
            return Print(map_value(inst.value), inst.source_location)
        else:
            # For any other instruction types, return as-is
            # This is conservative - may need to extend for new instruction types
            return inst

    def finalize(self) -> None:
        """Finalize the pass after running.

        Cleans up any temporary state.
        """
        self.inlining_depth.clear()

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats
