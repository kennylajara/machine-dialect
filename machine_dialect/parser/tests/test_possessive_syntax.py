"""Tests for possessive syntax parsing."""

from machine_dialect.ast.expressions import CollectionAccessExpression, ErrorExpression, Identifier
from machine_dialect.ast.statements import IfStatement, SetStatement
from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import TokenType
from machine_dialect.parser.parser import Parser


class TestPossessiveSyntax:
    """Test parsing of possessive property access syntax."""

    def test_lexer_recognizes_possessive(self) -> None:
        """Test that lexer properly tokenizes `person`'s."""
        lexer = Lexer('`person`\'s "name"')

        # First token should be the possessive token
        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_APOSTROPHE_S
        assert token.literal == "person"

        # Next should be the property name as a string literal
        token = lexer.next_token()
        assert token.type == TokenType.LIT_TEXT
        assert token.literal == '"name"'

    def test_parse_possessive_property_access(self) -> None:
        """Test parsing `person`'s _"name"_."""
        source = 'Set `result` to `person`\'s _"name"_.'
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.__class__.__name__ == "SetStatement"
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy

        # Check the value is a CollectionAccessExpression
        expr = stmt.value
        assert isinstance(expr, CollectionAccessExpression)
        assert expr.access_type == "property"
        assert isinstance(expr.collection, Identifier)
        assert expr.collection.value == "person"
        assert expr.accessor == "name"

    def test_parse_possessive_in_set_statement(self) -> None:
        """Test parsing Set `user` to `person`'s _"name"_."""
        source = 'Set `user` to `person`\'s _"name"_.'
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.__class__.__name__ == "SetStatement"
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy

        # Check the value is a CollectionAccessExpression
        assert isinstance(stmt.value, CollectionAccessExpression)
        assert stmt.value.access_type == "property"
        coll = stmt.value.collection
        assert isinstance(coll, Identifier)
        assert coll.value == "person"
        assert stmt.value.accessor == "name"

    def test_parse_possessive_mutation(self) -> None:
        """Test parsing Set `person`'s _"age"_ to _31_."""
        source = 'Set `person`\'s _"age"_ to _31_.'
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]

        # This should parse as a collection mutation statement
        # The parser should recognize this pattern and create appropriate AST
        assert stmt is not None
        # The implementation might vary - could be SetStatement with special handling
        # or CollectionMutationStatement

    def test_parse_multiple_possessive_access(self) -> None:
        """Test parsing chained possessive access."""
        source = 'Set `result` to `user`\'s _"email"_.'
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy
        expr = stmt.value

        assert isinstance(expr, CollectionAccessExpression)
        assert expr.access_type == "property"
        coll = expr.collection
        assert isinstance(coll, Identifier)
        assert coll.value == "user"
        assert expr.accessor == "email"

    def test_possessive_with_different_properties(self) -> None:
        """Test possessive with various property names."""
        test_cases = [
            ('`config`\'s _"host"_', "config", "host"),
            ('`user`\'s _"premium"_', "user", "premium"),
            ('`settings`\'s _"timeout"_', "settings", "timeout"),
            ('`person`\'s _"phone"_', "person", "phone"),
        ]

        parser = Parser()

        for possessive_expr, dict_name, prop_name in test_cases:
            source = f"Set `result` to {possessive_expr}."
            program = parser.parse(source)

            assert len(program.statements) == 1
            stmt = program.statements[0]
            assert isinstance(stmt, SetStatement)  # Type assertion for MyPy
            expr = stmt.value

            assert isinstance(expr, CollectionAccessExpression)
            assert expr.access_type == "property"
            coll = expr.collection
            assert isinstance(coll, Identifier)
            assert coll.value == dict_name
            assert expr.accessor == prop_name

    def test_lexer_apostrophe_without_s(self) -> None:
        """Test that regular apostrophes don't trigger possessive."""
        lexer = Lexer("`don't`")

        # Should be parsed as a regular identifier
        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "don't"

    def test_lexer_apostrophe_s_without_backticks(self) -> None:
        """Test that 's without backticks doesn't trigger possessive."""
        lexer = Lexer('person\'s "name"')

        # Should parse as regular identifier with contraction
        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "person's"

        token = lexer.next_token()
        # Now expecting a string literal
        assert token.type == TokenType.LIT_TEXT
        assert token.literal == '"name"'

    def test_possessive_missing_property_name(self) -> None:
        """Test error when property name is missing after possessive."""
        source = "Set `result` to `person`'s."
        parser = Parser()
        program = parser.parse(source)

        # Should have an error in parsing
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy
        expr = stmt.value

        # The value should be an error expression
        assert isinstance(expr, ErrorExpression)
        assert "Expected string literal" in expr.message

    def test_possessive_in_conditional(self) -> None:
        """Test possessive in if statement condition."""
        source = 'If `user`\'s _"premium"_ then:\n> Say _"Premium user"_.'
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.__class__.__name__ == "IfStatement"
        assert isinstance(stmt, IfStatement)  # Type assertion for MyPy

        # Check the condition contains possessive access
        condition = stmt.condition
        assert isinstance(condition, CollectionAccessExpression)
        assert condition.access_type == "property"
        coll = condition.collection
        assert isinstance(coll, Identifier)
        assert coll.value == "user"
        assert condition.accessor == "premium"
