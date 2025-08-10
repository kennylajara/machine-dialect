"""Tests for the interpreter objects module."""

import pytest

from machine_dialect.interpreter.objects import (
    URL,
    Boolean,
    Empty,
    Float,
    Integer,
    Object,
    ObjectType,
    String,
)


class TestObjectType:
    """Test the ObjectType enum."""

    def test_all_types_present(self) -> None:
        """Test that all expected object types are present."""
        expected_types = {
            "BOOLEAN",
            "EMPTY",
            "FLOAT",
            "INTEGER",
            "STRING",
            "URL",
        }
        actual_types = {member.name for member in ObjectType}
        assert actual_types == expected_types

    def test_enum_values_unique(self) -> None:
        """Test that enum values are unique."""
        values = [member.value for member in ObjectType]
        assert len(values) == len(set(values))


class TestBoolean:
    """Test the Boolean object type."""

    def test_singleton_true(self) -> None:
        """Test that Boolean(True) always returns the same instance."""
        bool1 = Boolean(True)
        bool2 = Boolean(True)
        assert bool1 is bool2

    def test_singleton_false(self) -> None:
        """Test that Boolean(False) always returns the same instance."""
        bool1 = Boolean(False)
        bool2 = Boolean(False)
        assert bool1 is bool2

    def test_different_values_different_instances(self) -> None:
        """Test that True and False are different instances."""
        true_bool = Boolean(True)
        false_bool = Boolean(False)
        assert true_bool is not false_bool

    def test_type_property(self) -> None:
        """Test that type property returns BOOLEAN."""
        true_bool = Boolean(True)
        false_bool = Boolean(False)
        assert true_bool.type == ObjectType.BOOLEAN
        assert false_bool.type == ObjectType.BOOLEAN

    def test_inspect_true(self) -> None:
        """Test that inspect() returns 'Yes' for True."""
        bool_obj = Boolean(True)
        assert bool_obj.inspect() == "Yes"

    def test_inspect_false(self) -> None:
        """Test that inspect() returns 'No' for False."""
        bool_obj = Boolean(False)
        assert bool_obj.inspect() == "No"

    def test_value_preserved(self) -> None:
        """Test that the boolean value is preserved internally."""
        true_bool = Boolean(True)
        false_bool = Boolean(False)
        # Access private attribute to verify value is stored correctly
        assert true_bool._value is True
        assert false_bool._value is False


class TestEmpty:
    """Test the Empty object type."""

    def test_singleton(self) -> None:
        """Test that Empty() always returns the same instance."""
        empty1 = Empty()
        empty2 = Empty()
        assert empty1 is empty2

    def test_multiple_creations(self) -> None:
        """Test that multiple Empty creations return the same instance."""
        empties = [Empty() for _ in range(10)]
        # All should be the same instance
        assert all(e is empties[0] for e in empties)

    def test_type_property(self) -> None:
        """Test that type property returns EMPTY."""
        empty = Empty()
        assert empty.type == ObjectType.EMPTY

    def test_inspect(self) -> None:
        """Test that inspect() returns 'Empty'."""
        empty = Empty()
        assert empty.inspect() == "Empty"


class TestInteger:
    """Test the Integer object type."""

    def test_type_property(self) -> None:
        """Test that type property returns INTEGER."""
        int_obj = Integer(42)
        assert int_obj.type == ObjectType.INTEGER

    def test_inspect_positive(self) -> None:
        """Test inspect() for positive integers."""
        int_obj = Integer(42)
        assert int_obj.inspect() == "42"

    def test_inspect_negative(self) -> None:
        """Test inspect() for negative integers."""
        int_obj = Integer(-42)
        assert int_obj.inspect() == "-42"

    def test_inspect_zero(self) -> None:
        """Test inspect() for zero."""
        int_obj = Integer(0)
        assert int_obj.inspect() == "0"

    def test_different_values_different_instances(self) -> None:
        """Test that different values create different instances."""
        int1 = Integer(42)
        int2 = Integer(42)
        int3 = Integer(43)
        # Different instances even for same value (no singleton)
        assert int1 is not int2
        assert int1 is not int3

    def test_large_numbers(self) -> None:
        """Test handling of large integers."""
        large = Integer(9876543210)
        assert large.inspect() == "9876543210"

    def test_value_preserved(self) -> None:
        """Test that the integer value is preserved internally."""
        int_obj = Integer(42)
        assert int_obj._value == 42


class TestFloat:
    """Test the Float object type."""

    def test_type_property(self) -> None:
        """Test that type property returns FLOAT."""
        float_obj = Float(3.14)
        assert float_obj.type == ObjectType.FLOAT

    def test_inspect_positive(self) -> None:
        """Test inspect() for positive floats."""
        float_obj = Float(3.14)
        assert float_obj.inspect() == "3.14"

    def test_inspect_negative(self) -> None:
        """Test inspect() for negative floats."""
        float_obj = Float(-3.14)
        assert float_obj.inspect() == "-3.14"

    def test_inspect_zero(self) -> None:
        """Test inspect() for zero."""
        float_obj = Float(0.0)
        assert float_obj.inspect() == "0.0"

    def test_different_values_different_instances(self) -> None:
        """Test that different values create different instances."""
        float1 = Float(3.14)
        float2 = Float(3.14)
        float3 = Float(2.71)
        # Different instances even for same value (no singleton)
        assert float1 is not float2
        assert float1 is not float3

    def test_scientific_notation(self) -> None:
        """Test handling of scientific notation."""
        float_obj = Float(1.23e-4)
        # Python's str() handles the conversion
        assert float_obj.inspect() == "0.000123"

    def test_value_preserved(self) -> None:
        """Test that the float value is preserved internally."""
        float_obj = Float(3.14)
        assert float_obj._value == 3.14


