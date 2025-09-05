"""Tests for environment edge cases and error handling."""


import pytest

from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Environment, Error, Function, String, WholeNumber
from machine_dialect.parser import Parser


class TestEnvironmentEdgeCases:
    """Test edge cases and error conditions for environments."""

    def _parse_and_evaluate(self, source: str, env: Environment | None = None) -> tuple[object | None, Environment]:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)
        if env is None:
            env = Environment()
        result = evaluate(program, env)
        return result, env

    @pytest.mark.skip(reason="Unicode identifiers not yet supported")
    def test_environment_with_unicode_names(self) -> None:
        """Test variable names with unicode characters."""
        source = """Set `变量` to _42_.
Set `переменная` to _"test"_.
Set `🚀` to _100_.

Give back `变量` + `🚀`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 142

        # Check unicode names are stored correctly
        assert "变量" in env.store
        assert "переменная" in env.store
        assert "🚀" in env.store

    def test_environment_with_empty_string_name(self) -> None:
        """Test variable with empty string as name."""
        env = Environment()
        env[""] = WholeNumber(42)

        assert "" in env
        assert isinstance(env[""], WholeNumber)
        assert env[""].value == 42

    def test_environment_with_very_long_name(self) -> None:
        """Test variable with very long name."""
        long_name = "x" * 1000
        source = f"""Set `{long_name}` to _42_.
Give back `{long_name}`."""

        result, _ = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 42

    def test_maximum_scope_depth(self) -> None:
        """Test deeply nested scopes."""
        # Create a deeply nested function chain
        depth = 20
        source = ""

        # Define nested functions
        for i in range(depth):
            source += f"""### **Utility**: `level{i}`

<details>
<summary>Level {i} function.</summary>

> Set `local{i}` to _{i}_.
"""
            if i < depth - 1:
                source += f"> Use `level{i+1}`.\n"
            else:
                source += f"> Give back `local{i}`.\n"
            source += """
</details>

"""

        source += "Use `level0`."

        result, _ = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == depth - 1

    def test_environment_with_large_data(self) -> None:
        """Test storing large objects in environment."""
        # Create a large string
        large_string = "x" * 10000
        source = f"""Set `large` to _"{large_string}"_.
Give back `large`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert len(result.value) == 10000
        assert result.value == large_string

    def test_many_variables_in_environment(self) -> None:
        """Test environment with many variables."""
        num_vars = 100
        source = ""

        # Create many variables
        for i in range(num_vars):
            source += f"Set `var{i}` to _{i}_.\n"

        source += "Set `sum` to _0_.\n"

        # Sum all variables
        for i in range(num_vars):
            source += f"Set `sum` to `sum` + `var{i}`.\n"

        source += "Give back `sum`."

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        # Sum of 0 to 99 = (99 * 100) / 2 = 4950
        assert result.value == sum(range(num_vars))

        # Check all variables exist
        for i in range(num_vars):
            assert f"var{i}" in env.store

    @pytest.mark.skip(reason="Mutual recursion test needs proper parameter passing")
    def test_circular_reference_prevention(self) -> None:
        """Test that circular references don't cause issues."""
        source = """### **Utility**: `circular1`

<details>
<summary>First circular function.</summary>

> If `depth` is greater than _0_, then:
> > Set `depth` to `depth` - _1_.
> > Use `circular2`.
> Give back `depth`.

</details>

### **Utility**: `circular2`

<details>
<summary>Second circular function.</summary>

> If `depth` is greater than _0_, then:
> > Set `depth` to `depth` - _1_.
> > Use `circular1`.
> Give back `depth`.

</details>

Set `depth` to _5_.
Use `circular1`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 0

    def test_environment_after_error(self) -> None:
        """Test that environment remains consistent after an error."""
        source = """Set `x` to _10_.
