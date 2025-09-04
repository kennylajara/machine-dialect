"""Tests for Utility statements (functions) in Machine Dialect."""

from machine_dialect.ast import BlockStatement, SetStatement, UtilityStatement
from machine_dialect.parser import Parser


class TestUtilityStatements:
    """Test parsing of Utility statements (functions)."""

    def test_simple_utility_without_parameters(self) -> None:
        """Test parsing a simple utility without parameters."""
        source = """### **Utility**: `calculate pi`

<details>
<summary>Calculates the value of pi.</summary>

> Set `result` to _3.14159_.
> Give back `result`.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "calculate pi"
        assert len(utility_stmt.inputs) == 0
        assert len(utility_stmt.outputs) == 0
        assert isinstance(utility_stmt.body, BlockStatement)
        assert len(utility_stmt.body.statements) == 2

        # Check first statement: Set `result` to _3.14159_.
        set_stmt = utility_stmt.body.statements[0]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "result"

    def test_utility_with_inputs_and_outputs(self) -> None:
        """Test parsing a utility with input and output parameters."""
        source = """### **Utility**: `add two numbers`

<details>
<summary>Adds two numbers and returns the result</summary>

> Set `result` to `addend 1` + `addend 2`.

</details>

#### Inputs:
- `addend 1` **as** Whole Number (required)
- `addend 2` **as** Whole Number (required)

#### Outputs:
- `result` **as** Yes/No (default: _Empty_)"""

        parser = Parser()
        program = parser.parse(source)

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

> Set `result` to `value` * _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

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

> Set `amount` to _1000_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

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
        program = parser.parse(source)

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

> Set `x` to _1_.

</details>

### **Utility**: `second utility`

<details>
<summary>Second utility.</summary>

> Set `y` to _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        # Check first utility
        first_utility = program.statements[0]
        assert isinstance(first_utility, UtilityStatement)
        assert first_utility.name.value == "first utility"
        assert len(first_utility.body.statements) == 1

        # Check second utility
        second_utility = program.statements[1]
        assert isinstance(second_utility, UtilityStatement)
        assert second_utility.name.value == "second utility"
        assert len(second_utility.body.statements) == 1

    def test_utility_with_complex_body(self) -> None:
        """Test utility with complex body including conditionals."""
        source = """### **Utility**: `absolute value`

<details>
<summary>Returns the absolute value of a number.</summary>

> If `number` < _0_ then:
> > Set `result` to -`number`.
> Else:
> > Set `result` to `number`.
>
> Give back `result`.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        utility_stmt = program.statements[0]
        assert isinstance(utility_stmt, UtilityStatement)
        assert utility_stmt.name.value == "absolute value"
        assert utility_stmt.description == "Returns the absolute value of a number."
        assert len(utility_stmt.body.statements) == 2  # If statement and Give back statement

    def test_mixed_statements_with_utility(self) -> None:
        """Test that utilities can coexist with actions and interactions."""
        source = """### **Action**: `private method`

<details>
<summary>A private action.</summary>

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

> Set `y` to _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

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
