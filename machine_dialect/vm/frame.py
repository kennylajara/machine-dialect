"""Call frame management for the VM.

This module provides call frames that maintain execution context
for functions and blocks.
"""

from dataclasses import dataclass, field
from typing import Any

from machine_dialect.codegen.objects import Chunk


@dataclass
class Frame:
    """Execution frame for function calls.

    A frame maintains the execution context for a function including
    its bytecode, program counter, and local variables.
    """

    chunk: Chunk
    pc: int = 0
    locals: list[Any] = field(default_factory=list)
    stack_base: int = 0  # Base pointer in the global stack

    def __post_init__(self) -> None:
        """Initialize locals array to the correct size."""
        if self.chunk.num_locals > 0:
            self.locals = [None] * self.chunk.num_locals

    def read_byte(self) -> int:
        """Read a byte from the bytecode and advance PC.

        Returns:
            The byte at the current PC.

        Raises:
            IndexError: If PC is out of bounds.
        """
        if self.pc >= len(self.chunk.bytecode):
            raise IndexError(f"PC {self.pc} out of bounds for chunk size {len(self.chunk.bytecode)}")
        byte = self.chunk.bytecode[self.pc]
        self.pc += 1
        return byte

    def read_u16(self) -> int:
        """Read a 16-bit unsigned integer and advance PC.

        Returns:
            The u16 value at the current PC.
        """
        low = self.read_byte()
        high = self.read_byte()
        return low | (high << 8)

    def read_i16(self) -> int:
        """Read a 16-bit signed integer and advance PC.

        Returns:
            The i16 value at the current PC.
        """
        value = self.read_u16()
        # Convert to signed
        if value >= 32768:
            value = value - 65536
        return value

    def jump(self, offset: int) -> None:
        """Jump by a relative offset.

        Args:
            offset: Relative offset to jump by.
        """
        self.pc += offset

    def set_local(self, slot: int, value: Any) -> None:
        """Set a local variable.

        Args:
            slot: Local variable slot.
            value: Value to set.

        Raises:
            IndexError: If slot is out of bounds.
        """
        if slot < 0 or slot >= len(self.locals):
            raise IndexError(f"Local slot {slot} out of bounds")
        self.locals[slot] = value

    def get_local(self, slot: int) -> Any:
        """Get a local variable.

        Args:
            slot: Local variable slot.

        Returns:
            The value in the slot.

        Raises:
            IndexError: If slot is out of bounds.
        """
        if slot < 0 or slot >= len(self.locals):
            raise IndexError(f"Local slot {slot} out of bounds")
        return self.locals[slot]

    def at_end(self) -> bool:
        """Check if we've reached the end of the bytecode.

        Returns:
            True if at or past the end, False otherwise.
        """
        return self.pc >= len(self.chunk.bytecode)

    def __str__(self) -> str:
        """String representation of the frame.

        Returns:
            String showing frame state.
        """
        return f"Frame(chunk={self.chunk.name}, pc={self.pc}, locals={len(self.locals)})"


class CallStack:
    """Manages the call stack of frames."""

    def __init__(self, max_depth: int = 1024) -> None:
        """Initialize an empty call stack.

        Args:
            max_depth: Maximum call depth to prevent infinite recursion.
        """
        self._frames: list[Frame] = []
        self._max_depth = max_depth

    def push(self, frame: Frame) -> None:
        """Push a new frame onto the call stack.

        Args:
            frame: The frame to push.

        Raises:
            RuntimeError: If maximum call depth is exceeded.
        """
        if len(self._frames) >= self._max_depth:
            raise RuntimeError(f"Maximum call depth exceeded: {self._max_depth}")
        self._frames.append(frame)

    def pop(self) -> Frame | None:
        """Pop a frame from the call stack.

        Returns:
            The popped frame or None if empty.
        """
        return self._frames.pop() if self._frames else None

    def current(self) -> Frame | None:
        """Get the current frame without removing it.

        Returns:
            The current frame or None if empty.
        """
        return self._frames[-1] if self._frames else None

    def depth(self) -> int:
        """Get the current call depth.

        Returns:
            Number of frames on the call stack.
        """
        return len(self._frames)

    def is_empty(self) -> bool:
        """Check if the call stack is empty.

        Returns:
            True if empty, False otherwise.
        """
        return len(self._frames) == 0

    def clear(self) -> None:
        """Clear all frames from the call stack."""
        self._frames.clear()

    def __str__(self) -> str:
        """String representation of the call stack.

        Returns:
            String showing call stack state.
        """
        if not self._frames:
            return "CallStack: []"
        frames_str = "\n  ".join(str(f) for f in self._frames)
        return f"CallStack (depth={self.depth()}):\n  {frames_str}"
