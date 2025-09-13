"""Test VM execution of various Machine Dialect™ programs."""

from __future__ import annotations

from machine_dialect.compiler.vm_runner import VMRunner


class TestVMExecution:
    """Test suite for VM execution."""

    def test_simple_arithmetic(self) -> None:
        """Test simple arithmetic operations."""
        source = """
Set `x` to _10_.
Set `y` to _20_.
Set `sum` to `x` + `y`.
Give back `sum`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 30

    def test_multiplication(self) -> None:
        """Test multiplication."""
        source = """
Set `a` to _5_.
Set `b` to _6_.
Set `product` to `a` * `b`.
Give back `product`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 30

    def test_division(self) -> None:
        """Test division."""
        source = """
Set `n` to _100_.
Set `d` to _4_.
Set `quotient` to `n` / `d`.
Give back `quotient`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 25

    def test_comparison(self) -> None:
        """Test comparison operations."""
        source = """
Set `x` to _10_.
Set `y` to _20_.
Set `result` to `x` < `y`.
Give back `result`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result is True

    def test_if_statement(self) -> None:
        """Test if statement execution."""
        source = """
Set `x` to _10_.
If `x` > _5_ then:
> Give back _42_.
Otherwise:
> Give back _0_.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 42

    def test_else_branch(self) -> None:
        """Test else branch execution."""
        source = """
Set `x` to _3_.
If `x` > _5_ then:
> Give back _42_.
Otherwise:
> Give back _99_.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 99

    def test_nested_arithmetic(self) -> None:
        """Test nested arithmetic expressions."""
        source = """
Set `a` to _10_.
Set `b` to _20_.
Set `c` to _30_.
Set `result` to (`a` + `b`) * `c`.
Give back `result`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 900

    def test_boolean_values(self) -> None:
        """Test boolean literal values."""
        source = """
Set `flag` to _true_.
Give back `flag`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result is True

    def test_empty_value(self) -> None:
        """Test empty/null value."""
        source = """
Set `nothing` to _empty_.
Give back `nothing`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result is None

    def test_variable_reassignment(self) -> None:
        """Test variable reassignment."""
        source = """
Set `x` to _10_.
Set `x` to _20_.
Set `x` to `x` + _5_.
Give back `x`.
"""
        runner = VMRunner(debug=False)
        result = runner.execute(source)
        assert result == 25
