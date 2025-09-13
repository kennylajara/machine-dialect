"""Tests for MIR value representations."""

from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Temp, Variable


class TestMIRValues:
    """Test MIR value types."""

    def setup_method(self) -> None:
        """Reset temp counter before each test."""
        Temp.reset_counter()

    def test_temp_creation(self) -> None:
        """Test temporary value creation."""
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.FLOAT)
        t3 = Temp(MIRType.STRING, temp_id=10)

        assert str(t1) == "t0"
        assert str(t2) == "t1"
        assert str(t3) == "t10"
        assert t1.type == MIRType.INT
        assert t2.type == MIRType.FLOAT
        assert t3.type == MIRType.STRING

    def test_temp_equality_and_hash(self) -> None:
        """Test temporary equality and hashing."""
        t1 = Temp(MIRType.INT, temp_id=5)
        t2 = Temp(MIRType.FLOAT, temp_id=5)  # Same ID, different type
        t3 = Temp(MIRType.INT, temp_id=6)

        # Equality is based on ID only
        assert t1 == t2
        assert t1 != t3

        # Can be used in sets/dicts
        temp_set = {t1, t2, t3}
        assert len(temp_set) == 2  # t1 and t2 are same

    def test_temp_counter_reset(self) -> None:
        """Test temporary counter reset."""
        t1 = Temp(MIRType.INT)
        assert t1.id == 0

        Temp.reset_counter()
        t2 = Temp(MIRType.INT)
        assert t2.id == 0

    def test_variable_creation(self) -> None:
        """Test variable creation."""
        v1 = Variable("x", MIRType.INT)
        v2 = Variable("y", MIRType.STRING, version=1)
        v3 = Variable("x", MIRType.INT, version=2)

        assert str(v1) == "x"
        assert str(v2) == "y.1"
        assert str(v3) == "x.2"
        assert v1.type == MIRType.INT
        assert v2.type == MIRType.STRING

    def test_variable_equality_and_hash(self) -> None:
        """Test variable equality and hashing."""
        v1 = Variable("x", MIRType.INT, version=1)
        v2 = Variable("x", MIRType.INT, version=1)
        v3 = Variable("x", MIRType.INT, version=2)
        v4 = Variable("y", MIRType.INT, version=1)

        assert v1 == v2
        assert v1 != v3  # Different version
        assert v1 != v4  # Different name

        # Can be used in sets/dicts
        var_set = {v1, v2, v3, v4}
        assert len(var_set) == 3  # v1 and v2 are same

    def test_variable_versioning(self) -> None:
        """Test variable versioning for SSA."""
        v1 = Variable("x", MIRType.INT, version=1)
        v2 = v1.with_version(2)
        v3 = v1.with_version(3)

        assert v1.name == v2.name
        assert v1.type == v2.type
        assert v2.version == 2
        assert v3.version == 3
        assert str(v2) == "x.2"
        assert str(v3) == "x.3"

    def test_constant_creation(self) -> None:
        """Test constant creation."""
        c1 = Constant(42)
        c2 = Constant(3.14)
        c3 = Constant("hello")
        c4 = Constant(True)
        c5 = Constant(None)
        c6 = Constant(100, MIRType.FLOAT)  # Explicit type

        assert str(c1) == "42"
        assert str(c2) == "3.14"
        assert str(c3) == '"hello"'
        assert str(c4) == "True"
        assert str(c5) == "null"
        assert str(c6) == "100"

        assert c1.type == MIRType.INT
        assert c2.type == MIRType.FLOAT
        assert c3.type == MIRType.STRING
        assert c4.type == MIRType.BOOL
        assert c5.type == MIRType.EMPTY
        assert c6.type == MIRType.FLOAT

    def test_constant_equality_and_hash(self) -> None:
        """Test constant equality and hashing."""
        c1 = Constant(42, MIRType.INT)
        c2 = Constant(42, MIRType.INT)
        c3 = Constant(42, MIRType.FLOAT)  # Same value, different type
        c4 = Constant(43, MIRType.INT)

        assert c1 == c2
        assert c1 != c3  # Different type
        assert c1 != c4  # Different value

        # Can be used in sets/dicts
        const_set = {c1, c2, c3, c4}
        assert len(const_set) == 3  # c1 and c2 are same

    def test_function_ref_creation(self) -> None:
        """Test function reference creation."""
        f1 = FunctionRef("main")
        f2 = FunctionRef("helper")

        assert str(f1) == "@main"
        assert str(f2) == "@helper"
        assert f1.type == MIRType.FUNCTION
        assert f1.name == "main"

    def test_function_ref_equality_and_hash(self) -> None:
        """Test function reference equality and hashing."""
        f1 = FunctionRef("foo")
        f2 = FunctionRef("foo")
        f3 = FunctionRef("bar")

        assert f1 == f2
        assert f1 != f3

        # Can be used in sets/dicts
        func_set = {f1, f2, f3}
        assert len(func_set) == 2  # f1 and f2 are same

    def test_mixed_value_comparisons(self) -> None:
        """Test that different value types are not equal."""
        temp = Temp(MIRType.INT, temp_id=1)
        var = Variable("t1", MIRType.INT)  # Same string repr
        const = Constant(1, MIRType.INT)
        func = FunctionRef("t1")

        # All should be different despite similar representations
        assert temp != var
        assert temp != const
        assert temp != func
        assert var != const
        assert var != func
        assert const != func

        # All can coexist in a set
        value_set = {temp, var, const, func}
        assert len(value_set) == 4
