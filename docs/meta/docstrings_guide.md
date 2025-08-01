# Google Style Python Docstrings Guide

This guide explains how to write Python docstrings following the Google Python Style Guide. Google-
style docstrings are structured, readable, and work well with documentation generation tools like
Sphinx.

## Overview

Google-style docstrings use a clean, readable format with distinct sections marked by headers
followed by indented content. They support multiple lines and can include reStructuredText
formatting.

## Module Docstrings

Module docstrings appear at the beginning of a Python file and describe the module's purpose and
contents.

### Basic Structure

```python
"""Module summary line.

Extended description of the module. This can span multiple lines and provides
more detailed information about what the module does.

Attributes:
    module_var1 (type): Description of module-level variable.
    module_var2 (type): Another module-level variable.

Todo:
    * First TODO item
    * Second TODO item

Example:
    Basic usage example::

        $ python module_name.py

"""
```

### Module-Level Variables

Module variables can be documented in two ways:

1. **In the module docstring's Attributes section:**

   ```python
   """Module with documented variables.

   Attributes:
       module_level_variable1 (int): Module level variables may be documented in
           either the ``Attributes`` section of the module docstring, or in an
           inline docstring immediately following the variable.
   """

   module_level_variable1 = 12345
   ```

1. **Inline after the variable:**

   ```python
   module_level_variable2 = 98765
   """int: Module level variable documented inline.

   The docstring may span multiple lines. The type may optionally be specified
   on the first line, separated by a colon.
   """
   ```

## Function Docstrings

Function docstrings explain what a function does, its parameters, return values, and any exceptions
it might raise.

### Basic Function Documentation

```python
def function_name(param1, param2=None, *args, **kwargs):
    """One-line summary of the function.

    Extended description providing more details about the function's behavior,
    implementation notes, or usage guidelines.

    Args:
        param1 (int): The first parameter.
        param2 (str, optional): The second parameter. Defaults to None.
            Second line of description should be indented.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bool: True if successful, False otherwise.

        The return type is optional and may be specified at the beginning of
        the Returns section followed by a colon.

    Raises:
        AttributeError: The Raises section lists all exceptions
            that are relevant to the interface.
        ValueError: If `param2` is equal to `param1`.

    """
```

### Functions with Type Annotations

When using PEP 484 type annotations, you don't need to repeat type information in the docstring:

```python
def function_with_annotations(param1: int, param2: str) -> bool:
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """
```

### Generator Functions

Generators use a `Yields` section instead of `Returns`:

```python
def example_generator(n):
    """Generators have a Yields section instead of a Returns section.

    Args:
        n (int): The upper limit of the range to generate, from 0 to `n` - 1.

    Yields:
        int: The next number in the range of 0 to `n` - 1.

    Examples:
        Examples should be written in doctest format:

        >>> print([i for i in example_generator(4)])
        [0, 1, 2, 3]

    """
    yield from range(n)
```

## Class Docstrings

Class docstrings document the class purpose, attributes, and general behavior.

### Basic Class Documentation

```python
class ExampleClass:
    """The summary line for a class docstring should fit on one line.

    Extended class description. If the class has public attributes, they may
    be documented here in an Attributes section.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (int, optional): Description of `attr2`.

    """

    def __init__(self, param1, param2, param3):
        """Initialize the ExampleClass.

        Note:
            Do not include the `self` parameter in the Args section.

        Args:
            param1 (str): Description of `param1`.
            param2 (int, optional): Description of `param2`. Multiple
                lines are supported.
            param3 (list[str]): Description of `param3`.

        """
```

### Documenting Class Attributes

Class attributes can be documented in several ways:

1. **In the class docstring:**

   ```python
   class MyClass:
       """Class with attributes documented in class docstring.

       Attributes:
           attr1 (str): Description of attr1.
           attr2 (int): Description of attr2.
       """
   ```

1. **Inline comments:**

   ```python
   self.attr3 = param3  #: Doc comment *inline* with attribute

   #: list[str]: Doc comment *before* attribute, with type specified
   self.attr4 = ['attr4']
   ```

1. **Docstrings after attribute:**

   ```python
   self.attr5 = None
   """str: Docstring *after* attribute, with type specified."""
   ```

### Properties

Properties should be documented in their getter method:

```python
@property
def readonly_property(self):
    """str: Properties should be documented in their getter method."""
    return 'readonly_property'

@property
def readwrite_property(self):
    """list[str]: Properties with both a getter and setter.

    If the setter method contains notable behavior, it should be
    mentioned here.
    """
    return self._readwrite_property
```

### Method Documentation

Class methods follow the same pattern as functions but exclude `self` from the Args section:

```python
def example_method(self, param1, param2):
    """Class methods are similar to regular functions.

    Note:
        Do not include the `self` parameter in the Args section.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        True if successful, False otherwise.

    """
```

## Exception Classes

Exception classes are documented like regular classes:

```python
class ExampleError(Exception):
    """Exceptions are documented in the same way as classes.

    The __init__ method may be documented in either the class level
    docstring, or as a docstring on the __init__ method itself.

    Note:
        Do not include the `self` parameter in the Args section.

    Args:
        msg (str): Human readable string describing the exception.
        code (int, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """
```

## PEP 526 Annotations

With PEP 526 variable annotations, you can specify types in the class body:

```python
class ExamplePEP526Class:
    """Class using PEP 526 annotations.

    Attributes:
        attr1: Description of `attr1`.
        attr2: Description of `attr2`.

    """

    attr1: str
    attr2: int
```

## Special Sections

Google-style docstrings support several special sections:

- **Args**: Function/method parameters
- **Returns**: Return values
- **Yields**: For generators
- **Raises**: Exceptions that may be raised
- **Note**: Important notes
- **Example/Examples**: Usage examples
- **Todo**: Future improvements
- **Attributes**: Class or module attributes
- **See Also**: References to related items
- **Warning**: Important warnings
- **Deprecated**: Deprecation notices

## Formatting Tips

1. **Section Headers**: Always follow section headers with a colon and indent the content
1. **Parameter Format**: `name (type): description`
1. **Multi-line Descriptions**: Indent continuation lines to align with the first line
1. **Code Examples**: Use double colons (`::`) to introduce code blocks
1. **Inline Code**: Use double backticks (``` `` ```) for inline code
1. **Optional Parameters**: Mark as `(type, optional)` and specify defaults

## Best Practices

1. **Be Consistent**: Choose one documentation style for module variables and class attributes
1. **Be Concise**: Summary lines should fit on one line (72-79 characters)
1. **Be Complete**: Document all public APIs
1. **Use Examples**: Include doctest-compatible examples when helpful
1. **Type Information**: With type annotations, avoid duplicating type info in docstrings

## Special Members

- **Special methods** (`__method__`): Only included in docs if they have docstrings and
  `napoleon_include_special_with_doc` is True in Sphinx config
- **Private methods** (`_method`): Only included if they have docstrings and
  `napoleon_include_private_with_doc` is True in Sphinx config

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 526 - Variable Annotations](https://www.python.org/dev/peps/pep-0526/)
- [Sphinx Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
