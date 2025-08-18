"""Integration tests for the Machine Dialect interpreter.

These tests validate end-to-end interpreter functionality, ensuring that
complete programs execute correctly regardless of other component status.
"""


from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import (
    URL,
    Boolean,
    Empty,
    Environment,
    Error,
    Float,
    Integer,
    String,
)
from machine_dialect.parser import Parser


class TestInterpreterIntegration:
    """Integration tests for the interpreter."""

    def test_basic_arithmetic(self) -> None:
        """Test basic arithmetic operations."""
        source = """
Set `a` to _10_.
Set `b` to _5_.
Set `sum` to `a` + `b`.
Set `difference` to `a` - `b`.
Set `product` to `a` * `b`.
Set `quotient` to `a` / `b`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["a"], Integer)
        assert env["a"].value == 10
        assert isinstance(env["b"], Integer)
        assert env["b"].value == 5
        assert isinstance(env["sum"], Integer)
        assert env["sum"].value == 15
        assert isinstance(env["difference"], Integer)
        assert env["difference"].value == 5
        assert isinstance(env["product"], Integer)
        assert env["product"].value == 50
        assert isinstance(env["quotient"], Float)
        assert env["quotient"].value == 2.0

    def test_string_operations(self) -> None:
        """Test string assignments and operations."""
        source = """
Set `greeting` to _"Hello"_.
Set `name` to _"World"_.
Set `url` to _"https://example.com"_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["greeting"], String)
        assert env["greeting"].value == "Hello"
        assert isinstance(env["name"], String)
        assert env["name"].value == "World"
        assert isinstance(env["url"], URL)
        assert env["url"].value == "https://example.com"

    def test_boolean_operations(self) -> None:
        """Test boolean values and comparisons."""
        source = """
Set `is_true` to _true_.
Set `is_false` to _false_.
Set `a` to _10_.
Set `b` to _5_.
Set `greater` to `a` > `b`.
Set `less` to `a` < `b`.
Set `equal` to `a` equals `b`.
Set `not_equal` to `a` is not equal to `b`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["is_true"], Boolean)
        assert env["is_true"].value is True
        assert isinstance(env["is_false"], Boolean)
        assert env["is_false"].value is False
        assert isinstance(env["greater"], Boolean)
        assert env["greater"].value is True
        assert isinstance(env["less"], Boolean)
        assert env["less"].value is False
        assert isinstance(env["equal"], Boolean)
        assert env["equal"].value is False
        assert isinstance(env["not_equal"], Boolean)
        assert env["not_equal"].value is True

    def test_empty_value(self) -> None:
        """Test empty (null) value handling."""
        source = """
Set `nothing` to _empty_.
Set `something` to _42_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["nothing"], Empty)
        assert isinstance(env["something"], Integer)
        assert env["something"].value == 42

    def test_if_else_statements(self) -> None:
        """Test if-else control flow."""
        source = """
Set `x` to _10_.
Set `result` to _0_.

If `x` > _5_ then:
> Set `result` to _100_.
Else:
> Set `result` to _200_.

Set `y` to _3_.
Set `result2` to _0_.

If `y` > _5_ then:
> Set `result2` to _100_.
Else:
> Set `result2` to _200_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["result"], Integer)
        assert env["result"].value == 100  # x > 5 is true
        assert isinstance(env["result2"], Integer)
        assert env["result2"].value == 200  # y > 5 is false

    def test_nested_if_statements(self) -> None:
        """Test nested if statements."""
        source = """
Set `score` to _75_.
Set `grade` to _"F"_.

If `score` >= _90_ then:
> Set `grade` to _"A"_.
Else:
> If `score` >= _80_ then:
> > Set `grade` to _"B"_.
> Else:
> > If `score` >= _70_ then:
> > > Set `grade` to _"C"_.
> > Else:
> > > If `score` >= _60_ then:
> > > > Set `grade` to _"D"_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["grade"], String)
        assert env["grade"].value == "C"  # score is 75, so grade is C

    def test_give_back_statement(self) -> None:
        """Test give back (return) statement."""
        source = """
Set `x` to _10_.
Give back `x` * _2_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, Integer)
        assert result.value == 20

    def test_utility_definition_and_call(self) -> None:
        """Test defining and calling utilities (functions)."""
        source = """
