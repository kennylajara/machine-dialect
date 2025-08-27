"""Shared test fixtures and configuration for runtime tests."""

from typing import Any

import pytest

from machine_dialect.runtime.types import MachineDialectType


class MockInterpreterValue:
    """Mock interpreter value object for testing.

    This class simulates objects that would be created by an interpreter
    to wrap runtime values with type information.
    """

    def __init__(self, value: Any, type_val: MachineDialectType) -> None:
        """Initialize a mock interpreter value.

        Args:
            value: The actual value.
            type_val: The Machine Dialect type.
        """
        self.value = value
        self.type = type_val

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"MockInterpreterValue({self.value!r}, {self.type})"

    def __eq__(self, other: object) -> bool:
        """Compare with another MockInterpreterValue."""
        if isinstance(other, MockInterpreterValue):
            return self.value == other.value and self.type == other.type
        return False

    def inspect(self) -> str:
        """Provide inspection string (some interpreter objects have this)."""
        return f"<MockValue: {self.value}>"


class MockEmpty:
    """Mock empty object that represents interpreter Empty type."""

    def __repr__(self) -> str:
        """Return string representation."""
        return "MockEmpty()"

    def __eq__(self, other: object) -> bool:
        """Compare with other objects."""
        return isinstance(other, MockEmpty)


