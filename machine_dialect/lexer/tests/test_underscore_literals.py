from machine_dialect.lexer import Lexer, Token, TokenMetaType, TokenType


def is_literal_token(token: Token) -> bool:
    return token.type.meta_type == TokenMetaType.LIT


class TestUnderscoreLiterals:
    def test_wrapped_integer(self) -> None:
        """Test underscore-wrapped integer literals."""
        source = "_42_"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_INT
        assert tokens[0].literal == "42"
        assert is_literal_token(tokens[0])

    def test_wrapped_float(self) -> None:
        """Test underscore-wrapped float literals."""
        source = "_3.14_"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_FLOAT
        assert tokens[0].literal == "3.14"
        assert is_literal_token(tokens[0])

    def test_wrapped_string(self) -> None:
        """Test underscore-wrapped string literals."""
        source = '_"Hello, World!"_'
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"Hello, World!"'
        assert is_literal_token(tokens[0])

    def test_unwrapped_integer(self) -> None:
        """Test unwrapped integer literals (backward compatibility)."""
        source = "42"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_INT
        assert tokens[0].literal == "42"
        assert is_literal_token(tokens[0])

    def test_unwrapped_float(self) -> None:
        """Test unwrapped float literals (backward compatibility)."""
        source = "3.14"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_FLOAT
        assert tokens[0].literal == "3.14"
        assert is_literal_token(tokens[0])

    def test_unwrapped_string(self) -> None:
        """Test unwrapped string literals (backward compatibility)."""
        source = '"Hello, World!"'
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"Hello, World!"'
        assert is_literal_token(tokens[0])

    def test_mixed_literals_in_expression(self) -> None:
        """Test both wrapped and unwrapped literals in same expression."""
        source = "Set `x` to _42_ and `y` to 3.14"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0

        # Find the numeric literal tokens (excluding backtick literals)
        numeric_literals = [t for t in tokens if t.type in (TokenType.LIT_INT, TokenType.LIT_FLOAT)]
        assert len(numeric_literals) == 2

        # First literal is wrapped
        assert numeric_literals[0].type == TokenType.LIT_INT
        assert numeric_literals[0].literal == "42"

        # Second literal is unwrapped
        assert numeric_literals[1].type == TokenType.LIT_FLOAT
        assert numeric_literals[1].literal == "3.14"

    def test_underscore_in_identifier(self) -> None:
        """Test that underscores in identifiers don't interfere with literal syntax."""
        source = "_var_name_"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "_var_name_"
        assert not is_literal_token(tokens[0])

    def test_incomplete_wrapped_literal(self) -> None:
        """Test incomplete wrapped literal falls back to identifier."""
        source = "_42"  # Missing closing underscore
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "_42"
