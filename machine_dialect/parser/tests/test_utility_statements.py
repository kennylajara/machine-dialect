"""Tests for Utility statements (functions) in Machine Dialect™."""

from machine_dialect.ast import BlockStatement, SetStatement, UtilityStatement
from machine_dialect.parser import Parser


class TestUtilityStatements:
    """Test parsing of Utility statements (functions)."""

    def test_simple_utility_without_parameters(self) -> None:
        """Test parsing a simple utility without parameters."""
        source = """### **Utility**: `calculate pi`

<details>
<summary>Calculates the value of pi.</summary>

> Define `result` as Number.
> Set `result` to _3.14159_.
> Give back `result`.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "calculate pi"
        assert len(utility_stmt.inputs) == 0
        assert len(utility_stmt.outputs) == 0
        assert isinstance(utility_stmt.body, BlockStatement)
        assert len(utility_stmt.body.statements) == 3  # Define + Set + Give back

        from machine_dialect.ast import DefineStatement

        # Check first statement: Define `result` as Number.
        define_stmt = utility_stmt.body.statements[0]
        assert isinstance(define_stmt, DefineStatement)
        assert define_stmt.name.value == "result"

        # Check second statement: Set `result` to _3.14159_.
        set_stmt = utility_stmt.body.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "result"

    def test_utility_with_inputs_and_outputs(self) -> None:
        """Test parsing a utility with input and output parameters."""
        source = """### **Utility**: `add two numbers`

<details>
<summary>Adds two numbers and returns the result</summary>

> Define `result` as Whole Number.
> Set `result` to `addend 1` + `addend 2`.

</details>

#### Inputs:
- `addend 1` **as** Whole Number (required)
- `addend 2` **as** Whole Number (required)

#### Outputs:
- `result` **as** Yes/No (default: _Empty_)"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "add two numbers"
        assert len(utility_stmt.inputs) == 2
        assert len(utility_stmt.outputs) == 1

        # Check inputs
        assert utility_stmt.inputs[0].name.value == "addend 1"
        assert utility_stmt.inputs[0].type_name == "Whole Number"
        assert utility_stmt.inputs[0].is_required is True

        assert utility_stmt.inputs[1].name.value == "addend 2"
        assert utility_stmt.inputs[1].type_name == "Whole Number"
        assert utility_stmt.inputs[1].is_required is True

        # Check outputs (now using Output class)
        from machine_dialect.ast import EmptyLiteral, Output

        assert len(utility_stmt.outputs) == 1
        assert isinstance(utility_stmt.outputs[0], Output)
        assert utility_stmt.outputs[0].name.value == "result"
        assert utility_stmt.outputs[0].type_name == "Yes/No"
        # Check that it has a default value of Empty
        assert utility_stmt.outputs[0].default_value is not None
        assert isinstance(utility_stmt.outputs[0].default_value, EmptyLiteral)

    def test_utility_with_heading_level(self) -> None:
        """Test that utility heading level (###) is parsed correctly."""
        source = """### **Utility**: `double value`

<details>
<summary>Doubles the input value.</summary>

> Define `result` as Number.
> Set `result` to `value` * _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "double value"

    def test_utility_with_multi_word_name(self) -> None:
        """Test utility with multi-word name in backticks."""
        source = """### **Utility**: `calculate compound interest`

<details>
<summary>Calculates compound interest.</summary>

> Define `amount` as Number.
> Set `amount` to _1000_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "calculate compound interest"

    def test_utility_with_empty_body(self) -> None:
        """Test utility with no statements in body."""
        source = """### **Utility**: `identity function`

<details>
<summary>Returns nothing.</summary>

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "identity function"
        assert len(utility_stmt.body.statements) == 0

    def test_multiple_utilities(self) -> None:
        """Test parsing multiple utilities in one program."""
        source = """### **Utility**: `first utility`

<details>
<summary>First utility.</summary>

> Define `x` as Number.
> Set `x` to _1_.

</details>

### **Utility**: `second utility`

<details>
<summary>Second utility.</summary>

> Define `second_y` as Number.
> Set `second_y` to _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        # Check first utility
        first_utility = program.statements[0]
        assert isinstance(first_utility, UtilityStatement)
        assert first_utility.name.value == "first utility"
        assert len(first_utility.body.statements) == 2  # Define + Set

        # Check second utility
        second_utility = program.statements[1]
        assert isinstance(second_utility, UtilityStatement)
        assert second_utility.name.value == "second utility"
        assert len(second_utility.body.statements) == 2  # Define + Set

    def test_utility_with_complex_body(self) -> None:
        """Test utility with complex body including conditionals."""
        source = """### **Utility**: `absolute value`

<details>
<summary>Returns the absolute value of a number.</summary>

> Define `result` as Number.
> If `number` < _0_ then:
> > Set `result` to -`number`.
> Else:
> > Set `result` to `number`.
>
> Give back `result`.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "absolute value"
        assert utility_stmt.description == "Returns the absolute value of a number."
        assert len(utility_stmt.body.statements) == 3  # Define + If statement + Give back statement

    def test_mixed_statements_with_utility(self) -> None:
        """Test that utilities can coexist with actions and interactions."""
        source = """### **Action**: `private method`

