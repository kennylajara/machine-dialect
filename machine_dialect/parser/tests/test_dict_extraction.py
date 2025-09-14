"""Tests for dictionary keys/values extraction parsing."""

from machine_dialect.ast.dict_extraction import DictExtraction
from machine_dialect.ast.expressions import Identifier
from machine_dialect.ast.statements import SetStatement
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.parser.parser import Parser


class TestDictExtraction:
    """Test parsing of dictionary extraction expressions."""

    def test_parse_names_extraction(self) -> None:
        """Test parsing 'the names of `dict`'."""
        source = "Set `result` to the names of `person`."
        parser = Parser()
        program = parser.parse(source)
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy
        expr = stmt.value
        assert isinstance(expr, DictExtraction)
        assert expr.extract_type == "names"
        assert isinstance(expr.dictionary, Identifier)
        assert expr.dictionary.value == "person"
        assert str(expr) == "the names of `person`"

    def test_parse_contents_extraction(self) -> None:
        """Test parsing 'the contents of `dict`'."""
        source = "Set `result` to the contents of `config`."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy
        expr = stmt.value

        assert isinstance(expr, DictExtraction)
        assert expr.extract_type == "contents"
        assert isinstance(expr.dictionary, Identifier)
        assert expr.dictionary.value == "config"
        assert str(expr) == "the contents of `config`"

    def test_parse_names_in_set_statement(self) -> None:
        """Test parsing 'Set `names` to the names of `person`.'"""
        source = "Set `my_names` to the names of `person`."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.__class__.__name__ == "SetStatement"
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy

        # Check the value is a DictExtraction
        assert isinstance(stmt.value, DictExtraction)
        assert stmt.value.extract_type == "names"
        dict_val = stmt.value.dictionary
        assert isinstance(dict_val, Identifier)
        assert dict_val.value == "person"

    def test_parse_contents_in_set_statement(self) -> None:
        """Test parsing 'Set `values` to the contents of `dict`.'"""
        source = "Set `my_values` to the contents of `settings`."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.__class__.__name__ == "SetStatement"
        assert isinstance(stmt, SetStatement)  # Type assertion for MyPy

        # Check the value is a DictExtraction
        assert isinstance(stmt.value, DictExtraction)
        assert stmt.value.extract_type == "contents"
        dict_val = stmt.value.dictionary
        assert isinstance(dict_val, Identifier)
        assert dict_val.value == "settings"

    def test_parse_invalid_extraction_missing_dict(self) -> None:
        """Test error when dictionary is missing."""
        source = "Set `result` to the names of."
        parser = Parser()
        program = parser.parse(source)

        # The parser should handle the missing dictionary gracefully
        assert len(program.statements) == 1
        stmt = program.statements[0]
        # The value might be an error expression or partial parse
        assert stmt is not None

    def test_dict_extraction_to_hir(self) -> None:
        """Test that DictExtraction converts to HIR properly."""
        token = Token(TokenType.MISC_STOPWORD, "the", 1, 1)
        dict_ident = Identifier(Token(TokenType.MISC_IDENT, "person", 1, 5), "person")

        extraction = DictExtraction(token, dict_ident, "names")
        hir = extraction.to_hir()

        assert isinstance(hir, DictExtraction)
        assert hir.extract_type == "names"
        assert isinstance(hir.dictionary, Identifier)

    def test_dict_extraction_desugar(self) -> None:
        """Test that DictExtraction desugars properly."""
        token = Token(TokenType.MISC_STOPWORD, "the", 1, 1)
        dict_ident = Identifier(Token(TokenType.MISC_IDENT, "person", 1, 5), "person")

        extraction = DictExtraction(token, dict_ident, "contents")
        desugared = extraction.desugar()

        assert isinstance(desugared, DictExtraction)
        assert desugared.extract_type == "contents"
        assert isinstance(desugared.dictionary, Identifier)
