"""Tests for MIR value representations."""

import unittest

from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Temp, Variable


class TestMIRValues(unittest.TestCase):
    """Test MIR value types."""

    def setUp(self) -> None:
        """Reset temp counter before each test."""
        Temp.reset_counter()

    def test_temp_creation(self) -> None:
        """Test temporary value creation."""
        t1 = Temp(MIRType.INT)
        t2 = Temp(MIRType.FLOAT)
        t3 = Temp(MIRType.STRING, temp_id=10)

        self.assertEqual(str(t1), "t0")
        self.assertEqual(str(t2), "t1")
        self.assertEqual(str(t3), "t10")
        self.assertEqual(t1.type, MIRType.INT)
        self.assertEqual(t2.type, MIRType.FLOAT)
        self.assertEqual(t3.type, MIRType.STRING)

    def test_temp_equality_and_hash(self) -> None:
        """Test temporary equality and hashing."""
        t1 = Temp(MIRType.INT, temp_id=5)
        t2 = Temp(MIRType.FLOAT, temp_id=5)  # Same ID, different type
        t3 = Temp(MIRType.INT, temp_id=6)

        # Equality is based on ID only
        self.assertEqual(t1, t2)
        self.assertNotEqual(t1, t3)

        # Can be used in sets/dicts
        temp_set = {t1, t2, t3}
        self.assertEqual(len(temp_set), 2)  # t1 and t2 are same

    def test_temp_counter_reset(self) -> None:
        """Test temporary counter reset."""
        t1 = Temp(MIRType.INT)
        self.assertEqual(t1.id, 0)

        Temp.reset_counter()
        t2 = Temp(MIRType.INT)
        self.assertEqual(t2.id, 0)

    def test_variable_creation(self) -> None:
        """Test variable creation."""
        v1 = Variable("x", MIRType.INT)
        v2 = Variable("y", MIRType.STRING, version=1)
        v3 = Variable("x", MIRType.INT, version=2)

        self.assertEqual(str(v1), "x")
        self.assertEqual(str(v2), "y.1")
        self.assertEqual(str(v3), "x.2")
        self.assertEqual(v1.type, MIRType.INT)
        self.assertEqual(v2.type, MIRType.STRING)

    def test_variable_equality_and_hash(self) -> None:
        """Test variable equality and hashing."""
        v1 = Variable("x", MIRType.INT, version=1)
        v2 = Variable("x", MIRType.INT, version=1)
        v3 = Variable("x", MIRType.INT, version=2)
        v4 = Variable("y", MIRType.INT, version=1)

        self.assertEqual(v1, v2)
        self.assertNotEqual(v1, v3)  # Different version
        self.assertNotEqual(v1, v4)  # Different name

        # Can be used in sets/dicts
        var_set = {v1, v2, v3, v4}
        self.assertEqual(len(var_set), 3)  # v1 and v2 are same

    def test_variable_versioning(self) -> None:
        """Test variable versioning for SSA."""
        v1 = Variable("x", MIRType.INT, version=1)
        v2 = v1.with_version(2)
        v3 = v1.with_version(3)

        self.assertEqual(v1.name, v2.name)
        self.assertEqual(v1.type, v2.type)
        self.assertEqual(v2.version, 2)
        self.assertEqual(v3.version, 3)
        self.assertEqual(str(v2), "x.2")
        self.assertEqual(str(v3), "x.3")

    def test_constant_creation(self) -> None:
        """Test constant creation."""
        c1 = Constant(42)
        c2 = Constant(3.14)
        c3 = Constant("hello")
        c4 = Constant(True)
        c5 = Constant(None)
        c6 = Constant(100, MIRType.FLOAT)  # Explicit type

        self.assertEqual(str(c1), "42")
        self.assertEqual(str(c2), "3.14")
        self.assertEqual(str(c3), '"hello"')
        self.assertEqual(str(c4), "True")
        self.assertEqual(str(c5), "null")
        self.assertEqual(str(c6), "100")

        self.assertEqual(c1.type, MIRType.INT)
        self.assertEqual(c2.type, MIRType.FLOAT)
        self.assertEqual(c3.type, MIRType.STRING)
        self.assertEqual(c4.type, MIRType.BOOL)
        self.assertEqual(c5.type, MIRType.EMPTY)
        self.assertEqual(c6.type, MIRType.FLOAT)

    def test_constant_equality_and_hash(self) -> None:
        """Test constant equality and hashing."""
        c1 = Constant(42, MIRType.INT)
        c2 = Constant(42, MIRType.INT)
        c3 = Constant(42, MIRType.FLOAT)  # Same value, different type
        c4 = Constant(43, MIRType.INT)

        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)  # Different type
        self.assertNotEqual(c1, c4)  # Different value

        # Can be used in sets/dicts
        const_set = {c1, c2, c3, c4}
        self.assertEqual(len(const_set), 3)  # c1 and c2 are same

    def test_function_ref_creation(self) -> None:
        """Test function reference creation."""
        f1 = FunctionRef("main")
        f2 = FunctionRef("helper")

        self.assertEqual(str(f1), "@main")
        self.assertEqual(str(f2), "@helper")
        self.assertEqual(f1.type, MIRType.FUNCTION)
        self.assertEqual(f1.name, "main")

    def test_function_ref_equality_and_hash(self) -> None:
        """Test function reference equality and hashing."""
        f1 = FunctionRef("foo")
        f2 = FunctionRef("foo")
        f3 = FunctionRef("bar")

        self.assertEqual(f1, f2)
        self.assertNotEqual(f1, f3)

        # Can be used in sets/dicts
        func_set = {f1, f2, f3}
        self.assertEqual(len(func_set), 2)  # f1 and f2 are same

    def test_mixed_value_comparisons(self) -> None:
        """Test that different value types are not equal."""
        temp = Temp(MIRType.INT, temp_id=1)
        var = Variable("t1", MIRType.INT)  # Same string repr
        const = Constant(1, MIRType.INT)
        func = FunctionRef("t1")

        # All should be different despite similar representations
        self.assertNotEqual(temp, var)
        self.assertNotEqual(temp, const)
        self.assertNotEqual(temp, func)
        self.assertNotEqual(var, const)
        self.assertNotEqual(var, func)
        self.assertNotEqual(const, func)

        # All can coexist in a set
        value_set = {temp, var, const, func}
        self.assertEqual(len(value_set), 4)


if __name__ == "__main__":
    unittest.main()
