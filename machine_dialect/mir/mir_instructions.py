"""MIR Three-Address Code Instructions.

This module defines the TAC instruction set used in the MIR.
Each instruction follows the three-address code format where possible.
"""

from abc import ABC, abstractmethod
from typing import Any

from .mir_types import MIRType, MIRUnionType
from .mir_values import Constant, FunctionRef, MIRValue, Temp, Variable


class MIRInstruction(ABC):
    """Base class for all MIR instructions with rich metadata."""

    def __init__(self, source_location: tuple[int, int]) -> None:
        """Initialize instruction with metadata.

        Args:
            source_location: Required (line, column) from source code for error reporting.
        """
        # Rich metadata for optimization
        self.result_type: MIRType | None = None  # Inferred type of result
        self.is_pure: bool = False  # No side effects
        self.can_throw: bool = False  # Can raise exceptions
        self.cost: int = 1  # Estimated execution cost
        self.is_commutative: bool = False  # Operands can be swapped
        self.is_associative: bool = False  # Can be regrouped
        self.memory_effects: set[str] = set()  # Memory locations affected
        # Source location for error reporting (REQUIRED for proper error messages)
        self.source_location: tuple[int, int] = source_location  # (line, column)

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

    def __init__(
        self, dest: MIRValue, op: str, left: MIRValue, right: MIRValue, source_location: tuple[int, int]
    ) -> None:
        """Initialize a binary operation.

        Args:
            dest: Destination to store result.
            op: Operator (+, -, *, /, %, ^, ==, !=, <, >, <=, >=, and, or).
            left: Left operand.
            right: Right operand.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.op = op
        self.left = left
        self.right = right

        # Set metadata based on operator
        if op in ["+", "*", "==", "!=", "and", "or"]:
            self.is_commutative = True
        if op in ["+", "*", "and", "or"]:
            self.is_associative = True
        if op in ["+", "-", "*", "==", "!=", "<", ">", "<=", ">="]:
            self.is_pure = True
        if op == "/":
            self.can_throw = True  # Division by zero

        # Set cost estimates
        if op in ["*", "/", "%", "**"]:
            self.cost = 3
        elif op in ["+", "-"]:
            self.cost = 1
        else:
            self.cost = 2

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

    def __init__(self, dest: MIRValue, op: str, operand: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize a unary operation.

        Args:
            dest: Destination to store result.
            op: Operator (-, not, abs).
            operand: Operand.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.op = op
        self.operand = operand

        # All unary ops are pure
        self.is_pure = True
        self.cost = 1

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


class ShiftOp(MIRInstruction):
    """Bitwise shift operation: dest = left op right.

    Used for strength reduction optimizations where multiply/divide
    by powers of 2 are converted to shift operations.
    """

    def __init__(
        self, dest: MIRValue, left: MIRValue, right: MIRValue, op: str, source_location: tuple[int, int]
    ) -> None:
        """Initialize a shift operation.

        Args:
            dest: Destination to store result.
            left: Value to shift.
            right: Shift amount.
            op: Shift operator ('<<' for left shift, '>>' for right shift).
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.left = left
        self.right = right
        self.op = op

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


