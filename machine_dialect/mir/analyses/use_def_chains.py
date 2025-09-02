"""Use-def and def-use chain analysis for MIR.

This module builds explicit use-def and def-use chains from the SSA form,
enabling efficient queries for optimization passes.
"""

from collections import defaultdict
from dataclasses import dataclass

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import MIRInstruction
from machine_dialect.mir.mir_values import MIRValue, Temp, Variable
from machine_dialect.mir.optimization_pass import (
    FunctionAnalysisPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


@dataclass
class UseDefInfo:
    """Use-def information for a value.

    Attributes:
        value: The MIR value.
        definition: Instruction that defines this value.
        uses: List of instructions that use this value.
        defining_block: Block containing the definition.
        use_blocks: Blocks containing uses.
    """

    value: MIRValue
    definition: MIRInstruction | None
    uses: list[MIRInstruction]
    defining_block: BasicBlock | None
    use_blocks: list[BasicBlock]


class UseDefChains:
    """Container for use-def and def-use chains."""

    def __init__(self) -> None:
        """Initialize use-def chains."""
        # Map from value to its use-def info
        self.use_def_map: dict[MIRValue, UseDefInfo] = {}
        # Map from instruction to values it defines
        self.inst_defs: dict[MIRInstruction, list[MIRValue]] = defaultdict(list)
        # Map from instruction to values it uses
        self.inst_uses: dict[MIRInstruction, list[MIRValue]] = defaultdict(list)

    def get_definition(self, value: MIRValue) -> MIRInstruction | None:
        """Get the instruction that defines a value.

        Args:
            value: The value to query.

        Returns:
            Defining instruction or None.
        """
        info = self.use_def_map.get(value)
        return info.definition if info else None

    def get_uses(self, value: MIRValue) -> list[MIRInstruction]:
        """Get instructions that use a value.

        Args:
            value: The value to query.

        Returns:
            List of using instructions.
        """
        info = self.use_def_map.get(value)
        return info.uses if info else []

    def get_defined_values(self, inst: MIRInstruction) -> list[MIRValue]:
        """Get values defined by an instruction.

        Args:
            inst: The instruction to query.

        Returns:
            List of defined values.
        """
        return self.inst_defs.get(inst, [])

    def get_used_values(self, inst: MIRInstruction) -> list[MIRValue]:
        """Get values used by an instruction.

        Args:
            inst: The instruction to query.

        Returns:
            List of used values.
        """
        return self.inst_uses.get(inst, [])

    def is_dead(self, value: MIRValue) -> bool:
        """Check if a value is dead (has no uses).

        Args:
            value: The value to check.

        Returns:
            True if the value has no uses.
        """
        info = self.use_def_map.get(value)
        return info is None or len(info.uses) == 0

    def has_single_use(self, value: MIRValue) -> bool:
        """Check if a value has exactly one use.

        Args:
            value: The value to check.

        Returns:
            True if the value has exactly one use.
        """
        info = self.use_def_map.get(value)
        return info is not None and len(info.uses) == 1

    def get_num_uses(self, value: MIRValue) -> int:
        """Get the number of uses of a value.

        Args:
            value: The value to check.

        Returns:
            Number of uses.
        """
        info = self.use_def_map.get(value)
        return len(info.uses) if info else 0


class UseDefChainsAnalysis(FunctionAnalysisPass):
    """Analysis pass that builds use-def chains."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="use-def-chains",
            description="Build use-def and def-use chains",
            pass_type=PassType.ANALYSIS,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def run_on_function(self, function: MIRFunction) -> UseDefChains:
        """Build use-def chains for a function.

        Args:
            function: The function to analyze.

        Returns:
            Use-def chains.
        """
        chains = UseDefChains()

        # Process all blocks
        for block in function.cfg.blocks.values():
            # Process phi nodes
            for phi in block.phi_nodes:
                self._process_instruction(phi, block, chains)

            # Process regular instructions
            for inst in block.instructions:
                self._process_instruction(inst, block, chains)

        return chains

    def _process_instruction(
        self,
        inst: MIRInstruction,
        block: BasicBlock,
        chains: UseDefChains,
    ) -> None:
        """Process a single instruction.

        Args:
            inst: Instruction to process.
            block: Containing block.
            chains: Chains to update.
        """
        # Process definitions
        for def_val in inst.get_defs():
            if isinstance(def_val, Variable | Temp):
                # Create or update use-def info
                if def_val not in chains.use_def_map:
                    chains.use_def_map[def_val] = UseDefInfo(
                        value=def_val,
                        definition=inst,
                        uses=[],
                        defining_block=block,
                        use_blocks=[],
                    )
                else:
                    # Update definition (for variables that may be redefined)
                    chains.use_def_map[def_val].definition = inst
                    chains.use_def_map[def_val].defining_block = block

                # Record instruction's definitions
                chains.inst_defs[inst].append(def_val)

        # Process uses
        for use_val in inst.get_uses():
            if isinstance(use_val, Variable | Temp):
                # Create use-def info if needed
                if use_val not in chains.use_def_map:
                    chains.use_def_map[use_val] = UseDefInfo(
                        value=use_val,
                        definition=None,  # No definition found yet
                        uses=[],
                        defining_block=None,
                        use_blocks=[],
                    )

                # Add this instruction as a use
                chains.use_def_map[use_val].uses.append(inst)
                if block not in chains.use_def_map[use_val].use_blocks:
                    chains.use_def_map[use_val].use_blocks.append(block)

                # Record instruction's uses
                chains.inst_uses[inst].append(use_val)

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
