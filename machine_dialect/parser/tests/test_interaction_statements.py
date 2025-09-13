"""Tests for Interaction statements (public methods) in Machine Dialect™."""

from machine_dialect.ast import (
    BlockStatement,
    EmptyLiteral,
    IfStatement,
    InteractionStatement,
    Output,
)
from machine_dialect.parser import Parser


class TestInteractionStatements:
    """Test parsing of Interaction statements (public methods)."""

    def test_simple_interaction_without_parameters(self) -> None:
        """Test parsing a simple interaction without parameters."""
        source = """### **Interaction**: `turn alarm off`

<details>
<summary>Turns off the alarm when it is on.</summary>

> Define `alarm is on` as Yes/No.
> Set `alarm is on` to _Yes_.
> **if** `alarm is on` **then**:
> >
> > **Set** `alarm is on` **to** _No_.
> > Say _"Alarm has been turned off"_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "turn alarm off"
        assert len(interaction_stmt.inputs) == 0
        assert len(interaction_stmt.outputs) == 0
        assert isinstance(interaction_stmt.body, BlockStatement)

        # The body should contain define + set + if statement
        assert len(interaction_stmt.body.statements) == 3
        if_stmt = interaction_stmt.body.statements[2]
        assert isinstance(if_stmt, IfStatement)

        # The if statement should have a consequence block with 2 statements
        assert isinstance(if_stmt.consequence, BlockStatement)
        assert len(if_stmt.consequence.statements) == 2

    def test_interaction_with_heading_level(self) -> None:
        """Test that interaction heading level (###) is parsed correctly."""
        source = """### **Interaction**: `get status`

<details>
<summary>Returns the current status.</summary>

> Say _"Status: OK"_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "get status"

    def test_interaction_with_multi_word_name(self) -> None:
        """Test interaction with multi-word name in backticks."""
        source = """### **Interaction**: `check system health`

<details>
<summary>Checks if the system is healthy.</summary>

> Define `health` as Text.
> Set `health` to _"Good"_.
> Say `health`.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "check system health"

    def test_interaction_plural_form(self) -> None:
        """Test that 'Interactions' keyword also works."""
        source = """### **Interactions**: `say hello`

<details>
<summary>Greets the user.</summary>

> Say _"Hello!"_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "say hello"

    def test_interaction_with_empty_body(self) -> None:
        """Test interaction with no statements in body."""
        source = """### **Interaction**: `noop`

<details>
<summary>No operation.</summary>

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "noop"
        assert len(interaction_stmt.body.statements) == 0

    def test_multiple_interactions(self) -> None:
        """Test parsing multiple interactions in one program."""
        source = """### **Interaction**: `start process`

<details>
<summary>Starts the process.</summary>

> Define `running` as Yes/No.
> Set `running` to _Yes_.

</details>

### **Interaction**: `stop process`

<details>
<summary>Stops the process.</summary>

> Define `is_running` as Yes/No.
> Set `is_running` to _No_.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        first_interaction = program.statements[0]
        assert isinstance(first_interaction, InteractionStatement)
        assert first_interaction.name.value == "start process"

        second_interaction = program.statements[1]
        assert isinstance(second_interaction, InteractionStatement)
        assert second_interaction.name.value == "stop process"

    def test_interaction_with_parameters(self) -> None:
        """Test parsing an interaction with input and output parameters."""
        source = """### **Interaction**: `get user info`

<details>
<summary>Gets user information.</summary>

> Define `user` as Text.
> Define `age` as Number.
> Set `user` to _"John Doe"_.
> Set `age` to _25_.
> Give back `user`.

</details>

#### Inputs:
- `userId` **as** Text (required)

#### Outputs:
- `user` **as** Text
- `age` **as** Number"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        interaction_stmt = program.statements[0]
        assert isinstance(interaction_stmt, InteractionStatement)
        assert interaction_stmt.name.value == "get user info"

        # Check inputs
        assert len(interaction_stmt.inputs) == 1
        input_param = interaction_stmt.inputs[0]
        assert input_param.name.value == "userId"
        assert input_param.type_name == "Text"
        assert input_param.is_required is True

        # Check outputs
        assert len(interaction_stmt.outputs) == 2

        user_param = interaction_stmt.outputs[0]
        assert isinstance(user_param, Output)
        assert user_param.name.value == "user"
        assert user_param.type_name == "Text"
        # All outputs have Empty as default when not specified
        assert isinstance(user_param.default_value, EmptyLiteral)

        age_param = interaction_stmt.outputs[1]
        assert isinstance(age_param, Output)
        assert age_param.name.value == "age"
        assert age_param.type_name == "Number"
        # All outputs have Empty as default when not specified
        assert isinstance(age_param.default_value, EmptyLiteral)

    def test_mixed_actions_and_interactions(self) -> None:
        """Test parsing both actions and interactions in same program."""
        source = """### **Action**: `internal process`

<details>
<summary>Internal processing.</summary>

> Define `data` as Text.
> Set `data` to _"processed"_.

</details>

### **Interaction**: `get data`

<details>
<summary>Returns processed data.</summary>

> Define `current_data` as Text.
> Say `current_data`.

</details>"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0
        assert len(program.statements) == 2

        # First should be an Action
        from machine_dialect.ast import ActionStatement

        action = program.statements[0]
        assert isinstance(action, ActionStatement)
        assert action.name.value == "internal process"

        # Second should be an Interaction
        interaction = program.statements[1]
        assert isinstance(interaction, InteractionStatement)
        assert interaction.name.value == "get data"
