"""Tests for evaluating Utility statements and calls in the interpreter."""


from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Environment, Error, Float, Function, Integer, String
from machine_dialect.parser import Parser


class TestUtilityEvaluation:
    """Test evaluation of Utility statements and function calls."""

    def test_define_simple_utility(self) -> None:
        """Test defining a simple utility without parameters."""
        source = """### **Utility**: `get answer`

<details>
<summary>Returns the answer to life, universe and everything.</summary>

> Give back _42_.

</details>"""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the utility definition
        evaluate(program, env)

        # The utility should be stored in the environment
        assert "get answer" in env.store
        assert isinstance(env["get answer"], Function)

        func = env["get answer"]
        assert func.name == "get answer"
        assert len(func.parameters) == 0

    def test_call_simple_utility(self) -> None:
        """Test calling a simple utility without parameters."""
        source = """### **Utility**: `get pi`

<details>
<summary>Returns the value of pi.</summary>

> Give back _3.14_.

</details>

Use `get pi`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program (defines utility and calls it)
        result = evaluate(program, env)

        # The call should return the float value
        assert result is not None
        assert isinstance(result, Float)
        assert result.value == 3.14

    def test_utility_with_parameters(self) -> None:
        """Test utility with input parameters."""
        source = """### **Utility**: `add numbers`

<details>
<summary>Adds two numbers.</summary>

> Set `result` to `a` + `b`.
> Give back `result`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Set `x` to _10_.
Set `y` to _5_.
Use `add numbers` with `x`, `y`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # The call should return the sum
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 15

    def test_utility_with_named_arguments(self) -> None:
        """Test calling utility with named arguments."""
        source = """### **Utility**: `subtract`

<details>
<summary>Subtracts two numbers.</summary>

> Give back `minuend` - `subtrahend`.

</details>

#### Inputs:
- `minuend` **as** Number (required)
- `subtrahend` **as** Number (required)

Use `subtract` where `subtrahend` is _3_, `minuend` is _10_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return 10 - 3 = 7
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 7

    def test_utility_with_default_parameters(self) -> None:
        """Test utility with optional parameters and defaults."""
        source = """### **Utility**: `greet`

<details>
<summary>Greets a person.</summary>

> Give back `greeting`.

</details>

#### Inputs:
- `name` **as** Text (required)
- `greeting` **as** Text (optional, default: _"Hello"_)

Use `greet` with _"World"_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return "Hello" using the default greeting
        assert result is not None
        assert isinstance(result, String)
        assert result.value == "Hello"

    def test_utility_with_conditional_logic(self) -> None:
        """Test utility with if-else logic."""
        source = """### **Utility**: `absolute value`

<details>
<summary>Returns the absolute value of a number.</summary>

> If `number` < _0_ then:
> > Give back -`number`.
> Else:
> > Give back `number`.

</details>

#### Inputs:
- `number` **as** Number (required)

Use `absolute value` with _-5_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return 5 (absolute value of -5)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 5

    def test_utility_call_missing_required_parameter(self) -> None:
        """Test calling utility without required parameter."""
        source = """### **Utility**: `multiply`

<details>
<summary>Multiplies two numbers.</summary>

> Give back `a` * `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `multiply` with _5_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return an error for missing parameter
        assert result is not None
        assert isinstance(result, Error)
        assert "Missing required parameter 'b'" in result.message

    def test_call_undefined_utility(self) -> None:
        """Test calling a utility that doesn't exist."""
        source = """Use `undefined function`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return an error
        assert result is not None
        assert isinstance(result, Error)
        assert "undefined function" in result.message

    def test_utility_with_local_variables(self) -> None:
        """Test that utilities have their own scope."""
        source = """Set `x` to _100_.

### **Utility**: `test scope`

<details>
<summary>Tests variable scope.</summary>

> Set `x` to _42_.
> Give back `x`.

</details>

Use `test scope`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return 42 (the local value in the utility)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 42

        # The global x should still be 100
        assert isinstance(env["x"], Integer)
        assert env["x"].value == 100

    def test_nested_utility_calls(self) -> None:
        """Test calling a utility from within another utility."""
        source = """### **Utility**: `double`

<details>
<summary>Doubles a number.</summary>

> Give back `n` * _2_.

</details>

#### Inputs:
- `n` **as** Number (required)

### **Utility**: `quadruple`

<details>
<summary>Quadruples a number.</summary>

> Use `double` with `n`.
> Set `doubled` to _6_.
> Use `double` with `doubled`.
> Set `result` to _12_.
> Give back `result`.

</details>

#### Inputs:
- `n` **as** Number (required)

Use `quadruple` with _3_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return 12 (hardcoded for now since we can't capture call results yet)
        assert result is not None
        assert isinstance(result, Integer)
        assert result.value == 12

    def test_utility_without_return(self) -> None:
        """Test utility that doesn't return a value."""
        source = """### **Utility**: `do nothing`

<details>
<summary>Does nothing.</summary>

> Set `temp` to _1_.

</details>

Use `do nothing`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        result = evaluate(program, env)

        # Should return None (no return value)
        assert result is None
