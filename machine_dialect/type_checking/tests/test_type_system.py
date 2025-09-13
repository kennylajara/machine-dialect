"""Tests for the Machine Dialect™ compile-time type system."""

from machine_dialect.ast import (
    EmptyLiteral,
    FloatLiteral,
    StringLiteral,
    URLLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.type_checking import (
    MDType,
    TypeSpec,
    check_type_compatibility,
    get_type_from_name,
    get_type_from_value,
    is_assignable_to,
)


class TestMDType:
    """Test the MDType enumeration and type name mappings."""

    def test_type_from_name(self) -> None:
        """Test converting type names to MDType enum."""
        assert get_type_from_name("Text") == MDType.TEXT
        assert get_type_from_name("Whole Number") == MDType.WHOLE_NUMBER
        assert get_type_from_name("Float") == MDType.FLOAT
        assert get_type_from_name("Number") == MDType.NUMBER
        assert get_type_from_name("Yes/No") == MDType.YES_NO
        assert get_type_from_name("URL") == MDType.URL
        assert get_type_from_name("Empty") == MDType.EMPTY
        assert get_type_from_name("Any") == MDType.ANY

    def test_type_from_invalid_name(self) -> None:
        """Test that invalid type names return None."""
        assert get_type_from_name("Invalid") is None
        assert get_type_from_name("") is None
        assert get_type_from_name("text") is None  # Case sensitive


class TestTypeSpec:
    """Test TypeSpec class for union type handling."""

    def test_single_type_spec(self) -> None:
        """Test TypeSpec with a single type."""
        spec = TypeSpec(["Whole Number"])
        assert spec.allows_type(MDType.WHOLE_NUMBER)
        assert not spec.allows_type(MDType.TEXT)
        assert str(spec) == "Whole Number"

    def test_union_type_spec(self) -> None:
        """Test TypeSpec with union types."""
        spec = TypeSpec(["Whole Number", "Text", "Yes/No"])
        assert spec.allows_type(MDType.WHOLE_NUMBER)
        assert spec.allows_type(MDType.TEXT)
        assert spec.allows_type(MDType.YES_NO)
        assert not spec.allows_type(MDType.FLOAT)
        assert str(spec) == "Whole Number or Text or Yes/No"

    def test_number_type_allows_subtypes(self) -> None:
        """Test that Number type allows Whole Number and Float."""
        spec = TypeSpec(["Number"])
        assert spec.allows_type(MDType.NUMBER)
        assert spec.allows_type(MDType.WHOLE_NUMBER)
        assert spec.allows_type(MDType.FLOAT)
        assert not spec.allows_type(MDType.TEXT)

    def test_any_type_allows_everything(self) -> None:
        """Test that Any type allows all types."""
        spec = TypeSpec(["Any"])
        assert spec.allows_type(MDType.TEXT)
        assert spec.allows_type(MDType.WHOLE_NUMBER)
        assert spec.allows_type(MDType.FLOAT)
        assert spec.allows_type(MDType.YES_NO)
        assert spec.allows_type(MDType.EMPTY)


class TestGetTypeFromValue:
    """Test determining types from AST literal values."""

    def test_whole_number_literal(self) -> None:
        """Test type detection for WholeNumberLiteral."""
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 1)
        literal = WholeNumberLiteral(token, 42)
        assert get_type_from_value(literal) == MDType.WHOLE_NUMBER

    def test_float_literal(self) -> None:
        """Test type detection for FloatLiteral."""
        token = Token(TokenType.LIT_FLOAT, "3.14", 1, 1)
        literal = FloatLiteral(token, 3.14)
        assert get_type_from_value(literal) == MDType.FLOAT

    def test_string_literal(self) -> None:
        """Test type detection for StringLiteral."""
        token = Token(TokenType.LIT_TEXT, "hello", 1, 1)
        literal = StringLiteral(token, "hello")
        assert get_type_from_value(literal) == MDType.TEXT

    def test_url_literal(self) -> None:
        """Test type detection for URLLiteral."""
        token = Token(TokenType.LIT_URL, "https://example.com", 1, 1)
        literal = URLLiteral(token, "https://example.com")
        assert get_type_from_value(literal) == MDType.URL

    def test_yes_no_literal(self) -> None:
        """Test type detection for YesNoLiteral."""
        token = Token(TokenType.LIT_YES, "yes", 1, 1)
        literal = YesNoLiteral(token, True)
        assert get_type_from_value(literal) == MDType.YES_NO

    def test_empty_literal(self) -> None:
        """Test type detection for EmptyLiteral."""
        token = Token(TokenType.KW_EMPTY, "empty", 1, 1)
        literal = EmptyLiteral(token)
        assert get_type_from_value(literal) == MDType.EMPTY

    def test_string_that_looks_like_url(self) -> None:
        """Test that strings starting with http are detected as URLs."""
        token = Token(TokenType.LIT_TEXT, "https://example.com", 1, 1)
        literal = StringLiteral(token, "https://example.com")
        assert get_type_from_value(literal) == MDType.URL

    def test_python_types(self) -> None:
        """Test type detection for raw Python values."""
        assert get_type_from_value(42) == MDType.WHOLE_NUMBER
        assert get_type_from_value(3.14) == MDType.FLOAT
        assert get_type_from_value("hello") == MDType.TEXT
        assert get_type_from_value(True) == MDType.YES_NO
        assert get_type_from_value(None) == MDType.EMPTY


