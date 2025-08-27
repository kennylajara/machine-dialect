"""Basic Blocks and Control Flow Graph.

This module implements basic blocks (sequences of instructions with single
entry and exit points) and the control flow graph that connects them.
"""

from .mir_instructions import ConditionalJump, Jump, Label, MIRInstruction, Phi, Return


class BasicBlock:
    """A basic block in the control flow graph.

    A basic block is a sequence of instructions with:
    - Single entry point (at the beginning)
    - Single exit point (at the end)
    - No branches except at the end
    """

    def __init__(self, label: str) -> None:
        """Initialize a basic block.

        Args:
            label: The block's label.
        """
        self.label = label
        self.instructions: list[MIRInstruction] = []
        self.phi_nodes: list[Phi] = []
        self.predecessors: list[BasicBlock] = []
        self.successors: list[BasicBlock] = []

    def add_instruction(self, inst: MIRInstruction) -> None:
        """Add an instruction to the block.

        Args:
            inst: The instruction to add.
        """
        if isinstance(inst, Phi):
            self.phi_nodes.append(inst)
        else:
            self.instructions.append(inst)

    def add_predecessor(self, pred: "BasicBlock") -> None:
        """Add a predecessor block.

        Args:
            pred: The predecessor block.
        """
        if pred not in self.predecessors:
            self.predecessors.append(pred)
            pred.successors.append(self)

    def add_successor(self, succ: "BasicBlock") -> None:
        """Add a successor block.

        Args:
            succ: The successor block.
        """
        if succ not in self.successors:
            self.successors.append(succ)
            succ.predecessors.append(self)

    def get_terminator(self) -> MIRInstruction | None:
        """Get the terminator instruction (last instruction if it's a branch/return).

        Returns:
            The terminator instruction or None.
        """
        if not self.instructions:
            return None
        last = self.instructions[-1]
        if isinstance(last, Jump | ConditionalJump | Return):
            return last
        return None

    def is_terminated(self) -> bool:
        """Check if the block has a terminator.

        Returns:
            True if the block ends with a terminator.
        """
        return self.get_terminator() is not None

    def __str__(self) -> str:
        """Return string representation of the block."""
        lines = [f"{self.label}:"]

        # Phi nodes come first
        for phi in self.phi_nodes:
            lines.append(f"  {phi}")

        # Then regular instructions
        for inst in self.instructions:
            if not isinstance(inst, Label):  # Labels are part of block headers
                lines.append(f"  {inst}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return debug representation."""
        pred_labels = [p.label for p in self.predecessors]
        succ_labels = [s.label for s in self.successors]
        return f"BasicBlock({self.label}, preds={pred_labels}, succs={succ_labels})"


class CFG:
    """Control Flow Graph.

    The CFG represents the control flow structure of a function as a
    directed graph of basic blocks.
    """

    def __init__(self) -> None:
        """Initialize a control flow graph."""
        self.blocks: dict[str, BasicBlock] = {}
        self.entry_block: BasicBlock | None = None
        self.exit_block: BasicBlock | None = None
        self.dominators: dict[BasicBlock, set[BasicBlock]] = {}
        self.dominance_frontiers: dict[BasicBlock, list[BasicBlock]] = {}
        self._next_label_id = 0

    def get_or_create_block(self, label: str) -> BasicBlock:
        """Get a block by label, creating it if necessary.

        Args:
            label: The block label.

        Returns:
            The basic block.
        """
        if label not in self.blocks:
            self.blocks[label] = BasicBlock(label)
        return self.blocks[label]

    def add_block(self, block: BasicBlock) -> None:
        """Add a block to the CFG.

        Args:
            block: The block to add.
        """
        self.blocks[block.label] = block

    def set_entry_block(self, block: BasicBlock) -> None:
        """Set the entry block of the CFG.

        Args:
            block: The entry block.
        """
        self.entry_block = block

    def get_block(self, label: str) -> BasicBlock | None:
        """Get a block by label.

        Args:
            label: The block label.

        Returns:
            The block or None if not found.
        """
        return self.blocks.get(label)

    def connect(self, from_block: BasicBlock, to_block: BasicBlock) -> None:
        """Connect two blocks.

        Args:
            from_block: Source block.
            to_block: Target block.
        """
        from_block.add_successor(to_block)

    def get_predecessors(self, block: BasicBlock) -> list[BasicBlock]:
        """Get predecessors of a block.

        Args:
            block: The block.

        Returns:
            List of predecessor blocks.
        """
        return block.predecessors

    def get_successors(self, block: BasicBlock) -> list[BasicBlock]:
        """Get successors of a block.

        Args:
            block: The block.

        Returns:
            List of successor blocks.
        """
        return block.successors

    def generate_label(self, prefix: str = "L") -> str:
        """Generate a unique label.

        Args:
            prefix: Label prefix.

        Returns:
            A unique label.
        """
        label = f"{prefix}{self._next_label_id}"
        self._next_label_id += 1
        return label

    def connect_blocks(self, from_label: str, to_label: str) -> None:
        """Connect two blocks by label.

        Args:
            from_label: Source block label.
            to_label: Target block label.
        """
        from_block = self.get_or_create_block(from_label)
        to_block = self.get_or_create_block(to_label)
        from_block.add_successor(to_block)

    def find_exit_blocks(self) -> list[BasicBlock]:
        """Find all exit blocks (blocks with return instructions).

        Returns:
            List of exit blocks.
        """
        exit_blocks = []
        for block in self.blocks.values():
            terminator = block.get_terminator()
            if isinstance(terminator, Return):
                exit_blocks.append(block)
        return exit_blocks

    def compute_dominance(self) -> None:
        """Compute dominance relationships for all blocks.

        A block X dominates block Y if all paths from entry to Y go through X.
        Stores results in self.dominators.
        """
        if not self.entry_block:
            return

        # Initialize dominators - block -> set of dominators
        self.dominators = {}
        all_blocks = set(self.blocks.values())

        # Entry block is only dominated by itself
        self.dominators[self.entry_block] = {self.entry_block}

        # All other blocks are initially dominated by all blocks
        for block in all_blocks:
            if block != self.entry_block:
                self.dominators[block] = all_blocks.copy()

        # Iteratively refine dominators
        changed = True
        while changed:
            changed = False
            for block in all_blocks:
                if block == self.entry_block:
                    continue

                # New dominators = {self} U (intersection of dominators of predecessors)
                if block.predecessors:
                    new_doms = set(all_blocks)
                    for pred in block.predecessors:
                        new_doms &= self.dominators[pred]
                    new_doms.add(block)

                    if new_doms != self.dominators[block]:
                        self.dominators[block] = new_doms
                        changed = True

    def compute_dominance_frontiers(self) -> None:
        """Compute dominance frontiers for all blocks.

        The dominance frontier of a block X is the set of blocks Y where:
        - X dominates a predecessor of Y
        - X does not strictly dominate Y

        Must be called after compute_dominance().
        Stores results in self.dominance_frontiers.
        """
        if not self.dominators:
            self.compute_dominance()

        self.dominance_frontiers = {block: [] for block in self.blocks.values()}

        for block in self.blocks.values():
            # Skip if no predecessors
            if len(block.predecessors) < 2:
                continue

            for pred in block.predecessors:
                runner = pred
                while runner != self._immediate_dominator(block):
                    if block not in self.dominance_frontiers[runner]:
                        self.dominance_frontiers[runner].append(block)
                    runner = self._immediate_dominator(runner)

    def _immediate_dominator(self, block: BasicBlock) -> BasicBlock:
        """Find the immediate dominator of a block.

        Args:
            block: The block to find immediate dominator for.

        Returns:
            The immediate dominator.
        """
        doms = self.dominators[block] - {block}
        if not doms:
            return block  # Entry block

        # Find the dominator that doesn't dominate any other dominator
        for candidate in doms:
            is_immediate = True
            for other in doms:
                if other != candidate and candidate in self.dominators[other]:
                    is_immediate = False
                    break
            if is_immediate:
                return candidate

        return block  # Shouldn't happen

    def topological_sort(self) -> list[BasicBlock]:
        """Perform topological sort of blocks.

        Returns:
            List of blocks in topological order.
        """
        if not self.entry_block:
            return []

        visited = set()
        result = []

        def visit(block: BasicBlock) -> None:
            if block in visited:
                return
            visited.add(block)
            for succ in block.successors:
                visit(succ)
            result.append(block)

        visit(self.entry_block)
        result.reverse()
        return result

    def to_dot(self) -> str:
        """Generate Graphviz DOT representation of the CFG.

        Returns:
            DOT format string.
        """
        lines = ["digraph CFG {"]
        lines.append("  node [shape=box];")

        # Add nodes
        for label, block in self.blocks.items():
            # Escape special characters for DOT
            content = str(block).replace('"', '\\"').replace("\n", "\\l")
            lines.append(f'  "{label}" [label="{content}\\l"];')

        # Add edges
        for label, block in self.blocks.items():
            for succ in block.successors:
                lines.append(f'  "{label}" -> "{succ.label}";')

        lines.append("}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return string representation of the CFG."""
        if not self.entry_block:
            return "<empty CFG>"

        lines = []
        visited = set()

        def visit(block: BasicBlock) -> None:
            if block.label in visited:
                return
            visited.add(block.label)
            lines.append(str(block))
            for succ in block.successors:
                visit(succ)

        visit(self.entry_block)
        return "\n\n".join(lines)
