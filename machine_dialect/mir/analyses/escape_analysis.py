"""Escape analysis for MIR variables.

This module analyzes variable escape behavior to determine which variables
can be safely allocated on the stack instead of the heap, improving memory
efficiency and cache locality.
"""

from dataclasses import dataclass, field
from enum import Enum

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Call,
    Copy,
    MIRInstruction,
    Return,
    SetAttr,
    StoreVar,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Variable
from machine_dialect.mir.optimization_pass import (
    FunctionAnalysisPass,
    PassInfo,
    PassType,
    PreservationLevel,
)


class EscapeState(Enum):
    """Escape state of a variable."""

    NO_ESCAPE = "no_escape"  # Can be stack allocated
    ARG_ESCAPE = "arg_escape"  # Escapes as function argument
    RETURN_ESCAPE = "return_escape"  # Escapes via return
    HEAP_ESCAPE = "heap_escape"  # Stored in heap object
    GLOBAL_ESCAPE = "global_escape"  # Escapes globally


@dataclass
class VariableEscapeInfo:
    """Information about a variable's escape behavior.

    Attributes:
        variable: The variable being analyzed.
        state: Current escape state.
        escape_sites: Instructions where escape occurs.
        aliases: Other variables that alias this one.
        stack_eligible: Whether eligible for stack allocation.
    """

    variable: Variable
    state: EscapeState = EscapeState.NO_ESCAPE
    escape_sites: list[MIRInstruction] = field(default_factory=list)
    aliases: set[Variable] = field(default_factory=set)
    stack_eligible: bool = True

    def mark_escape(self, state: EscapeState, site: MIRInstruction) -> None:
        """Mark variable as escaping.

        Args:
            state: New escape state.
            site: Instruction causing escape.
        """
        # Upgrade escape state (more restrictive wins)
        if state == EscapeState.GLOBAL_ESCAPE or self.state == EscapeState.GLOBAL_ESCAPE:
            self.state = EscapeState.GLOBAL_ESCAPE
            self.stack_eligible = False
        elif state == EscapeState.HEAP_ESCAPE or self.state == EscapeState.HEAP_ESCAPE:
            self.state = EscapeState.HEAP_ESCAPE
            self.stack_eligible = False
        elif state == EscapeState.RETURN_ESCAPE or self.state == EscapeState.RETURN_ESCAPE:
            self.state = EscapeState.RETURN_ESCAPE
            self.stack_eligible = False
        elif state == EscapeState.ARG_ESCAPE or self.state == EscapeState.ARG_ESCAPE:
            self.state = EscapeState.ARG_ESCAPE
            self.stack_eligible = False

        self.escape_sites.append(site)


class EscapeInfo:
    """Container for escape analysis results."""

    def __init__(self) -> None:
        """Initialize escape information."""
        self.variable_info: dict[str, VariableEscapeInfo] = {}
        self.stack_eligible: set[Variable] = set()
        self.escaping_vars: set[Variable] = set()

    def get_info(self, var: Variable) -> VariableEscapeInfo | None:
        """Get escape info for a variable.

        Args:
            var: The variable to query.

        Returns:
            Escape information or None.
        """
        return self.variable_info.get(var.name)

    def is_stack_eligible(self, var: Variable) -> bool:
        """Check if variable can be stack allocated.

        Args:
            var: The variable to check.

        Returns:
            True if stack eligible.
        """
        info = self.get_info(var)
        return info.stack_eligible if info else False

    def does_escape(self, var: Variable) -> bool:
        """Check if variable escapes.

        Args:
            var: The variable to check.

        Returns:
            True if variable escapes.
        """
        info = self.get_info(var)
        return info.state != EscapeState.NO_ESCAPE if info else False


