from machine_dialect.ast import (
    BlockStatement,
    DefineStatement,
    Identifier,
    SetStatement,
    StringLiteral,
    WholeNumberLiteral,
)
from machine_dialect.lexer import Token, TokenType


class TestDefineStatement:
    """Test DefineStatement AST node."""

    def test_simple_definition(self) -> None:
        """Test basic variable definition without default."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "count", 1, 8), "count")
        type_spec = ["Whole Number"]

        stmt = DefineStatement(token, name, type_spec)

        assert str(stmt) == "Define `count` as Whole Number."
        assert stmt.initial_value is None
        assert stmt.type_spec == ["Whole Number"]

    def test_definition_with_default(self) -> None:
        """Test variable definition with default value."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "message", 1, 8), "message")
        type_spec = ["Text"]
        default = StringLiteral(Token(TokenType.LIT_TEXT, '"Hello"', 1, 30), "Hello")

        stmt = DefineStatement(token, name, type_spec, default)

        assert str(stmt) == 'Define `message` as Text (default: _"Hello"_).'
        assert stmt.initial_value == default

    def test_union_type_definition(self) -> None:
        """Test definition with union types."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "value", 1, 8), "value")
        type_spec = ["Whole Number", "Text", "Yes/No"]

        stmt = DefineStatement(token, name, type_spec)

        assert str(stmt) == "Define `value` as Whole Number or Text or Yes/No."

    def test_desugar_without_default(self) -> None:
        """Test desugaring when no default value."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 8), "x")
        type_spec = ["Whole Number"]

        stmt = DefineStatement(token, name, type_spec)
        desugared = stmt.desugar()

        # Should return self when no default
        assert desugared is stmt

    def test_desugar_with_default(self) -> None:
        """Test desugaring with default value."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "count", 1, 8), "count")
        type_spec = ["Whole Number"]
        default = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "0", 1, 30), 0)

        stmt = DefineStatement(token, name, type_spec, default)
        desugared = stmt.desugar()

        # Should return a BlockStatement with Define and Set
        assert isinstance(desugared, BlockStatement)
        assert len(desugared.statements) == 2

        # First statement should be Define without default
        define_stmt = desugared.statements[0]
        assert isinstance(define_stmt, DefineStatement)
        assert define_stmt.initial_value is None
        assert define_stmt.name.value == "count"
        assert define_stmt.type_spec == ["Whole Number"]

        # Second statement should be Set
        set_stmt = desugared.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert set_stmt.name is not None
        assert set_stmt.name.value == "count"
        assert set_stmt.value == default

    def test_multiple_types_string_representation(self) -> None:
        """Test string representation with multiple types."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "data", 1, 8), "data")
        type_spec = ["Number", "Text", "Yes/No", "Empty"]

        stmt = DefineStatement(token, name, type_spec)

        assert str(stmt) == "Define `data` as Number or Text or Yes/No or Empty."

    def test_all_type_names(self) -> None:
        """Test that all supported type names work correctly."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)

        type_names = [
            "Text",
            "Whole Number",
            "Float",
            "Number",
            "Yes/No",
            "URL",
            "Date",
            "DateTime",
            "Time",
            "List",
            "Empty",
        ]

        for type_name in type_names:
            name = Identifier(Token(TokenType.MISC_IDENT, "var", 1, 8), "var")
            stmt = DefineStatement(token, name, [type_name])
            assert str(stmt) == f"Define `var` as {type_name}."

    def test_desugar_preserves_name_reference(self) -> None:
        """Test that desugaring preserves the same name reference."""
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "test", 1, 8), "test")
        type_spec = ["Text"]
        default = StringLiteral(Token(TokenType.LIT_TEXT, '"value"', 1, 30), "value")

        stmt = DefineStatement(token, name, type_spec, default)
        desugared = stmt.desugar()

        assert isinstance(desugared, BlockStatement)
        define_stmt = desugared.statements[0]
        set_stmt = desugared.statements[1]

        # Both statements should reference the same variable name
        assert isinstance(define_stmt, DefineStatement)
        assert isinstance(set_stmt, SetStatement)
        assert isinstance(define_stmt.name, Identifier)
        assert isinstance(set_stmt.name, Identifier)
        assert define_stmt.name.value == "test"
        assert set_stmt.name.value == "test"
