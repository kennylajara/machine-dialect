"""Machine Dialect™ exception classes.

This module defines the exception hierarchy for the Machine Dialect™ language.
All exceptions inherit from MDBaseException, which provides a common base
for error handling throughout the system.
"""

from abc import ABC, abstractmethod
from typing import Any

from machine_dialect.errors.messages import ErrorTemplate


class MDBaseException(ABC):
    """Base Machine Dialect™ Exception.

    The base class for all built-in Machine Dialect™ exceptions.
    This is an abstract base class and should not be instantiated directly.

    Attributes:
        message (str): The error message.
        line (int, optional): The line number where the error occurred.
        column (int, optional): The column number where the error occurred.
        filename (str, optional): The filename where the error occurred.

    Note:
        This is a pure ABC that does not inherit from Python's Exception.
        These exceptions represent errors in Machine Dialect™ code, not Python code.
    """

    def __init__(
        self, message: ErrorTemplate, line: int, column: int, filename: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize the Machine Dialect™ exception.

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
        in Machine Dialect™ terms (e.g., "SyntaxError", "NameError").

        Returns:
            The error type as a string.
        """
        pass


class MDException(MDBaseException):
    """General Machine Dialect™ Exception.

    This is the base class for all non-syntax Machine Dialect™ exceptions.
    It provides a concrete implementation of MDBaseException that can be
    instantiated directly for general errors.

    Note:
        Most specific error conditions should use a more specialized
        exception subclass when available.
    """

    def error_type(self) -> str:
        """Return the error type identifier.

        Returns:
            "Exception" for general Machine Dialect™ exceptions.
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

    This exception is raised when an assert statement fails in Machine Dialect™ code.
    It corresponds to Python's built-in AssertionError.

    Example:
        >>> assert False, "This will raise MDAssertionError"
        Traceback (most recent call last):
            ...
        MDAssertionError: This will raise MDAssertionError
    """


class MDSystemExit(MDException):
    """Raised to exit from the Machine Dialect™ interpreter.

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

    def __init__(self, message: str | ErrorTemplate, line: int = 0, column: int = 0, **kwargs: Any) -> None:
        """Initialize name error.

        Args:
            message: Error message string or ErrorTemplate
            line: Line number where error occurred
            column: Column position where error occurred
            **kwargs: Additional template parameters if message is ErrorTemplate
        """
        if isinstance(message, str):
            # Create a simple ErrorTemplate from the string
            from machine_dialect.errors.messages import ErrorTemplate

            template = ErrorTemplate(message)
            super().__init__(template, line, column, **kwargs)
        else:
            super().__init__(message, line, column, **kwargs)


class MDSyntaxError(MDException):
    """Raised when a syntax error is encountered.

    This exception is raised when the parser encounters syntactically
    incorrect Machine Dialect™ code. This includes malformed expressions,
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

    def __init__(self, message: str | ErrorTemplate, line: int = 0, column: int = 0, **kwargs: Any) -> None:
        """Initialize type error.

        Args:
            message: Error message string or ErrorTemplate
            line: Line number where error occurred
            column: Column position where error occurred
            **kwargs: Additional template parameters if message is ErrorTemplate
        """
        if isinstance(message, str):
            # Create a simple ErrorTemplate from the string
            from machine_dialect.errors.messages import ErrorTemplate

            template = ErrorTemplate(message)
            super().__init__(template, line, column, **kwargs)
        else:
            super().__init__(message, line, column, **kwargs)


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


class MDUninitializedError(MDException):
    """Raised when a variable is used before being initialized.

    This exception is raised during semantic analysis when a variable
    that has been defined but not yet assigned a value is used in an
    expression or assignment.

    Example:
        >>> Define `x` as Whole Number.
        >>> Set `y` to `x`.
        Traceback (most recent call last):
            ...
        MDUninitializedError: Variable 'x' is used before being initialized
    """

    def __init__(self, message: str | ErrorTemplate, line: int = 0, position: int = 0, **kwargs: Any) -> None:
        """Initialize uninitialized variable error.

        Args:
            message: Error message string or ErrorTemplate
            line: Line number where error occurred
            position: Column position where error occurred
            **kwargs: Additional template parameters if message is ErrorTemplate
        """
        if isinstance(message, str):
            # Create a simple ErrorTemplate from the string
            from machine_dialect.errors.messages import ErrorTemplate

            template = ErrorTemplate(message)
            super().__init__(template, line, position, **kwargs)
        else:
            super().__init__(message, line, position, **kwargs)


class MDRuntimeError(Exception):
    """Machine Dialect™ Runtime Error.

    Raised during runtime execution with optional source location.
    This is used for errors that occur during MIR interpretation or VM execution.

    Note: This inherits from Python's Exception (not MDException) because
    it represents runtime errors that need to be caught by Python's exception
    handling mechanism.
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        filename: str | None = None,
    ) -> None:
        """Initialize runtime error.

        Args:
            message: Error message string.
            line: Line number where error occurred (None if unknown).
            column: Column position where error occurred (None if unknown).
            filename: Source file name (None if unknown).
        """
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename or "<standard-input>"
        super().__init__(str(self))

    def __str__(self) -> str:
        """Return formatted error message with location."""
        parts = []
        if self.filename != "<standard-input>":
            parts.append(f'File "{self.filename}"')
        if self.line is not None and self.line > 0:
            parts.append(f"line {self.line}")
        if self.column is not None and self.column > 0:
            parts.append(f"column {self.column}")

        location = ", ".join(parts)
        if location:
            return f"{location}: {self.message}"
        return self.message
