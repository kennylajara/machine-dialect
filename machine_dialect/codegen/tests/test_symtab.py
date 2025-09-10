"""Tests for symbol table management."""

from __future__ import annotations

import pytest

from machine_dialect.codegen.symtab import Scope, Symbol, SymbolTable, SymbolType


class TestSymbolType:
    """Test SymbolType enum."""

    def test_symbol_types(self) -> None:
        """Test all symbol type values."""
        assert SymbolType.LOCAL.value == "local"
        assert SymbolType.GLOBAL.value == "global"
        assert SymbolType.PARAMETER.value == "parameter"


class TestSymbol:
    """Test Symbol dataclass."""

    def test_create_symbol(self) -> None:
        """Test creating a symbol."""
        symbol = Symbol("x", SymbolType.LOCAL, 0)
        assert symbol.name == "x"
        assert symbol.symbol_type == SymbolType.LOCAL
        assert symbol.slot == 0

    def test_create_global_symbol(self) -> None:
        """Test creating a global symbol."""
        symbol = Symbol("global_var", SymbolType.GLOBAL, -1)
        assert symbol.name == "global_var"
        assert symbol.symbol_type == SymbolType.GLOBAL
        assert symbol.slot == -1

    def test_create_parameter_symbol(self) -> None:
        """Test creating a parameter symbol."""
        symbol = Symbol("param", SymbolType.PARAMETER, 1)
        assert symbol.name == "param"
        assert symbol.symbol_type == SymbolType.PARAMETER
        assert symbol.slot == 1


class TestScope:
    """Test Scope class."""

    def test_create_global_scope(self) -> None:
        """Test creating a global scope."""
        scope = Scope()
        assert scope.parent is None
        assert scope.name == "global"
        assert scope.is_global is True
        assert len(scope.symbols) == 0
        assert scope.next_slot == 0

    def test_create_nested_scope(self) -> None:
        """Test creating a nested scope."""
        parent = Scope()
        child = Scope(parent, "function")
        assert child.parent is parent
        assert child.name == "function"
        assert child.is_global is False
        assert len(child.symbols) == 0
        assert child.next_slot == 0

    def test_define_local_variable(self) -> None:
        """Test defining a local variable."""
        scope = Scope(Scope(), "function")
        symbol = scope.define_local("x")

        assert symbol.name == "x"
        assert symbol.symbol_type == SymbolType.LOCAL
        assert symbol.slot == 0
        assert scope.next_slot == 1
        assert "x" in scope.symbols

    def test_define_local_variable_already_exists(self) -> None:
        """Test defining a local variable that already exists."""
        scope = Scope(Scope(), "function")
        symbol1 = scope.define_local("x")
        symbol2 = scope.define_local("x")

        # Should return the same symbol
        assert symbol1 is symbol2
        assert scope.next_slot == 1  # Should not increment

    def test_define_multiple_local_variables(self) -> None:
        """Test defining multiple local variables."""
        scope = Scope(Scope(), "function")
        x = scope.define_local("x")
        y = scope.define_local("y")
        z = scope.define_local("z")

        assert x.slot == 0
        assert y.slot == 1
        assert z.slot == 2
        assert scope.next_slot == 3

    def test_define_parameter(self) -> None:
        """Test defining a parameter."""
        scope = Scope(Scope(), "function")
        symbol = scope.define_parameter("param")

        assert symbol.name == "param"
        assert symbol.symbol_type == SymbolType.PARAMETER
        assert symbol.slot == 0
        assert scope.next_slot == 1
        assert "param" in scope.symbols

    def test_define_multiple_parameters(self) -> None:
        """Test defining multiple parameters."""
        scope = Scope(Scope(), "function")
        a = scope.define_parameter("a")
        b = scope.define_parameter("b")

        assert a.slot == 0
        assert b.slot == 1
        assert scope.next_slot == 2

    def test_define_global_variable(self) -> None:
        """Test defining a global variable."""
        scope = Scope()
        symbol = scope.define_global("global_var")

        assert symbol.name == "global_var"
        assert symbol.symbol_type == SymbolType.GLOBAL
        assert symbol.slot == -1
        assert scope.next_slot == 0  # Globals don't use slots
        assert "global_var" in scope.symbols

    def test_resolve_in_current_scope(self) -> None:
        """Test resolving a variable in the current scope."""
        scope = Scope(Scope(), "function")
        defined_symbol = scope.define_local("x")
        resolved_symbol = scope.resolve("x")

        assert resolved_symbol is defined_symbol

    def test_resolve_in_parent_scope(self) -> None:
        """Test resolving a variable in parent scope."""
        parent = Scope()
        parent_symbol = parent.define_global("global_var")
        child = Scope(parent, "function")

        resolved_symbol = child.resolve("global_var")
        assert resolved_symbol is parent_symbol

    def test_resolve_nested_scopes(self) -> None:
        """Test resolving through multiple nested scopes."""
        grandparent = Scope()
        grandparent_symbol = grandparent.define_global("x")

        parent = Scope(grandparent, "outer")
        child = Scope(parent, "inner")

        resolved_symbol = child.resolve("x")
        assert resolved_symbol is grandparent_symbol

    def test_resolve_not_found(self) -> None:
        """Test resolving a non-existent variable."""
        scope = Scope()
        resolved_symbol = scope.resolve("nonexistent")
        assert resolved_symbol is None

    def test_resolve_shadowing(self) -> None:
        """Test variable shadowing."""
        parent = Scope()
        parent.define_global("x")

        child = Scope(parent, "function")
        child_symbol = child.define_local("x")

        # Should resolve to child's x, not parent's
        resolved_symbol = child.resolve("x")
        assert resolved_symbol is child_symbol
        assert resolved_symbol.symbol_type == SymbolType.LOCAL

    def test_num_locals(self) -> None:
        """Test getting number of locals."""
        scope = Scope(Scope(), "function")
        assert scope.num_locals() == 0

        scope.define_local("x")
        assert scope.num_locals() == 1

        scope.define_local("y")
        assert scope.num_locals() == 2

        # Parameters also count as locals for slot allocation
        scope.define_parameter("param")
        assert scope.num_locals() == 3

    def test_num_locals_globals_dont_count(self) -> None:
        """Test that globals don't count toward num_locals."""
        scope = Scope()
        scope.define_global("global1")
        scope.define_global("global2")
        assert scope.num_locals() == 0


