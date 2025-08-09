"""Machine Dialect exception classes.

This module defines the exception hierarchy for the Machine Dialect language.
All exceptions inherit from MDBaseException, which provides a common base
for error handling throughout the system.
"""

from abc import ABC, abstractmethod
from typing import Any

from machine_dialect.errors.messages import ErrorTemplate


class MDBaseException(ABC):
    """Base Machine Dialect Exception.

    The base class for all built-in Machine Dialect exceptions.
    This is an abstract base class and should not be instantiated directly.

    Attributes:
        message (str): The error message.
        line (int, optional): The line number where the error occurred.
        column (int, optional): The column number where the error occurred.
        filename (str, optional): The filename where the error occurred.

    Note:
        This is a pure ABC that does not inherit from Python's Exception.
        These exceptions represent errors in Machine Dialect code, not Python code.
    """

    def __init__(
        self, message: ErrorTemplate, line: int, column: int, filename: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize the Machine Dialect exception.

        Args:
            message: The error message template.
            line: The line number where the error occurred.
            column: The column number where the error occurred.
            filename: The filename where the error occurred.
            **kwargs: Template substitution parameters.
        """
        # Format the message with any provided kwargs
        # If no kwargs, call substitute with empty dict to get the template with no substitutions
        self._message = message.format(**kwargs) if kwargs else message.substitute()
        self._line = line
        self._column = column
        self._filename = filename or "<standard-input>"

    def __str__(self) -> str:
        """Return string representation of the exception.

        Returns:
            A formatted error message with location information if available.
        """
        parts = []
        if self._filename:
            parts.append(f'File "{self._filename}"')
        if self._line is not None:
            parts.append(f"line {self._line}")
        if self._column is not None:
            parts.append(f"column {self._column}")

        location = ", ".join(parts)
        if location:
            return f"{location}: {self._message}"
        return self._message

    def __repr__(self) -> str:
        """Return detailed representation of the exception.

        Returns:
            A string showing the exception class and all attributes.
        """
        mydict = {
            "message": self._message.__repr__(),
            "line": self._line,
            "column": self._column,
            "filename": self._filename.__repr__(),
        }
        concatenated = ", ".join([f"{k}={v}" for k, v in mydict.items()])
        return f"{self.__class__.__name__}({concatenated})"

    @abstractmethod
    def error_type(self) -> str:
        """Return the error type identifier for this exception.

        This should return a string that identifies the type of error
        in Machine Dialect terms (e.g., "SyntaxError", "NameError").

        Returns:
            The error type as a string.
        """
        pass


class MDException(MDBaseException):
    """General Machine Dialect Exception.

    This is the base class for all non-syntax Machine Dialect exceptions.
    It provides a concrete implementation of MDBaseException that can be
    instantiated directly for general errors.

    Note:
        Most specific error conditions should use a more specialized
        exception subclass when available.
    """

    def error_type(self) -> str:
        """Return the error type identifier.

        Returns:
            "Exception" for general Machine Dialect exceptions.
        """
        return "Exception"


class MDDivisionByZero(MDException):
    """Raised when a division or modulo operation has zero as divisor.

    This exception is raised when attempting to divide by zero or perform
    a modulo operation with zero as the divisor.

    Example:
        >>> 10 / 0
        Traceback (most recent call last):
            ...
        MDDivisionByZero: division by zero

        >>> 10 % 0
        Traceback (most recent call last):
            ...
        MDDivisionByZero: integer division or modulo by zero
    """


class MDAssertionError(MDException):
    """Raised when an assertion fails.

    This exception is raised when an assert statement fails in Machine Dialect code.
    It corresponds to Python's built-in AssertionError.

    Example:
        >>> assert False, "This will raise MDAssertionError"
        Traceback (most recent call last):
            ...
        MDAssertionError: This will raise MDAssertionError
    """


class MDSystemExit(MDException):
    """Raised to exit from the Machine Dialect interpreter.

    This exception is used to exit from the interpreter or terminate
    program execution. It corresponds to Python's SystemExit.

    Attributes:
        code (int | str | None): The exit status code. If None, defaults to 0.
            An integer gives the exit status (0 means success).
            A string prints the message to stderr and exits with status 1.

    Example:
        >>> exit(0)  # Normal termination
        >>> exit(1)  # Termination with error
        >>> exit("Error message")  # Print message and exit with status 1
    """


class MDNameError(MDException):
    """Raised when a name is not found in any scope.

    This exception is raised when a local or global name is not found.
    This applies to unqualified names within functions, methods, or
    the global scope.

    Attributes:
        name (str, optional): The name that could not be found.

    Example:
        >>> print(undefined_variable)
        Traceback (most recent call last):
            ...
        MDNameError: name 'undefined_variable' is not defined

        >>> del nonexistent
        Traceback (most recent call last):
            ...
        MDNameError: name 'nonexistent' is not defined
    """


class MDSyntaxError(MDException):
    """Raised when a syntax error is encountered.

    This exception is raised when the parser encounters syntactically
    incorrect Machine Dialect code. This includes malformed expressions,
    invalid statement structure, or improper use of keywords.

    Example:
        >>> if x = 5:  # Should use 'is' for comparison
        ...     pass
        Traceback (most recent call last):
            ...
        MDSyntaxError: invalid syntax

        >>> def function(
        ...     # Missing closing parenthesis
        Traceback (most recent call last):
            ...
        MDSyntaxError: unexpected EOF while parsing
    """


class MDTypeError(MDException):
    """Raised when an operation is applied to an inappropriate type.

    This exception is raised when an operation or function is applied to
    an object of inappropriate type. It can occur during parsing when
    type validation fails.

    Example:
        >>> "string" + 5
        Traceback (most recent call last):
            ...
        MDTypeError: can only concatenate str (not "int") to str

        >>> len(42)
        Traceback (most recent call last):
            ...
        MDTypeError: object of type 'int' has no len()
    """


class MDValueError(MDException):
    """Raised when a value is inappropriate for the operation.

    This exception is raised when an operation or function receives an
    argument that has the right type but an inappropriate value. It can
    occur during parsing when value validation fails.

    Example:
        >>> int("not a number")
        Traceback (most recent call last):
            ...
        MDValueError: invalid literal for int() with base 10: 'not a number'

        >>> list.remove([1, 2, 3], 4)
        Traceback (most recent call last):
            ...
        MDValueError: list.remove(x): x not in list
    """
