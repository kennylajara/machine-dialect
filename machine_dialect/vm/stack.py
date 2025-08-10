"""Stack implementation for the VM.

This module provides a stack data structure for holding intermediate
values during bytecode execution.
"""

from typing import Any

from machine_dialect.vm.errors import StackUnderflowError


class Stack:
    """A stack for VM execution.

    The stack holds intermediate values and results during bytecode execution.
    It supports standard push/pop operations as well as peek and manipulation.
    """

    def __init__(self, max_size: int = 2048) -> None:
        """Initialize an empty stack.

        Args:
            max_size: Maximum stack size to prevent infinite growth.
        """
        self._items: list[Any] = []
        self._max_size = max_size

    def push(self, value: Any) -> None:
        """Push a value onto the stack.

        Args:
            value: The value to push.

        Raises:
            RuntimeError: If stack exceeds maximum size.
        """
        if len(self._items) >= self._max_size:
            raise RuntimeError(f"Stack overflow: exceeds maximum size of {self._max_size}")
        self._items.append(value)

    def pop(self) -> Any:
        """Pop a value from the stack.

        Returns:
            The top value from the stack.

        Raises:
            StackUnderflowError: If the stack is empty.
        """
        if not self._items:
            raise StackUnderflowError("Cannot pop from empty stack")
        return self._items.pop()

    def peek(self, offset: int = 0) -> Any:
        """Peek at a value on the stack without removing it.

        Args:
            offset: How far from the top to peek (0 = top).

        Returns:
            The value at the specified position.

        Raises:
            StackUnderflowError: If offset is out of bounds.
        """
        index = -(offset + 1)
        if abs(index) > len(self._items):
            raise StackUnderflowError(f"Cannot peek at offset {offset}: stack too small")
        return self._items[index]

    def dup(self) -> None:
        """Duplicate the top value on the stack.

        Raises:
            StackUnderflowError: If the stack is empty.
        """
        if not self._items:
            raise StackUnderflowError("Cannot duplicate: stack is empty")
        self.push(self._items[-1])

    def swap(self) -> None:
        """Swap the top two values on the stack.

        Raises:
            StackUnderflowError: If there are fewer than 2 items.
        """
        if len(self._items) < 2:
            raise StackUnderflowError("Cannot swap: need at least 2 items on stack")
        self._items[-1], self._items[-2] = self._items[-2], self._items[-1]

    def size(self) -> int:
        """Get the current size of the stack.

        Returns:
            Number of items on the stack.
        """
        return len(self._items)

    def is_empty(self) -> bool:
        """Check if the stack is empty.

        Returns:
            True if empty, False otherwise.
        """
        return len(self._items) == 0

    def clear(self) -> None:
        """Clear all items from the stack."""
        self._items.clear()

    def top(self) -> Any | None:
        """Get the top value without removing it.

        Returns:
            The top value or None if empty.
        """
        return self._items[-1] if self._items else None

    def __str__(self) -> str:
        """String representation of the stack.

        Returns:
            String showing stack contents.
        """
        if not self._items:
            return "Stack: []"
        # Show top of stack on the right
        return f"Stack: [{', '.join(str(item) for item in self._items)}]"

    def __repr__(self) -> str:
        """Developer representation of the stack.

        Returns:
            String representation for debugging.
        """
        return f"Stack(size={self.size()}, items={self._items})"
