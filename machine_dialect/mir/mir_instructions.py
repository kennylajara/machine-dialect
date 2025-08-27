"""MIR Three-Address Code Instructions.

This module defines the TAC instruction set used in the MIR.
Each instruction follows the three-address code format where possible.
"""

from abc import ABC, abstractmethod
from typing import Any

from .mir_values import Constant, FunctionRef, MIRValue, Variable


class MIRInstruction(ABC):
    """Base class for all MIR instructions."""

    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the instruction."""
        pass

    @abstractmethod
    def get_uses(self) -> list[MIRValue]:
        """Get values used (read) by this instruction.

        Returns:
            List of values that this instruction reads.
        """
        pass

    @abstractmethod
    def get_defs(self) -> list[MIRValue]:
        """Get values defined (written) by this instruction.

        Returns:
            List of values that this instruction writes.
        """
        pass

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:  # noqa: B027
        """Replace uses of a value in this instruction.

        Args:
            old_value: The value to replace.
            new_value: The replacement value.
        """
        # Default implementation does nothing - this is intentional
        # Subclasses should override if they have uses
        # Not abstract because many instructions don't use values
        pass


class BinaryOp(MIRInstruction):
    """Binary operation: dest = left op right."""

    def __init__(self, dest: MIRValue, op: str, left: MIRValue, right: MIRValue) -> None:
        """Initialize a binary operation.

        Args:
            dest: Destination to store result.
            op: Operator (+, -, *, /, %, ^, ==, !=, <, >, <=, >=, and, or).
            left: Left operand.
            right: Right operand.
        """
        self.dest = dest
        self.op = op
        self.left = left
        self.right = right

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.left} {self.op} {self.right}"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.left, self.right]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.left == old_value:
            self.left = new_value
        if self.right == old_value:
            self.right = new_value


class UnaryOp(MIRInstruction):
    """Unary operation: dest = op operand."""

    def __init__(self, dest: MIRValue, op: str, operand: MIRValue) -> None:
        """Initialize a unary operation.

        Args:
            dest: Destination to store result.
            op: Operator (-, not).
            operand: Operand.
        """
        self.dest = dest
        self.op = op
        self.operand = operand

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.op} {self.operand}"

    def get_uses(self) -> list[MIRValue]:
        """Get operand used."""
        return [self.operand]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.operand == old_value:
            self.operand = new_value


class Copy(MIRInstruction):
    """Copy instruction: dest = source."""

    def __init__(self, dest: MIRValue, source: MIRValue) -> None:
        """Initialize a copy instruction.

        Args:
            dest: Destination.
            source: Source value.
        """
        self.dest = dest
        self.source = source

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.source}"

    def get_uses(self) -> list[MIRValue]:
        """Get source used."""
        return [self.source]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.source == old_value:
            self.source = new_value


class LoadConst(MIRInstruction):
    """Load constant: dest = constant."""

    def __init__(self, dest: MIRValue, value: Any) -> None:
        """Initialize a load constant instruction.

        Args:
            dest: Destination.
            value: Constant value to load.
        """
        self.dest = dest
        self.constant = Constant(value) if not isinstance(value, Constant) else value

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.constant}"

    def get_uses(self) -> list[MIRValue]:
        """Constants are not uses."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]


class LoadVar(MIRInstruction):
    """Load variable: dest = variable."""

    def __init__(self, dest: MIRValue, var: Variable) -> None:
        """Initialize a load variable instruction.

        Args:
            dest: Destination temporary.
            var: Variable to load from.
        """
        self.dest = dest
        self.var = var

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.var}"

    def get_uses(self) -> list[MIRValue]:
        """Get variable used."""
        return [self.var]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.var == old_value and isinstance(new_value, Variable):
            self.var = new_value


class StoreVar(MIRInstruction):
    """Store to variable: variable = source."""

    def __init__(self, var: Variable, source: MIRValue) -> None:
        """Initialize a store variable instruction.

        Args:
            var: Variable to store to.
            source: Source value.
        """
        self.var = var
        self.source = source

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.var} = {self.source}"

    def get_uses(self) -> list[MIRValue]:
        """Get source used."""
        return [self.source]

    def get_defs(self) -> list[MIRValue]:
        """Get variable defined."""
        return [self.var]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.source == old_value:
            self.source = new_value


