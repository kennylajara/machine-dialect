"""Symbol table for tracking variable definitions in Machine Dialect™.

This module provides the symbol table implementation for tracking variable
definitions and their types. The symbol table supports nested scopes and
type checking for variable assignments.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from machine_dialect.ast import ASTNode


@dataclass
class VariableInfo:
    """Information about a defined variable.

    Attributes:
        type_spec: List of allowed type names (for union types)
        defined: Whether the variable has been defined
        initialized: Whether the variable has been assigned a value
        definition_line: Line number where variable was defined
        definition_pos: Column position where variable was defined
        return_type: For functions, the return type (optional)
        last_assigned_value: The last value assigned to this variable (for type tracking)
        inferred_element_types: For collections, the inferred element types
    """

    type_spec: list[str]
    defined: bool = True
    initialized: bool = False
    definition_line: int = 0
    definition_pos: int = 0
    return_type: str | None = None
    last_assigned_value: "ASTNode | None" = None  # Stores the AST node of the last assigned value
    inferred_element_types: list[str] | None = None  # For tracking collection element types

    def allows_type(self, type_name: str) -> bool:
        """Check if this variable allows the given type.

        Args:
            type_name: The type to check

        Returns:
            True if type is allowed, False otherwise
        """
        return type_name in self.type_spec

    def __str__(self) -> str:
        """Return string representation."""
        type_str = " or ".join(self.type_spec)
        status = "initialized" if self.initialized else "uninitialized"
        return f"VariableInfo(types={type_str}, {status})"


class SymbolTable:
    """Symbol table for tracking variable definitions.

    Maintains a mapping of variable names to their type information
    and tracks scoping through parent/child relationships.

    Attributes:
        symbols: Dictionary mapping variable names to their info
        parent: Parent symbol table for outer scope (if any)
    """

    def __init__(self, parent: "SymbolTable | None" = None) -> None:
        """Initialize a symbol table.

        Args:
            parent: Optional parent symbol table for outer scope
        """
        self.symbols: dict[str, VariableInfo] = {}
        self.parent = parent

    def define(self, name: str, type_spec: list[str], line: int = 0, position: int = 0) -> None:
        """Define a new variable.

        Args:
            name: Variable name
            type_spec: List of allowed types
            line: Line number of definition
            position: Column position of definition

        Raises:
            NameError: If variable is already defined in this scope
        """
        if name in self.symbols:
            existing = self.symbols[name]
            raise NameError(f"Variable '{name}' is already defined at line {existing.definition_line}")

        self.symbols[name] = VariableInfo(
            type_spec=type_spec, defined=True, initialized=False, definition_line=line, definition_pos=position
        )

    def lookup(self, name: str) -> VariableInfo | None:
        """Look up a variable definition.

        Searches this scope and parent scopes for the variable.

        Args:
            name: Variable name to look up

        Returns:
            VariableInfo if found, None otherwise
        """
        if name in self.symbols:
            return self.symbols[name]

        if self.parent:
            return self.parent.lookup(name)

        return None

    def mark_initialized(self, name: str) -> None:
        """Mark a variable as initialized.

        Args:
            name: Variable name to mark as initialized

        Raises:
            NameError: If variable is not defined
        """
        info = self.lookup(name)
        if not info:
            raise NameError(f"Variable '{name}' is not defined")

        # Mark in the scope where it's defined
        if name in self.symbols:
            self.symbols[name].initialized = True
        elif self.parent:
            self.parent.mark_initialized(name)

    def enter_scope(self) -> "SymbolTable":
        """Create a new child scope.

        Returns:
            A new SymbolTable with this table as parent
        """
        return SymbolTable(parent=self)

    def exit_scope(self) -> "SymbolTable | None":
        """Return to parent scope.

        Returns:
            The parent symbol table, or None if at global scope
        """
        return self.parent

    def is_defined_in_current_scope(self, name: str) -> bool:
        """Check if variable is defined in current scope only.

        Args:
            name: Variable name to check

        Returns:
            True if defined in this scope, False otherwise
        """
        return name in self.symbols

    def __str__(self) -> str:
        """Return string representation of symbol table."""
        lines = ["Symbol Table:"]
        for name, info in self.symbols.items():
            lines.append(f"  {name}: {info}")
        if self.parent:
            lines.append("  (has parent scope)")
        return "\n".join(lines)
