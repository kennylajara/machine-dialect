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

    def __init__(self, entry_label: str = "entry") -> None:
        """Initialize a control flow graph.

        Args:
            entry_label: Label for the entry block.
        """
        self.entry_block = BasicBlock(entry_label)
        self.blocks: dict[str, BasicBlock] = {entry_label: self.entry_block}
        self.exit_blocks: list[BasicBlock] = []
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
        """Connect two blocks.

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

    def compute_dominators(self) -> dict[str, set[str]]:
        """Compute dominators for all blocks.

        A block X dominates block Y if all paths from entry to Y go through X.

        Returns:
            Map from block label to set of dominator labels.
        """
        # Initialize dominators
        dominators: dict[str, set[str]] = {}
        all_blocks = set(self.blocks.keys())

        # Entry block is only dominated by itself
        dominators[self.entry_block.label] = {self.entry_block.label}

        # All other blocks are initially dominated by all blocks
        for label in all_blocks:
            if label != self.entry_block.label:
                dominators[label] = all_blocks.copy()

        # Iteratively refine dominators
        changed = True
        while changed:
            changed = False
            for label, block in self.blocks.items():
                if label == self.entry_block.label:
                    continue

                # New dominators = {self} U (intersection of dominators of predecessors)
                if block.predecessors:
                    new_doms = set(all_blocks)
                    for pred in block.predecessors:
                        new_doms &= dominators[pred.label]
                    new_doms.add(label)

                    if new_doms != dominators[label]:
                        dominators[label] = new_doms
                        changed = True

        return dominators

    def compute_dominance_frontiers(self) -> dict[str, set[str]]:
        """Compute dominance frontiers for all blocks.

        The dominance frontier of a block X is the set of blocks Y where:
        - X dominates a predecessor of Y
        - X does not strictly dominate Y

        Returns:
            Map from block label to set of frontier block labels.
        """
        dominators = self.compute_dominators()
        frontiers: dict[str, set[str]] = {label: set() for label in self.blocks}

        for label, block in self.blocks.items():
            # Skip if no predecessors
            if len(block.predecessors) < 2:
                continue

            for pred in block.predecessors:
                runner = pred.label
                while runner != self.immediate_dominator(label, dominators):
                    frontiers[runner].add(label)
                    runner = self.immediate_dominator(runner, dominators)

        return frontiers

    def immediate_dominator(self, block_label: str, dominators: dict[str, set[str]]) -> str:
        """Find the immediate dominator of a block.

        Args:
            block_label: The block to find immediate dominator for.
            dominators: Precomputed dominators.

        Returns:
            The immediate dominator's label.
        """
        doms = dominators[block_label] - {block_label}
        if not doms:
            return block_label  # Entry block

        # Find the dominator that doesn't dominate any other dominator
        for candidate in doms:
            is_immediate = True
            for other in doms:
                if other != candidate and candidate in dominators[other]:
                    is_immediate = False
                    break
            if is_immediate:
                return candidate

        return block_label  # Shouldn't happen

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
