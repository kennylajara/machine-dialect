from machine_dialect.lexer import Lexer, Token, TokenMetaType, TokenType


def is_literal_token(token: Token) -> bool:
    return token.type.meta_type == TokenMetaType.LIT


class TestBooleanLiterals:
    def test_wrapped_true(self) -> None:
        """Test underscore-wrapped True literal."""
        source = "_True_"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TRUE
        assert tokens[0].literal == "True"
        assert is_literal_token(tokens[0])

    def test_wrapped_false(self) -> None:
        """Test underscore-wrapped False literal."""
        source = "_False_"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_FALSE
        assert tokens[0].literal == "False"
        assert is_literal_token(tokens[0])

    def test_unwrapped_true(self) -> None:
        """Test unwrapped True literal (backward compatibility)."""
        source = "True"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TRUE
        assert tokens[0].literal == "True"
        assert is_literal_token(tokens[0])

    def test_unwrapped_false(self) -> None:
        """Test unwrapped False literal (backward compatibility)."""
        source = "False"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_FALSE
        assert tokens[0].literal == "False"
        assert is_literal_token(tokens[0])

    def test_boolean_in_expression(self) -> None:
        """Test boolean literals in expressions."""
        source = "if x > 0 then give back _True_ else give back False"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0

        # Find the boolean tokens
        boolean_tokens = [t for t in tokens if t.type in (TokenType.LIT_TRUE, TokenType.LIT_FALSE)]
        assert len(boolean_tokens) == 2

        # First boolean is wrapped
        assert boolean_tokens[0].type == TokenType.LIT_TRUE
        assert boolean_tokens[0].literal == "True"

        # Second boolean is unwrapped
        assert boolean_tokens[1].type == TokenType.LIT_FALSE
        assert boolean_tokens[1].literal == "False"

    def test_lowercase_not_boolean(self) -> None:
        """Test that lowercase true/false are not boolean literals."""
        source = "true false"
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "true"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "false"

    def test_incomplete_wrapped_boolean(self) -> None:
        """Test incomplete wrapped boolean falls back to identifier."""
        source = "_True"  # Missing closing underscore
        lexer = Lexer(source)
        errors, tokens = lexer.tokenize()

        assert len(errors) == 0
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "_True"
        assert not is_literal_token(tokens[0])
