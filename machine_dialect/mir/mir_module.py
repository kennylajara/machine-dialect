"""MIR Module Representation.

This module defines the MIRModule class that represents a complete
compilation unit in the MIR.
"""

from typing import Any

from .mir_function import MIRFunction
from .mir_types import MIRType, MIRUnionType
from .mir_values import Constant, Variable


class ConstantPool:
    """Pool of constants used in the module."""

    def __init__(self) -> None:
        """Initialize the constant pool."""
        self.constants: list[Constant] = []
        self._value_to_index: dict[tuple[Any, MIRType | MIRUnionType], int] = {}

    def add(self, constant: Constant) -> int:
        """Add a constant to the pool.

        Args:
            constant: The constant to add.

        Returns:
            The index of the constant in the pool.
        """
        key = (constant.value, constant.type)
        if key in self._value_to_index:
            return self._value_to_index[key]

        index = len(self.constants)
        self.constants.append(constant)
        self._value_to_index[key] = index
        return index

    def get(self, index: int) -> Constant | None:
        """Get a constant by index.

        Args:
            index: The index.

        Returns:
            The constant or None if index is out of bounds.
        """
        if 0 <= index < len(self.constants):
            return self.constants[index]
        return None

    def size(self) -> int:
        """Get the number of constants in the pool.

        Returns:
            The size of the pool.
        """
        return len(self.constants)

    def __str__(self) -> str:
        """Return string representation."""
        lines = ["Constants:"]
        for i, const in enumerate(self.constants):
            lines.append(f"  [{i}] {const}")
        return "\n".join(lines)


class MIRModule:
    """A module in MIR representation.

    A module is a compilation unit containing functions, global variables,
    and constants.
    """

    def __init__(self, name: str) -> None:
        """Initialize a MIR module.

        Args:
            name: Module name.
        """
        self.name = name
        self.functions: dict[str, MIRFunction] = {}
        self.globals: dict[str, Variable] = {}
        self.constants = ConstantPool()
        self.main_function: str | None = None

    def add_function(self, func: MIRFunction) -> None:
        """Add a function to the module.

        Args:
            func: The function to add.
        """
        self.functions[func.name] = func

    def get_function(self, name: str) -> MIRFunction | None:
        """Get a function by name.

        Args:
            name: Function name.

        Returns:
            The function or None if not found.
        """
        return self.functions.get(name)

    def add_global(self, var: Variable) -> None:
        """Add a global variable.

        Args:
            var: The global variable.
        """
        self.globals[var.name] = var

    def get_global(self, name: str) -> Variable | None:
        """Get a global variable by name.

        Args:
            name: Variable name.

        Returns:
            The variable or None if not found.
        """
        return self.globals.get(name)

    def set_main_function(self, name: str) -> None:
        """Set the main function name.

        Args:
            name: The name of the main function.
        """
        self.main_function = name

    def get_main_function(self) -> MIRFunction | None:
        """Get the main function.

        Returns:
            The main function or None if not found.
        """
        if self.main_function is None:
            return None
        return self.functions.get(self.main_function)

    def validate(self) -> list[str]:
        """Validate the module for correctness.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        # Check main function exists
        if self.main_function and self.main_function not in self.functions:
            errors.append(f"Main function '{self.main_function}' not found")

        # Check each function
        for name, func in self.functions.items():
            # Check CFG has entry block
            if not func.cfg.entry_block:
                errors.append(f"Function '{name}' has no entry block")

            # Check all blocks are terminated
            for label, block in func.cfg.blocks.items():
                if not block.is_terminated() and block != func.cfg.entry_block:
                    # Entry block might not be terminated if function is empty
                    if block.instructions:  # Only error if block has instructions
                        errors.append(f"Block '{label}' in function '{name}' is not terminated")

            # Check all jumps target existing blocks
            for _label, block in func.cfg.blocks.items():
                terminator = block.get_terminator()
                if terminator:
                    from .mir_instructions import ConditionalJump, Jump

                    if isinstance(terminator, Jump):
                        if terminator.label not in func.cfg.blocks:
                            errors.append(f"Jump to undefined label '{terminator.label}' in function '{name}'")
                    elif isinstance(terminator, ConditionalJump):
                        if terminator.true_label not in func.cfg.blocks:
                            errors.append(f"Jump to undefined label '{terminator.true_label}' in function '{name}'")
                        if terminator.false_label and terminator.false_label not in func.cfg.blocks:
                            errors.append(f"Jump to undefined label '{terminator.false_label}' in function '{name}'")

        return errors

    def to_string(self, include_constants: bool = True, include_globals: bool = True) -> str:
        """Convert module to string representation.

        Args:
            include_constants: Whether to include the constant pool.
            include_globals: Whether to include global variables.

        Returns:
            String representation of the module.
        """
        lines = [f"module {self.name} {{"]

        # Constants
        if include_constants and self.constants.size() > 0:
            lines.append(f"  {self.constants}")

        # Globals
        if include_globals and self.globals:
            lines.append("  globals:")
            for name, var in self.globals.items():
                lines.append(f"    {name}: {var.type}")

        # Functions
        lines.append("  functions:")
        for name in sorted(self.functions.keys()):
            func = self.functions[name]
            func_str = func.to_string()
            for line in func_str.split("\n"):
                lines.append(f"    {line}")

        lines.append("}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return string representation."""
        return self.to_string()

    def __repr__(self) -> str:
        """Return debug representation."""
        return f"MIRModule({self.name}, functions={len(self.functions)}, globals={len(self.globals)})"
