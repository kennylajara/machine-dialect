"""Tests for Action statements (private methods) in Machine Dialect™."""

from machine_dialect.ast import ActionStatement, BlockStatement, EmptyLiteral, Output, SetStatement
from machine_dialect.parser import Parser


class TestActionStatements:
    """Test parsing of Action statements (private methods)."""

    def test_simple_action_without_parameters(self) -> None:
        """Test parsing a simple action without parameters."""
        source = """### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

> Define `noise` as Text.
> Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.
> Say `noise`.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "make noise"
        assert len(action_stmt.inputs) == 0
        assert len(action_stmt.outputs) == 0
        assert isinstance(action_stmt.body, BlockStatement)
        assert len(action_stmt.body.statements) == 3

        # Check first statement: Define `noise` as Text.
        from machine_dialect.ast import DefineStatement

        define_stmt = action_stmt.body.statements[0]
        assert isinstance(define_stmt, DefineStatement)
        assert define_stmt.name.value == "noise"

        # Check second statement: Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.
        set_stmt = action_stmt.body.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "noise"

        # Check third statement: Say `noise`.
        say_stmt = action_stmt.body.statements[2]
        from machine_dialect.ast import SayStatement

        assert isinstance(say_stmt, SayStatement)

    def test_action_with_heading_level(self) -> None:
        """Test that action heading level (###) is parsed correctly."""
        source = """### **Action**: `calculate`

<details>
<summary>Performs a calculation.</summary>

> Define `result` as Whole Number.
> Set `result` to _42_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "calculate"

    def test_action_with_multi_word_name(self) -> None:
        """Test action with multi-word name in backticks."""
        source = """### **Action**: `send alert message`

<details>
<summary>Sends an alert.</summary>

> Say _"Alert!"_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "send alert message"

    def test_action_plural_form(self) -> None:
        """Test that 'Actions' keyword also works."""
        source = """### **Actions**: `make noise`

<details>
<summary>Emits sound.</summary>

> Say _"Noise"_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "make noise"

    def test_action_with_empty_body(self) -> None:
        """Test action with no statements in body."""
        source = """### **Action**: `do nothing`

<details>
<summary>Does nothing.</summary>

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "do nothing"
        assert len(action_stmt.body.statements) == 0

    def test_multiple_actions(self) -> None:
        """Test parsing multiple actions in one program."""
        source = """### **Action**: `first action`

<details>
<summary>First action.</summary>

> Define `x` as Whole Number.
> Set `x` to _1_.

</details>

### **Action**: `second action`

<details>
<summary>Second action.</summary>

> Define `y` as Whole Number.
> Set `y` to _2_.

</details>"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        first_action = program.statements[0]
        assert isinstance(first_action, ActionStatement)
        assert first_action.name.value == "first action"

        second_action = program.statements[1]
        assert isinstance(second_action, ActionStatement)
        assert second_action.name.value == "second action"

    def test_action_with_input_parameters(self) -> None:
        """Test parsing an action with input parameters."""
        source = """### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

> Define `noise` as Text.
> Set `noise` to `sound`.
> Say `noise`.

</details>

#### Inputs:
- `sound` **as** Text (required)
- `volume` **as** Whole Number (optional, default: _60_)"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "make noise"

        # Check inputs
        assert len(action_stmt.inputs) == 2

        # First input: sound (required)
        sound_param = action_stmt.inputs[0]
        assert sound_param.name.value == "sound"
        assert sound_param.type_name == "Text"
        assert sound_param.is_required is True
        assert sound_param.default_value is None

        # Second input: volume (optional with default)
        volume_param = action_stmt.inputs[1]
        assert volume_param.name.value == "volume"
        assert volume_param.type_name == "Whole Number"
        assert volume_param.is_required is False
        assert volume_param.default_value is not None
        from machine_dialect.ast import WholeNumberLiteral

        assert isinstance(volume_param.default_value, WholeNumberLiteral)
        assert volume_param.default_value.value == 60

        # No outputs
        assert len(action_stmt.outputs) == 0

    def test_action_with_output_parameters(self) -> None:
        """Test parsing an action with output parameters."""
        source = """### **Action**: `calculate`

<details>
<summary>Performs a calculation.</summary>

> Define `result` as Number.
> Set `result` to _42_.
> Give back `result`.

</details>

#### Outputs:
- `result` **as** Number
- `success` **as** Yes/No"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "calculate"

        # No inputs
        assert len(action_stmt.inputs) == 0

        # Check outputs
        assert len(action_stmt.outputs) == 2

        # First output: result
        result_param = action_stmt.outputs[0]
        assert isinstance(result_param, Output)
        assert result_param.name.value == "result"
        assert result_param.type_name == "Number"

        # Second output: success
        success_param = action_stmt.outputs[1]
        assert isinstance(success_param, Output)
        assert success_param.name.value == "success"
        assert success_param.type_name == "Yes/No"

    def test_action_with_both_inputs_and_outputs(self) -> None:
        """Test parsing an action with both input and output parameters."""
        source = """### **Action**: `process data`

<details>
<summary>Processes input data.</summary>

> Define `result` as Text.
> Set `result` to `input`.
> Give back `result`.

</details>

#### Inputs:
- `input` **as** Text (required)
- `format` **as** Text (optional, default: _"json"_)

#### Outputs:
- `result` **as** Text
- `error` **as** Text"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        action_stmt = program.statements[0]
        assert isinstance(action_stmt, ActionStatement)
        assert action_stmt.name.value == "process data"

        # Check inputs
        assert len(action_stmt.inputs) == 2

        input_param = action_stmt.inputs[0]
        assert input_param.name.value == "input"
        assert input_param.type_name == "Text"
        assert input_param.is_required is True

        format_param = action_stmt.inputs[1]
        assert format_param.name.value == "format"
        assert format_param.type_name == "Text"
        assert format_param.is_required is False
        assert format_param.default_value is not None
        from machine_dialect.ast import StringLiteral

        assert isinstance(format_param.default_value, StringLiteral)
        assert format_param.default_value.value == "json"

        # Check outputs
        assert len(action_stmt.outputs) == 2

        result_param = action_stmt.outputs[0]
        assert isinstance(result_param, Output)
        assert result_param.name.value == "result"
        assert result_param.type_name == "Text"

        error_param = action_stmt.outputs[1]
        assert isinstance(error_param, Output)
        assert error_param.name.value == "error"
        assert error_param.type_name == "Text"
        # Outputs without explicit defaults should have Empty as default
        assert error_param.default_value is not None
        assert isinstance(error_param.default_value, EmptyLiteral)
