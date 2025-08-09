"""Tests for Action statements (private methods) in Machine Dialect."""


from machine_dialect.ast import ActionStatement, BlockStatement, SetStatement
from machine_dialect.parser import Parser


class TestActionStatements:
    """Test parsing of Action statements (private methods)."""

    def test_simple_action_without_parameters(self) -> None:
        """Test parsing a simple action without parameters."""
        source = """### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

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
        assert len(action_stmt.parameters) == 0
        assert isinstance(action_stmt.body, BlockStatement)
        assert len(action_stmt.body.statements) == 2

        # Check first statement: Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.
        set_stmt = action_stmt.body.statements[0]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name and set_stmt.name.value == "noise"

        # Check second statement: Say `noise`.
        say_stmt = action_stmt.body.statements[1]
        from machine_dialect.ast import SayStatement

        assert isinstance(say_stmt, SayStatement)

    def test_action_with_heading_level(self) -> None:
        """Test that action heading level (###) is parsed correctly."""
        source = """### **Action**: `calculate`

<details>
<summary>Performs a calculation.</summary>

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

> Set `x` to _1_.

</details>

### **Action**: `second action`

<details>
<summary>Second action.</summary>

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