class TestTypeAssignability:
    """Test type assignability rules."""

    def test_exact_match_allowed(self) -> None:
        """Test that exact type matches are allowed."""
        assert is_assignable_to(MDType.WHOLE_NUMBER, MDType.WHOLE_NUMBER)
        assert is_assignable_to(MDType.TEXT, MDType.TEXT)
        assert is_assignable_to(MDType.FLOAT, MDType.FLOAT)

    def test_any_accepts_all(self) -> None:
        """Test that Any type accepts all values."""
        assert is_assignable_to(MDType.TEXT, MDType.ANY)
        assert is_assignable_to(MDType.WHOLE_NUMBER, MDType.ANY)
        assert is_assignable_to(MDType.EMPTY, MDType.ANY)

    def test_number_accepts_numeric(self) -> None:
        """Test that Number accepts Whole Number and Float."""
        assert is_assignable_to(MDType.WHOLE_NUMBER, MDType.NUMBER)
        assert is_assignable_to(MDType.FLOAT, MDType.NUMBER)
        assert not is_assignable_to(MDType.TEXT, MDType.NUMBER)

    def test_empty_assignable_to_any_type(self) -> None:
        """Test that Empty can be assigned to any type."""
        assert is_assignable_to(MDType.EMPTY, MDType.TEXT)
        assert is_assignable_to(MDType.EMPTY, MDType.WHOLE_NUMBER)
        assert is_assignable_to(MDType.EMPTY, MDType.YES_NO)

    def test_no_implicit_conversions(self) -> None:
        """Test that no implicit conversions are allowed (per spec)."""
        assert not is_assignable_to(MDType.WHOLE_NUMBER, MDType.TEXT)
        assert not is_assignable_to(MDType.TEXT, MDType.WHOLE_NUMBER)
        assert not is_assignable_to(MDType.WHOLE_NUMBER, MDType.YES_NO)
        assert not is_assignable_to(MDType.FLOAT, MDType.WHOLE_NUMBER)


class TestTypeCompatibility:
    """Test type compatibility checking with TypeSpec."""

    def test_compatible_single_type(self) -> None:
        """Test compatibility with single type spec."""
        spec = TypeSpec(["Whole Number"])
        is_compatible, error = check_type_compatibility(MDType.WHOLE_NUMBER, spec)
        assert is_compatible
        assert error is None

    def test_incompatible_single_type(self) -> None:
        """Test incompatibility with single type spec."""
        spec = TypeSpec(["Whole Number"])
        is_compatible, error = check_type_compatibility(MDType.TEXT, spec)
        assert not is_compatible
        assert error == "Cannot assign Text value to variable of type Whole Number"

    def test_compatible_union_type(self) -> None:
        """Test compatibility with union type spec."""
        spec = TypeSpec(["Whole Number", "Text"])

        # Both types should be compatible
        is_compatible, error = check_type_compatibility(MDType.WHOLE_NUMBER, spec)
        assert is_compatible
        assert error is None

        is_compatible, error = check_type_compatibility(MDType.TEXT, spec)
        assert is_compatible
        assert error is None

    def test_incompatible_union_type(self) -> None:
        """Test incompatibility with union type spec."""
        spec = TypeSpec(["Whole Number", "Text"])
        is_compatible, error = check_type_compatibility(MDType.YES_NO, spec)
        assert not is_compatible
        assert error == "Cannot assign Yes/No value to variable of type Whole Number or Text"

    def test_number_type_compatibility(self) -> None:
        """Test Number type accepts both integers and floats."""
        spec = TypeSpec(["Number"])

        # Whole Number should be compatible
        is_compatible, error = check_type_compatibility(MDType.WHOLE_NUMBER, spec)
        assert is_compatible
        assert error is None

        # Float should be compatible
        is_compatible, error = check_type_compatibility(MDType.FLOAT, spec)
        assert is_compatible
        assert error is None

        # Text should not be compatible
        is_compatible, error = check_type_compatibility(MDType.TEXT, spec)
        assert not is_compatible

    def test_empty_compatible_with_all(self) -> None:
        """Test that Empty is compatible with all types."""
        for type_name in ["Text", "Whole Number", "Float", "Yes/No", "URL"]:
            spec = TypeSpec([type_name])
            is_compatible, error = check_type_compatibility(MDType.EMPTY, spec)
            assert is_compatible
            assert error is None