class EscapeAnalysis(FunctionAnalysisPass):
    """Analyze variable escape behavior for stack allocation optimization."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="escape-analysis",
            description="Analyze variable escape behavior",
            pass_type=PassType.ANALYSIS,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def run_on_function(self, function: MIRFunction) -> EscapeInfo:
        """Analyze escape behavior in a function.

        Args:
            function: The function to analyze.

        Returns:
            Escape analysis results.
        """
        escape_info = EscapeInfo()

        # Initialize info for all variables
        self._initialize_variables(function, escape_info)

        # Analyze each block
        for block in function.cfg.blocks.values():
            self._analyze_block(block, escape_info)

        # Propagate escape through aliases
        self._propagate_escapes(escape_info)

        # Collect final results
        self._finalize_results(escape_info)

        return escape_info

    def _initialize_variables(self, function: MIRFunction, escape_info: EscapeInfo) -> None:
        """Initialize escape info for all variables.

        Args:
            function: The function being analyzed.
            escape_info: Escape information to populate.
        """
        # Add local variables
        for var_name in function.locals:
            var = Variable(var_name, MIRType.INT)  # Default to INT for simplicity
            escape_info.variable_info[var_name] = VariableEscapeInfo(variable=var)

        # Parameters are more complex - they're already "from outside"
        # but we track if they escape further
        for param in function.params:
            info = VariableEscapeInfo(variable=param)
            # Parameters themselves don't escape just by existing
            escape_info.variable_info[param.name] = info

    def _analyze_block(self, block: BasicBlock, escape_info: EscapeInfo) -> None:
        """Analyze escape behavior in a block.

        Args:
            block: The block to analyze.
            escape_info: Escape information to update.
        """
        for inst in block.instructions:
            self._analyze_instruction(inst, escape_info)

    def _analyze_instruction(self, inst: MIRInstruction, escape_info: EscapeInfo) -> None:
        """Analyze escape behavior of an instruction.

        Args:
            inst: The instruction to analyze.
            escape_info: Escape information to update.
        """
        # Check for returns
        if isinstance(inst, Return):
            if inst.value and isinstance(inst.value, Variable):
                info = escape_info.variable_info.get(inst.value.name)
                if info:
                    info.mark_escape(EscapeState.RETURN_ESCAPE, inst)

        # Check for function calls
        elif isinstance(inst, Call):
            # Arguments to calls may escape
            for arg in inst.args:
                if isinstance(arg, Variable):
                    info = escape_info.variable_info.get(arg.name)
                    if info:
                        # Conservative: assume args escape
                        # Could be refined with interprocedural analysis
                        info.mark_escape(EscapeState.ARG_ESCAPE, inst)

        # Check for stores to heap objects
        elif isinstance(inst, SetAttr):
            if isinstance(inst.value, Variable):
                info = escape_info.variable_info.get(inst.value.name)
                if info:
                    info.mark_escape(EscapeState.HEAP_ESCAPE, inst)

        # Check for copies (creates aliases)
        elif isinstance(inst, Copy):
            if isinstance(inst.source, Variable) and isinstance(inst.dest, Variable):
                src_info = escape_info.variable_info.get(inst.source.name)
                dest_info = escape_info.variable_info.get(inst.dest.name)
                if src_info and dest_info:
                    # Track aliasing
                    src_info.aliases.add(inst.dest)
                    dest_info.aliases.add(inst.source)

        # Check for stores to global/external locations
        elif isinstance(inst, StoreVar):
            if isinstance(inst.source, Variable):
                info = escape_info.variable_info.get(inst.source.name)
                if info:
                    # Storing to another variable might be escape
                    # Conservative for now
                    if inst.var.name not in escape_info.variable_info:
                        # Storing to unknown location
                        info.mark_escape(EscapeState.GLOBAL_ESCAPE, inst)

    def _propagate_escapes(self, escape_info: EscapeInfo) -> None:
        """Propagate escape states through aliases.

        Args:
            escape_info: Escape information to update.
        """
        # If a variable escapes, all its aliases escape
        changed = True
        while changed:
            changed = False
            for var_info in escape_info.variable_info.values():
                if var_info.state != EscapeState.NO_ESCAPE:
                    for alias in var_info.aliases:
                        alias_info = escape_info.variable_info.get(alias.name)
                        if alias_info and alias_info.state == EscapeState.NO_ESCAPE:
                            alias_info.state = var_info.state
                            alias_info.stack_eligible = False
                            changed = True

    def _finalize_results(self, escape_info: EscapeInfo) -> None:
        """Finalize escape analysis results.

        Args:
            escape_info: Escape information to finalize.
        """
        for var_info in escape_info.variable_info.values():
            if var_info.stack_eligible:
                escape_info.stack_eligible.add(var_info.variable)
            else:
                escape_info.escaping_vars.add(var_info.variable)

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
