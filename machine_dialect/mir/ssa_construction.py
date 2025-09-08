"""SSA (Static Single Assignment) construction for MIR.

This module implements SSA construction with dominance frontier calculation
and phi node insertion for the MIR representation.
"""

from collections import OrderedDict, defaultdict

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import Copy, LoadConst, LoadVar, MIRInstruction, Phi, StoreVar
from machine_dialect.mir.mir_values import Variable


class DominanceInfo:
    """Dominance information for a control flow graph."""

    def __init__(self, cfg: CFG) -> None:
        """Initialize dominance information.

        Args:
            cfg: The control flow graph to analyze.
        """
        self.cfg = cfg
        self.dominators: dict[BasicBlock, set[BasicBlock]] = {}
        self.immediate_dominators: dict[BasicBlock, BasicBlock | None] = {}
        self.dominance_frontier: dict[BasicBlock, set[BasicBlock]] = {}
        self.dominator_tree_children: dict[BasicBlock, set[BasicBlock]] = defaultdict(set)

        self._compute_dominators()
        self._compute_immediate_dominators()
        self._compute_dominance_frontier()

    def _compute_dominators(self) -> None:
        """Compute dominators for all blocks using iterative algorithm."""
        entry = self.cfg.entry_block
        if not entry:
            return

        # Initialize dominators
        blocks = list(self.cfg.blocks.values())
        self.dominators[entry] = {entry}

        # All other blocks are initially dominated by all blocks
        for block in blocks:
            if block != entry:
                self.dominators[block] = set(blocks)

        # Iterate until fixed point
        changed = True
        while changed:
            changed = False
            for block in blocks:
                if block == entry:
                    continue

                # Compute new dominators
                new_doms = set(blocks)
                for pred in block.predecessors:
                    if pred in self.dominators:
                        new_doms &= self.dominators[pred]
                new_doms.add(block)

                # Check if changed
                if new_doms != self.dominators[block]:
                    self.dominators[block] = new_doms
                    changed = True

    def _compute_immediate_dominators(self) -> None:
        """Compute immediate dominators from dominator sets."""
        for block in self.dominators:
            # Immediate dominator is the unique dominator that doesn't
            # dominate any other dominators
            doms = self.dominators[block] - {block}
            if not doms:
                self.immediate_dominators[block] = None
                continue

            # Find the immediate dominator
            idom = None
            for dom in doms:
                # Check if dom dominates any other dominator
                is_immediate = True
                for other in doms:
                    if other != dom and dom in self.dominators.get(other, set()):
                        is_immediate = False
                        break
                if is_immediate:
                    idom = dom
                    break

            self.immediate_dominators[block] = idom
            if idom:
                self.dominator_tree_children[idom].add(block)

    def _compute_dominance_frontier(self) -> None:
        """Compute dominance frontier for all blocks."""
        # Initialize empty frontiers
        for block in self.dominators:
            self.dominance_frontier[block] = set()

        # For each block
        for block in self.dominators:
            # Check each successor
            for succ in block.successors:
                # Walk up dominator tree from block
                runner: BasicBlock | None = block
                while runner and runner != self.immediate_dominators.get(succ):
                    self.dominance_frontier[runner].add(succ)
                    runner = self.immediate_dominators.get(runner)

    def dominates(self, a: BasicBlock, b: BasicBlock) -> bool:
        """Check if block a dominates block b.

        Args:
            a: Potential dominator block.
            b: Block to check.

        Returns:
            True if a dominates b.
        """
        return a in self.dominators.get(b, set())

    def strictly_dominates(self, a: BasicBlock, b: BasicBlock) -> bool:
        """Check if block a strictly dominates block b.

        Args:
            a: Potential dominator block.
            b: Block to check.

        Returns:
            True if a strictly dominates b (dominates and a != b).
        """
        return a != b and self.dominates(a, b)


