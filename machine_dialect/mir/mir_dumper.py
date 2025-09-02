"""MIR dumper for pretty-printing and debugging.

This module provides utilities for dumping MIR in various formats with
syntax highlighting and different verbosity levels.
"""

import sys
from enum import Enum
from io import StringIO
from typing import Any, TextIO

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_printer import MIRPrinter


class DumpVerbosity(Enum):
    """Verbosity levels for MIR dumping."""

    MINIMAL = "minimal"  # Just function signatures and basic blocks
    NORMAL = "normal"  # Include instructions
    DETAILED = "detailed"  # Include types and metadata
    DEBUG = "debug"  # Include all available information

    @classmethod
    def from_string(cls, value: str) -> "DumpVerbosity":
        """Create DumpVerbosity from string.

        Args:
            value: String representation of verbosity level.

        Returns:
            DumpVerbosity enum value.
        """
        for member in cls:
            if member.value == value.lower():
                return member
        # Default to NORMAL if not found
        return cls.NORMAL


class ColorCode:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


class MIRDumper:
    """Pretty-printer for MIR with syntax highlighting and formatting."""

    def __init__(
        self,
        use_color: bool = True,
        verbosity: DumpVerbosity = DumpVerbosity.NORMAL,
        show_stats: bool = False,
        show_annotations: bool = True,
    ) -> None:
        """Initialize MIR dumper.

        Args:
            use_color: Whether to use ANSI color codes.
            verbosity: Level of detail to include.
            show_stats: Whether to show optimization statistics.
            show_annotations: Whether to show optimization annotations.
        """
        self.use_color = use_color and sys.stdout.isatty()
        self.verbosity = verbosity
        self.show_stats = show_stats
        self.show_annotations = show_annotations
        self.printer = MIRPrinter()

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled.

        Args:
            text: Text to color.
            color: Color code to apply.

        Returns:
            Colored text or original text.
        """
        if self.use_color:
            return f"{color}{text}{ColorCode.RESET}"
        return text

    def dump_module(self, module: MIRModule, output: TextIO | None = None) -> str:
        """Dump a MIR module with formatting.

        Args:
            module: Module to dump.
            output: Optional output stream (defaults to stdout).

        Returns:
            Formatted module string.
        """
        if output is None:
            output = sys.stdout

        buffer = StringIO()

        # Module header
        header = f"=== MIR Module: {module.name} ==="
        buffer.write(self._color(header, ColorCode.BOLD + ColorCode.CYAN))
        buffer.write("\n\n")

        # Module-level information
        if self.verbosity in [DumpVerbosity.DETAILED, DumpVerbosity.DEBUG]:
            if hasattr(module, "optimization_level"):
                buffer.write(self._color("Optimization Level: ", ColorCode.YELLOW))
                buffer.write(f"{getattr(module, 'optimization_level', 0)}\n")

            if hasattr(module, "profile_data") and module.profile_data:
                buffer.write(self._color("Profile Data: ", ColorCode.YELLOW))
                buffer.write("Available\n")

            buffer.write("\n")

        # Dump each function
        for _, function in module.functions.items():
            self._dump_function(function, buffer)
            buffer.write("\n")

        # Statistics
        if self.show_stats:
            buffer.write(self._dump_statistics(module))

        result = buffer.getvalue()
        output.write(result)
        return result

    def dump_function(self, function: MIRFunction, output: TextIO | None = None) -> str:
        """Dump a single MIR function.

        Args:
            function: Function to dump.
            output: Optional output stream.

        Returns:
            Formatted function string.
        """
        if output is None:
            output = sys.stdout

        buffer = StringIO()
        self._dump_function(function, buffer)
        result = buffer.getvalue()
        output.write(result)
        return result

    def _dump_function(self, function: MIRFunction, buffer: StringIO) -> None:
        """Internal function dumper.

        Args:
            function: Function to dump.
            buffer: String buffer to write to.
        """
        # Function signature
        sig = f"Function {function.name}"
        if function.params:
            param_str = ", ".join(f"{p.name}: {getattr(p, 'mir_type', 'unknown')}" for p in function.params)
            sig += f"({param_str})"
        else:
            sig += "()"

        if function.return_type:
            sig += f" -> {function.return_type.value}"

        buffer.write(self._color(sig, ColorCode.BOLD + ColorCode.GREEN))
        buffer.write("\n")

        # Function attributes
        if self.verbosity in [DumpVerbosity.DETAILED, DumpVerbosity.DEBUG]:
            if hasattr(function, "is_inline") and function.is_inline:
                buffer.write(self._color("  @inline", ColorCode.DIM + ColorCode.MAGENTA))
                buffer.write("\n")

            if hasattr(function, "is_hot") and function.is_hot:
                buffer.write(self._color("  @hot", ColorCode.DIM + ColorCode.RED))
                buffer.write("\n")

            if hasattr(function, "optimization_hints"):
                for hint in function.optimization_hints:
                    buffer.write(
                        self._color(
                            f"  @hint({hint})",
                            ColorCode.DIM + ColorCode.BLUE,
                        )
                    )
                    buffer.write("\n")

        # Basic blocks
        if self.verbosity != DumpVerbosity.MINIMAL:
            # Get blocks from CFG
            if hasattr(function, "cfg") and function.cfg:
                # Process blocks in order, starting with entry block
                if function.cfg.entry_block:
                    visited = set()
                    to_visit = [function.cfg.entry_block]
                    while to_visit:
                        block = to_visit.pop(0)
                        if block.label in visited:
                            continue
                        visited.add(block.label)
                        self._dump_block(block, buffer)
                        # Add successors
                        for succ in block.successors:
                            if succ.label not in visited:
                                to_visit.append(succ)

    def _dump_block(self, block: Any, buffer: StringIO) -> None:
        """Dump a basic block.

        Args:
            block: Basic block to dump.
            buffer: String buffer to write to.
        """
        # Block header
        block_header = f"\n  {block.label}:"
        if hasattr(block, "predecessors") and block.predecessors:
            pred_str = ", ".join(p.label for p in block.predecessors)
            block_header += f" (preds: {pred_str})"

        buffer.write(self._color(block_header, ColorCode.BOLD + ColorCode.BLUE))
        buffer.write("\n")

        # Annotations
        if self.show_annotations:
            if hasattr(block, "loop_depth") and block.loop_depth > 0:
                buffer.write(
                    self._color(
                        f"    ; loop depth: {block.loop_depth}",
                        ColorCode.DIM,
                    )
                )
                buffer.write("\n")

            if hasattr(block, "frequency"):
                buffer.write(
                    self._color(
                        f"    ; frequency: {block.frequency:.2f}",
                        ColorCode.DIM,
                    )
                )
                buffer.write("\n")

        # Instructions
        for inst in block.instructions:
            inst_str = f"    {inst!s}"

            # Color based on instruction type
            if "call" in inst_str.lower():
                inst_str = self._color(inst_str, ColorCode.YELLOW)
            elif "jump" in inst_str.lower() or "branch" in inst_str.lower():
                inst_str = self._color(inst_str, ColorCode.MAGENTA)
            elif "return" in inst_str.lower():
                inst_str = self._color(inst_str, ColorCode.RED)
            elif "=" in inst_str:
                # Assignment operations
                parts = inst_str.split("=", 1)
                if len(parts) == 2:
                    lhs = self._color(parts[0].strip(), ColorCode.CYAN)
                    inst_str = f"    {lhs} = {parts[1].strip()}"

            buffer.write(inst_str)

            # Add type information in detailed mode
            if self.verbosity == DumpVerbosity.DEBUG:
                if hasattr(inst, "result") and hasattr(inst.result, "mir_type"):
                    type_info = f" : {inst.result.mir_type.value}"
                    buffer.write(self._color(type_info, ColorCode.DIM + ColorCode.GREEN))

            buffer.write("\n")

    def _dump_statistics(self, module: MIRModule) -> str:
        """Dump module statistics.

        Args:
            module: Module to analyze.

        Returns:
            Statistics string.
        """
        buffer = StringIO()
        buffer.write("\n")
        buffer.write(self._color("=== Statistics ===", ColorCode.BOLD + ColorCode.CYAN))
        buffer.write("\n")

        # Count statistics
        num_functions = len(module.functions)

        block_counts = []
        for f in module.functions.values():
            if hasattr(f, "cfg") and f.cfg:
                block_counts.append(len(f.cfg.blocks))
            else:
                block_counts.append(0)
        num_blocks = sum(block_counts)

        instruction_counts = []
        for f in module.functions.values():
            if hasattr(f, "cfg") and f.cfg:
                instruction_counts.append(sum(len(b.instructions) for b in f.cfg.blocks.values()))
            else:
                instruction_counts.append(0)
        num_instructions = sum(instruction_counts)

        buffer.write(f"  Functions: {num_functions}\n")
        buffer.write(f"  Basic Blocks: {num_blocks}\n")
        buffer.write(f"  Instructions: {num_instructions}\n")

        # Optimization statistics if available
        if hasattr(module, "optimization_stats"):
            buffer.write("\n")
            buffer.write(self._color("Optimizations Applied:", ColorCode.YELLOW))
            buffer.write("\n")
            for pass_name, stats in module.optimization_stats.items():
                buffer.write(f"  {pass_name}:\n")
                for stat, value in stats.items():
                    buffer.write(f"    {stat}: {value}\n")

        return buffer.getvalue()


def dump_mir(
    module_or_function: MIRModule | MIRFunction,
    use_color: bool = True,
    verbosity: str = "normal",
    show_stats: bool = False,
) -> None:
    """Convenience function to dump MIR to stdout.

    Args:
        module_or_function: Module or function to dump.
        use_color: Whether to use colors.
        verbosity: Verbosity level (minimal, normal, detailed, debug).
        show_stats: Whether to show statistics.
    """
    dumper = MIRDumper(
        use_color=use_color,
        verbosity=DumpVerbosity(verbosity),
        show_stats=show_stats,
    )

    if isinstance(module_or_function, MIRModule):
        dumper.dump_module(module_or_function)
    else:
        dumper.dump_function(module_or_function)