class Call(MIRInstruction):
    """Function call: dest = call func(args)."""

    def __init__(self, dest: MIRValue | None, func: FunctionRef | str, args: list[MIRValue]) -> None:
        """Initialize a function call.

        Args:
            dest: Optional destination for return value.
            func: Function to call (FunctionRef or name string).
            args: Arguments to pass.
        """
        self.dest = dest
        self.func = FunctionRef(func) if isinstance(func, str) else func
        self.args = args

    def __str__(self) -> str:
        """Return string representation."""
        args_str = ", ".join(str(arg) for arg in self.args)
        if self.dest:
            return f"{self.dest} = call {self.func}({args_str})"
        else:
            return f"call {self.func}({args_str})"

    def get_uses(self) -> list[MIRValue]:
        """Get arguments used."""
        return self.args.copy()

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined if any."""
        return [self.dest] if self.dest else []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value in arguments."""
        self.args = [new_value if arg == old_value else arg for arg in self.args]


class Return(MIRInstruction):
    """Return instruction: return value."""

    def __init__(self, value: MIRValue | None = None) -> None:
        """Initialize a return instruction.

        Args:
            value: Optional value to return.
        """
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        if self.value:
            return f"return {self.value}"
        else:
            return "return"

    def get_uses(self) -> list[MIRValue]:
        """Get value used if any."""
        return [self.value] if self.value else []

    def get_defs(self) -> list[MIRValue]:
        """Return defines nothing."""
        return []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old_value:
            self.value = new_value


class Jump(MIRInstruction):
    """Unconditional jump: goto label."""

    def __init__(self, label: str) -> None:
        """Initialize a jump instruction.

        Args:
            label: Target label.
        """
        self.label = label

    def __str__(self) -> str:
        """Return string representation."""
        return f"goto {self.label}"

    def get_uses(self) -> list[MIRValue]:
        """Jump uses nothing."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Jump defines nothing."""
        return []


class ConditionalJump(MIRInstruction):
    """Conditional jump: if condition goto true_label else false_label."""

    def __init__(self, condition: MIRValue, true_label: str, false_label: str | None = None) -> None:
        """Initialize a conditional jump.

        Args:
            condition: Condition to test.
            true_label: Label to jump to if true.
            false_label: Optional label to jump to if false (falls through if None).
        """
        self.condition = condition
        self.true_label = true_label
        self.false_label = false_label

    def __str__(self) -> str:
        """Return string representation."""
        if self.false_label:
            return f"if {self.condition} goto {self.true_label} else {self.false_label}"
        else:
            return f"if {self.condition} goto {self.true_label}"

    def get_uses(self) -> list[MIRValue]:
        """Get condition used."""
        return [self.condition]

    def get_defs(self) -> list[MIRValue]:
        """Conditional jump defines nothing."""
        return []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.condition == old_value:
            self.condition = new_value


class Phi(MIRInstruction):
    """SSA phi node: dest = φ(value1, value2, ...).

    Phi nodes are used at join points in SSA form to merge values
    from different control flow paths.
    """

    def __init__(self, dest: MIRValue, incoming: list[tuple[MIRValue, str]]) -> None:
        """Initialize a phi node.

        Args:
            dest: Destination to store merged value.
            incoming: List of (value, predecessor_label) pairs.
        """
        self.dest = dest
        self.incoming = incoming

    def __str__(self) -> str:
        """Return string representation."""
        args = ", ".join(f"{val}:{label}" for val, label in self.incoming)
        return f"{self.dest} = φ({args})"

    def get_uses(self) -> list[MIRValue]:
        """Get all incoming values."""
        return [val for val, _ in self.incoming]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value in incoming values."""
        self.incoming = [(new_value if val == old_value else val, label) for val, label in self.incoming]

    def add_incoming(self, value: MIRValue, label: str) -> None:
        """Add an incoming value from a predecessor.

        Args:
            value: The value from the predecessor.
            label: The predecessor's label.
        """
        self.incoming.append((value, label))


class Label(MIRInstruction):
    """Label pseudo-instruction: label_name:."""

    def __init__(self, name: str) -> None:
        """Initialize a label.

        Args:
            name: Label name.
        """
        self.name = name

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name}:"

    def get_uses(self) -> list[MIRValue]:
        """Labels use nothing."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Labels define nothing."""
        return []