class SSAConstructor:
    """Constructs SSA form for MIR functions."""

    def __init__(self, function: MIRFunction) -> None:
        """Initialize SSA constructor.

        Args:
            function: The function to convert to SSA form.
        """
        self.function = function
        self.dominance = DominanceInfo(function.cfg)
        self.variable_definitions: dict[Variable, set[BasicBlock]] = defaultdict(set)
        self.variable_uses: dict[Variable, set[BasicBlock]] = defaultdict(set)
        self.phi_nodes: dict[tuple[BasicBlock, Variable], Phi] = {}
        self.variable_stacks: dict[Variable, list[Variable]] = defaultdict(list)
        self.version_counters: dict[str, int] = defaultdict(int)

    def construct_ssa(self) -> None:
        """Convert the function to SSA form."""
        self._collect_variable_info()
        self._insert_phi_nodes()
        self._rename_variables()

    def _collect_variable_info(self) -> None:
        """Collect information about variable definitions and uses."""
        for block in self.function.cfg.blocks.values():
            for inst in block.instructions:
                # Check for variable definitions
                for def_val in inst.get_defs():
                    if isinstance(def_val, Variable):
                        self.variable_definitions[def_val].add(block)

                # Check for variable uses
                for use_val in inst.get_uses():
                    if isinstance(use_val, Variable):
                        self.variable_uses[use_val].add(block)

    def _insert_phi_nodes(self) -> None:
        """Insert phi nodes at dominance frontiers."""
        # For each variable
        for var in self.variable_definitions:
            # Get blocks where variable is defined
            def_blocks = self.variable_definitions[var]

            # Compute iterated dominance frontier
            worklist = list(def_blocks)
            phi_blocks = set()
            processed = set()

            while worklist:
                block = worklist.pop()
                if block in processed:
                    continue
                processed.add(block)

                # Add phi nodes at dominance frontier
                for df_block in self.dominance.dominance_frontier.get(block, set()):
                    if df_block not in phi_blocks:
                        phi_blocks.add(df_block)

                        # Create phi node
                        phi_var = self._new_version(var)
                        # TODO: Review if (0, 0) is the best approach for generated phi nodes' source location
                        phi = Phi(phi_var, [], (0, 0))  # Default source location for generated phi nodes

                        # Insert phi in phi_nodes list
                        df_block.phi_nodes.append(phi)
                        self.phi_nodes[(df_block, var)] = phi

                        # Phi node is also a definition
                        if df_block not in def_blocks:
                            worklist.append(df_block)

    def _rename_variables(self) -> None:
        """Rename variables to SSA form."""
        entry = self.function.cfg.entry_block
        if entry:
            self._rename_block(entry, set())

    def _rename_block(self, block: BasicBlock, visited: set[BasicBlock]) -> None:
        """Rename variables in a block and its dominated blocks.

        Args:
            block: The block to process.
            visited: Set of already visited blocks.
        """
        if block in visited:
            return
        visited.add(block)

        # Save stack state
        stack_state: dict[Variable, int] = {}
        for var in self.variable_stacks:
            stack_state[var] = len(self.variable_stacks[var])

        # Process phi nodes first
        for phi in block.phi_nodes:
            # Find original variable for this phi
            for (phi_block, var), stored_phi in self.phi_nodes.items():
                if phi_block == block and stored_phi == phi:
                    # Push new version (phi.dest is MIRValue but should be Variable)
                    if isinstance(phi.dest, Variable):
                        self.variable_stacks[var].append(phi.dest)
                    break

        # Rebuild instruction list, preserving LoadConst and other non-Variable instructions
        new_instructions: list[MIRInstruction] = []
        temp_definitions = OrderedDict()  # Track LoadConst for ordering

        # Rename uses and definitions
        for inst in block.instructions:
            if isinstance(inst, Phi):
                continue  # Already handled in phi_nodes list

            # Special handling for LoadConst - preserve as-is
            if isinstance(inst, LoadConst):
                # LoadConst defines a Temp, not a Variable, so don't rename
                # Just preserve the instruction
                new_instructions.append(inst)
                if hasattr(inst.dest, "name"):
                    temp_definitions[inst.dest] = inst
                continue

            # Rename uses for Variable-based instructions
            if isinstance(inst, StoreVar):
                # Special case: StoreVar uses source, defines var
                if isinstance(inst.source, Variable):
                    if self.variable_stacks[inst.source]:
                        inst.source = self.variable_stacks[inst.source][-1]
            elif isinstance(inst, LoadVar):
                # Special case: LoadVar uses var, defines dest
                if self.variable_stacks[inst.var]:
                    inst.var = self.variable_stacks[inst.var][-1]
            else:
                # General case: rename all uses
                for use_val in inst.get_uses():
                    if isinstance(use_val, Variable):
                        if self.variable_stacks[use_val]:
                            inst.replace_use(use_val, self.variable_stacks[use_val][-1])

            # Rename definitions
            for def_val in inst.get_defs():
                if isinstance(def_val, Variable):
                    new_var = self._new_version(def_val)
                    if isinstance(inst, StoreVar):
                        inst.var = new_var
                    elif isinstance(inst, Copy) and inst.dest == def_val:
                        inst.dest = new_var
                    # Push new version
                    self.variable_stacks[def_val].append(new_var)

            new_instructions.append(inst)

        # Replace the instruction list with the rebuilt one
        block.instructions = new_instructions

        # Update phi nodes in successors
        for succ in block.successors:
            # Phi nodes are now in the phi_nodes list, not instructions
            for phi in succ.phi_nodes:
                # Find original variable for this phi
                for (phi_block, var), stored_phi in self.phi_nodes.items():
                    if phi_block == succ and stored_phi == phi:
                        # Add incoming value from this block
                        if self.variable_stacks[var]:
                            phi.add_incoming(
                                self.variable_stacks[var][-1],
                                block.label,
                            )
                        break

        # Process dominated blocks
        for child in self.dominance.dominator_tree_children.get(block, set()):
            self._rename_block(child, visited)

        # Restore stack state
        for var, old_size in stack_state.items():
            while len(self.variable_stacks[var]) > old_size:
                self.variable_stacks[var].pop()

    def _new_version(self, var: Variable) -> Variable:
        """Create a new SSA version of a variable.

        Args:
            var: The original variable.

        Returns:
            A new versioned variable.
        """
        base_name = var.name
        version = self.version_counters[base_name]
        self.version_counters[base_name] += 1

        # Create new variable with version number
        new_var = Variable(base_name, var.type, version=version)
        return new_var


def construct_ssa(function: MIRFunction) -> None:
    """Convert a MIR function to SSA form.

    Args:
        function: The function to convert.
    """
    constructor = SSAConstructor(function)
    constructor.construct_ssa()
