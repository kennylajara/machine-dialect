"""Virtual Machine for executing Machine Dialect bytecode.

This module implements the main VM that executes bytecode produced
by the code generator.
"""

from typing import Any

from machine_dialect.codegen.isa import Opcode
from machine_dialect.codegen.objects import Chunk, Module
from machine_dialect.vm.errors import (
    DivisionByZeroError,
    InvalidOpcodeError,
)
from machine_dialect.vm.errors import (
    TypeError as VMTypeError,
)
from machine_dialect.vm.frame import CallStack, Frame
from machine_dialect.vm.natives import get_native_function
from machine_dialect.vm.objects import NativeFunction, equals, is_truthy, strict_equals
from machine_dialect.vm.stack import Stack


class VM:
    """Virtual Machine for executing Machine Dialect bytecode."""

    def __init__(self, debug: bool = False) -> None:
        """Initialize the VM.

        Args:
            debug: Enable debug output.
        """
        self.stack = Stack()
        self.call_stack = CallStack()
        self.globals: dict[str, Any] = {}
        self.debug = debug

    def run(self, module: Module) -> Any:
        """Execute a compiled module.

        Args:
            module: The module to execute.

        Returns:
            The final result left on the stack.
        """
        # Check module type
        if module.is_procedural():
            # Execute procedural module - just run main chunk
            return self.run_chunk(module.main_chunk)
        else:
            # Class module - for now, same behavior
            # Future: initialize class, run constructor if needed
            return self.run_chunk(module.main_chunk)

    def run_chunk(self, chunk: Chunk) -> Any:
        """Execute a chunk of bytecode.

        Args:
            chunk: The chunk to execute.

        Returns:
            The final result left on the stack.
        """
        # Create initial frame
        frame = Frame(chunk)
        self.call_stack.push(frame)

        try:
            while not frame.at_end():
                if self.debug:
                    self._debug_state(frame)

                # Fetch opcode
                opcode = frame.read_byte()

                # Decode and execute
                self._execute_instruction(opcode, frame)

                # Check if we need to switch frames
                current = self.call_stack.current()
                if current != frame:
                    if current is None:
                        # Finished execution
                        break
                    frame = current

        except Exception as e:
            if self.debug:
                print(f"VM Error: {e}")
                self._debug_state(frame)
            raise

        # Return top of stack if anything
        return self.stack.top() if not self.stack.is_empty() else None

    def _execute_instruction(self, opcode: int, frame: Frame) -> None:
        """Execute a single instruction.

        Args:
            opcode: The opcode to execute.
            frame: Current execution frame.

        Raises:
            InvalidOpcodeError: If opcode is unknown.
            Various VM errors for runtime issues.
        """
        try:
            op = Opcode(opcode)
        except ValueError:
            raise InvalidOpcodeError(f"Unknown opcode: {opcode}") from None

        # Dispatch to handler
        if op == Opcode.LOAD_CONST:
            self._op_load_const(frame)
        elif op == Opcode.LOAD_LOCAL:
            self._op_load_local(frame)
        elif op == Opcode.STORE_LOCAL:
            self._op_store_local(frame)
        elif op == Opcode.LOAD_GLOBAL:
            self._op_load_global(frame)
        elif op == Opcode.STORE_GLOBAL:
            self._op_store_global(frame)
        elif op == Opcode.POP:
            self._op_pop()
        elif op == Opcode.DUP:
            self._op_dup()
        elif op == Opcode.SWAP:
            self._op_swap()
        elif op == Opcode.ADD:
            self._op_add()
        elif op == Opcode.SUB:
            self._op_sub()
        elif op == Opcode.MUL:
            self._op_mul()
        elif op == Opcode.DIV:
            self._op_div()
        elif op == Opcode.MOD:
            self._op_mod()
        elif op == Opcode.NEG:
            self._op_neg()
        elif op == Opcode.NOT:
            self._op_not()
        elif op == Opcode.EQ:
            self._op_eq()
        elif op == Opcode.NEQ:
            self._op_neq()
        elif op == Opcode.LT:
            self._op_lt()
        elif op == Opcode.GT:
            self._op_gt()
        elif op == Opcode.LTE:
            self._op_lte()
        elif op == Opcode.GTE:
            self._op_gte()
        elif op == Opcode.STRICT_EQ:
            self._op_strict_eq()
        elif op == Opcode.STRICT_NEQ:
            self._op_strict_neq()
        elif op == Opcode.AND:
            self._op_and()
        elif op == Opcode.OR:
            self._op_or()
        elif op == Opcode.JUMP:
            self._op_jump(frame)
        elif op == Opcode.JUMP_IF_FALSE:
            self._op_jump_if_false(frame)
        elif op == Opcode.RETURN:
            self._op_return()
        elif op == Opcode.CALL:
            self._op_call(frame)
        elif op == Opcode.NOP:
            pass  # No operation
        elif op == Opcode.HALT:
            # Set PC to end to stop execution
            frame.pc = len(frame.chunk.bytecode)
        else:
            raise InvalidOpcodeError(f"Unimplemented opcode: {op.name}")

    # Load/Store operations

    def _op_load_const(self, frame: Frame) -> None:
        """Load a constant onto the stack."""
        index = frame.read_u16()
        value = frame.chunk.get_constant(index)
        self.stack.push(value)

    def _op_load_local(self, frame: Frame) -> None:
        """Load a local variable onto the stack."""
        slot = frame.read_u16()
        value = frame.get_local(slot)
        self.stack.push(value)

    def _op_store_local(self, frame: Frame) -> None:
        """Store top of stack to a local variable."""
        slot = frame.read_u16()
        value = self.stack.pop()
        frame.set_local(slot, value)

    def _op_load_global(self, frame: Frame) -> None:
        """Load a global variable onto the stack."""
        index = frame.read_u16()
        name = frame.chunk.get_constant(index)
        if not isinstance(name, str):
            raise VMTypeError(f"Global name must be string, got {type(name).__name__}")

        # Check for native function first
        native_func = get_native_function(name)
        if native_func:
            self.stack.push(native_func)
        elif name in self.globals:
            self.stack.push(self.globals[name])
        else:
            # Undefined global - push None
            self.stack.push(None)

    def _op_store_global(self, frame: Frame) -> None:
        """Store top of stack to a global variable."""
        index = frame.read_u16()
        name = frame.chunk.get_constant(index)
        if not isinstance(name, str):
            raise VMTypeError(f"Global name must be string, got {type(name).__name__}")
        value = self.stack.pop()
        self.globals[name] = value

    # Stack operations

    def _op_pop(self) -> None:
        """Pop and discard top of stack."""
        self.stack.pop()

    def _op_dup(self) -> None:
        """Duplicate top of stack."""
        self.stack.dup()

    def _op_swap(self) -> None:
        """Swap top two stack items."""
        self.stack.swap()

    # Arithmetic operations

    def _op_add(self) -> None:
        """Add top two values."""
        b = self.stack.pop()
        a = self.stack.pop()

        # String concatenation
        if isinstance(a, str) or isinstance(b, str):
            result: Any = str(a) + str(b)
        # Numeric addition
        elif isinstance(a, int | float) and isinstance(b, int | float):
            result = a + b
        else:
            raise VMTypeError(f"Cannot add {type(a).__name__} and {type(b).__name__}")

        self.stack.push(result)

    def _op_sub(self) -> None:
        """Subtract top two values."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot subtract {type(b).__name__} from {type(a).__name__}")

        self.stack.push(a - b)

    def _op_mul(self) -> None:
        """Multiply top two values."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot multiply {type(a).__name__} and {type(b).__name__}")

        self.stack.push(a * b)

    def _op_div(self) -> None:
        """Divide top two values."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot divide {type(a).__name__} by {type(b).__name__}")

        if b == 0:
            raise DivisionByZeroError("Division by zero")

        # Use true division
        self.stack.push(a / b)

    def _op_mod(self) -> None:
        """Modulo top two values."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot modulo {type(a).__name__} by {type(b).__name__}")

        if b == 0:
            raise DivisionByZeroError("Modulo by zero")

        self.stack.push(a % b)

    def _op_neg(self) -> None:
        """Negate top of stack."""
        value = self.stack.pop()

        if not isinstance(value, int | float):
            raise VMTypeError(f"Cannot negate {type(value).__name__}")

        self.stack.push(-value)

    def _op_not(self) -> None:
        """Logical NOT of top of stack."""
        value = self.stack.pop()
        self.stack.push(not is_truthy(value))

    # Comparison operations

    def _op_eq(self) -> None:
        """Check equality."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(equals(a, b))

    def _op_neq(self) -> None:
        """Check inequality."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(not equals(a, b))

    def _op_lt(self) -> None:
        """Check less than."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot compare {type(a).__name__} and {type(b).__name__}")

        self.stack.push(a < b)

    def _op_gt(self) -> None:
        """Check greater than."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot compare {type(a).__name__} and {type(b).__name__}")

        self.stack.push(a > b)

    def _op_lte(self) -> None:
        """Check less than or equal."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot compare {type(a).__name__} and {type(b).__name__}")

        self.stack.push(a <= b)

    def _op_gte(self) -> None:
        """Check greater than or equal."""
        b = self.stack.pop()
        a = self.stack.pop()

        if not isinstance(a, int | float) or not isinstance(b, int | float):
            raise VMTypeError(f"Cannot compare {type(a).__name__} and {type(b).__name__}")

        self.stack.push(a >= b)

    def _op_strict_eq(self) -> None:
        """Check strict equality (type and value)."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(strict_equals(a, b))

    def _op_strict_neq(self) -> None:
        """Check strict inequality (type or value)."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(not strict_equals(a, b))

    # Logical operations

    def _op_and(self) -> None:
        """Logical AND (no short-circuit)."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(is_truthy(a) and is_truthy(b))

    def _op_or(self) -> None:
        """Logical OR (no short-circuit)."""
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(is_truthy(a) or is_truthy(b))

    # Control flow

    def _op_jump(self, frame: Frame) -> None:
        """Unconditional jump."""
        offset = frame.read_i16()
        frame.jump(offset)

    def _op_jump_if_false(self, frame: Frame) -> None:
        """Jump if top of stack is falsy."""
        offset = frame.read_i16()
        condition = self.stack.pop()
        if not is_truthy(condition):
            frame.jump(offset)

    def _op_return(self) -> None:
        """Return from current function."""
        # Pop current frame
        self.call_stack.pop()
        # Result stays on stack

    def _op_call(self, frame: Frame) -> None:
        """Call a function."""
        nargs = frame.read_byte()

        # Get arguments from stack
        args: list[Any] = []
        for _ in range(nargs):
            args.insert(0, self.stack.pop())

        # Get function
        func = self.stack.pop()

        if isinstance(func, NativeFunction):
            # Call native function
            result = func.call(args)
            self.stack.push(result)
        else:
            raise VMTypeError(f"Cannot call {type(func).__name__}")

    # Debug helpers

    def _debug_state(self, frame: Frame) -> None:
        """Print debug information about VM state."""
        print("=== VM State ===")
        print(f"PC: {frame.pc:04d}")
        print(f"Stack: {self.stack}")
        print(f"Locals: {frame.locals}")
        print(f"Globals: {self.globals}")
        print()