### **Utility**: `add`

<details>
<summary>Adds two numbers.</summary>

> Give back `a` + `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `add` with _10_, _20_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, Integer)
        assert result.value == 30

    def test_utility_with_named_arguments(self) -> None:
        """Test calling utilities with named arguments."""
        source = """
### **Utility**: `divide`

<details>
<summary>Divides two numbers.</summary>

> Give back `dividend` / `divisor`.

</details>

#### Inputs:
- `dividend` **as** Number (required)
- `divisor` **as** Number (required)

Use `divide` where `divisor` is _5_, `dividend` is _100_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, Float)
        assert result.value == 20.0

    def test_utility_with_default_parameters(self) -> None:
        """Test utilities with default parameter values."""
        source = """
### **Utility**: `greet`

<details>
<summary>Creates a greeting message.</summary>

> Give back `greeting`.

</details>

#### Inputs:
- `name` **as** Text (required)
- `greeting` **as** Text (optional, default: _"Hello"_)

Use `greet` with _"World"_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, String)
        assert result.value == "Hello"  # Uses default greeting

    def test_set_using_utility(self) -> None:
        """Test the new 'using' keyword for capturing function returns."""
        source = """
### **Utility**: `square`

<details>
<summary>Squares a number.</summary>

> Give back `n` * `n`.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `x` to _5_.
Set `squared` using `square` with `x`.
Set `result` to `squared` + _10_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["x"], Integer)
        assert env["x"].value == 5
        assert isinstance(env["squared"], Integer)
        assert env["squared"].value == 25
        assert isinstance(env["result"], Integer)
        assert env["result"].value == 35

    def test_set_using_with_named_arguments(self) -> None:
        """Test 'using' with named arguments."""
        source = """
### **Utility**: `subtract`

<details>
<summary>Subtracts two numbers.</summary>

> Give back `minuend` - `subtrahend`.

</details>

#### Inputs:
- `minuend` **as** Number (required)
- `subtrahend` **as** Number (required)

Set `result` using `subtract` where `subtrahend` is _7_, `minuend` is _20_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["result"], Integer)
        assert env["result"].value == 13

    def test_utility_with_conditional_logic(self) -> None:
        """Test utilities containing if-else logic."""
        source = """
### **Utility**: `max`

<details>
<summary>Returns the maximum of two numbers.</summary>

> If `a` > `b` then:
> > Give back `a`.
> Else:
> > Give back `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Set `larger` using `max` with _15_, _8_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["larger"], Integer)
        assert env["larger"].value == 15

    def test_nested_utility_calls(self) -> None:
        """Test utilities calling other utilities."""
        source = """
### **Utility**: `double`

<details>
<summary>Doubles a number.</summary>

> Give back `n` * _2_.

</details>

#### Inputs:
- `n` **as** Number (required)

### **Utility**: `double_twice`

<details>
<summary>Doubles a number twice.</summary>

> Set `once` using `double` with `n`.
> Set `twice` using `double` with `once`.
> Give back `twice`.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `result` using `double_twice` with _5_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["result"], Integer)
        assert env["result"].value == 20  # 5 * 2 * 2

    def test_utility_scope_isolation(self) -> None:
        """Test that utilities have isolated scopes."""
        source = """
Set `x` to _100_.

### **Utility**: `modify_x`

<details>
<summary>Sets x to a different value.</summary>

> Set `x` to _42_.
> Give back `x`.

</details>

Set `result` using `modify_x`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        # Function returned its local x
        assert isinstance(env["result"], Integer)
        assert env["result"].value == 42

        # But global x is unchanged
        assert isinstance(env["x"], Integer)
        assert env["x"].value == 100

    def test_complex_expression_evaluation(self) -> None:
        """Test complex nested expressions."""
        source = """
Set `a` to _10_.
Set `b` to _5_.
Set `c` to _2_.
Set `result` to (`a` + `b`) * `c` - _10_ / `b`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["result"], Float)
        # (10 + 5) * 2 - 10 / 5 = 15 * 2 - 2 = 30 - 2 = 28
        assert env["result"].value == 28.0

    def test_conditional_expression(self) -> None:
        """Test conditional (ternary) expressions."""
        source = """
