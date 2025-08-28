"""Tests for closures and higher-order functions."""

import pytest

from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Environment, Integer, String
from machine_dialect.parser import Parser


@pytest.mark.skip(reason="Closures not yet implemented in Machine Dialect")
class TestClosures:
    """Test closure behavior in functions."""

    def _parse_and_evaluate(self, source: str, env: Environment | None = None) -> tuple[object | None, Environment]:
        """Helper to parse and evaluate source code, returning both result and environment."""
        parser = Parser()
        program = parser.parse(source)
        if env is None:
            env = Environment()
        result = evaluate(program, env)
        return result, env

    def test_closure_captures_environment(self) -> None:
        """Test that a function captures its defining environment."""
        source = """Set `captured` to _100_.

### **Utility**: `get captured`

<details>
<summary>Returns captured variable.</summary>

> Give back `captured`.

</details>

Set `captured` to _200_.
Use `get captured`."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 200  # Function sees current value

    def test_closure_with_mutable_state(self) -> None:
        """Test that closures can work with mutable state."""
        source = """Set `counter` to _0_.

### **Utility**: `increment`

<details>
<summary>Increments counter.</summary>

> Set `counter` to `counter` + _1_.
> Give back `counter`.

</details>

Use `increment`.
Use `increment`.
Use `increment`."""

        result, env = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 3
        assert isinstance(env["counter"], Integer)
        assert env["counter"].value == 3

    def test_multiple_closures_share_environment(self) -> None:
        """Test that multiple functions from the same scope share the environment."""
        source = """Set `shared` to _10_.

### **Utility**: `getter`

<details>
<summary>Gets shared value.</summary>

> Give back `shared`.

</details>

### **Utility**: `setter`

<details>
<summary>Sets shared value.</summary>

> Set `shared` to `value`.

</details>

#### Inputs:
- `value` **as** Number (required)

Use `setter` with `value` as _42_.
Use `getter`."""

        result, env = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 42
        assert isinstance(env["shared"], Integer)
        assert env["shared"].value == 42

    def test_nested_closures(self) -> None:
        """Test closures within closures."""
        source = """Set `outer_var` to _1_.

### **Utility**: `outer`

<details>
<summary>Outer function.</summary>

> Set `middle_var` to _2_.
> Use `middle`.
> Give back `middle_var`.

</details>

### **Utility**: `middle`

<details>
<summary>Middle function.</summary>

> Set `inner_var` to _3_.
> Use `inner`.

</details>

### **Utility**: `inner`

<details>
<summary>Inner function.</summary>

> Set `result` to `outer_var` + `middle_var` + `inner_var`.
> Set `middle_var` to `result`.

</details>

Use `outer`."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 6  # 1 + 2 + 3

    def test_closure_after_outer_scope_exits(self) -> None:
        """Test that closures persist after their defining scope exits."""
        source = """### **Utility**: `make counter`

<details>
<summary>Creates a counter function.</summary>

> Set `count` to _0_.
>
> ### **Utility**: `counter`
>
> <details>
> <summary>Increments and returns count.</summary>
>
> > Set `count` to `count` + _1_.
> > Give back `count`.
>
> </details>
>
> Give back _0_.

</details>

Use `make counter`.
Use `counter`.
Use `counter`."""

        result, env = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        # This tests that the counter function exists and works
        assert "counter" in env

    def test_function_returning_function(self) -> None:
        """Test functions that return other functions."""
        # Note: Machine Dialect doesn't directly support returning functions,
        # but we can test that functions defined within functions are available
        source = """### **Utility**: `create adder`

<details>
<summary>Creates an adder function.</summary>

> ### **Utility**: `add`
>
> <details>
> <summary>Adds base to input.</summary>
>
> > Give back `base` + `n`.
>
> </details>
>
> #### Inputs:
> - `n` **as** Number (required)
>
> Give back _0_.

</details>

#### Inputs:
- `base` **as** Number (required)

Use `create adder` with `base` as _10_.
Use `add` with `n` as _5`."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 15  # 10 + 5

    def test_closure_with_default_parameters(self) -> None:
        """Test closures with functions that have default parameters."""
        source = """Set `multiplier` to _2_.

### **Utility**: `multiply`

<details>
<summary>Multiplies by captured multiplier.</summary>

> Give back `n` * `multiplier`.

</details>

#### Inputs:
- `n` **as** Number (default: _10_)

Set `multiplier` to _3_.
Use `multiply`.
Use `multiply` with `n` as _5_."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 15  # 5 * 3

    def test_recursive_closure(self) -> None:
        """Test recursive functions with closures."""
        source = """Set `depth` to _0_.

### **Utility**: `recurse`

<details>
<summary>Recursive function with closure.</summary>

> Set `depth` to `depth` + _1_.
> If `n` is greater than _0_, then:
> > Use `recurse` with `n` as `n` - _1_.
> Give back `depth`.

</details>

#### Inputs:
- `n` **as** Number (required)

Use `recurse` with `n` as _3_."""

        result, env = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 4  # depth incremented 4 times (initial call + 3 recursions)
        assert isinstance(env["depth"], Integer)
        assert env["depth"].value == 4

    def test_closure_with_conditionals(self) -> None:
        """Test closures in conditional statements."""
        source = """Set `mode` to _"add"_.

### **Utility**: `operation`

<details>
<summary>Performs operation based on mode.</summary>

> If `mode` is equal to _"add"_, then:
> > Give back `a` + `b`.
> Otherwise:
> > Give back `a` - `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `operation` with `a` as _10_ and `b` as _3_.
Set `mode` to _"subtract"_.
Use `operation` with `a` as _10_ and `b` as _3_."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 7  # 10 - 3 (mode changed to subtract)

    def test_closure_isolation(self) -> None:
        """Test that different function instances have isolated closures."""
        source = """### **Utility**: `make accumulator`

<details>
<summary>Creates an accumulator.</summary>

> Set `total` to _0_.
>
> ### **Utility**: `accumulate`
>
> <details>
> <summary>Adds to total.</summary>
>
> > Set `total` to `total` + `amount`.
> > Give back `total`.
>
> </details>
>
> #### Inputs:
> - `amount` **as** Number (required)

</details>

Use `make accumulator`.
Use `accumulate` with `amount` as _5_.
Use `accumulate` with `amount` as _3_."""

        result, env = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 8  # 5 + 3
        assert "accumulate" in env

    def test_closure_with_string_manipulation(self) -> None:
        """Test closures with string values."""
        source = """Set `prefix` to _"Hello, "_.

### **Utility**: `greet`

<details>
<summary>Greets with prefix.</summary>

> Give back `prefix`.

</details>

#### Inputs:
- `name` **as** Text (required)

Set `prefix` to _"Hi, "_.
Use `greet` with `name` as _"World"_."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, String)
        assert result.value == "Hi, "  # Returns the updated prefix

    def test_closure_preserves_function_definition_env(self) -> None:
        """Test that functions preserve their definition environment."""
        source = """Set `x` to _1_.

### **Utility**: `first`

<details>
<summary>First function.</summary>

> Set `x` to _2_.
>
> ### **Utility**: `second`
>
> <details>
> <summary>Second function.</summary>
>
> > Give back `x`.
>
> </details>
>
> Use `second`.

</details>

Set `x` to _3_.
Use `first`."""

        result, _ = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 2  # second sees first's x, not global
