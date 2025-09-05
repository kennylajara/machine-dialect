"""MIR printer and dumper for debugging.

This module provides utilities to print and dump MIR in human-readable formats,
including textual representation and GraphViz DOT format for visualization.
"""

import io
from typing import TextIO

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    GetAttr,
    Jump,
    Label,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Nop,
    Phi,
    Print,
    Return,
    Scope,
    Select,
    SetAttr,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, FunctionRef, MIRValue, Temp, Variable


def format_type(mir_type: MIRType | MIRUnionType) -> str:
    """Format a MIR type for display.

    Args:
        mir_type: The type to format.

    Returns:
        String representation of the type.
    """
    if isinstance(mir_type, MIRUnionType):
        return f"Union[{', '.join(t.name for t in mir_type.types)}]"
    elif isinstance(mir_type, MIRType):
        return mir_type.name
    return str(mir_type)


class MIRPrinter:
    """Prints MIR in human-readable text format."""

    def __init__(self, output: TextIO | None = None) -> None:
        """Initialize the MIR printer.

        Args:
            output: Output stream (defaults to internal buffer).
        """
        self.output = output or io.StringIO()
        self.indent_level = 0
        self.indent_str = "  "

    def print_module(self, module: MIRModule) -> str:
        """Print a MIR module.

        Args:
            module: The module to print.

        Returns:
            String representation of the module.
        """
        self._write(f"Module: {module.name}")
        self._write("")

        # Print globals if any
        if hasattr(module, "globals") and module.globals:
            self._write("Globals:")
            self._indent()
            for name, value in module.globals.items():
                self._write(f"{name}: {self._format_value(value)}")
            self._dedent()
            self._write("")

        # Print functions
        for _func_name, func in module.functions.items():
            self.print_function(func)
            self._write("")

        # Print main function designation
        if module.main_function:
            self._write(f"Main: {module.main_function}")

        if isinstance(self.output, io.StringIO):
            return self.output.getvalue()
        return ""

    def print_function(self, func: MIRFunction) -> str:
        """Print a MIR function.

        Args:
            func: The function to print.

        Returns:
            String representation of the function.
        """
        # Function signature
        params = ", ".join(
            f"{p.name}: {format_type(p.type)}" if hasattr(p, "name") and hasattr(p, "type") else str(p)
            for p in func.params
        )
        self._write(f"Function {func.name}({params}) -> {format_type(func.return_type)} {{")
        self._indent()

        # Print locals
        if func.locals:
            self._write("Locals:")
            self._indent()
            for local in func.locals.values():
                if hasattr(local, "name") and hasattr(local, "type"):
                    self._write(f"{local.name}: {format_type(local.type)}")
                else:
                    self._write(str(local))
            self._dedent()
            self._write("")

        # Print temporaries
        if func.temporaries:
            self._write("Temporaries:")
            self._indent()
            for temp in func.temporaries:
                if hasattr(temp, "name") and hasattr(temp, "type"):
                    self._write(f"{temp.name}: {format_type(temp.type)}")
                else:
                    self._write(str(temp))
            self._dedent()
            self._write("")

        # Print basic blocks
        self._write("Blocks:")
        self._indent()

        # Print entry block first
        if func.cfg.entry_block:
            self._print_block(func.cfg.entry_block, func.cfg)

        # Print other blocks
        for block in func.cfg.blocks.values():
            if block != func.cfg.entry_block:
                self._print_block(block, func.cfg)

        self._dedent()
        self._dedent()
        self._write("}")

        if isinstance(self.output, io.StringIO):
            return self.output.getvalue()
        return ""

    def _print_block(self, block: BasicBlock, cfg: CFG) -> None:
        """Print a basic block.

        Args:
            block: The block to print.
            cfg: The containing CFG.
        """
        # Block header with predecessors
        preds = [p.label for p in block.predecessors]
        if preds:
            self._write(f"{block.label}: (preds: {', '.join(preds)})")
        else:
            self._write(f"{block.label}:")

        self._indent()

        # Print phi nodes first
        for phi in block.phi_nodes:
            self._write(self._format_instruction(phi))

        # Print instructions
        for inst in block.instructions:
            self._write(self._format_instruction(inst))

        # Print successors
        succs = [s.label for s in block.successors]
        if succs:
            self._write(f"// successors: {', '.join(succs)}")

        self._dedent()
        self._write("")

    def _format_instruction(self, inst: MIRInstruction) -> str:
        """Format an instruction as a string.

        Args:
            inst: The instruction to format.

        Returns:
            String representation of the instruction.
        """
        if isinstance(inst, BinaryOp):
            dest = self._format_value(inst.dest)
            left = self._format_value(inst.left)
            right = self._format_value(inst.right)
            return f"{dest} = {left} {inst.op} {right}"
        elif isinstance(inst, UnaryOp):
            return f"{self._format_value(inst.dest)} = {inst.op} {self._format_value(inst.operand)}"
        elif isinstance(inst, Copy):
            return f"{self._format_value(inst.dest)} = {self._format_value(inst.source)}"
        elif isinstance(inst, LoadConst):
            return f"{self._format_value(inst.dest)} = const {self._format_value(inst.constant)}"
        elif isinstance(inst, LoadVar):
            return f"{self._format_value(inst.dest)} = load {self._format_value(inst.var)}"
        elif isinstance(inst, StoreVar):
            return f"store {self._format_value(inst.var)}, {self._format_value(inst.source)}"
        elif isinstance(inst, Call):
            args = ", ".join(self._format_value(arg) for arg in inst.args)
            if inst.dest:
                return f"{self._format_value(inst.dest)} = call {inst.func.name}({args})"
            else:
                return f"call {inst.func.name}({args})"
        elif isinstance(inst, Return):
            if inst.value:
                return f"return {self._format_value(inst.value)}"
            else:
                return "return"
        elif isinstance(inst, Jump):
            return f"goto {inst.label}"
        elif isinstance(inst, ConditionalJump):
            if inst.false_label:
                return f"if {self._format_value(inst.condition)} goto {inst.true_label} else {inst.false_label}"
            else:
                return f"if {self._format_value(inst.condition)} goto {inst.true_label}"
        elif isinstance(inst, Phi):
            incoming = ", ".join(f"{self._format_value(val)}:{label}" for val, label in inst.incoming)
            return f"{self._format_value(inst.dest)} = φ({incoming})"
        elif isinstance(inst, Select):
            dest = self._format_value(inst.dest)
            cond = self._format_value(inst.condition)
            true_v = self._format_value(inst.true_val)
            false_v = self._format_value(inst.false_val)
            return f"{dest} = select {cond}, {true_v}, {false_v}"
        elif isinstance(inst, Print):
            return f"print {self._format_value(inst.value)}"
        elif isinstance(inst, Assert):
            if inst.message:
                return f'assert {self._format_value(inst.condition)}, "{inst.message}"'
            return f"assert {self._format_value(inst.condition)}"
        elif isinstance(inst, Scope):
            return "begin_scope" if inst.is_begin else "end_scope"
        elif isinstance(inst, GetAttr):
            return f"{self._format_value(inst.dest)} = {self._format_value(inst.obj)}.{inst.attr}"
        elif isinstance(inst, SetAttr):
            return f"{self._format_value(inst.obj)}.{inst.attr} = {self._format_value(inst.value)}"
        elif isinstance(inst, Label):
            return f"{inst.name}:"
        elif isinstance(inst, Nop):
            return "nop"
        else:
            return str(inst)

    def _format_value(self, value: MIRValue) -> str:
        """Format a MIR value as a string.

        Args:
            value: The value to format.

        Returns:
            String representation of the value.
        """
        if isinstance(value, Variable):
            return f"%{value.name}"
        elif isinstance(value, Temp):
            return f"#{value.name if hasattr(value, 'name') else str(value)}"
        elif isinstance(value, Constant):
            if value.value is None:
                return "null"
            elif isinstance(value.value, str):
                return f'"{value.value}"'
            elif isinstance(value.value, bool):
                return "true" if value.value else "false"
            else:
                return str(value.value)
        elif isinstance(value, FunctionRef):
            return f"@{value.name}"
        else:
            return str(value)

    def _write(self, text: str) -> None:
        """Write text with current indentation.

        Args:
            text: Text to write.
        """
        if text:
            self.output.write(self.indent_str * self.indent_level + text)
        self.output.write("\n")

    def _indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def _dedent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)