Set `x` to _10_.
Set `y` to _5_.
Set `max` to `x` if `x` > `y` else `y`.
Set `min` to `x` if `x` < `y` else `y`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["max"], Integer)
        assert env["max"].value == 10
        assert isinstance(env["min"], Integer)
        assert env["min"].value == 5

    def test_error_handling_undefined_variable(self) -> None:
        """Test error handling for undefined variables."""
        source = """
Set `result` to `undefined_var` + _10_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        # Should get an error, not crash
        assert isinstance(result, Error)
        # When an undefined variable is used in an expression, it first produces an ERROR object
        # which then causes a type error when used with operators
        assert "Unsupported operand type(s) for +: 'ERROR'" in result.message

    def test_error_handling_undefined_utility(self) -> None:
        """Test error handling for undefined utilities."""
        source = """
Use `undefined_function` with _10_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, Error)
        assert "undefined_function" in result.message

    def test_error_handling_missing_required_parameter(self) -> None:
        """Test error handling for missing required parameters."""
        source = """
### **Utility**: `add`

<details>
<summary>Adds two numbers.</summary>

> Give back `a` + `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `add` with _10_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        result = evaluate(program, env)

        assert isinstance(result, Error)
        assert "Missing required parameter" in result.message
        assert "b" in result.message

    def test_say_statement(self) -> None:
        """Test Say statement evaluation."""
        source = """
Set `message` to _"Hello, World!"_.
Say `message`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        # Say statements don't return values, but should evaluate without error
        result = evaluate(program, env)
        assert result is None  # No return value from Say

        # But the variable should be set
        assert isinstance(env["message"], String)
        assert env["message"].value == "Hello, World!"

    def test_mixed_data_types(self) -> None:
        """Test handling of mixed data types."""
        source = """
Set `int_val` to _42_.
Set `float_val` to _3.14_.
Set `string_val` to _"test"_.
Set `bool_val` to _true_.
Set `url_val` to _"https://example.com"_.
Set `empty_val` to _empty_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["int_val"], Integer)
        assert env["int_val"].value == 42
        assert isinstance(env["float_val"], Float)
        assert env["float_val"].value == 3.14
        assert isinstance(env["string_val"], String)
        assert env["string_val"].value == "test"
        assert isinstance(env["bool_val"], Boolean)
        assert env["bool_val"].value is True
        assert isinstance(env["url_val"], URL)
        assert env["url_val"].value == "https://example.com"
        assert isinstance(env["empty_val"], Empty)

    def test_utility_recursion(self) -> None:
        """Test recursive utility calls (factorial example)."""
        source = """
### **Utility**: `factorial`

<details>
<summary>Calculates factorial of a number.</summary>

> If `n` <= _1_ then:
> > Give back _1_.
> Else:
> > Set `n_minus_1` to `n` - _1_.
> > Set `sub_factorial` using `factorial` with `n_minus_1`.
> > Give back `n` * `sub_factorial`.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `result` using `factorial` with _5_.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["result"], Integer)
        assert env["result"].value == 120  # 5! = 120

    def test_complex_utility_workflow(self) -> None:
        """Test a complex workflow with multiple utilities working together."""
        source = """
### **Utility**: `calculate_discount`

<details>
<summary>Calculates discount amount.</summary>

> Give back `price` * `discount_rate` / _100_.

</details>

#### Inputs:
- `price` **as** Number (required)
- `discount_rate` **as** Number (required)

### **Utility**: `apply_discount`

<details>
<summary>Applies discount to a price.</summary>

> Set `discount_amount` using `calculate_discount` where `price` is `original_price`, `discount_rate` is `rate`.
> Set `final_price` to `original_price` - `discount_amount`.
> Give back `final_price`.

</details>

#### Inputs:
- `original_price` **as** Number (required)
- `rate` **as** Number (required)

Set `item_price` to _100_.
Set `discount` to _20_.
Set `final_cost` using `apply_discount` where `original_price` is `item_price`, `rate` is `discount`.
"""
        parser = Parser()
        program = parser.parse(source)
        env = Environment()

        evaluate(program, env)

        assert isinstance(env["final_cost"], Float)
        assert env["final_cost"].value == 80.0  # 100 - (100 * 20 / 100) = 80