<details>
<summary>A private action.</summary>

> Define `x` as Number.
> Set `x` to _1_.

</details>

### **Utility**: `helper function`

<details>
<summary>A utility function.</summary>

> Give back _42_.

</details>

### **Interaction**: `public method`

<details>
<summary>A public interaction.</summary>

> Define `y` as Number.
> Set `y` to _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 3

        # Check action
        from machine_dialect.ast import ActionStatement, InteractionStatement

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "private method"

        # Check utility
        utility_stmt = program.statements[1]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "helper function"

        # Check interaction
        interaction_stmt = program.statements[2]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "public method"

    def test_utility_with_recursive_call(self) -> None:
        """Test utility with recursive call (Fibonacci example)."""
        source = """### **Utility**: `Fibonacci`

<details>
<summary>Calculate the nth Fibonacci number recursively</summary>

> If `n` is less than or equal to _1_:
> >
> > Give back `n`.
> >
> Else:
> >
> > Define `n_minus_1` as Whole Number.
> > Set `n_minus_1` to `n` - _1_.
> > Define `n_minus_2` as Whole Number.
> > Set `n_minus_2` to `n` - _2_.
> > Define `fib_1` as Whole Number.
> > Set `fib_1` using `Fibonacci` with `n_minus_1`.
> > Define `fib_2` as Whole Number.
> > Set `fib_2` using `Fibonacci` with `n_minus_2`.
> > Define `result` as Whole Number.
> > Set `result` to `fib_1` + `fib_2`.
> > Give back `result`.

</details>

#### Inputs:

- `n` **as** Whole Number (required)

#### Outputs:

- `result` **as** Whole Number

Define `m` as Whole Number.
Set `m` to _10_.

Define `final result` as Whole Number.
Set `final result` using `Fibonacci` with `m`.

Say `final result`."""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert (
            len(program.statements) == 6
        )  # Utility + Define m + Set m + Define final result + Set final result using + Say

        # Check the utility statement
        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "Fibonacci"
        assert utility_stmt.description == "Calculate the nth Fibonacci number recursively"

        # Check inputs
        assert len(utility_stmt.inputs) == 1
        assert utility_stmt.inputs[0].name.value == "n"
        assert utility_stmt.inputs[0].type_name == "Whole Number"
        assert utility_stmt.inputs[0].is_required is True

        # Check outputs
        assert len(utility_stmt.outputs) == 1
        assert utility_stmt.outputs[0].name.value == "result"
        assert utility_stmt.outputs[0].type_name == "Whole Number"

        # Check the body contains an if statement
        from machine_dialect.ast import DefineStatement, IfStatement, ReturnStatement, SayStatement

        assert len(utility_stmt.body.statements) == 1
        if_stmt = utility_stmt.body.statements[0]
        assert isinstance(if_stmt, IfStatement)

        # Check the if branch (n <= 1)
        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 1
        assert isinstance(if_stmt.consequence.statements[0], ReturnStatement)

        # Check the else branch (recursive case)
        assert if_stmt.alternative is not None
        assert isinstance(if_stmt.alternative, BlockStatement)
        else_statements = if_stmt.alternative.statements

        # Should have: 2 Define, 2 Set for n_minus_1 and n_minus_2
        # Then 2 Define, 2 Set using for fib_1 and fib_2
        # Then 1 Define, 1 Set for result, and 1 Give back
        assert len(else_statements) == 11

        # Check recursive calls (Set using statements with CallExpression)
        from machine_dialect.ast import CallExpression

        recursive_calls = [
            stmt
            for stmt in else_statements
            if isinstance(stmt, SetStatement) and isinstance(stmt.value, CallExpression)
        ]
        assert len(recursive_calls) == 2

        # Both should call "Fibonacci"
        from machine_dialect.ast import Identifier

        for call in recursive_calls:
            assert isinstance(call.value, CallExpression)
            assert call.value.function_name is not None
            assert isinstance(call.value.function_name, Identifier)
            assert call.value.function_name.value == "Fibonacci"

        # Check the main program statements after the utility
        assert isinstance(program.statements[1], DefineStatement)
        assert program.statements[1].name.value == "m"

        assert isinstance(program.statements[2], SetStatement)
        set_m = program.statements[2]
        assert set_m.name is not None
        assert set_m.name.value == "m"

        assert isinstance(program.statements[3], DefineStatement)
        assert program.statements[3].name.value == "final result"

        # Check the utility call in main program
        assert isinstance(program.statements[4], SetStatement)
        set_final = program.statements[4]
        assert set_final.name is not None
        assert set_final.name.value == "final result"
        assert isinstance(set_final.value, CallExpression)
        assert set_final.value.function_name is not None
        assert isinstance(set_final.value.function_name, Identifier)
        assert set_final.value.function_name.value == "Fibonacci"

        # Check the Say statement
        assert isinstance(program.statements[5], SayStatement)
        say_stmt = program.statements[5]
        # The Say statement should reference the final result identifier
        assert isinstance(say_stmt.expression, Identifier)
        assert say_stmt.expression.value == "final result"
