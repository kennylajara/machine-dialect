"""Debug information tracking for MIR compilation.

This module tracks source locations and variable information for debugging.
"""

from dataclasses import dataclass
from typing import Any

from machine_dialect.mir.mir_instructions import MIRInstruction
from machine_dialect.mir.mir_values import Variable


@dataclass
class SourceLocation:
    """Represents a source code location.

    Attributes:
        file: Source file name.
        line: Line number (1-based).
        column: Column number (1-based).
    """

    file: str
    line: int
    column: int

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class DebugVariable:
    """Debug information for a variable.

    Attributes:
        name: Original variable name.
        type_name: Type name as string.
        scope_level: Scope nesting level.
        is_parameter: Whether this is a function parameter.
    """

    name: str
    type_name: str
    scope_level: int = 0
    is_parameter: bool = False


@dataclass
class LineMapping:
    """Maps bytecode offset to source line.

    Attributes:
        bytecode_offset: Offset in bytecode.
        source_line: Source line number.
    """

    bytecode_offset: int
    source_line: int


class DebugInfo:
    """Tracks debug information during compilation."""

    def __init__(self) -> None:
        """Initialize debug information tracker."""
        # Map MIR instructions to source locations
        self.instruction_locations: dict[MIRInstruction, SourceLocation] = {}

        # Map variables to debug info
        self.variable_info: dict[Variable, DebugVariable] = {}

        # Line number mappings for bytecode
        self.line_mappings: list[LineMapping] = []

        # Current source file being compiled
        self.current_file: str = "<unknown>"

        # Symbol table for debugging
        self.symbols: dict[str, DebugVariable] = {}

    def set_instruction_location(self, inst: MIRInstruction, location: SourceLocation) -> None:
        """Set source location for an instruction.

        Args:
            inst: The MIR instruction.
            location: The source location.
        """
        self.instruction_locations[inst] = location

    def get_instruction_location(self, inst: MIRInstruction) -> SourceLocation | None:
        """Get source location for an instruction.

        Args:
            inst: The MIR instruction.

        Returns:
            The source location or None.
        """
        return self.instruction_locations.get(inst)

    def add_variable(self, var: Variable, debug_var: DebugVariable) -> None:
        """Add debug information for a variable.

        Args:
            var: The MIR variable.
            debug_var: The debug information.
        """
        self.variable_info[var] = debug_var
        self.symbols[debug_var.name] = debug_var

    def add_line_mapping(self, mapping: LineMapping) -> None:
        """Add a line number mapping.

        Args:
            mapping: The line mapping to add.
        """
        self.line_mappings.append(mapping)

    def get_line_for_offset(self, offset: int) -> int | None:
        """Get source line for bytecode offset.

        Args:
            offset: Bytecode offset.

        Returns:
            Source line number or None.
        """
        # Find the mapping with the largest offset <= given offset
        best_line = None
        for mapping in self.line_mappings:
            if mapping.bytecode_offset <= offset:
                best_line = mapping.source_line
            else:
                break
        return best_line

    def generate_source_map(self) -> dict[str, Any]:
        """Generate a source map for debugging.

        Returns:
            Source map data structure.
        """
        return {
            "version": 1,
            "file": self.current_file,
            "mappings": [
                {"bytecode_offset": m.bytecode_offset, "source_line": m.source_line}
                for m in sorted(self.line_mappings, key=lambda x: x.bytecode_offset)
            ],
            "symbols": {
                name: {"type": var.type_name, "scope_level": var.scope_level, "is_parameter": var.is_parameter}
                for name, var in self.symbols.items()
            },
        }


class DebugInfoBuilder:
    """Builder for constructing debug information during lowering."""

    def __init__(self) -> None:
        """Initialize the debug info builder."""
        self.debug_info = DebugInfo()
        self.current_line = 1
        self.scope_level = 0

    def enter_scope(self) -> None:
        """Enter a new scope."""
        self.scope_level += 1

    def exit_scope(self) -> None:
        """Exit the current scope."""
        if self.scope_level > 0:
            self.scope_level -= 1

    def track_variable(self, name: str, var: Variable, type_name: str, is_parameter: bool = False) -> None:
        """Track a variable for debugging.

        Args:
            name: Original variable name.
            var: The MIR variable.
            type_name: Type name as string.
            is_parameter: Whether this is a parameter.
        """
        debug_var = DebugVariable(
            name=name, type_name=type_name, scope_level=self.scope_level, is_parameter=is_parameter
        )
        self.debug_info.add_variable(var, debug_var)

    def track_instruction(self, inst: MIRInstruction, line: int, column: int = 1) -> None:
        """Track an instruction's source location.

        Args:
            inst: The MIR instruction.
            line: Source line number.
            column: Source column number.
        """
        location = SourceLocation(file=self.debug_info.current_file, line=line, column=column)
        self.debug_info.set_instruction_location(inst, location)
        self.current_line = line

    def get_debug_info(self) -> DebugInfo:
        """Get the constructed debug information.

        Returns:
            The debug information.
        """
        return self.debug_info