class Copy(MIRInstruction):
    """Copy instruction: dest = source."""

    def __init__(self, dest: MIRValue, source: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize a copy instruction.

        Args:
            dest: Destination.
            source: Source value.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(self, dest: MIRValue, value: Any, source_location: tuple[int, int]) -> None:
        """Initialize a load constant instruction.

        Args:
            dest: Destination.
            value: Constant value to load.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(self, dest: MIRValue, var: Variable, source_location: tuple[int, int]) -> None:
        """Initialize a load variable instruction.

        Args:
            dest: Destination temporary.
            var: Variable to load from.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(self, var: Variable, source: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize a store variable instruction.

        Args:
            var: Variable to store to.
            source: Source value.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(
        self,
        dest: MIRValue | None,
        func: FunctionRef | str,
        args: list[MIRValue],
        source_location: tuple[int, int],
        is_tail_call: bool = False,
    ) -> None:
        """Initialize a function call.

        Args:
            dest: Optional destination for return value.
            func: Function to call (FunctionRef or name string).
            args: Arguments to pass.
            source_location: Source code location (line, column).
            is_tail_call: Whether this is a tail call that can be optimized.
        """
        super().__init__(source_location)
        self.dest = dest
        self.func = FunctionRef(func) if isinstance(func, str) else func
        self.args = args
        self.is_tail_call = is_tail_call

    def __str__(self) -> str:
        """Return string representation."""
        args_str = ", ".join(str(arg) for arg in self.args)
        tail_str = " [tail]" if self.is_tail_call else ""
        if self.dest:
            return f"{self.dest} = call {self.func}({args_str}){tail_str}"
        else:
            return f"call {self.func}({args_str}){tail_str}"

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

    def __init__(self, source_location: tuple[int, int], value: MIRValue | None = None) -> None:
        """Initialize a return instruction.

        Args:
            source_location: Source code location (line, column).
            value: Optional value to return.
        """
        super().__init__(source_location)
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

    def __init__(self, label: str, source_location: tuple[int, int]) -> None:
        """Initialize a jump instruction.

        Args:
            label: Target label.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(
        self, condition: MIRValue, true_label: str, source_location: tuple[int, int], false_label: str | None = None
    ) -> None:
        """Initialize a conditional jump.

        Args:
            condition: Condition to test.
            true_label: Label to jump to if true.
            source_location: Source code location (line, column).
            false_label: Optional label to jump to if false (falls through if None).
        """
        super().__init__(source_location)
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

    def __init__(self, dest: MIRValue, incoming: list[tuple[MIRValue, str]], source_location: tuple[int, int]) -> None:
        """Initialize a phi node.

        Args:
            dest: Destination to store merged value.
            incoming: List of (value, predecessor_label) pairs.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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

    def __init__(self, name: str, source_location: tuple[int, int]) -> None:
        """Initialize a label.

        Args:
            name: Label name.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
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


class Print(MIRInstruction):
    """Print instruction for Say/Tell statements: print value."""

    def __init__(self, value: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize a print instruction.

        Args:
            value: Value to print.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"print {self.value}"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Print defines nothing."""
        return []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old_value:
            self.value = new_value


class Nop(MIRInstruction):
    """No-operation instruction."""

    def __str__(self) -> str:
        """Return string representation."""
        return "nop"

    def get_uses(self) -> list[MIRValue]:
        """Nop uses nothing."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Nop defines nothing."""
        return []


class Assert(MIRInstruction):
    """Assert instruction for runtime checks: assert condition."""

    def __init__(self, condition: MIRValue, source_location: tuple[int, int], message: str | None = None) -> None:
        """Initialize an assert instruction.

        Args:
            condition: Condition to check.
            source_location: Source code location (line, column).
            message: Optional error message.
        """
        super().__init__(source_location)
        self.condition = condition
        self.message = message

    def __str__(self) -> str:
        """Return string representation."""
        if self.message:
            return f'assert {self.condition}, "{self.message}"'
        return f"assert {self.condition}"

    def get_uses(self) -> list[MIRValue]:
        """Get condition used."""
        return [self.condition]

    def get_defs(self) -> list[MIRValue]:
        """Assert defines nothing."""
        return []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.condition == old_value:
            self.condition = new_value


class Select(MIRInstruction):
    """Select instruction (ternary): dest = condition ? true_val : false_val."""

    def __init__(
        self,
        dest: MIRValue,
        condition: MIRValue,
        true_val: MIRValue,
        false_val: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize a select instruction.

        Args:
            dest: Destination to store result.
            condition: Condition to test.
            true_val: Value when condition is true.
            false_val: Value when condition is false.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.condition = condition
        self.true_val = true_val
        self.false_val = false_val

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = select {self.condition}, {self.true_val}, {self.false_val}"

    def get_uses(self) -> list[MIRValue]:
        """Get values used."""
        return [self.condition, self.true_val, self.false_val]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.condition == old_value:
            self.condition = new_value
        if self.true_val == old_value:
            self.true_val = new_value
        if self.false_val == old_value:
            self.false_val = new_value


class Scope(MIRInstruction):
    """Scope instruction for block management: begin_scope/end_scope."""

    def __init__(self, source_location: tuple[int, int], is_begin: bool = True) -> None:
        """Initialize a scope instruction.

        Args:
            source_location: Source code location (line, column).
            is_begin: True for begin_scope, False for end_scope.
        """
        super().__init__(source_location)
        self.is_begin = is_begin

    def __str__(self) -> str:
        """Return string representation."""
        return "begin_scope" if self.is_begin else "end_scope"

    def get_uses(self) -> list[MIRValue]:
        """Scope uses nothing."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Scope defines nothing."""
        return []


class GetAttr(MIRInstruction):
    """Get attribute instruction: dest = object.attr."""

    def __init__(self, dest: MIRValue, obj: MIRValue, attr: str) -> None:
        """Initialize a get attribute instruction.

        Args:
            dest: Destination to store attribute value.
            obj: Object to get attribute from.
            attr: Attribute name.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.obj = obj
        self.attr = attr

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.obj}.{self.attr}"

    def get_uses(self) -> list[MIRValue]:
        """Get object used."""
        return [self.obj]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.obj == old_value:
            self.obj = new_value


class SetAttr(MIRInstruction):
    """Set attribute instruction: object.attr = value."""

    def __init__(self, obj: MIRValue, attr: str, value: MIRValue) -> None:
        """Initialize a set attribute instruction.

        Args:
            obj: Object to set attribute on.
            attr: Attribute name.
            value: Value to set.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.obj = obj
        self.attr = attr
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.obj}.{self.attr} = {self.value}"

    def get_uses(self) -> list[MIRValue]:
        """Get object and value used."""
        return [self.obj, self.value]

    def get_defs(self) -> list[MIRValue]:
        """SetAttr defines nothing directly."""
        return []

    def replace_use(self, old_value: MIRValue, new_value: MIRValue) -> None:
        """Replace uses of a value."""
        if self.obj == old_value:
            self.obj = new_value
        if self.value == old_value:
            self.value = new_value


class Pop(MIRInstruction):
    """Pop instruction to discard a value from the stack.

    This instruction is used when an expression result is not needed,
    such as in expression statements where the value is computed but
    then discarded.
    """

    def __init__(self, value: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize a pop instruction.

        Args:
            value: The value to pop/discard.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"pop {self.value}"

    def get_uses(self) -> list[MIRValue]:
        """Get values used by this instruction."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get values defined by this instruction."""
        return []  # Pop doesn't define any values

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace a used value."""
        if self.value == old:
            self.value = new


class TypeCast(MIRInstruction):
    """Type cast instruction: dest = cast(value, target_type).

    Explicit type conversion between compatible types.
    """

    def __init__(self, dest: MIRValue, value: MIRValue, target_type: MIRType | MIRUnionType) -> None:
        """Initialize a type cast instruction.

        Args:
            dest: Destination to store cast result.
            value: Value to cast.
            target_type: Target type to cast to.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.value = value
        self.target_type = target_type

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = cast({self.value}, {self.target_type})"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old:
            self.value = new


class TypeCheck(MIRInstruction):
    """Type check instruction: dest = is_type(value, type).

    Runtime type checking for union types or dynamic typing.
    """

    def __init__(self, dest: MIRValue, value: MIRValue, check_type: MIRType | MIRUnionType) -> None:
        """Initialize a type check instruction.

        Args:
            dest: Destination to store boolean result.
            value: Value to check type of.
            check_type: Type to check against.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.value = value
        self.check_type = check_type

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = is_type({self.value}, {self.check_type})"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old:
            self.value = new


class TypeAssert(MIRInstruction):
    """Type assertion instruction: assert_type(value, type).

    Assert that a value has a specific type at runtime.
    Throws error if type mismatch.
    """

    def __init__(self, value: MIRValue, assert_type: MIRType | MIRUnionType) -> None:
        """Initialize a type assertion instruction.

        Args:
            value: Value to assert type of.
            assert_type: Expected type.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.value = value
        self.assert_type = assert_type

    def __str__(self) -> str:
        """Return string representation."""
        return f"assert_type({self.value}, {self.assert_type})"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """No values defined."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old:
            self.value = new


class NarrowType(MIRInstruction):
    """Type narrowing instruction: dest = narrow(value, type).

    Used after type checks to narrow union types to specific types.
    This is a compile-time hint for optimization, not a runtime operation.
    """

    def __init__(self, dest: MIRValue, value: MIRValue, narrow_type: MIRType) -> None:
        """Initialize a type narrowing instruction.

        Args:
            dest: Destination with narrowed type.
            value: Value to narrow.
            narrow_type: The specific type to narrow to.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.value = value
        self.narrow_type = narrow_type
        self.is_pure = True
        self.cost = 0  # Compile-time only

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = narrow({self.value}, {self.narrow_type})"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old:
            self.value = new


# New specialized instructions for better optimization


class SelectOp(MIRInstruction):
    """Conditional select without branches: dest = cond ? true_val : false_val."""

    def __init__(self, dest: MIRValue, cond: MIRValue, true_val: MIRValue, false_val: MIRValue) -> None:
        """Initialize a select operation.

        Args:
            dest: Destination to store result.
            cond: Condition to test.
            true_val: Value if condition is true.
            false_val: Value if condition is false.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.cond = cond
        self.true_val = true_val
        self.false_val = false_val
        self.is_pure = True
        self.cost = 1  # Branchless on modern CPUs

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = select({self.cond}, {self.true_val}, {self.false_val})"

    def get_uses(self) -> list[MIRValue]:
        """Get values used."""
        return [self.cond, self.true_val, self.false_val]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.cond == old:
            self.cond = new
        if self.true_val == old:
            self.true_val = new
        if self.false_val == old:
            self.false_val = new


class MinOp(MIRInstruction):
    """Minimum operation: dest = min(left, right)."""

    def __init__(self, dest: MIRValue, left: MIRValue, right: MIRValue) -> None:
        """Initialize a min operation.

        Args:
            dest: Destination to store result.
            left: Left operand.
            right: Right operand.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.left = left
        self.right = right
        self.is_pure = True
        self.is_commutative = True
        self.cost = 1

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = min({self.left}, {self.right})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.left, self.right]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.left == old:
            self.left = new
        if self.right == old:
            self.right = new


class MaxOp(MIRInstruction):
    """Maximum operation: dest = max(left, right)."""

    def __init__(self, dest: MIRValue, left: MIRValue, right: MIRValue) -> None:
        """Initialize a max operation.

        Args:
            dest: Destination to store result.
            left: Left operand.
            right: Right operand.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.left = left
        self.right = right
        self.is_pure = True
        self.is_commutative = True
        self.cost = 1

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = max({self.left}, {self.right})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.left, self.right]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.left == old:
            self.left = new
        if self.right == old:
            self.right = new


class SaturatingAddOp(MIRInstruction):
    """Saturating addition: dest = saturating_add(left, right, min, max)."""

    def __init__(
        self,
        dest: MIRValue,
        left: MIRValue,
        right: MIRValue,
        min_val: MIRValue | None = None,
        max_val: MIRValue | None = None,
    ) -> None:
        """Initialize a saturating add operation.

        Args:
            dest: Destination to store result.
            left: Left operand.
            right: Right operand.
            min_val: Minimum value (saturates to this).
            max_val: Maximum value (saturates to this).
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.left = left
        self.right = right
        self.min_val = min_val
        self.max_val = max_val
        self.is_pure = True
        self.is_commutative = True
        self.cost = 2

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = saturating_add({self.left}, {self.right})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        uses = [self.left, self.right]
        if self.min_val:
            uses.append(self.min_val)
        if self.max_val:
            uses.append(self.max_val)
        return uses

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.left == old:
            self.left = new
        if self.right == old:
            self.right = new
        if self.min_val == old:
            self.min_val = new
        if self.max_val == old:
            self.max_val = new


class PopCountOp(MIRInstruction):
    """Population count (count set bits): dest = popcount(value)."""

    def __init__(self, dest: MIRValue, value: MIRValue) -> None:
        """Initialize a popcount operation.

        Args:
            dest: Destination to store result.
            value: Value to count bits in.
        """
        super().__init__((0, 0))  # TODO: Add proper source_location
        self.dest = dest
        self.value = value
        self.is_pure = True
        self.cost = 1  # Hardware instruction on modern CPUs

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = popcount({self.value})"

    def get_uses(self) -> list[MIRValue]:
        """Get value used."""
        return [self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.value == old:
            self.value = new


# Array/List operations
class ArrayCreate(MIRInstruction):
    """Create a new array: dest = new_array(size)."""

    def __init__(self, dest: MIRValue, size: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize array creation.

        Args:
            dest: Destination to store array reference.
            size: Initial size of the array.
            source_location: Source location in original code.
        """
        super().__init__(source_location)
        self.dest = dest
        self.size = size
        self.cost = 2

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = new_array({self.size})"

    def get_uses(self) -> list[MIRValue]:
        """Get size value used."""
        return [self.size]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.size == old:
            self.size = new


class ArrayGet(MIRInstruction):
    """Get array element: dest = array[index]."""

    def __init__(
        self,
        dest: MIRValue,
        array: MIRValue,
        index: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array get operation.

        Args:
            dest: Destination to store the value.
            array: Array to get from.
            index: Index to access.
            source_location: Source location in original code.
        """
        super().__init__(source_location)
        self.dest = dest
        self.array = array
        self.index = index
        self.is_pure = True
        self.cost = 1

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.array}[{self.index}]"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.index]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.index == old:
            self.index = new


class ArraySet(MIRInstruction):
    """Set array element: array[index] = value."""

    def __init__(
        self,
        array: MIRValue,
        index: MIRValue,
        value: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array set operation.

        Args:
            array: Array to modify.
            index: Index to set.
            value: Value to store.
            source_location: Source location in original code.
        """
        super().__init__(source_location)
        self.array = array
        self.index = index
        self.value = value
        self.has_side_effects = True
        self.cost = 1

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.array}[{self.index}] = {self.value}"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.index, self.value]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies array in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.index == old:
            self.index = new
        if self.value == old:
            self.value = new


class ArrayLength(MIRInstruction):
    """Get array length: dest = len(array)."""

    def __init__(self, dest: MIRValue, array: MIRValue, source_location: tuple[int, int]) -> None:
        """Initialize array length operation.

        Args:
            dest: Destination to store length.
            array: Array to get length of.
            source_location: Source location in original code.
        """
        super().__init__(source_location)
        self.dest = dest
        self.array = array
        self.is_pure = True
        self.cost = 1

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = len({self.array})"

    def get_uses(self) -> list[MIRValue]:
        """Get array used."""
        return [self.array]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new


class ArrayAppend(MIRInstruction):
    """Append to array: array.append(value)."""

    def __init__(
        self,
        array: MIRValue,
        value: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array append operation.

        Args:
            array: Array to append to.
            value: Value to append.
            source_location: Source location in original code.
        """
        super().__init__(source_location)
        self.array = array
        self.value = value
        self.has_side_effects = True
        self.cost = 2

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.array}.append({self.value})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.value]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies array in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.value == old:
            self.value = new


class ArrayRemove(MIRInstruction):
    """Remove element from array at index: array.remove(index)."""

    def __init__(
        self,
        array: MIRValue,
        index: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array remove operation.

        Args:
            array: The array to remove from.
            index: The index to remove at.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.array = array
        self.index = index

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.array}.remove({self.index})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.index]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies array in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.index == old:
            self.index = new


class ArrayInsert(MIRInstruction):
    """Insert element into array at index: array.insert(index, value)."""

    def __init__(
        self,
        array: MIRValue,
        index: MIRValue,
        value: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array insert operation.

        Args:
            array: The array to insert into.
            index: The index to insert at.
            value: The value to insert.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.array = array
        self.index = index
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.array}.insert({self.index}, {self.value})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.index, self.value]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies array in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.index == old:
            self.index = new
        if self.value == old:
            self.value = new


