"""Alias analysis for MIR.

This module provides alias analysis to determine when different variables
may refer to the same memory location, supporting optimizations like
escape analysis and redundant load elimination.
"""

from dataclasses import dataclass, field
from enum import Enum

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Copy,
    GetAttr,
    LoadVar,
    MIRInstruction,
    Phi,
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


class AliasType(Enum):
    """Type of aliasing relationship."""

    NO_ALIAS = "no_alias"  # Definitely different locations
    MAY_ALIAS = "may_alias"  # Might be the same location
    MUST_ALIAS = "must_alias"  # Definitely the same location
    PARTIAL_ALIAS = "partial_alias"  # Overlapping but not identical


@dataclass
class AliasSet:
    """Set of potentially aliasing values.

    Attributes:
        members: Values that may alias each other.
        alias_type: Type of aliasing relationship.
        attributes: Attributes accessed on these values.
    """

    members: set[Variable] = field(default_factory=set)
    alias_type: AliasType = AliasType.MAY_ALIAS
    attributes: set[str] = field(default_factory=set)

    def add_member(self, var: Variable) -> None:
        """Add a variable to the alias set.

        Args:
            var: Variable to add.
        """
        self.members.add(var)

    def merge(self, other: "AliasSet") -> None:
        """Merge another alias set into this one.

        Args:
            other: Alias set to merge.
        """
        self.members.update(other.members)
        self.attributes.update(other.attributes)
        # Downgrade alias type to be conservative
        if other.alias_type == AliasType.MAY_ALIAS or self.alias_type == AliasType.MAY_ALIAS:
            self.alias_type = AliasType.MAY_ALIAS


class AliasInfo:
    """Container for alias analysis results."""

    def __init__(self) -> None:
        """Initialize alias information."""
        self.alias_sets: list[AliasSet] = []
        self.var_to_set: dict[str, AliasSet] = {}

    def get_aliases(self, var: Variable) -> set[Variable]:
        """Get all variables that may alias with the given variable.

        Args:
            var: Variable to query.

        Returns:
            Set of potentially aliasing variables.
        """
        alias_set = self.var_to_set.get(var.name)
        if alias_set:
            return alias_set.members - {var}
        return set()

    def may_alias(self, var1: Variable, var2: Variable) -> bool:
        """Check if two variables may alias.

        Args:
            var1: First variable.
            var2: Second variable.

        Returns:
            True if variables may alias.
        """
        set1 = self.var_to_set.get(var1.name)
        set2 = self.var_to_set.get(var2.name)
        return set1 is set2 if (set1 and set2) else False

    def must_alias(self, var1: Variable, var2: Variable) -> bool:
        """Check if two variables must alias.

        Args:
            var1: First variable.
            var2: Second variable.

        Returns:
            True if variables must alias.
        """
        set1 = self.var_to_set.get(var1.name)
        set2 = self.var_to_set.get(var2.name)
        if set1 is set2 and set1:
            return set1.alias_type == AliasType.MUST_ALIAS
        return False


