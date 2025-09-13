"""MIR interpreter for direct execution of MIR code.

This module provides an interpreter that can directly execute MIR instructions
without generating bytecode, useful for testing and debugging.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from machine_dialect.errors.exceptions import MDRuntimeError
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Nop,
    Phi,
    Pop,
    Print,
    Return,
    Scope,
    Select,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_values import Constant, FunctionRef, MIRValue, Temp, Variable


class ExecutionState(Enum):
    """Execution state of the interpreter."""

    RUNNING = "running"
    RETURNED = "returned"
    ERROR = "error"


@dataclass
class Frame:
    """Represents a function call frame.

    Attributes:
        function: The MIR function being executed.
        locals: Local variable storage.
        temps: Temporary value storage.
        current_block: Current basic block.
        instruction_index: Index of current instruction.
        return_value: Return value when function completes.
    """

    function: MIRFunction
    locals: dict[str, Any]
    temps: dict[int, Any]
    current_block: BasicBlock
    instruction_index: int
    return_value: Any = None


class MIRInterpreter:
    """Interprets MIR instructions directly."""

    def __init__(self) -> None:
        """Initialize the MIR interpreter."""
        self.module: MIRModule | None = None
        self.frames: list[Frame] = []
        self.globals: dict[str, Any] = {}
        self.state = ExecutionState.RUNNING
        self.output: list[str] = []
        self.trace_enabled = False
        self.step_count = 0
        self.max_steps = 100_000_000  # Prevent infinite loops # TODO: Make it configurable

    def interpret_module(self, module: MIRModule, trace: bool = False) -> Any:
        """Interpret a MIR module.

        Args:
            module: The MIR module to interpret.
            trace: Whether to enable execution tracing.

        Returns:
            The return value of the main function.
        """
        self.module = module
        self.trace_enabled = trace
        self.state = ExecutionState.RUNNING
        self.output.clear()
        self.step_count = 0

        # Find main function
        main_func = module.get_function("__main__")
        if not main_func:
            self.state = ExecutionState.ERROR
            raise RuntimeError("No main function found")

        # Execute main function
        return self.call_function(main_func, [])

    def call_function(self, function: MIRFunction, args: list[Any]) -> Any:
        """Call a MIR function.

        Args:
            function: The function to call.
            args: Arguments to pass.

        Returns:
            The function's return value.
        """
        # Create new frame
        if not function.cfg.entry_block:
            raise RuntimeError(f"Function {function.name} has no entry block")
        frame = Frame(
            function=function,
            locals={},
            temps={},
            current_block=function.cfg.entry_block,
            instruction_index=0,
        )

        # Initialize parameters
        for i, param in enumerate(function.params):
            if i < len(args):
                frame.locals[param.name if hasattr(param, "name") else str(param)] = args[i]

        # Push frame
        self.frames.append(frame)

        # Execute function
        while self.state == ExecutionState.RUNNING and self.frames and frame in self.frames:
            self.step()

        # Return the value (frame was already popped by Return instruction)
        return frame.return_value

    def step(self) -> None:
        """Execute one instruction."""
        if not self.frames:
            self.state = ExecutionState.RETURNED
            return

        # Check step limit
        self.step_count += 1
        if self.step_count > self.max_steps:
            self.state = ExecutionState.ERROR
            raise RuntimeError(f"Execution limit exceeded ({self.max_steps} steps)")

        frame = self.frames[-1]

        # Check if we've reached the end of the block
        if frame.instruction_index >= len(frame.current_block.instructions):
            # Handle implicit fall-through or error
            self.state = ExecutionState.ERROR
            raise RuntimeError(f"Reached end of block {frame.current_block.label} without terminator")

        # Get current instruction
        inst = frame.current_block.instructions[frame.instruction_index]

        if self.trace_enabled:
            self._trace_instruction(inst)

        # Execute instruction
        self._execute_instruction(inst)

        # Move to next instruction unless we jumped
        if isinstance(inst, Jump | ConditionalJump | Return):
            # Control flow instructions handle their own program counter
            pass
        else:
            frame.instruction_index += 1

    def _execute_instruction(self, inst: MIRInstruction) -> None:
        """Execute a single MIR instruction.

        Args:
            inst: The instruction to execute.
        """
        frame = self.frames[-1]

        if isinstance(inst, LoadConst):
            self._store_value(inst.dest, inst.constant.value)

        elif isinstance(inst, LoadVar):
            value = self._load_value(inst.var)
            self._store_value(inst.dest, value)

        elif isinstance(inst, StoreVar):
            value = self._load_value(inst.source)
            self._store_value(inst.var, value)

        elif isinstance(inst, Copy):
            value = self._load_value(inst.source)
            self._store_value(inst.dest, value)

        elif isinstance(inst, BinaryOp):
            left = self._load_value(inst.left)
            right = self._load_value(inst.right)
            result = self._eval_binary_op(inst.op, left, right)
            self._store_value(inst.dest, result)

        elif isinstance(inst, UnaryOp):
            operand = self._load_value(inst.operand)
            result = self._eval_unary_op(inst.op, operand)
            self._store_value(inst.dest, result)

        elif isinstance(inst, Jump):
            self._jump_to_block(inst.label)

        elif isinstance(inst, ConditionalJump):
            condition = self._load_value(inst.condition)
            if self._is_truthy(condition):
                self._jump_to_block(inst.true_label)
            elif inst.false_label:
                self._jump_to_block(inst.false_label)
            else:
                # Fall through to next instruction
                frame.instruction_index += 1

        elif isinstance(inst, Return):
            if inst.value:
                frame.return_value = self._load_value(inst.value)
            else:
                frame.return_value = None
            # For non-main functions, pop the frame immediately
            if len(self.frames) > 1:
                self.frames.pop()
            else:
                # For main function, set state to returned
                self.state = ExecutionState.RETURNED

        elif isinstance(inst, Call):
            # Get function
            if isinstance(inst.func, FunctionRef):
                func_name = inst.func.name
                if self.module:
                    called_func = self.module.get_function(func_name)
                    if called_func:
                        # Evaluate arguments
                        arg_values = [self._load_value(arg) for arg in inst.args]
                        # Call function
                        result = self.call_function(called_func, arg_values)
                        # Store result if needed
                        if inst.dest:
                            self._store_value(inst.dest, result)
                    else:
                        # Built-in function
                        self._call_builtin(func_name, inst.args, inst.dest, inst)
                else:
                    raise RuntimeError(f"No module context for function call: {func_name}")
            else:
                raise RuntimeError(f"Unsupported function reference: {inst.func}")

        elif isinstance(inst, Print):
            value = self._load_value(inst.value)
            self.output.append(str(value))
            if self.trace_enabled:
                print(f"OUTPUT: {value}")

        elif isinstance(inst, Assert):
            condition = self._load_value(inst.condition)
            if not self._is_truthy(condition):
                message = inst.message or "Assertion failed"
                self.state = ExecutionState.ERROR
                raise AssertionError(message)

        elif isinstance(inst, Select):
            condition = self._load_value(inst.condition)
            if self._is_truthy(condition):
                value = self._load_value(inst.true_val)
            else:
                value = self._load_value(inst.false_val)
            self._store_value(inst.dest, value)

        elif isinstance(inst, Phi):
            # Phi nodes are handled during SSA construction
            # In interpreter, we just copy the appropriate value
            # This is simplified - real phi handling needs predecessor tracking
            if inst.incoming:
                value = self._load_value(inst.incoming[0][0])
                self._store_value(inst.dest, value)

        elif isinstance(inst, Scope):
            # Scope markers don't affect execution
            pass

        elif isinstance(inst, Pop):
            # Pop instruction - just load the value to evaluate it
            # but don't store it anywhere (side effects only)
            self._load_value(inst.value)

        elif isinstance(inst, Nop):
            # No operation
            pass

        else:
            raise RuntimeError(f"Unsupported instruction: {type(inst).__name__}")

    def _load_value(self, value: MIRValue) -> Any:
        """Load a value from storage.

        Args:
            value: The MIR value to load.

        Returns:
            The actual value.
        """
        frame = self.frames[-1]

        if isinstance(value, Constant):
            return value.value
        elif isinstance(value, Variable):
            name = value.name if hasattr(value, "name") else str(value)
            if name in frame.locals:
                return frame.locals[name]
            elif name in self.globals:
                return self.globals[name]
            else:
                raise RuntimeError(f"Undefined variable: {name}")
        elif isinstance(value, Temp):
            if value.id in frame.temps:
                return frame.temps[value.id]
            else:
                raise RuntimeError(f"Undefined temporary: t{value.id}")
        else:
            raise RuntimeError(f"Unsupported value type: {type(value).__name__}")

    def _store_value(self, dest: MIRValue, value: Any) -> None:
        """Store a value to a destination.

        Args:
            dest: The destination MIR value.
            value: The value to store.
        """
        frame = self.frames[-1]

        if isinstance(dest, Variable):
            name = dest.name if hasattr(dest, "name") else str(dest)
            frame.locals[name] = value
        elif isinstance(dest, Temp):
            frame.temps[dest.id] = value
        else:
            raise RuntimeError(f"Cannot store to {type(dest).__name__}")

    def _eval_binary_op(self, op: str, left: Any, right: Any) -> Any:
        """Evaluate a binary operation.

        Args:
            op: The operation.
            left: Left operand.
            right: Right operand.

        Returns:
            The result.
        """
        from machine_dialect.errors.exceptions import MDRuntimeError

        try:
            if op == "+":
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                if right == 0:
                    frame = self.frames[-1]
                    current_inst = frame.current_block.instructions[frame.instruction_index - 1]
                    line, column = current_inst.source_location
                    raise MDRuntimeError("Division by zero", line=line, column=column)
                return left / right if isinstance(left, float) or isinstance(right, float) else left // right
            elif op == "%":
                return left % right
            elif op == "<":
                return left < right
            elif op == ">":
                return left > right
            elif op == "<=":
                return left <= right
            elif op == ">=":
                return left >= right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "&&":
                return self._is_truthy(left) and self._is_truthy(right)
            elif op == "||":
                return self._is_truthy(left) or self._is_truthy(right)
            else:
                frame = self.frames[-1]
                current_inst = frame.current_block.instructions[frame.instruction_index - 1]
                line, column = current_inst.source_location
                raise MDRuntimeError(f"Unsupported binary operation: {op}", line=line, column=column)
        except TypeError as err:
            frame = self.frames[-1]
            current_inst = frame.current_block.instructions[frame.instruction_index - 1]
            left_type = type(left).__name__
            right_type = type(right).__name__
            left_repr = repr(left) if left is not None else "None"
            right_repr = repr(right) if right is not None else "None"
            line, column = current_inst.source_location
            raise MDRuntimeError(
                f"Cannot apply '{op}' to {left_type} and {right_type}: {left_repr} {op} {right_repr}",
                line=line,
                column=column,
            ) from err

    def _eval_unary_op(self, op: str, operand: Any) -> Any:
        """Evaluate a unary operation.

        Args:
            op: The operation.
            operand: The operand.

        Returns:
            The result.
        """
        if op == "-":
            try:
                return -operand
            except TypeError:
                from machine_dialect.errors.exceptions import MDRuntimeError

                # Get current instruction for debugging context
                frame = self.frames[-1]
                current_inst = frame.current_block.instructions[frame.instruction_index - 1]
                operand_type = type(operand).__name__
                operand_repr = repr(operand) if operand is not None else "None"
                # Use source_location from instruction
                line, column = current_inst.source_location
                raise MDRuntimeError(
                    f"Cannot apply unary minus to {operand_type}: {operand_repr}. Instruction: {current_inst}",
                    line=line,
                    column=column,
                ) from None
        elif op == "!":
            return not self._is_truthy(operand)
        else:
            from machine_dialect.errors.exceptions import MDRuntimeError

            frame = self.frames[-1]
            current_inst = frame.current_block.instructions[frame.instruction_index - 1]
            line, column = current_inst.source_location
            raise MDRuntimeError(f"Unsupported unary operation: {op}", line=line, column=column)

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy.

        Args:
            value: The value to check.

        Returns:
            Whether the value is truthy.
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int | float):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def _jump_to_block(self, label: str) -> None:
        """Jump to a labeled block.

        Args:
            label: The block label.
        """
        frame = self.frames[-1]
        block = frame.function.cfg.get_block(label)
        if block:
            frame.current_block = block
            frame.instruction_index = 0
        else:
            raise RuntimeError(f"Jump to undefined block: {label}")

    def _call_builtin(self, name: str, args: list[MIRValue], dest: MIRValue | None, inst: MIRInstruction) -> None:
        """Call a built-in function.

        Args:
            name: Function name.
            args: Arguments.
            dest: Destination for result.
            inst: The Call instruction (for error reporting).
        """
        # Evaluate arguments
        arg_values = [self._load_value(arg) for arg in args]

        # Handle built-ins
        if name == "print":
            for val in arg_values:
                self.output.append(str(val))
                if self.trace_enabled:
                    print(f"OUTPUT: {val}")
            if dest:
                self._store_value(dest, None)
        elif name == "len":
            if arg_values:
                result_len = len(arg_values[0])
                if dest:
                    self._store_value(dest, result_len)
        elif name == "str":
            if arg_values:
                result_str = str(arg_values[0])
                if dest:
                    self._store_value(dest, result_str)
        elif name == "int":
            if arg_values:
                result_int = int(arg_values[0])
                if dest:
                    self._store_value(dest, result_int)
        elif name == "float":
            if arg_values:
                result_float = float(arg_values[0])
                if dest:
                    self._store_value(dest, result_float)
        else:
            # Get source location from instruction if available
            line = inst.source_location[0] if inst.source_location else None
            column = inst.source_location[1] if inst.source_location else None
            raise MDRuntimeError(f"Unknown built-in function: `{name}`", line=line, column=column)

    def _trace_instruction(self, inst: MIRInstruction) -> None:
        """Trace instruction execution.

        Args:
            inst: The instruction being executed.
        """
        frame = self.frames[-1]
        print(f"[{self.step_count}] {frame.current_block.label}:{frame.instruction_index} - {inst}")

    def get_output(self) -> list[str]:
        """Get the output produced during execution.

        Returns:
            List of output strings.
        """
        return self.output.copy()

    def reset(self) -> None:
        """Reset the interpreter state."""
        self.frames.clear()
        self.globals.clear()
        self.output.clear()
        self.state = ExecutionState.RUNNING
        self.step_count = 0