class ArrayFindIndex(MIRInstruction):
    """Find index of value in array: dest = array.index(value)."""

    def __init__(
        self,
        dest: MIRValue,
        array: MIRValue,
        value: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array find index operation.

        Args:
            dest: Destination for the index (-1 if not found).
            array: The array to search in.
            value: The value to find.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.array = array
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.array}.index({self.value})"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array, self.value]

    def get_defs(self) -> list[MIRValue]:
        """Get destination defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new
        if self.value == old:
            self.value = new


class ArrayClear(MIRInstruction):
    """Clear all elements from array: array.clear()."""

    def __init__(
        self,
        array: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize array clear operation.

        Args:
            array: The array to clear.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.array = array

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.array}.clear()"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.array]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies array in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.array == old:
            self.array = new


# Dictionary Operations


class DictCreate(MIRInstruction):
    """Create a new dictionary: dest = {}."""

    def __init__(
        self,
        dest: Temp,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary creation.

        Args:
            dest: Destination temp for the new dictionary.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {{}}"

    def get_uses(self) -> list[MIRValue]:
        """DictCreate uses nothing."""
        return []

    def get_defs(self) -> list[MIRValue]:
        """Get defined value."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        pass  # No uses to replace


class DictGet(MIRInstruction):
    """Get value from dictionary by key: dest = dict[key]."""

    def __init__(
        self,
        dest: Temp,
        dict_val: MIRValue,
        key: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary get operation.

        Args:
            dest: Destination temp for the value.
            dict_val: The dictionary to get from.
            key: The key to look up.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.dict_val = dict_val
        self.key = key

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.dict_val}[{self.key}]"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val, self.key]

    def get_defs(self) -> list[MIRValue]:
        """Get defined value."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.key == old:
            self.key = new


class DictSet(MIRInstruction):
    """Set value in dictionary: dict[key] = value."""

    def __init__(
        self,
        dict_val: MIRValue,
        key: MIRValue,
        value: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary set operation.

        Args:
            dict_val: The dictionary to modify.
            key: The key to set.
            value: The value to set.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dict_val = dict_val
        self.key = key
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dict_val}[{self.key}] = {self.value}"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val, self.key, self.value]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies dict in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.key == old:
            self.key = new
        if self.value == old:
            self.value = new


class DictRemove(MIRInstruction):
    """Remove key from dictionary: del dict[key]."""

    def __init__(
        self,
        dict_val: MIRValue,
        key: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary remove operation.

        Args:
            dict_val: The dictionary to modify.
            key: The key to remove.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dict_val = dict_val
        self.key = key

    def __str__(self) -> str:
        """Return string representation."""
        return f"del {self.dict_val}[{self.key}]"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val, self.key]

    def get_defs(self) -> list[MIRValue]:
        """No direct defs, modifies dict in place."""
        return []

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.key == old:
            self.key = new


class DictKeys(MIRInstruction):
    """Get all keys from a dictionary as an array: dest = dict.keys()."""

    def __init__(
        self,
        dest: MIRValue,
        dict_val: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary keys extraction.

        Args:
            dest: Destination register for the keys array.
            dict_val: The dictionary to get keys from.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.dict_val = dict_val

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.dict_val}.keys()"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val]

    def get_defs(self) -> list[MIRValue]:
        """Get values defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.dest == old:
            self.dest = new


