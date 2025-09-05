import pytest

from machine_dialect.parser.symbol_table import SymbolTable, VariableInfo


class TestVariableInfo:
    """Test VariableInfo class."""

    def test_single_type(self) -> None:
        """Test variable with single type."""
        info = VariableInfo(["Whole Number"])
        assert info.allows_type("Whole Number")
        assert not info.allows_type("Text")
        assert str(info) == "VariableInfo(types=Whole Number, uninitialized)"

    def test_union_types(self) -> None:
        """Test variable with union types."""
        info = VariableInfo(["Whole Number", "Text", "Yes/No"])
        assert info.allows_type("Whole Number")
        assert info.allows_type("Text")
        assert info.allows_type("Yes/No")
        assert not info.allows_type("Float")

    def test_initialized_status(self) -> None:
        """Test initialized status tracking."""
        info = VariableInfo(["Text"], initialized=False)
        assert str(info) == "VariableInfo(types=Text, uninitialized)"

        info.initialized = True
        assert str(info) == "VariableInfo(types=Text, initialized)"

    def test_definition_location(self) -> None:
        """Test that definition location is tracked."""
        info = VariableInfo(["Whole Number"], definition_line=10, definition_pos=5)
        assert info.definition_line == 10
        assert info.definition_pos == 5


class TestSymbolTable:
    """Test SymbolTable class."""

    def test_define_and_lookup(self) -> None:
        """Test defining and looking up variables."""
        table = SymbolTable()

        # Define a variable
        table.define("count", ["Whole Number"], line=1, position=5)

        # Look it up
        info = table.lookup("count")
        assert info is not None
        assert info.type_spec == ["Whole Number"]
        assert not info.initialized

    def test_redefinition_error(self) -> None:
        """Test that redefinition raises error."""
        table = SymbolTable()

        # First definition should succeed
        table.define("x", ["Whole Number"], line=1, position=1)

        # Second definition should raise error
        with pytest.raises(NameError) as exc_info:
            table.define("x", ["Text"], line=2, position=1)

        assert "already defined" in str(exc_info.value)
        assert "line 1" in str(exc_info.value)

    def test_lookup_undefined(self) -> None:
        """Test looking up undefined variable returns None."""
        table = SymbolTable()
        info = table.lookup("undefined")
        assert info is None

    def test_mark_initialized(self) -> None:
        """Test marking variable as initialized."""
        table = SymbolTable()
        table.define("message", ["Text"])

        # Should be uninitialized at first
        info = table.lookup("message")
        assert info is not None
        assert not info.initialized

        # Mark as initialized
        table.mark_initialized("message")

        # Should now be initialized
        info = table.lookup("message")
        assert info is not None
        assert info.initialized

    def test_mark_undefined_raises_error(self) -> None:
        """Test marking undefined variable raises error."""
        table = SymbolTable()

        with pytest.raises(NameError) as exc_info:
            table.mark_initialized("undefined")

        assert "not defined" in str(exc_info.value)

    def test_nested_scopes(self) -> None:
        """Test nested scope handling."""
        # Global scope
        global_table = SymbolTable()
        global_table.define("global_var", ["Whole Number"])

        # Enter function scope
        func_table = global_table.enter_scope()
        func_table.define("local_var", ["Text"])

        # Can see both variables from inner scope
        assert func_table.lookup("global_var") is not None
        assert func_table.lookup("local_var") is not None

        # Can only see global from outer scope
        assert global_table.lookup("global_var") is not None
        assert global_table.lookup("local_var") is None

    def test_exit_scope(self) -> None:
        """Test exiting scope returns parent."""
        global_table = SymbolTable()
        func_table = global_table.enter_scope()

        # Exit should return to parent
        parent = func_table.exit_scope()
        assert parent is global_table

        # Exit from global should return None
        assert global_table.exit_scope() is None

    def test_is_defined_in_current_scope(self) -> None:
        """Test checking if variable is in current scope only."""
        global_table = SymbolTable()
        global_table.define("x", ["Whole Number"])

        local_table = global_table.enter_scope()
        local_table.define("y", ["Text"])

        # x is not in local scope (it's in parent)
        assert not local_table.is_defined_in_current_scope("x")
        # y is in local scope
        assert local_table.is_defined_in_current_scope("y")
        # x is in global scope
        assert global_table.is_defined_in_current_scope("x")

    def test_mark_initialized_in_parent_scope(self) -> None:
        """Test marking variable in parent scope as initialized."""
        global_table = SymbolTable()
        global_table.define("global_var", ["Whole Number"])

        # Enter nested scope
        local_table = global_table.enter_scope()

        # Mark parent's variable as initialized from child scope
        local_table.mark_initialized("global_var")

        # Check it's marked in the parent
        info = global_table.lookup("global_var")
        assert info is not None
        assert info.initialized

    def test_multiple_nested_scopes(self) -> None:
        """Test multiple levels of nesting."""
        level1 = SymbolTable()
        level1.define("var1", ["Whole Number"])

        level2 = level1.enter_scope()
        level2.define("var2", ["Text"])

        level3 = level2.enter_scope()
        level3.define("var3", ["Yes/No"])

        # Level 3 can see all variables
        assert level3.lookup("var1") is not None
        assert level3.lookup("var2") is not None
        assert level3.lookup("var3") is not None

        # Level 2 can see var1 and var2
        assert level2.lookup("var1") is not None
        assert level2.lookup("var2") is not None
        assert level2.lookup("var3") is None

        # Level 1 can only see var1
        assert level1.lookup("var1") is not None
        assert level1.lookup("var2") is None
        assert level1.lookup("var3") is None

    def test_string_representation(self) -> None:
        """Test string representation of symbol table."""
        table = SymbolTable()
        table.define("x", ["Whole Number"])
        table.define("y", ["Text", "Number"])

        str_repr = str(table)
        assert "Symbol Table:" in str_repr
        assert "x: VariableInfo" in str_repr
        assert "y: VariableInfo" in str_repr

        # Test with parent
        child = table.enter_scope()
        child.define("z", ["Yes/No"])
        str_repr = str(child)
        assert "has parent scope" in str_repr

    def test_union_type_checking(self) -> None:
        """Test type checking with union types."""
        table = SymbolTable()
        table.define("value", ["Whole Number", "Text", "Empty"])

        info = table.lookup("value")
        assert info is not None
        assert info.allows_type("Whole Number")
        assert info.allows_type("Text")
        assert info.allows_type("Empty")
        assert not info.allows_type("Float")
        assert not info.allows_type("Yes/No")
