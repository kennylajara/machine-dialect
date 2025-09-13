"""Tests for escape analysis."""

from machine_dialect.mir.analyses.escape_analysis import EscapeAnalysis, EscapeState
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    Copy,
    LoadConst,
    Return,
    SetAttr,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Variable


def create_simple_function() -> MIRFunction:
    """Create a simple function for testing.

    def simple(x):
        a = 10
        b = a + x
        return b
    """
    func = MIRFunction("simple", [Variable("x", MIRType.INT)])
    func.locals["a"] = Variable("a", MIRType.INT)
    func.locals["b"] = Variable("b", MIRType.INT)

    entry = func.cfg.get_or_create_block("entry")
    func.cfg.entry_block = entry

    x_var = Variable("x", MIRType.INT)
    a_var = Variable("a", MIRType.INT)
    b_var = Variable("b", MIRType.INT)

    entry.instructions = [
        LoadConst(a_var, Constant(10), (1, 1)),
        BinaryOp(b_var, "+", a_var, x_var, (1, 1)),
        Return((1, 1), b_var),
    ]

    return func


def create_escaping_function() -> MIRFunction:
    """Create a function with escaping variables.

    def escaping(x):
        a = 10
        b = foo(a)  # a escapes as argument
        return b
    """
    func = MIRFunction("escaping", [Variable("x", MIRType.INT)])
    func.locals["a"] = Variable("a", MIRType.INT)
    func.locals["b"] = Variable("b", MIRType.INT)

    entry = func.cfg.get_or_create_block("entry")
    func.cfg.entry_block = entry

    a_var = Variable("a", MIRType.INT)
    b_var = Variable("b", MIRType.INT)

    entry.instructions = [
        LoadConst(a_var, Constant(10), (1, 1)),
        Call(b_var, FunctionRef("foo"), [a_var], (1, 1)),
        Return((1, 1), b_var),
    ]

    return func


def create_aliasing_function() -> MIRFunction:
    """Create a function with aliasing variables.

    def aliasing():
        a = 10
        b = a  # b aliases a
        c = b  # c aliases b and a
        return c
    """
    func = MIRFunction("aliasing")
    func.locals["a"] = Variable("a", MIRType.INT)
    func.locals["b"] = Variable("b", MIRType.INT)
    func.locals["c"] = Variable("c", MIRType.INT)

    entry = func.cfg.get_or_create_block("entry")
    func.cfg.entry_block = entry

    a_var = Variable("a", MIRType.INT)
    b_var = Variable("b", MIRType.INT)
    c_var = Variable("c", MIRType.INT)

    entry.instructions = [
        LoadConst(a_var, Constant(10), (1, 1)),
        Copy(b_var, a_var, (1, 1)),  # b = a
        Copy(c_var, b_var, (1, 1)),  # c = b
        Return((1, 1), c_var),
    ]

    return func


def create_heap_escape_function() -> MIRFunction:
    """Create a function where variable escapes to heap.

    def heap_escape(obj):
        a = 10
        obj.field = a  # a escapes to heap
        return obj
    """
    func = MIRFunction("heap_escape", [Variable("obj", MIRType.INT)])
    func.locals["a"] = Variable("a", MIRType.INT)

    entry = func.cfg.get_or_create_block("entry")
    func.cfg.entry_block = entry

    obj_var = Variable("obj", MIRType.INT)  # Use INT as placeholder
    a_var = Variable("a", MIRType.INT)

    entry.instructions = [
        LoadConst(a_var, Constant(10), (1, 1)),
        SetAttr(obj_var, "field", a_var),
        Return((1, 1), obj_var),
    ]

    return func


class TestEscapeAnalysis:
    """Test escape analysis."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analysis = EscapeAnalysis()

    def test_no_escape(self) -> None:
        """Test variables that don't escape."""
        func = create_simple_function()
        escape_info = self.analysis.run_on_function(func)

        # 'a' should not escape (only used locally)
        a_var = Variable("a", MIRType.INT)
        assert not escape_info.does_escape(a_var)
        assert escape_info.is_stack_eligible(a_var)

        # 'b' escapes via return
        b_var = Variable("b", MIRType.INT)
        assert escape_info.does_escape(b_var)
        assert not escape_info.is_stack_eligible(b_var)

    def test_argument_escape(self) -> None:
        """Test variables escaping as function arguments."""
        func = create_escaping_function()
        escape_info = self.analysis.run_on_function(func)

        # 'a' escapes as argument to foo()
        a_var = Variable("a", MIRType.INT)
        assert escape_info.does_escape(a_var)
        assert not escape_info.is_stack_eligible(a_var)

        info = escape_info.get_info(a_var)
        assert info is not None
        if info:
            assert info.state == EscapeState.ARG_ESCAPE

    def test_alias_propagation(self) -> None:
        """Test escape propagation through aliases."""
        func = create_aliasing_function()
        escape_info = self.analysis.run_on_function(func)

        # 'c' escapes via return
        c_var = Variable("c", MIRType.INT)
        assert escape_info.does_escape(c_var)

        # 'b' aliases 'c', so it should also escape
        b_var = Variable("b", MIRType.INT)
        assert escape_info.does_escape(b_var)

        # 'a' aliases 'b' which aliases 'c', so it should also escape
        a_var = Variable("a", MIRType.INT)
        assert escape_info.does_escape(a_var)

    def test_heap_escape(self) -> None:
        """Test variables escaping to heap."""
        func = create_heap_escape_function()
        escape_info = self.analysis.run_on_function(func)

        # 'a' escapes to heap via SetAttr
        a_var = Variable("a", MIRType.INT)
        assert escape_info.does_escape(a_var)
        assert not escape_info.is_stack_eligible(a_var)

        info = escape_info.get_info(a_var)
        assert info is not None
        if info:
            assert info.state == EscapeState.HEAP_ESCAPE

    def test_parameter_handling(self) -> None:
        """Test handling of function parameters."""
        func = create_simple_function()
        escape_info = self.analysis.run_on_function(func)

        # Parameters are tracked but not considered escaping just by existing
        x_var = Variable("x", MIRType.INT)
        # 'x' is used in computation but doesn't escape further
        assert not escape_info.does_escape(x_var)

    def test_escape_sites(self) -> None:
        """Test tracking of escape sites."""
        func = create_escaping_function()
        escape_info = self.analysis.run_on_function(func)

        a_var = Variable("a", MIRType.INT)
        info = escape_info.get_info(a_var)
        assert info is not None

        # Should have one escape site (the Call instruction)
        if info:
            assert len(info.escape_sites) == 1
            assert isinstance(info.escape_sites[0], Call)

    def test_stack_eligible_collection(self) -> None:
        """Test collection of stack-eligible variables."""
        func = create_simple_function()
        escape_info = self.analysis.run_on_function(func)

        # 'a' should be stack eligible
        a_var = Variable("a", MIRType.INT)
        assert a_var in escape_info.stack_eligible

        # 'b' should not be stack eligible (escapes via return)
        b_var = Variable("b", MIRType.INT)
        assert b_var in escape_info.escaping_vars
