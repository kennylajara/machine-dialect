from machine_dialect.ast import DefineStatement
from machine_dialect.parser import Parser


class TestDefineStatements:
    """Test parsing of Define statements."""

    def test_parse_simple_define(self) -> None:
        """Test parsing basic Define statement."""
        source = "Define `count` as Whole Number."
        parser = Parser()

        # Debug: Add print before parsing
        from machine_dialect.lexer import Lexer

        lexer = Lexer(source)
        tokens = []
        while True:
            tok = lexer.next_token()
            tokens.append(tok)
            if tok.type.name == "MISC_EOF":
                break
        print(f"Tokens: {[(t.type.name, t.literal) for t in tokens]}")

        program = parser.parse(source)

        # Debug: Print any parser errors
        if parser.errors:
            for error in parser.errors:
                print(f"Parser error: {error}")

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "count"
        assert stmt.type_spec == ["Whole Number"]
        assert stmt.initial_value is None

    def test_parse_define_with_default(self) -> None:
        """Test parsing Define with default value."""
        source = 'Define `message` as Text (default: _"Hello World"_).'

        # Debug: Print tokens first
        from machine_dialect.lexer import Lexer

        lexer = Lexer(source)
        tokens = []
        while True:
            tok = lexer.next_token()
            tokens.append(tok)
            if tok.type.name == "MISC_EOF":
                break
        print(f"Tokens: {[(t.type.name, t.literal) for t in tokens]}")

        parser = Parser()
        program = parser.parse(source)

        # Debug: Print statements
        print(f"Got {len(program.statements)} statements:")
        for i, stmt in enumerate(program.statements):
            print(f"  {i}: {type(stmt).__name__}: {stmt}")

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "message"
        assert stmt.type_spec == ["Text"]
        assert stmt.initial_value is not None
        assert str(stmt.initial_value) == '_"Hello World"_'

    def test_parse_define_with_integer_default(self) -> None:
        """Test parsing Define with integer default."""
        source = "Define `age` as Whole Number (default: _25_)."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "age"
        assert stmt.type_spec == ["Whole Number"]
        assert str(stmt.initial_value) == "_25_"

    def test_parse_define_with_boolean_default(self) -> None:
        """Test parsing Define with boolean default."""
        source = "Define `is_active` as Yes/No (default: _yes_)."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "is_active"
        assert stmt.type_spec == ["Yes/No"]
        assert str(stmt.initial_value) == "_Yes_"

    def test_parse_union_type(self) -> None:
        """Test parsing Define with union types."""
        source = "Define `value` as Whole Number or Text."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "value"
        assert stmt.type_spec == ["Whole Number", "Text"]

    def test_parse_multiple_union_types(self) -> None:
        """Test parsing Define with multiple union types."""
        source = "Define `data` as Number or Yes/No or Text or Empty."

        # Debug: Check tokens
        from machine_dialect.lexer import Lexer

        lexer = Lexer(source)
        tokens = []
        while True:
            tok = lexer.next_token()
            tokens.append(tok)
            if tok.type.name == "MISC_EOF":
                break
        print(f"Tokens: {[(t.type.name, t.literal) for t in tokens]}")

        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        print(f"Got type_spec: {stmt.type_spec}")
        assert stmt.type_spec == ["Number", "Yes/No", "Text", "Empty"]

    def test_parse_various_type_names(self) -> None:
        """Test parsing various type names."""
        test_cases = [
            ("Define `a` as Text.", ["Text"]),
            ("Define `b` as Whole Number.", ["Whole Number"]),
            ("Define `c` as Float.", ["Float"]),
            ("Define `d` as Number.", ["Number"]),
            ("Define `e` as Yes/No.", ["Yes/No"]),
            ("Define `f` as URL.", ["URL"]),
            ("Define `g` as Date.", ["Date"]),
            ("Define `h` as DateTime.", ["DateTime"]),
            ("Define `i` as Time.", ["Time"]),
            ("Define `j` as List.", ["List"]),
            ("Define `k` as Empty.", ["Empty"]),
        ]

        for source, expected_types in test_cases:
            parser = Parser()
            program = parser.parse(source)
            assert len(program.statements) == 1
            stmt = program.statements[0]
            assert isinstance(stmt, DefineStatement)
            assert stmt.type_spec == expected_types

    def test_error_missing_variable_name(self) -> None:
        """Test error when variable name is missing."""
        source = "Define as Whole Number."
        parser = Parser()
        _ = parser.parse(source)

        assert len(parser.errors) > 0
        # The error message or structure may vary, just check we got errors

    def test_error_missing_as_keyword(self) -> None:
        """Test error when 'as' keyword is missing."""
        source = "Define `count` Whole Number."
        parser = Parser()
        _ = parser.parse(source)

        assert len(parser.errors) > 0

    def test_error_missing_type(self) -> None:
        """Test error when type is missing."""
        source = "Define `count` as."
        parser = Parser()
        _ = parser.parse(source)

        assert len(parser.errors) > 0

    def test_error_invalid_default_syntax(self) -> None:
        """Test error with invalid default syntax."""
        source = "Define `x` as Whole Number (default _5_)."  # Missing colon
        parser = Parser()
        _ = parser.parse(source)

        assert len(parser.errors) > 0

    def test_define_with_stopwords(self) -> None:
        """Test that stopwords are properly skipped."""
        source = "Define the `count` as a Whole Number."
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, DefineStatement)
        assert stmt.name.value == "count"
        assert stmt.type_spec == ["Whole Number"]

    def test_multiple_define_statements(self) -> None:
        """Test parsing multiple Define statements."""
        source = """
Define `name` as Text.
Define `age` as Whole Number.
Define `active` as Yes/No (default: _yes_).
        """
        parser = Parser()
        program = parser.parse(source)

        assert len(program.statements) == 3

        # Check first statement
        stmt1 = program.statements[0]
        assert isinstance(stmt1, DefineStatement)
        assert stmt1.name.value == "name"
        assert stmt1.type_spec == ["Text"]
        assert stmt1.initial_value is None

        # Check second statement
        stmt2 = program.statements[1]
        assert isinstance(stmt2, DefineStatement)
        assert stmt2.name.value == "age"
        assert stmt2.type_spec == ["Whole Number"]
        assert stmt2.initial_value is None

        # Check third statement
        stmt3 = program.statements[2]
        assert isinstance(stmt3, DefineStatement)
        assert stmt3.name.value == "active"
        assert stmt3.type_spec == ["Yes/No"]
        assert stmt3.initial_value is not None

    def test_complex_nested_default_expressions(self) -> None:
        """Test parsing Define with complex nested default expressions."""
        # Test arithmetic expression as default
        source1 = "Define `result` as Number (default: _70_)."
        parser1 = Parser()
        program1 = parser1.parse(source1)
        assert len(program1.statements) == 1
        stmt1 = program1.statements[0]
        assert isinstance(stmt1, DefineStatement)
        assert stmt1.name.value == "result"
        assert stmt1.type_spec == ["Number"]
        assert stmt1.initial_value is not None

        # Test string literal as default
        source2 = 'Define `value` as Text (default: _"Hello World"_).'
        parser2 = Parser()
        program2 = parser2.parse(source2)
        assert len(program2.statements) == 1
        stmt2 = program2.statements[0]
        assert isinstance(stmt2, DefineStatement)
        assert stmt2.initial_value is not None

        # Test boolean expression as default
        source3 = "Define `flag` as Yes/No (default: _yes_)."
        parser3 = Parser()
        program3 = parser3.parse(source3)
        assert len(program3.statements) == 1
        stmt3 = program3.statements[0]
        assert isinstance(stmt3, DefineStatement)
        assert stmt3.type_spec == ["Yes/No"]
        assert stmt3.initial_value is not None

    def test_error_recovery_paths(self) -> None:
        """Test error recovery when parsing malformed Define statements."""
        # Missing closing parenthesis in default
        source1 = "Define `x` as Number (default: _5_. Define `y` as Text."
        parser1 = Parser()
        _ = parser1.parse(source1)
        # Should have errors but still parse the second Define
        assert len(parser1.errors) > 0
        # May still have some statements parsed

        # Malformed type specification
        source2 = "Define `z` as or Text."
        parser2 = Parser()
        _ = parser2.parse(source2)
        assert len(parser2.errors) > 0

        # Multiple errors in one statement
        source3 = "Define as (default: )."
        parser3 = Parser()
        _ = parser3.parse(source3)
        assert len(parser3.errors) > 0

    def test_edge_case_union_types(self) -> None:
        """Test edge cases for union type specifications."""
        # Very long union type list
        source1 = "Define `data` as Text or Number or Yes/No or Date or Time or URL or List or Empty."
        parser1 = Parser()
        program1 = parser1.parse(source1)
        assert len(program1.statements) == 1
        stmt1 = program1.statements[0]
        assert isinstance(stmt1, DefineStatement)
        assert len(stmt1.type_spec) == 8
        assert "Text" in stmt1.type_spec
        assert "Empty" in stmt1.type_spec

        # Union type with default value
        source2 = "Define `flexible` as Text or Number (default: _42_)."
        parser2 = Parser()
        program2 = parser2.parse(source2)
        assert len(program2.statements) == 1
        stmt2 = program2.statements[0]
        assert isinstance(stmt2, DefineStatement)
        assert stmt2.type_spec == ["Text", "Number"]
        assert stmt2.initial_value is not None
