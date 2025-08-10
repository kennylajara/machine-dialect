"""Constant pool for bytecode generation.

This module provides a deduplicated storage for compile-time constants
like numbers, strings, and identifiers.
"""

ConstantValue = int | float | str | bool | None


class ConstantPool:
    """Pool of deduplicated constants for bytecode.

    The constant pool stores literals and identifiers used in the program,
    providing deduplication to reduce memory usage.
    """

    def __init__(self) -> None:
        """Initialize an empty constant pool."""
        self._constants: list[ConstantValue] = []
        self._index_map: dict[tuple[type, ConstantValue], int] = {}

    def add(self, value: ConstantValue) -> int:
        """Add a constant to the pool and return its index.

        If the constant already exists, returns the existing index.

        Args:
            value: The constant value to add.

        Returns:
            Index of the constant in the pool.
        """
        # Create a key that includes type to distinguish 1 from 1.0
        key = (type(value), value)

        # Check if already exists
        if key in self._index_map:
            return self._index_map[key]

        # Add new constant
        index = len(self._constants)
        self._constants.append(value)
        self._index_map[key] = index
        return index

    def get(self, index: int) -> ConstantValue:
        """Get a constant by index.

        Args:
            index: Index of the constant.

        Returns:
            The constant value.

        Raises:
            IndexError: If index is out of bounds.
        """
        if index < 0 or index >= len(self._constants):
            raise IndexError(f"Constant index {index} out of bounds")
        return self._constants[index]

    def size(self) -> int:
        """Get the number of constants in the pool.

        Returns:
            Number of constants.
        """
        return len(self._constants)

    def constants(self) -> list[ConstantValue]:
        """Get all constants in the pool.

        Returns:
            List of all constants in order of insertion.
        """
        return self._constants.copy()

    def clear(self) -> None:
        """Clear all constants from the pool."""
        self._constants.clear()
        self._index_map.clear()

    def __str__(self) -> str:
        """String representation of the constant pool.

        Returns:
            Formatted string showing all constants with indices.
        """
        lines = ["Constants:"]
        for i, const in enumerate(self._constants):
            const_repr = repr(const) if isinstance(const, str) else str(const)
            lines.append(f"  [{i:3d}] {const_repr}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Developer representation of the constant pool.

        Returns:
            String showing pool size and contents.
        """
        return f"ConstantPool(size={self.size()}, constants={self._constants})"