Set `y` to _20_.
Set `z` to `undefined_var`.
Set `w` to _30_."""

        result, env = self._parse_and_evaluate(source)

        # Should get an error
        assert result is not None
        assert isinstance(result, Error)

        # But x and y should be set
        assert "x" in env.store
        assert "y" in env.store
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 10
        assert isinstance(env["y"], WholeNumber)
        assert env["y"].value == 20

        # w should not be set (error occurred before)
        assert "w" not in env.store

    def test_shadowing_with_different_types(self) -> None:
        """Test shadowing variables with different types."""
        source = """Set `var` to _42_.

### **Utility**: `shadow with string`

<details>
<summary>Shadows with string.</summary>

> Set `var` to _"string"_.
> Give back `var`.

</details>

### **Utility**: `shadow with boolean`

<details>
<summary>Shadows with boolean.</summary>

> Set `var` to _Yes_.
> Give back `var`.

</details>

Use `shadow with string`.
Use `shadow with boolean`.
Give back `var`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 42  # Original type preserved

    def test_parameter_with_same_name_as_global(self) -> None:
        """Test parameter shadowing with exact same name as global."""
        source = """Set `value` to _100_.

### **Utility**: `process`

<details>
<summary>Processes value.</summary>

> Give back `value` * _2_.

</details>

#### Inputs:
- `value` **as** Number (required)

Use `process` where `value` is _5_."""

        result, _ = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 10  # 5 * 2, not 100 * 2

    def test_nested_set_using_statements(self) -> None:
        """Test nested Set using statements."""
        source = """### **Utility**: `add`

<details>
<summary>Adds two numbers.</summary>

> Give back `a` + `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

### **Utility**: `multiply`

<details>
<summary>Multiplies two numbers.</summary>

> Give back `a` * `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Set `x` using `add` where `a` is _3_, `b` is _4_.
Set `y` using `multiply` where `a` is `x`, `b` is _2_.
Give back `y`."""

        result, _ = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 14  # (3 + 4) * 2

    def test_environment_with_null_like_values(self) -> None:
        """Test environment handling of empty/null-like values."""
        source = """Set `empty_var` to empty.
Set `zero` to _0_.
Set `empty_string` to _""_.
Set `false` to _No_.

If `empty_var` is equal to empty then:
> Give back _"correct"_.

Give back _"wrong"_."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.value == "correct"

        # Check all values are stored
        assert "empty_var" in env.store
        assert "zero" in env.store
        assert "empty_string" in env.store
        assert "false" in env.store

    def test_function_redefinition(self) -> None:
        """Test redefining a function in the same scope."""
        source = """### **Utility**: `func`

<details>
<summary>First definition.</summary>

> Give back _1_.

</details>

Use `func`.

### **Utility**: `func`

<details>
<summary>Second definition.</summary>

> Give back _2_.

</details>

Use `func`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 2  # Uses second definition

        # Check that func is a Function
        assert "func" in env.store
        assert isinstance(env["func"], Function)

    def test_deeply_nested_data_structures(self) -> None:
        """Test deeply nested expressions and data."""
        # Create a deeply nested arithmetic expression
        source = "Set `result` to _1_"
        for i in range(2, 21):
            source += f" + _{i}_"
        source += ".\nGive back `result`."

        result, _ = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == sum(range(1, 21))  # 210

    def test_environment_consistency_across_returns(self) -> None:
        """Test that early returns don't corrupt environment."""
        source = """Set `global` to _100_.

### **Utility**: `early return`

<details>
<summary>Has early return.</summary>

> Set `local` to _200_.
> If _Yes_ is equal to _Yes_, then:
> > Give back `local`.
>
> Set `never_reached` to _300_.
> Give back `never_reached`.

</details>

Use `early return`.
Give back `global`."""

        result, env = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, WholeNumber)
        assert result.value == 100

        # Check global environment is clean
        assert "global" in env.store
        assert "local" not in env.store
        assert "never_reached" not in env.store