class MockInterpreter:
    """Mock interpreter for integration testing.

    Provides a simple interface for managing variables and function calls,
    simulating what a real interpreter might do.
    """

    def __init__(self) -> None:
        """Initialize the mock interpreter."""
        self.variables: dict[str, Any] = {}
        self.call_stack: list[str] = []

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the interpreter.

        Args:
            name: Variable name.
            value: Variable value.
        """
        self.variables[name] = value

    def get_variable(self, name: str) -> Any:
        """Get a variable from the interpreter.

        Args:
            name: Variable name.

        Returns:
            The variable value.

        Raises:
            NameError: If variable is not defined.
        """
        from machine_dialect.runtime.errors import NameError

        if name not in self.variables:
            raise NameError(f"Name '{name}' is not defined")
        return self.variables[name]

    def has_variable(self, name: str) -> bool:
        """Check if a variable is defined.

        Args:
            name: Variable name.

        Returns:
            True if variable exists, False otherwise.
        """
        return name in self.variables

    def clear_variables(self) -> None:
        """Clear all variables."""
        self.variables.clear()

    def push_call(self, name: str) -> None:
        """Push a function call onto the call stack.

        Args:
            name: Function name.
        """
        self.call_stack.append(name)

    def pop_call(self) -> str | None:
        """Pop a function call from the call stack.

        Returns:
            The function name, or None if stack is empty.
        """
        return self.call_stack.pop() if self.call_stack else None

    def get_call_stack(self) -> list[str]:
        """Get the current call stack.

        Returns:
            Copy of the call stack.
        """
        return self.call_stack.copy()


@pytest.fixture
def mock_interpreter() -> MockInterpreter:
    """Fixture providing a mock interpreter instance.

    Returns:
        A fresh MockInterpreter instance.
    """
    return MockInterpreter()


@pytest.fixture
def mock_integer() -> MockInterpreterValue:
    """Fixture providing a mock integer value.

    Returns:
        MockInterpreterValue representing integer 42.
    """
    return MockInterpreterValue(42, MachineDialectType.INTEGER)


@pytest.fixture
def mock_float() -> MockInterpreterValue:
    """Fixture providing a mock float value.

    Returns:
        MockInterpreterValue representing float 3.14.
    """
    return MockInterpreterValue(3.14, MachineDialectType.FLOAT)


@pytest.fixture
def mock_string() -> MockInterpreterValue:
    """Fixture providing a mock string value.

    Returns:
        MockInterpreterValue representing string "hello".
    """
    return MockInterpreterValue("hello", MachineDialectType.STRING)


@pytest.fixture
def mock_boolean_true() -> MockInterpreterValue:
    """Fixture providing a mock boolean True value.

    Returns:
        MockInterpreterValue representing boolean True.
    """
    return MockInterpreterValue(True, MachineDialectType.BOOLEAN)


@pytest.fixture
def mock_boolean_false() -> MockInterpreterValue:
    """Fixture providing a mock boolean False value.

    Returns:
        MockInterpreterValue representing boolean False.
    """
    return MockInterpreterValue(False, MachineDialectType.BOOLEAN)


@pytest.fixture
def mock_empty() -> MockEmpty:
    """Fixture providing a mock empty value.

    Returns:
        MockEmpty instance representing empty/null value.
    """
    return MockEmpty()


@pytest.fixture
def numeric_test_values() -> list[Any]:
    """Fixture providing various numeric test values.

    Returns:
        List of numeric values for testing.
    """
    return [0, 1, -1, 42, -42, 0.0, 1.0, -1.0, 3.14, -3.14, float("inf"), float("-inf"), float("nan")]


@pytest.fixture
def string_test_values() -> list[str]:
    """Fixture providing various string test values.

    Returns:
        List of string values for testing.
    """
    return [
        "",
        "hello",
        "Hello, World!",
        "123",
        "3.14",
        "true",
        "false",
        "   ",
        "hello world",
        "unicode: 世界",
        "special: !@#$%^&*()",
    ]


@pytest.fixture
def mixed_type_values() -> list[Any]:
    """Fixture providing values of different types.

    Returns:
        List of mixed-type values for testing.
    """
    return [
        None,
        True,
        False,
        0,
        1,
        -1,
        0.0,
        1.0,
        -1.0,
        "",
        "hello",
        "123",
        float("inf"),
        float("nan"),
        [],
        [1, 2, 3],
        {},
        {"key": "value"},
        lambda: None,
    ]


@pytest.fixture
def interpreter_test_values() -> list[MockInterpreterValue]:
    """Fixture providing interpreter value objects for testing.

    Returns:
        List of MockInterpreterValue instances.
    """
    return [
        MockInterpreterValue(42, MachineDialectType.INTEGER),
        MockInterpreterValue(-17, MachineDialectType.INTEGER),
        MockInterpreterValue(3.14, MachineDialectType.FLOAT),
        MockInterpreterValue(-2.71, MachineDialectType.FLOAT),
        MockInterpreterValue("hello", MachineDialectType.STRING),
        MockInterpreterValue("", MachineDialectType.STRING),
        MockInterpreterValue(True, MachineDialectType.BOOLEAN),
        MockInterpreterValue(False, MachineDialectType.BOOLEAN),
    ]


@pytest.fixture(autouse=True)
def reset_builtin_registry() -> None:
    """Fixture to ensure builtin function registry is clean for each test.

    This fixture automatically runs for every test to ensure that any
    custom builtin functions registered during testing are cleaned up.
    """
    from machine_dialect.runtime.builtins import BUILTIN_FUNCTIONS

    # Store original builtins
    original_builtins = BUILTIN_FUNCTIONS.copy()

    yield

    # Restore original builtins (remove any added during test)
    BUILTIN_FUNCTIONS.clear()
    BUILTIN_FUNCTIONS.update(original_builtins)


class TestDataGenerator:
    """Utility class for generating test data."""

    @staticmethod
    def create_interpreter_values(values: list[Any], type_val: MachineDialectType) -> list[MockInterpreterValue]:
        """Create interpreter values from raw values.

        Args:
            values: List of raw values.
            type_val: Type to assign to all values.

        Returns:
            List of MockInterpreterValue instances.
        """
        return [MockInterpreterValue(value, type_val) for value in values]

    @staticmethod
    def create_mixed_interpreter_values() -> list[MockInterpreterValue]:
        """Create a mixed set of interpreter values.

        Returns:
            List of MockInterpreterValue instances with different types.
        """
        return [
            MockInterpreterValue(42, MachineDialectType.INTEGER),
            MockInterpreterValue(3.14, MachineDialectType.FLOAT),
            MockInterpreterValue("test", MachineDialectType.STRING),
            MockInterpreterValue(True, MachineDialectType.BOOLEAN),
        ]

    @staticmethod
    def create_numeric_range(start: int, end: int, step: int = 1) -> list[int]:
        """Create a range of numeric values for testing.

        Args:
            start: Start value.
            end: End value (exclusive).
            step: Step size.

        Returns:
            List of integers in the range.
        """
        return list(range(start, end, step))

    @staticmethod
    def create_float_range(start: float, end: float, count: int) -> list[float]:
        """Create a range of float values for testing.

        Args:
            start: Start value.
            end: End value.
            count: Number of values to generate.

        Returns:
            List of floats evenly spaced between start and end.
        """
        if count <= 1:
            return [start]

        step = (end - start) / (count - 1)
        return [start + i * step for i in range(count)]


@pytest.fixture
def test_data_generator() -> TestDataGenerator:
    """Fixture providing test data generator utility.

    Returns:
        TestDataGenerator instance.
    """
    return TestDataGenerator()


# Custom pytest markers for categorizing tests
def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (may take longer to run)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "edge_case: marks tests that cover edge cases")
    config.addinivalue_line("markers", "error_handling: marks tests that test error handling")