class TestString:
    """Test the String object type."""

    def test_type_property(self) -> None:
        """Test that type property returns STRING."""
        str_obj = String("hello")
        assert str_obj.type == ObjectType.STRING

    def test_inspect_regular_string(self) -> None:
        """Test inspect() for regular strings."""
        str_obj = String("hello world")
        assert str_obj.inspect() == "hello world"

    def test_inspect_empty_string(self) -> None:
        """Test inspect() for empty string."""
        str_obj = String("")
        assert str_obj.inspect() == ""

    def test_inspect_with_quotes(self) -> None:
        """Test inspect() for strings containing quotes."""
        str_obj = String('"Hello, World!"')
        assert str_obj.inspect() == '"Hello, World!"'

    def test_inspect_special_characters(self) -> None:
        """Test inspect() for strings with special characters."""
        str_obj = String("line1\nline2\ttab")
        assert str_obj.inspect() == "line1\nline2\ttab"

    def test_different_values_different_instances(self) -> None:
        """Test that different values create different instances."""
        str1 = String("hello")
        str2 = String("hello")
        str3 = String("world")
        # Different instances even for same value (no singleton)
        assert str1 is not str2
        assert str1 is not str3

    def test_unicode_support(self) -> None:
        """Test handling of Unicode characters."""
        str_obj = String("Hello 世界 🌍")
        assert str_obj.inspect() == "Hello 世界 🌍"

    def test_value_preserved(self) -> None:
        """Test that the string value is preserved internally."""
        str_obj = String("test")
        assert str_obj._value == "test"


class TestURL:
    """Test the URL object type."""

    def test_inheritance_from_string(self) -> None:
        """Test that URL inherits from String."""
        url_obj = URL("https://example.com")
        assert isinstance(url_obj, String)
        assert isinstance(url_obj, Object)

    def test_type_property(self) -> None:
        """Test that type property returns URL."""
        url_obj = URL("https://example.com")
        assert url_obj.type == ObjectType.URL

    def test_inspect_http_url(self) -> None:
        """Test inspect() for HTTP URLs."""
        url_obj = URL('"https://example.com"')
        assert url_obj.inspect() == '"https://example.com"'

    def test_inspect_complex_url(self) -> None:
        """Test inspect() for complex URLs."""
        url_obj = URL('"https://api.example.com/v1/users?id=123&active=true#profile"')
        assert url_obj.inspect() == '"https://api.example.com/v1/users?id=123&active=true#profile"'

    def test_inspect_ftp_url(self) -> None:
        """Test inspect() for FTP URLs."""
        url_obj = URL('"ftp://files.example.com/data.zip"')
        assert url_obj.inspect() == '"ftp://files.example.com/data.zip"'

    def test_inspect_mailto_url(self) -> None:
        """Test inspect() for mailto URLs."""
        url_obj = URL('"mailto:user@example.com"')
        assert url_obj.inspect() == '"mailto:user@example.com"'

    def test_different_values_different_instances(self) -> None:
        """Test that different values create different instances."""
        url1 = URL("https://example.com")
        url2 = URL("https://example.com")
        url3 = URL("https://other.com")
        # Different instances even for same value (no singleton)
        assert url1 is not url2
        assert url1 is not url3

    def test_value_preserved(self) -> None:
        """Test that the URL value is preserved internally."""
        url_obj = URL("https://example.com")
        assert url_obj._value == "https://example.com"

    def test_string_methods_available(self) -> None:
        """Test that String methods are available on URL."""
        url_obj = URL("https://example.com")
        # Should have access to String's inspect method
        assert hasattr(url_obj, "inspect")
        assert hasattr(url_obj, "type")


class TestObjectAbstraction:
    """Test the Object abstract base class."""

    def test_cannot_instantiate_object(self) -> None:
        """Test that Object cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Object()  # type: ignore

    def test_all_concrete_classes_implement_interface(self) -> None:
        """Test that all concrete classes implement the Object interface."""
        concrete_classes = [Boolean, Empty, Float, Integer, String, URL]

        for cls in concrete_classes:
            # Create an instance (with appropriate arguments)
            if cls == Boolean:
                obj = cls(True)
            elif cls == Empty:
                obj = cls()
            elif cls in (Float, Integer, String, URL):
                obj = cls(42) if cls in (Float, Integer) else cls("test")

            # Check that required methods/properties are present
            assert hasattr(obj, "type")
            assert hasattr(obj, "inspect")
            assert isinstance(obj.type, ObjectType)
            assert isinstance(obj.inspect(), str)