class TestSymbolTable:
    """Test SymbolTable class."""

    def test_create_symbol_table(self) -> None:
        """Test creating a symbol table."""
        symtab = SymbolTable()
        assert symtab.current_scope is symtab.global_scope
        assert symtab.current_scope.name == "global"
        assert symtab.is_global_scope() is True

    def test_enter_scope(self) -> None:
        """Test entering a new scope."""
        symtab = SymbolTable()
        symtab.enter_scope("function")

        assert symtab.current_scope.name == "function"
        assert symtab.current_scope.parent is symtab.global_scope
        assert symtab.is_global_scope() is False

    def test_exit_scope(self) -> None:
        """Test exiting a scope."""
        symtab = SymbolTable()
        symtab.enter_scope("function")
        symtab.exit_scope()

        assert symtab.current_scope is symtab.global_scope
        assert symtab.is_global_scope() is True

    def test_exit_global_scope_raises_error(self) -> None:
        """Test that exiting global scope raises an error."""
        symtab = SymbolTable()
        with pytest.raises(RuntimeError, match="Cannot exit global scope"):
            symtab.exit_scope()

    def test_nested_scopes(self) -> None:
        """Test nested scope management."""
        symtab = SymbolTable()

        # Enter function scope
        symtab.enter_scope("function")
        function_scope = symtab.current_scope

        # Enter block scope
        symtab.enter_scope("block")
        block_scope = symtab.current_scope

        assert block_scope.parent is function_scope
        assert function_scope.parent is symtab.global_scope

        # Exit back to function
        symtab.exit_scope()
        assert symtab.current_scope is function_scope

        # Exit back to global
        symtab.exit_scope()
        assert symtab.current_scope is symtab.global_scope

    def test_define_in_global_scope(self) -> None:
        """Test defining variables in global scope."""
        symtab = SymbolTable()
        symbol = symtab.define("global_var")

        assert symbol.symbol_type == SymbolType.GLOBAL
        assert symbol.slot == -1
        assert symbol.name == "global_var"

    def test_define_in_local_scope(self) -> None:
        """Test defining variables in local scope."""
        symtab = SymbolTable()
        symtab.enter_scope("function")

        symbol = symtab.define("local_var")
        assert symbol.symbol_type == SymbolType.LOCAL
        assert symbol.slot == 0
        assert symbol.name == "local_var"

    def test_define_parameter(self) -> None:
        """Test defining parameters."""
        symtab = SymbolTable()
        symtab.enter_scope("function")

        symbol = symtab.define("param", is_parameter=True)
        assert symbol.symbol_type == SymbolType.PARAMETER
        assert symbol.slot == 0
        assert symbol.name == "param"

    def test_define_parameter_in_global_scope(self) -> None:
        """Test that parameters in global scope become globals."""
        symtab = SymbolTable()
        symbol = symtab.define("param", is_parameter=True)

        # In global scope, parameters become globals
        assert symbol.symbol_type == SymbolType.GLOBAL
        assert symbol.slot == -1

    def test_resolve_local_variable(self) -> None:
        """Test resolving a local variable."""
        symtab = SymbolTable()
        symtab.enter_scope("function")

        defined_symbol = symtab.define("x")
        resolved_symbol = symtab.resolve("x")

        assert resolved_symbol is defined_symbol

    def test_resolve_global_variable(self) -> None:
        """Test resolving a global variable."""
        symtab = SymbolTable()
        global_symbol = symtab.define("global_var")

        symtab.enter_scope("function")
        resolved_symbol = symtab.resolve("global_var")

        assert resolved_symbol is global_symbol

    def test_resolve_creates_implicit_global(self) -> None:
        """Test that resolving undefined variable creates implicit global."""
        symtab = SymbolTable()
        symtab.enter_scope("function")

        resolved_symbol = symtab.resolve("undefined_var")

        assert resolved_symbol is not None
        assert resolved_symbol.name == "undefined_var"
        assert resolved_symbol.symbol_type == SymbolType.GLOBAL
        assert resolved_symbol.slot == -1

    def test_resolve_in_global_scope_returns_none(self) -> None:
        """Test that resolving undefined var in global scope returns None."""
        symtab = SymbolTable()
        resolved_symbol = symtab.resolve("undefined_var")
        assert resolved_symbol is None

    def test_num_locals(self) -> None:
        """Test getting number of locals in current scope."""
        symtab = SymbolTable()
        assert symtab.num_locals() == 0

        symtab.enter_scope("function")
        assert symtab.num_locals() == 0

        symtab.define("x")
        assert symtab.num_locals() == 1

        symtab.define("y")
        assert symtab.num_locals() == 2

    def test_current_scope_name(self) -> None:
        """Test getting current scope name."""
        symtab = SymbolTable()
        assert symtab.current_scope_name() == "global"

        symtab.enter_scope("function")
        assert symtab.current_scope_name() == "function"

        symtab.enter_scope("block")
        assert symtab.current_scope_name() == "block"

    def test_complex_scoping_scenario(self) -> None:
        """Test a complex scenario with multiple scopes and variables."""
        symtab = SymbolTable()

        # Define global variable
        global_var = symtab.define("global_var")

        # Enter function scope
        symtab.enter_scope("function")
        param1 = symtab.define("param1", is_parameter=True)
        param2 = symtab.define("param2", is_parameter=True)
        local1 = symtab.define("local1")

        # Enter block scope
        symtab.enter_scope("block")
        local2 = symtab.define("local2")

        # Test resolution from deepest scope
        assert symtab.resolve("local2") is local2
        assert symtab.resolve("local1") is local1
        assert symtab.resolve("param1") is param1
        assert symtab.resolve("global_var") is global_var

        # Test slot allocation
        assert param1.slot == 0
        assert param2.slot == 1
        assert local1.slot == 2
        assert local2.slot == 0  # New scope, new slot numbering

        # Test scope info
        assert symtab.current_scope_name() == "block"
        assert symtab.num_locals() == 1  # Only local2 in current scope

        symtab.exit_scope()
        assert symtab.num_locals() == 3  # param1, param2, local1

    def test_variable_shadowing_through_symbol_table(self) -> None:
        """Test variable shadowing through symbol table interface."""
        symtab = SymbolTable()

        # Define global x
        global_x = symtab.define("x")

        # Enter function and define local x
        symtab.enter_scope("function")
        local_x = symtab.define("x")

        # Should resolve to local x
        resolved_x = symtab.resolve("x")
        assert resolved_x is local_x
        assert resolved_x.symbol_type == SymbolType.LOCAL

        # Exit function scope
        symtab.exit_scope()

        # Should now resolve to global x
        resolved_x = symtab.resolve("x")
        assert resolved_x is global_x
        assert resolved_x.symbol_type == SymbolType.GLOBAL