class DictValues(MIRInstruction):
    """Get all values from a dictionary as an array: dest = dict.values()."""

    def __init__(
        self,
        dest: MIRValue,
        dict_val: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary values extraction.

        Args:
            dest: Destination register for the values array.
            dict_val: The dictionary to get values from.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.dict_val = dict_val

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.dict_val}.values()"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val]

    def get_defs(self) -> list[MIRValue]:
        """Get values defined."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.dest == old:
            self.dest = new


class DictContains(MIRInstruction):
    """Check if key exists in dictionary: dest = key in dict."""

    def __init__(
        self,
        dest: Temp,
        dict_val: MIRValue,
        key: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary contains check.

        Args:
            dest: Destination temp for the boolean result.
            dict_val: The dictionary to check.
            key: The key to look for.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dest = dest
        self.dict_val = dict_val
        self.key = key

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.dest} = {self.key} in {self.dict_val}"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val, self.key]

    def get_defs(self) -> list[MIRValue]:
        """Get defined value."""
        return [self.dest]

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
        if self.key == old:
            self.key = new


class DictClear(MIRInstruction):
    """Clear all entries from dictionary: dict.clear()."""

    def __init__(
        self,
        dict_val: MIRValue,
        source_location: tuple[int, int],
    ) -> None:
        """Initialize dictionary clear operation.

        Args:
            dict_val: The dictionary to clear.
            source_location: Source code location (line, column).
        """
        super().__init__(source_location)
        self.dict_val = dict_val
        self.has_side_effects = True
        self.cost = 2

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"DictClear {self.dict_val}"

    def get_uses(self) -> list[MIRValue]:
        """Get operands used."""
        return [self.dict_val]

    def get_defs(self) -> list[MIRValue]:
        """Get defined values."""
        return []  # Modifies dict in-place

    def replace_use(self, old: MIRValue, new: MIRValue) -> None:
        """Replace uses of a value."""
        if self.dict_val == old:
            self.dict_val = new