class AliasAnalysis(FunctionAnalysisPass):
    """Analyze pointer aliasing relationships."""

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="alias-analysis",
            description="Analyze variable aliasing relationships",
            pass_type=PassType.ANALYSIS,
            requires=[],
            preserves=PreservationLevel.ALL,
        )

    def run_on_function(self, function: MIRFunction) -> AliasInfo:
        """Analyze aliasing in a function.

        Args:
            function: The function to analyze.

        Returns:
            Alias analysis results.
        """
        alias_info = AliasInfo()

        # Initialize each variable in its own set
        self._initialize_variables(function, alias_info)

        # Analyze instructions to find aliasing
        for block in function.cfg.blocks.values():
            self._analyze_block(block, alias_info)

        # Handle phi nodes specially
        self._analyze_phi_nodes(function, alias_info)

        return alias_info

    def _initialize_variables(self, function: MIRFunction, alias_info: AliasInfo) -> None:
        """Initialize alias sets for all variables.

        Args:
            function: The function being analyzed.
            alias_info: Alias information to populate.
        """
        # Create initial alias sets for locals
        for var_name in function.locals:
            var = Variable(var_name, MIRType.INT)
            alias_set = AliasSet()
            alias_set.add_member(var)
            alias_set.alias_type = AliasType.NO_ALIAS  # Initially no aliases
            alias_info.alias_sets.append(alias_set)
            alias_info.var_to_set[var_name] = alias_set

        # Create initial sets for parameters
        for param in function.params:
            alias_set = AliasSet()
            alias_set.add_member(param)
            # Parameters may alias with external data
            alias_set.alias_type = AliasType.MAY_ALIAS
            alias_info.alias_sets.append(alias_set)
            alias_info.var_to_set[param.name] = alias_set

    def _analyze_block(self, block: BasicBlock, alias_info: AliasInfo) -> None:
        """Analyze aliasing in a block.

        Args:
            block: The block to analyze.
            alias_info: Alias information to update.
        """
        for inst in block.instructions:
            self._analyze_instruction(inst, alias_info)

    def _analyze_instruction(self, inst: MIRInstruction, alias_info: AliasInfo) -> None:
        """Analyze aliasing effects of an instruction.

        Args:
            inst: The instruction to analyze.
            alias_info: Alias information to update.
        """
        # Copy creates must-alias relationship
        if isinstance(inst, Copy):
            if isinstance(inst.source, Variable) and isinstance(inst.dest, Variable):
                self._merge_alias_sets(inst.source, inst.dest, AliasType.MUST_ALIAS, alias_info)

        # Load creates may-alias relationship
        elif isinstance(inst, LoadVar):
            if isinstance(inst.dest, Variable) and isinstance(inst.var, Variable):
                self._merge_alias_sets(inst.var, inst.dest, AliasType.MAY_ALIAS, alias_info)

        # Store can create aliasing through memory
        elif isinstance(inst, StoreVar):
            if isinstance(inst.source, Variable) and isinstance(inst.var, Variable):
                self._merge_alias_sets(inst.var, inst.source, AliasType.MAY_ALIAS, alias_info)

        # GetAttr tracks attribute access
        elif isinstance(inst, GetAttr):
            if isinstance(inst.obj, Variable) and isinstance(inst.dest, Variable):
                obj_set = alias_info.var_to_set.get(inst.obj.name)
                if obj_set:
                    obj_set.attributes.add(inst.attr)
                # Result may alias with the field
                self._merge_alias_sets(inst.obj, inst.dest, AliasType.PARTIAL_ALIAS, alias_info)

        # SetAttr tracks attribute modification
        elif isinstance(inst, SetAttr):
            if isinstance(inst.obj, Variable):
                obj_set = alias_info.var_to_set.get(inst.obj.name)
                if obj_set:
                    obj_set.attributes.add(inst.attr)

    def _merge_alias_sets(
        self,
        var1: Variable,
        var2: Variable,
        alias_type: AliasType,
        alias_info: AliasInfo,
    ) -> None:
        """Merge alias sets for two variables.

        Args:
            var1: First variable.
            var2: Second variable.
            alias_type: Type of aliasing.
            alias_info: Alias information to update.
        """
        set1 = alias_info.var_to_set.get(var1.name)
        set2 = alias_info.var_to_set.get(var2.name)

        if not set1 and not set2:
            # Create new set for both
            new_set = AliasSet()
            new_set.add_member(var1)
            new_set.add_member(var2)
            new_set.alias_type = alias_type
            alias_info.alias_sets.append(new_set)
            alias_info.var_to_set[var1.name] = new_set
            alias_info.var_to_set[var2.name] = new_set
        elif set1 and not set2:
            # Add var2 to set1
            set1.add_member(var2)
            if alias_type == AliasType.MAY_ALIAS or set1.alias_type != alias_type:
                set1.alias_type = AliasType.MAY_ALIAS
            alias_info.var_to_set[var2.name] = set1
        elif not set1 and set2:
            # Add var1 to set2
            set2.add_member(var1)
            if alias_type == AliasType.MAY_ALIAS or set2.alias_type != alias_type:
                set2.alias_type = AliasType.MAY_ALIAS
            alias_info.var_to_set[var1.name] = set2
        elif set1 and set2 and set1 is not set2:
            # Merge sets
            set1.merge(set2)
            if alias_type == AliasType.MAY_ALIAS:
                set1.alias_type = AliasType.MAY_ALIAS
            # Update all members of set2 to point to set1
            for member in set2.members:
                alias_info.var_to_set[member.name] = set1
            # Remove set2 from list
            alias_info.alias_sets.remove(set2)

    def _analyze_phi_nodes(self, function: MIRFunction, alias_info: AliasInfo) -> None:
        """Analyze phi nodes for aliasing.

        Args:
            function: The function being analyzed.
            alias_info: Alias information to update.
        """
        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, Phi):
                    # All phi inputs may alias with the output
                    if isinstance(inst.dest, Variable):
                        for value, _ in inst.incoming:
                            if isinstance(value, Variable):
                                self._merge_alias_sets(
                                    inst.dest,
                                    value,
                                    AliasType.MAY_ALIAS,
                                    alias_info,
                                )

    def finalize(self) -> None:
        """Finalize the pass."""
        pass
