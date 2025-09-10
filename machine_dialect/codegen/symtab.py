"""Symbol table for variable management during code generation.

This module provides scope management and variable resolution for
local and global variables.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SymbolType(Enum):
    """Type of symbol in the symbol table."""

    LOCAL = "local"
    GLOBAL = "global"
    PARAMETER = "parameter"


@dataclass
class Symbol:
    """Represents a symbol in the symbol table.

    Attributes:
        name: The symbol's identifier name.
        symbol_type: The type of symbol (local, global, or parameter).
        slot: Slot index for locals/parameters, -1 for globals.
    """

    name: str
    symbol_type: SymbolType
    slot: int  # Slot index for locals/parameters, -1 for globals


class Scope:
    """Represents a lexical scope in the program."""

    def __init__(self, parent: Optional["Scope"] = None, name: str = "global") -> None:
        """Initialize a new scope.

        Args:
            parent: Parent scope, None for global scope.
            name: Name of the scope for debugging.
        """
        self.parent = parent
        self.name = name
        self.symbols: dict[str, Symbol] = {}
        self.next_slot = 0  # Next available local slot
        self.is_global = parent is None

    def define_local(self, name: str) -> Symbol:
        """Define a new local variable in this scope.

        Args:
            name: Variable name.

        Returns:
            The created symbol.
        """
        if name in self.symbols:
            # Variable already exists in this scope
            return self.symbols[name]

        symbol = Symbol(name, SymbolType.LOCAL, self.next_slot)
        self.symbols[name] = symbol
        self.next_slot += 1
        return symbol

    def define_parameter(self, name: str) -> Symbol:
        """Define a function parameter in this scope.

        Args:
            name: Parameter name.

        Returns:
            The created symbol.
        """
        symbol = Symbol(name, SymbolType.PARAMETER, self.next_slot)
        self.symbols[name] = symbol
        self.next_slot += 1
        return symbol

    def define_global(self, name: str) -> Symbol:
        """Define a global variable.

        Args:
            name: Variable name.

        Returns:
            The created symbol.
        """
        symbol = Symbol(name, SymbolType.GLOBAL, -1)
        self.symbols[name] = symbol
        return symbol

    def resolve(self, name: str) -> Symbol | None:
        """Resolve a variable name in this scope or parent scopes.

        Args:
            name: Variable name to resolve.

        Returns:
            The symbol if found, None otherwise.
        """
        # Check current scope
        if name in self.symbols:
            return self.symbols[name]

        # Check parent scopes
        if self.parent:
            return self.parent.resolve(name)

        return None

    def num_locals(self) -> int:
        """Get the number of local variables in this scope.

        Returns:
            Number of local slots used.
        """
        return self.next_slot


class SymbolTable:
    """Manages nested scopes and symbol resolution."""

    def __init__(self) -> None:
        """Initialize with a global scope."""
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope

    def enter_scope(self, name: str = "block") -> None:
        """Enter a new nested scope.

        Args:
            name: Name of the scope for debugging.
        """
        new_scope = Scope(parent=self.current_scope, name=name)
        self.current_scope = new_scope

    def exit_scope(self) -> None:
        """Exit the current scope and return to parent scope.

        Raises:
            RuntimeError: If trying to exit global scope.
        """
        if self.current_scope.parent is None:
            raise RuntimeError("Cannot exit global scope")
        self.current_scope = self.current_scope.parent

    def define(self, name: str, is_parameter: bool = False) -> Symbol:
        """Define a new variable in the current scope.

        Args:
            name: Variable name.
            is_parameter: Whether this is a function parameter.

        Returns:
            The created symbol.
        """
        if self.current_scope.is_global:
            return self.current_scope.define_global(name)
        elif is_parameter:
            return self.current_scope.define_parameter(name)
        else:
            return self.current_scope.define_local(name)

    def resolve(self, name: str) -> Symbol | None:
        """Resolve a variable name starting from current scope.

        Args:
            name: Variable name to resolve.

        Returns:
            The symbol if found, None otherwise.
        """
        symbol = self.current_scope.resolve(name)

        # If not found anywhere, treat as global
        if symbol is None and self.current_scope != self.global_scope:
            # Create implicit global reference
            symbol = Symbol(name, SymbolType.GLOBAL, -1)

        return symbol

    def is_global_scope(self) -> bool:
        """Check if currently in global scope.

        Returns:
            True if in global scope, False otherwise.
        """
        return self.current_scope.is_global

    def num_locals(self) -> int:
        """Get the number of locals in current scope.

        Returns:
            Number of local slots used in current scope.
        """
        return self.current_scope.num_locals()

    def current_scope_name(self) -> str:
        """Get the name of the current scope.

        Returns:
            Current scope name.
        """
        return self.current_scope.name
