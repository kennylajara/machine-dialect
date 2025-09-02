"""Tail call optimization pass.

This module implements tail call optimization to transform recursive calls
in tail position into jumps, eliminating stack growth for tail-recursive functions.
"""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import Call, Copy, Return
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import (
    ModulePass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class TailCallOptimization(ModulePass):
    """Tail call optimization pass.

    This pass identifies function calls in tail position and marks them
    for optimization. A call is in tail position if:
    1. It's immediately followed by a return of its result
    2. Or it's the last instruction before a return (for void calls)

    The actual transformation to jumps happens during bytecode generation.
    """

    def __init__(self) -> None:
        """Initialize the tail call optimization pass."""
        super().__init__()
        self.stats = {
            "tail_calls_found": 0,
            "functions_optimized": 0,
            "recursive_tail_calls": 0,
        }

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="tail-call",
            description="Optimize tail calls into jumps",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.CFG,
        )

    def finalize(self) -> None:
        """Finalize the pass after running.

        Override from base class - no special finalization needed.
        """
        pass

    def run_on_module(self, module: MIRModule) -> bool:
        """Run tail call optimization on a module.

        Args:
            module: The module to optimize.

        Returns:
            True if the module was modified.
        """
        modified = False

        # Process each function
        for func_name, function in module.functions.items():
            if self._optimize_tail_calls_in_function(function, func_name):
                modified = True
                self.stats["functions_optimized"] += 1

        return modified

    def _optimize_tail_calls_in_function(self, function: MIRFunction, func_name: str) -> bool:
        """Optimize tail calls in a single function.

        Args:
            function: The function to optimize.
            func_name: Name of the function (for recursive call detection).

        Returns:
            True if the function was modified.
        """
        modified = False

        # Process each basic block
        for block in function.cfg.blocks.values():
            if self._optimize_tail_calls_in_block(block, func_name):
                modified = True

        return modified

    def _optimize_tail_calls_in_block(self, block: BasicBlock, func_name: str) -> bool:
        """Optimize tail calls in a basic block.

        Args:
            block: The basic block to process.
            func_name: Name of the containing function.

        Returns:
            True if the block was modified.
        """
        modified = False
        instructions = block.instructions

        # Look for tail call patterns
        i = 0
        while i < len(instructions):
            inst = instructions[i]

            # Pattern 1: Call followed by Return of its result
            if isinstance(inst, Call) and not inst.is_tail_call:
                if i + 1 < len(instructions):
                    next_inst = instructions[i + 1]

                    # Direct return of call result
                    if isinstance(next_inst, Return) and next_inst.value == inst.dest:
                        inst.is_tail_call = True
                        self.stats["tail_calls_found"] += 1
                        modified = True

                        # Check if it's a recursive call
                        if hasattr(inst.func, "name") and inst.func.name == func_name:
                            self.stats["recursive_tail_calls"] += 1

                    # Call result copied to variable, then returned
                    elif i + 2 < len(instructions) and isinstance(next_inst, Copy):
                        third_inst = instructions[i + 2]
                        if (
                            isinstance(third_inst, Return)
                            and next_inst.source == inst.dest
                            and third_inst.value == next_inst.dest
                        ):
                            inst.is_tail_call = True
                            self.stats["tail_calls_found"] += 1
                            modified = True

                            # Check if it's a recursive call
                            if hasattr(inst.func, "name") and inst.func.name == func_name:
                                self.stats["recursive_tail_calls"] += 1

            # Pattern 2: Void call followed by return
            elif isinstance(inst, Call) and inst.dest is None and not inst.is_tail_call:
                if i + 1 < len(instructions):
                    next_inst = instructions[i + 1]
                    if isinstance(next_inst, Return) and next_inst.value is None:
                        inst.is_tail_call = True
                        self.stats["tail_calls_found"] += 1
                        modified = True

                        # Check if it's a recursive call
                        if hasattr(inst.func, "name") and inst.func.name == func_name:
                            self.stats["recursive_tail_calls"] += 1

            i += 1

        return modified

    def _is_tail_position(self, block: BasicBlock, instruction_index: int) -> bool:
        """Check if an instruction is in tail position.

        An instruction is in tail position if all paths from it lead
        directly to a return without any other side effects.

        Args:
            block: The basic block containing the instruction.
            instruction_index: Index of the instruction in the block.

        Returns:
            True if the instruction is in tail position.
        """
        # Simple check: instruction is followed only by a return
        instructions = block.instructions

        # Check remaining instructions after this one
        for i in range(instruction_index + 1, len(instructions)):
            inst = instructions[i]

            # Return is ok
            if isinstance(inst, Return):
                return True

            # Copy is ok if it's just moving the result
            if isinstance(inst, Copy):
                continue

            # Any other instruction means not in tail position
            return False

        # If we reach end of block without return, check if block
        # has a single successor that starts with return
        # (This would require more complex CFG analysis)

        return False

    def get_statistics(self) -> dict[str, int]:
        """Get optimization statistics.

        Returns:
            Dictionary of statistics.
        """
        return self.stats
