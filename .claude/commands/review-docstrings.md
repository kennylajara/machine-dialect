# Review and Update Python Documentation

Reviews and updates Python file documentation to comply with Google-style docstring standards.

<context>
Target file: {{file_path}}
Style guide reference: docs/meta/docstrings_guide.md
Project uses: Python 3.12+ with type annotations throughout

Key requirements from this project:

- Google Python Style Guide for all docstrings
- Type annotations are present - do NOT duplicate types in docstrings
- Args format: `name: description` (no type since using annotations)
- Summary lines must fit within 72-79 characters
- All public APIs must be documented
- Private methods (starting with _) only if already documented
</context>

<examples>
<example>
Input: Function without docstring
```python
def calculate_discount(price: float, percentage: float) -> float:
    return price * (1 - percentage / 100)
```

Output: Function with Google-style docstring

```python
def calculate_discount(price: float, percentage: float) -> float:
    """Calculate the discounted price based on percentage.
    
    Args:
        price: Original price of the item.
        percentage: Discount percentage to apply.
    
    Returns:
        The final price after applying the discount.
    """
    return price * (1 - percentage / 100)
```

</example>

<example>
Input: Class with missing documentation
```python
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
```

Output: Class with complete Google-style documentation

```python
class User:
    """Represents a user in the system.
    
    Attributes:
        name: The user's full name.
        email: The user's email address.
    """
    
    def __init__(self, name: str, email: str):
        """Initialize a new User instance.
        
        Args:
            name: The user's full name.
            email: The user's email address.
        """
        self.name = name
        self.email = email
```

</example>

<example>
Input: Method with incorrect format
```python
def process_data(self, data: list[dict], validate: bool = True) -> dict:
    """Process data
    :param data: Data to process
    :param validate: Whether to validate
    :return: Processed results
    """
    if validate:
        self._validate(data)
    return {"processed": len(data)}
```

Output: Method with correct Google-style format

```python
def process_data(self, data: list[dict], validate: bool = True) -> dict:
    """Process and transform input data.
    
    Args:
        data: List of dictionaries containing raw data.
        validate: Whether to validate data before processing.
            Defaults to True.
    
    Returns:
        Dictionary containing processing results with 'processed' count.
    """
    if validate:
        self._validate(data)
    return {"processed": len(data)}
```

</example>

<example>
Input: Generator without proper Yields section
```python
def fibonacci(n: int):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
```

Output: Generator with Yields section

```python
def fibonacci(n: int):
    """Generate Fibonacci sequence up to n numbers.
    
    Args:
        n: Number of Fibonacci numbers to generate.
    
    Yields:
        The next number in the Fibonacci sequence.
    
    Example:
        >>> list(fibonacci(5))
        [0, 1, 1, 2, 3]
    """
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
```

</example>

<example>
Input: Property without documentation
```python
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"
```

Output: Property with proper documentation

```python
@property
def full_name(self) -> str:
    """str: The user's full name combining first and last names."""
    return f"{self.first_name} {self.last_name}"
```

</example>
</examples>

<thinking>
I need to systematically review the Python file for:
1. Missing docstrings at module, class, method, and function levels
2. Incorrect formatting (wrong style, duplicated types, missing sections)
3. Incomplete documentation (missing Args, Returns, Raises sections)
4. Opportunities to add helpful sections (Example, Note, Warning)
5. Summary lines that exceed 72-79 characters
</thinking>

<instructions>
1. Read the entire Python file to understand its structure and purpose
2. Create a mental map of all documentable elements:
   - Module-level docstring
   - Classes and their attributes
   - Methods and functions
   - Properties
   - Module-level variables (if any)
3. For each element, check:
   - Does it have a docstring?
   - Is the format Google-style?
   - Are all sections present and correct?
   - Is the summary line within 72-79 characters?
4. Apply fixes in this priority order:
   - Add missing module docstring
   - Add missing class docstrings with Attributes sections
   - Add missing method/function docstrings
   - Fix format violations (convert to Google-style)
   - Enhance content for clarity
5. Special handling:
   - Generators: Use Yields instead of Returns
   - Properties: Document in getter with type prefix
   - Private methods: Only document if already have docstrings
   - Type annotations: Never duplicate in Args descriptions
6. If unsure about a function's purpose, add: "TODO: Verify this documentation"
</instructions>

<validation_checklist>
After making changes, verify:

- [ ] Module has a docstring describing its purpose
- [ ] All public classes have docstrings with Attributes sections
- [ ] All public methods/functions have complete docstrings
- [ ] Args sections list parameters without 'self'
- [ ] No type information duplicated when annotations exist
- [ ] Returns/Yields sections describe what is returned/yielded
- [ ] Raises sections list exceptions (where applicable)
- [ ] Properties documented with type prefix in getter
- [ ] All summary lines fit within 72-79 characters
- [ ] Special sections (Note, Example, Todo, Warning) added where helpful
- [ ] Format follows exact Google-style structure
</validation_checklist>

<constraints>
- MUST NOT duplicate type information when type annotations are present
- MUST NOT include 'self' parameter in Args sections
- MUST preserve existing correct documentation
- MUST use exact format: `name: description` for arguments (no parentheses)
- MUST keep summary lines within 72-79 characters
- If unsure about functionality, MUST add "TODO: Verify this documentation"
</constraints>

<answer>
When reviewing {{file_path}}, I will:
1. First scan for all missing documentation
2. Then identify and fix any format violations
3. Finally enhance descriptions for better clarity
4. Report a summary of all changes made
</answer>