class MIRDotExporter:
    """Exports MIR CFG to GraphViz DOT format for visualization."""

    def __init__(self) -> None:
        """Initialize the DOT exporter."""
        self.node_counter = 0
        self.node_ids: dict[BasicBlock, str] = {}

    def export_module(self, module: MIRModule) -> str:
        """Export all functions in a module to DOT format.

        Args:
            module: The module to export.

        Returns:
            DOT format string with all functions.
        """
        lines = []
        lines.append("digraph MIR {")
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box];")
        lines.append("")

        for func_name, func in module.functions.items():
            lines.append(f"  subgraph cluster_{func_name} {{")
            lines.append(f'    label="{func_name}";')

            # Export the function and extract its body
            func_dot = self.export_function(func)
            func_lines = func_dot.split("\n")

            # Skip the digraph header and closing brace, add indentation
            for line in func_lines[3:-1]:  # Skip first 3 lines and last line
                if line.strip():
                    lines.append("    " + line)

            lines.append("  }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines)

    def export_function(self, func: MIRFunction) -> str:
        """Export a function's CFG to DOT format.

        Args:
            func: The function to export.

        Returns:
            DOT format string.
        """
        self.node_counter = 0
        self.node_ids.clear()

        lines = []
        lines.append(f'digraph "{func.name}" {{')
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box, style=rounded];")
        lines.append("")

        # Add nodes
        for block in func.cfg.blocks.values():
            node_id = self._get_node_id(block)
            label = self._format_block_label(block)
            color = "lightgreen" if block == func.cfg.entry_block else "lightblue"
            lines.append(f'  {node_id} [label="{label}", fillcolor={color}, style="rounded,filled"];')

        lines.append("")

        # Add edges
        for block in func.cfg.blocks.values():
            src_id = self._get_node_id(block)
            for succ in block.successors:
                dst_id = self._get_node_id(succ)

                # Determine edge label based on terminator
                edge_label = ""
                if block.instructions:
                    last_inst = block.instructions[-1]
                    if isinstance(last_inst, ConditionalJump):
                        if succ.label == last_inst.true_label:
                            edge_label = "true"
                        elif succ.label == last_inst.false_label:
                            edge_label = "false"

                if edge_label:
                    lines.append(f'  {src_id} -> {dst_id} [label="{edge_label}"];')
                else:
                    lines.append(f"  {src_id} -> {dst_id};")

        lines.append("}")
        return "\n".join(lines)

    def _get_node_id(self, block: BasicBlock) -> str:
        """Get or create a node ID for a block.

        Args:
            block: The block.

        Returns:
            Node ID string.
        """
        if block not in self.node_ids:
            self.node_ids[block] = f"node{self.node_counter}"
            self.node_counter += 1
        return self.node_ids[block]

    def _format_block_label(self, block: BasicBlock) -> str:
        """Format a block's label for DOT.

        Args:
            block: The block.

        Returns:
            Formatted label string.
        """
        lines = [f"{block.label}:"]

        # Add first few instructions
        max_inst = 5
        for _i, inst in enumerate(block.instructions[:max_inst]):
            inst_str = str(inst).replace('"', '\\"')
            lines.append(inst_str)

        if len(block.instructions) > max_inst:
            lines.append(f"... ({len(block.instructions) - max_inst} more)")

        return "\\l".join(lines) + "\\l"


def dump_mir_module(module: MIRModule, output: TextIO | None = None) -> str:
    """Dump a MIR module as text.

    Args:
        module: The module to dump.
        output: Optional output stream.

    Returns:
        String representation of the module.
    """
    printer = MIRPrinter(output)
    return printer.print_module(module)


def dump_mir_function(func: MIRFunction, output: TextIO | None = None) -> str:
    """Dump a MIR function as text.

    Args:
        func: The function to dump.
        output: Optional output stream.

    Returns:
        String representation of the function.
    """
    printer = MIRPrinter(output)
    return printer.print_function(func)


def export_cfg_dot(func: MIRFunction) -> str:
    """Export a function's CFG to DOT format.

    Args:
        func: The function to export.

    Returns:
        DOT format string.
    """
    exporter = MIRDotExporter()
    return exporter.export_function(func)
