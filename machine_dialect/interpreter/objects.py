from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import ClassVar, Optional


class ObjectType(Enum):
    """Represents an object type."""

    BOOLEAN = auto()
    EMPTY = auto()
    FLOAT = auto()
    INTEGER = auto()
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


class Boolean(Object):
    _instances: ClassVar[dict[bool, Optional["Boolean"]]] = {True: None, False: None}

    def __new__(cls, value: bool) -> "Boolean":
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

    def inspect(self) -> str:
        return "Yes" if self._value else "No"


class Empty(Object):
    _instance: Optional["Empty"] = None

    def __new__(cls) -> "Empty":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        pass

    @property
    def type(self) -> ObjectType:
        return ObjectType.EMPTY

    def inspect(self) -> str:
        return "Empty"


class Float(Object):
    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.FLOAT

    def inspect(self) -> str:
        return str(self._value)


class Integer(Object):
    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.INTEGER

    def inspect(self) -> str:
        return str(self._value)


class String(Object):
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.STRING

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
