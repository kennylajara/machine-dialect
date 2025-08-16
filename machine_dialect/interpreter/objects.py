from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import ClassVar

from machine_dialect.errors.messages import (
    DIVISION_BY_ZERO,
    UNSUPPORTED_OPERAND_TYPE,
    UNSUPPORTED_UNARY_OPERAND,
)


class ObjectType(Enum):
    """Represents an object type."""

    BOOLEAN = auto()
    EMPTY = auto()
    ERROR = auto()
    FLOAT = auto()
    INTEGER = auto()
    RETURN = auto()
    STRING = auto()
    URL = auto()


class Object(ABC):
    """Represents an abstract object type."""

    @property
    @abstractmethod
    def type(self) -> ObjectType:
        pass

    @abstractmethod
    def inspect(self) -> str:
        pass

    def react_to_infix_operator_addition(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="+", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_substraction(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="-", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_multiplication(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="*", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_division(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="/", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than_or_equal(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than_or_equal(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_equals(self, other: Object) -> Object:
        # Value equality: compare inspect() values
        return Boolean(self.inspect() == other.inspect())

    def react_to_infix_operator_not_equals(self, other: Object) -> Object:
        # Value inequality: compare inspect() values
        return Boolean(self.inspect() != other.inspect())

    def react_to_infix_operator_strict_equals(self, other: Object) -> Object:
        # Strict equality: same type AND same value
        return Boolean(self.type == other.type and self.inspect() == other.inspect())

    def react_to_infix_operator_strict_not_equals(self, other: Object) -> Object:
        # Strict inequality: different type OR different value
        return Boolean(self.type != other.type or self.inspect() != other.inspect())

    def react_to_prefix_operator_not(self) -> Object:
        return Error(UNSUPPORTED_UNARY_OPERAND.format(operator="not", type=self.type.name))

    def react_to_prefix_operator_minus(self) -> Object:
        return Error(UNSUPPORTED_UNARY_OPERAND.format(operator="-", type=self.type.name))

    def react_to_infix_operator_and(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="and", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_or(self, other: Object) -> Object:
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="or", left_type=self.type.name, right_type=other.type.name)
        )


class Boolean(Object):
    _instances: ClassVar[dict[bool, Boolean | None]] = {True: None, False: None}

    def __new__(cls, value: bool) -> Boolean:
        if cls._instances[value] is None:
            instance = super().__new__(cls)
            cls._instances[value] = instance
        return cls._instances[value]  # type: ignore[return-value]

    def __init__(self, value: bool) -> None:
        if not hasattr(self, "_value"):
            self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    @property
    def value(self) -> bool:
        return self._value

    def inspect(self) -> str:
        return "Yes" if self._value else "No"

    def react_to_prefix_operator_not(self) -> Object:
        return Boolean(not self._value)

    def react_to_infix_operator_and(self, other: Object) -> Object:
        if isinstance(other, Boolean):
            return Boolean(self.value and other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="and", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_or(self, other: Object) -> Object:
        if isinstance(other, Boolean):
            return Boolean(self.value or other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="or", left_type=self.type.name, right_type=other.type.name)
        )


class Environment:
    """Environment for storing variables."""

    def __init__(self) -> None:
        """Initialize an empty environment."""
        self.store: dict[str, Object] = {}

    def __getitem__(self, key: str) -> Object:
        return self.store[key]

    def __setitem__(self, key: str, value: Object) -> None:
        self.store[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.store


class Empty(Object):
    _instance: Empty | None = None

    def __new__(cls) -> Empty:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        pass

    @property
    def type(self) -> ObjectType:
        return ObjectType.EMPTY

    @property
    def value(self) -> None:
        return None

    def inspect(self) -> str:
        return "Empty"


class Error(Object):
    """Represents an error that occurred during evaluation."""

    def __init__(self, message: str) -> None:
        """Initialize an Error object.

        Args:
            message: The formatted error message.
        """
        self.message = message

    @property
    def type(self) -> ObjectType:
        return ObjectType.ERROR

    def inspect(self) -> str:
        return f"ERROR: {self.message}"


class Float(Object):
    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.FLOAT

    @property
    def value(self) -> float:
        return self._value

    def inspect(self) -> str:
        return str(self._value)

    def react_to_infix_operator_addition(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Float(self._value + other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="+", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_substraction(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Float(self._value - other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="-", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_multiplication(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Float(self._value * other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="*", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_division(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            if other.value == 0:
                return Error(DIVISION_BY_ZERO.format())
            return Float(self._value / other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="/", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Boolean(self._value < other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Boolean(self._value > other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than_or_equal(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Boolean(self._value <= other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than_or_equal(self, other: Object) -> Object:
        if isinstance(other, Float) or isinstance(other, Integer):
            return Boolean(self._value >= other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_equals(self, other: Object) -> Object:
        # Allow numeric comparison between Float and Integer
        if isinstance(other, Float | Integer):
            return Boolean(self._value == other.value)
        return super().react_to_infix_operator_equals(other)

    def react_to_infix_operator_not_equals(self, other: Object) -> Object:
        # Allow numeric comparison between Float and Integer
        if isinstance(other, Float | Integer):
            return Boolean(self._value != other.value)
        return super().react_to_infix_operator_not_equals(other)

    def react_to_prefix_operator_minus(self) -> Object:
        return Float(-self._value if self._value != 0.0 else 0.0)


class Integer(Object):
    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.INTEGER

    @property
    def value(self) -> int:
        return self._value

    def inspect(self) -> str:
        return str(self._value)

    def react_to_infix_operator_addition(self, other: Object) -> Object:
        if isinstance(other, Integer):
            return Integer(self._value + other.value)
        elif isinstance(other, Float):
            return Float(self._value + other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="+", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_substraction(self, other: Object) -> Object:
        if isinstance(other, Integer):
            return Integer(self._value - other.value)
        elif isinstance(other, Float):
            return Float(self._value - other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="-", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_multiplication(self, other: Object) -> Object:
        if isinstance(other, Integer):
            return Integer(self._value * other.value)
        elif isinstance(other, Float):
            return Float(self._value * other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="*", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_division(self, other: Object) -> Object:
        if isinstance(other, Integer) or isinstance(other, Float):
            if other.value == 0:
                return Error(DIVISION_BY_ZERO.format())
            # Integer division always returns a Float
            return Float(self._value / other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="/", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than(self, other: Object) -> Object:
        if isinstance(other, Integer) or isinstance(other, Float):
            return Boolean(self._value < other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than(self, other: Object) -> Object:
        if isinstance(other, Integer) or isinstance(other, Float):
            return Boolean(self._value > other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_less_than_or_equal(self, other: Object) -> Object:
        if isinstance(other, Integer) or isinstance(other, Float):
            return Boolean(self._value <= other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator="<=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_greater_than_or_equal(self, other: Object) -> Object:
        if isinstance(other, Integer) or isinstance(other, Float):
            return Boolean(self._value >= other.value)
        return Error(
            UNSUPPORTED_OPERAND_TYPE.format(operator=">=", left_type=self.type.name, right_type=other.type.name)
        )

    def react_to_infix_operator_equals(self, other: Object) -> Object:
        # Allow numeric comparison between Integer and Float
        if isinstance(other, Integer | Float):
            return Boolean(self._value == other.value)
        return super().react_to_infix_operator_equals(other)

    def react_to_infix_operator_not_equals(self, other: Object) -> Object:
        # Allow numeric comparison between Integer and Float
        if isinstance(other, Integer | Float):
            return Boolean(self._value != other.value)
        return super().react_to_infix_operator_not_equals(other)

    def react_to_prefix_operator_minus(self) -> Object:
        return Integer(-self._value if self._value != 0 else 0)


class Return(Object):
    def __init__(self, value: Object) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.RETURN

    @property
    def value(self) -> Object:
        return self._value

    def inspect(self) -> str:
        return str(self._value.inspect())


class String(Object):
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.STRING

    @property
    def value(self) -> str:
        return self._value

    def inspect(self) -> str:
        return self._value


class URL(String):
    """URL object, a specialized type of String."""

    @property
    def type(self) -> ObjectType:
        return ObjectType.URL

    def inspect(self) -> str:
        # URLs display without quotes to distinguish from regular strings
        return self._value
