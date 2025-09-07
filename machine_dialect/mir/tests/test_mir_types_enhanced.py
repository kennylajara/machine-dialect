"""Tests for enhanced MIR type system."""

from machine_dialect.mir.mir_types import (
    MIRType,
    MIRUnionType,
    can_cast,
    is_assignable,
)
from machine_dialect.mir.mir_values import Constant, Temp, Variable


class TestEnhancedTypeSystem:
    """Test enhanced MIR type system functionality."""

    def test_can_cast_same_type(self) -> None:
        """Test that same types can be cast to each other."""
        assert can_cast(MIRType.INT, MIRType.INT)
        assert can_cast(MIRType.STRING, MIRType.STRING)
        assert can_cast(MIRType.BOOL, MIRType.BOOL)

    def test_can_cast_numeric(self) -> None:
        """Test numeric type casting."""
        assert can_cast(MIRType.INT, MIRType.FLOAT)
        assert can_cast(MIRType.FLOAT, MIRType.INT)

    def test_can_cast_bool_numeric(self) -> None:
        """Test bool to numeric casting."""
        assert can_cast(MIRType.BOOL, MIRType.INT)
        assert can_cast(MIRType.BOOL, MIRType.FLOAT)
        assert can_cast(MIRType.INT, MIRType.BOOL)
        assert can_cast(MIRType.FLOAT, MIRType.BOOL)

    def test_can_cast_to_string(self) -> None:
        """Test that all types can be cast to string."""
        assert can_cast(MIRType.INT, MIRType.STRING)
        assert can_cast(MIRType.FLOAT, MIRType.STRING)
        assert can_cast(MIRType.BOOL, MIRType.STRING)
        assert can_cast(MIRType.EMPTY, MIRType.STRING)

    def test_can_cast_empty(self) -> None:
        """Test that empty (null) can be cast to any type."""
        assert can_cast(MIRType.EMPTY, MIRType.INT)
        assert can_cast(MIRType.EMPTY, MIRType.FLOAT)
        assert can_cast(MIRType.EMPTY, MIRType.STRING)
        assert can_cast(MIRType.EMPTY, MIRType.BOOL)

    def test_cannot_cast_invalid(self) -> None:
        """Test invalid casts."""
        assert not can_cast(MIRType.STRING, MIRType.INT)
        assert not can_cast(MIRType.STRING, MIRType.FLOAT)
        assert not can_cast(MIRType.STRING, MIRType.BOOL)

    def test_is_assignable_single_types(self) -> None:
        """Test assignment compatibility for single types."""
        assert is_assignable(MIRType.INT, MIRType.INT)
        assert is_assignable(MIRType.INT, MIRType.FLOAT)
        assert is_assignable(MIRType.EMPTY, MIRType.INT)
        assert not is_assignable(MIRType.STRING, MIRType.INT)

    def test_is_assignable_union_to_single(self) -> None:
        """Test assigning union type to single type."""
        union = MIRUnionType([MIRType.INT, MIRType.FLOAT])
        # Union of numeric types CAN be assigned to bool (all members can cast)
        assert is_assignable(union, MIRType.BOOL)
        # Individual numeric types can be cast to string
        assert is_assignable(union, MIRType.STRING)

        # Union with non-castable type
        union2 = MIRUnionType([MIRType.STRING, MIRType.URL])
        assert not is_assignable(union2, MIRType.INT)  # String can't cast to int

    def test_is_assignable_single_to_union(self) -> None:
        """Test assigning single type to union type."""
        union = MIRUnionType([MIRType.INT, MIRType.STRING])
        assert is_assignable(MIRType.INT, union)
        assert is_assignable(MIRType.STRING, union)
        assert is_assignable(MIRType.EMPTY, union)  # Empty can be assigned to any
        assert is_assignable(MIRType.FLOAT, union)  # Float can cast to INT in union

    def test_is_assignable_union_to_union(self) -> None:
        """Test assigning union type to union type."""
        union1 = MIRUnionType([MIRType.INT, MIRType.FLOAT])
        union2 = MIRUnionType([MIRType.INT, MIRType.FLOAT, MIRType.STRING])
        assert is_assignable(union1, union2)  # Subset is assignable
        assert not is_assignable(union2, union1)  # Superset is not

    def test_variable_with_union_type(self) -> None:
        """Test creating variables with union types."""
        union = MIRUnionType([MIRType.INT, MIRType.STRING])
        var = Variable("x", union)

        # Check that union type is properly stored
        assert var.union_type == union
        assert var.type == MIRType.UNKNOWN  # Base type is unknown for unions

    def test_temp_with_union_type(self) -> None:
        """Test creating temporaries with union types."""
        union = MIRUnionType([MIRType.FLOAT, MIRType.BOOL])
        temp = Temp(union, 42)

        # Check that union type is properly stored
        assert temp.union_type == union
        assert temp.type == MIRType.UNKNOWN  # Base type is unknown for unions
        assert temp.id == 42

    def test_constant_type_tracking(self) -> None:
        """Test that constants properly track their types."""
        int_const = Constant(42, MIRType.INT)
        assert int_const.type == MIRType.INT
        assert int_const.union_type is None

        str_const = Constant("hello", MIRType.STRING)
        assert str_const.type == MIRType.STRING
        assert str_const.union_type is None

    def test_union_type_equality(self) -> None:
        """Test union type equality checking."""
        union1 = MIRUnionType([MIRType.INT, MIRType.STRING])
        union2 = MIRUnionType([MIRType.STRING, MIRType.INT])  # Different order
        union3 = MIRUnionType([MIRType.INT, MIRType.FLOAT])

        assert union1 == union2  # Order doesn't matter
        assert union1 != union3  # Different types

    def test_union_type_contains(self) -> None:
        """Test union type contains method."""
        union = MIRUnionType([MIRType.INT, MIRType.STRING, MIRType.BOOL])
        assert union.contains(MIRType.INT)
        assert union.contains(MIRType.STRING)
        assert union.contains(MIRType.BOOL)
        assert not union.contains(MIRType.FLOAT)
        assert not union.contains(MIRType.EMPTY)
