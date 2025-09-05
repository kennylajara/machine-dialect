"""Tests for Set statements with 'using' for function calls."""

from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Environment, WholeNumber
from machine_dialect.parser import Parser


class TestSetUsingFunctions:
    """Test Set statements that capture function return values using 'using'."""

    def test_set_using_function_no_args(self) -> None:
        """Test Set with using for a function without arguments."""
        source = """### **Utility**: `get_answer`

<details>
<summary>Returns the answer to life, universe and everything.</summary>

> Give back _42_.

</details>

Set `answer` using `get_answer`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # The answer should be stored in the environment
        assert "answer" in env.store
        assert isinstance(env["answer"], WholeNumber)
        assert env["answer"].value == 42

    def test_set_using_function_with_positional_args(self) -> None:
        """Test Set with using for a function with positional arguments."""
        source = """### **Utility**: `multiply`

<details>
<summary>Multiplies two numbers.</summary>

> Give back `a` * `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Set `x` to _5_.
Set `y` to _7_.
Set `product` using `multiply` with `x`, `y`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # The product should be stored in the environment
        assert "product" in env.store
        assert isinstance(env["product"], WholeNumber)
        assert env["product"].value == 35

    def test_set_using_function_with_named_args(self) -> None:
        """Test Set with using for a function with named arguments."""
        source = """### **Utility**: `divide`

<details>
<summary>Divides two numbers.</summary>

> Give back `dividend` / `divisor`.

</details>

#### Inputs:
- `dividend` **as** Number (required)
- `divisor` **as** Number (required)

Set `result` using `divide` where `dividend` is _100_, `divisor` is _4_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # The result should be stored in the environment
        assert "result" in env.store
        # Division returns a Float
        from machine_dialect.interpreter.objects import Float

        assert isinstance(env["result"], Float)
        assert env["result"].value == 25.0

    def test_set_using_chained_function_calls(self) -> None:
        """Test Set with using in a chain of function calls."""
        source = """### **Utility**: `double`

<details>
<summary>Doubles a number.</summary>

> Give back `n` * _2_.

</details>

#### Inputs:
- `n` **as** Number (required)

### **Utility**: `add_ten`

<details>
<summary>Adds 10 to a number.</summary>

> Give back `n` + _10_.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `x` to _5_.
Set `doubled` using `double` with `x`.
Set `final` using `add_ten` with `doubled`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # Check the chain of operations
        assert "x" in env.store
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 5

        assert "doubled" in env.store
        assert isinstance(env["doubled"], WholeNumber)
        assert env["doubled"].value == 10

        assert "final" in env.store
        assert isinstance(env["final"], WholeNumber)
        assert env["final"].value == 20

    def test_set_using_with_default_parameters(self) -> None:
        """Test Set with using for a function with default parameters."""
        source = """### **Utility**: `greet`

<details>
<summary>Creates a greeting.</summary>

> Give back `greeting`.

</details>

#### Inputs:
- `name` **as** Text (required)
- `greeting` **as** Text (optional, default: _"Hello"_)

Set `message1` using `greet` with _"World"_.
Set `message2` using `greet` where `name` is _"Alice"_, `greeting` is _"Hi"_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # Check both messages
        from machine_dialect.interpreter.objects import String

        assert "message1" in env.store
        assert isinstance(env["message1"], String)
        assert env["message1"].value == "Hello"  # Uses default

        assert "message2" in env.store
        assert isinstance(env["message2"], String)
        assert env["message2"].value == "Hi"  # Uses provided value

    def test_set_using_preserves_scope(self) -> None:
        """Test that Set with using doesn't pollute the outer scope."""
        source = """Set `x` to _100_.

### **Utility**: `test_scope`

<details>
<summary>Tests variable scope.</summary>

> Set `x` to _42_.
> Give back `x`.

</details>

Set `result` using `test_scope`."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # The result should be the function's local value
        assert "result" in env.store
        assert isinstance(env["result"], WholeNumber)
        assert env["result"].value == 42

        # The global x should still be 100
        assert "x" in env.store
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 100

    def test_set_using_in_expression(self) -> None:
        """Test using the result of Set with using in an expression."""
        source = """### **Utility**: `square`

<details>
<summary>Squares a number.</summary>

> Give back `n` * `n`.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `base` to _5_.
Set `squared` using `square` with `base`.
Set `result` to `squared` + _10_."""

        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Evaluate the program
        evaluate(program, env)

        # Check the calculations
        assert "base" in env.store
        assert isinstance(env["base"], WholeNumber)
        assert env["base"].value == 5

        assert "squared" in env.store
        assert isinstance(env["squared"], WholeNumber)
        assert env["squared"].value == 25

        assert "result" in env.store
        assert isinstance(env["result"], WholeNumber)
        assert env["result"].value == 35
