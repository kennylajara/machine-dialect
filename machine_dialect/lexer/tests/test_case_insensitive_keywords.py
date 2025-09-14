from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tests.helpers import collect_all_tokens
from machine_dialect.lexer.tokens import TokenType, keywords_mapping


class TestCaseInsensitiveKeywords:
    """Test case-insensitive keyword matching while preserving canonical form."""

    def test_all_keywords_case_variations(self) -> None:
        """Test that all keywords in keywords_mapping are case-insensitive."""
        for canonical_form, token_type in keywords_mapping.items():
            # Test different case variations
            test_cases = [
                canonical_form,  # Original form
                canonical_form.lower(),  # Lowercase
                canonical_form.upper(),  # Uppercase
                canonical_form.title(),  # Title case
            ]

            # Add a mixed case variant
            if len(canonical_form) > 2:
                # Create a mixed case like "fLoAt" or "tRuE"
                mixed = ""
                for i, char in enumerate(canonical_form):
                    if char == " ":
                        mixed += " "
                    elif i % 2 == 0:
                        mixed += char.lower()
                    else:
                        mixed += char.upper()
                test_cases.append(mixed)

            for variant in test_cases:
                # Skip if variant is the same as one we already tested
                if test_cases.count(variant) > 1:
                    continue

                lexer = Lexer(variant)
                tokens = collect_all_tokens(lexer)
                assert len(tokens) == 1, f"Expected 1 token for '{variant}', got {len(tokens)}"
                assert tokens[0].type == token_type, f"Expected {token_type} for '{variant}', got {tokens[0].type}"
                # Special case for boolean literals which canonicalize to Yes/No
                if token_type in (TokenType.LIT_YES, TokenType.LIT_NO):
                    expected = "Yes" if token_type == TokenType.LIT_YES else "No"
                    assert tokens[0].literal == expected, (
                        f"Expected literal '{expected}' for '{variant}', got '{tokens[0].literal}'"
                    )
                else:
                    assert tokens[0].literal == canonical_form, (
                        f"Expected literal '{canonical_form}' for '{variant}', got '{tokens[0].literal}'"
                    )

    def test_double_asterisk_keywords_all_cases(self) -> None:
        """Test that all keywords work with double-asterisk wrapping in different cases."""
        # Test a subset of keywords with double asterisks
        test_keywords = ["define", "Float", "Integer", "Boolean", "rule", "Set", "Tell"]

        for keyword in test_keywords:
            if keyword not in keywords_mapping:
                continue

            token_type = keywords_mapping[keyword]
            test_cases = [
                f"**{keyword}**",
                f"**{keyword.lower()}**",
                f"**{keyword.upper()}**",
            ]

            for source in test_cases:
                lexer = Lexer(source)
                tokens = collect_all_tokens(lexer)
                assert len(tokens) == 1
                assert tokens[0].type == token_type
                # Special handling for boolean literals
                if token_type in (TokenType.LIT_YES, TokenType.LIT_NO):
                    expected = "Yes" if token_type == TokenType.LIT_YES else "No"
                    assert tokens[0].literal == expected
                else:
                    assert tokens[0].literal == keyword

    def test_backtick_keywords_all_cases(self) -> None:
        """Test that keywords in backticks become identifiers (case-insensitive)."""
        # Test a subset of keywords with backticks
        test_keywords = ["Float", "Integer", "True", "False", "define", "rule"]

        for keyword in test_keywords:
            if keyword not in keywords_mapping:
                continue

            test_cases = [
                f"`{keyword}`",
                f"`{keyword.lower()}`",
                f"`{keyword.upper()}`",
            ]

            for source in test_cases:
                lexer = Lexer(source)
                tokens = collect_all_tokens(lexer)
                assert len(tokens) == 1
                # Backticks force content to be identifiers
                assert tokens[0].type == TokenType.MISC_IDENT
                # The literal should be the actual text within backticks
                assert tokens[0].literal.lower() == keyword.lower()

    def test_underscore_wrapped_booleans_all_cases(self) -> None:
        """Test underscore-wrapped boolean literals in different cases."""
        # Test both True/False and Yes/No inputs
        test_inputs = [
            ("True", TokenType.LIT_YES, "Yes"),
            ("False", TokenType.LIT_NO, "No"),
            ("Yes", TokenType.LIT_YES, "Yes"),
            ("No", TokenType.LIT_NO, "No"),
        ]

        for input_form, token_type, expected_literal in test_inputs:
            test_cases = [
                f"_{input_form}_",
                f"_{input_form.lower()}_",
                f"_{input_form.upper()}_",
            ]

            for source in test_cases:
                lexer = Lexer(source)
                tokens = collect_all_tokens(lexer)
                assert len(tokens) == 1
                assert tokens[0].type == token_type
                assert tokens[0].literal == expected_literal

    def test_identifiers_preserve_case(self) -> None:
        """Test that non-keyword identifiers preserve their case."""
        # These should NOT match any keywords
        test_cases = [
            ("myVariable", "myVariable"),
            ("MyVariable", "MyVariable"),
            ("MYVARIABLE", "MYVARIABLE"),
            ("userName", "userName"),
            ("floatValue", "floatValue"),  # Contains "float" but not a keyword
            ("integerCount", "integerCount"),  # Contains "integer" but not a keyword
        ]

        for source, expected_literal in test_cases:
            lexer = Lexer(source)
            tokens = collect_all_tokens(lexer)
            assert len(tokens) == 1
            assert tokens[0].type == TokenType.MISC_IDENT
            assert tokens[0].literal == expected_literal

    def test_complex_expression_mixed_case(self) -> None:
        """Test complex expressions with mixed case keywords."""
        test_cases = [
            ("SET x AS integer", ["Set", "x", "as", "integer"]),
            ("set X as INTEGER", ["Set", "X", "as", "INTEGER"]),
            ("define RULE myFunc", ["define", "rule", "myFunc"]),
            ("DEFINE rule MyFunc", ["define", "rule", "MyFunc"]),
            ("if YES then GIVE BACK no", ["if", "Yes", "then", "give back", "No"]),
        ]

        for source, expected_literals in test_cases:
            lexer = Lexer(source)
            tokens = collect_all_tokens(lexer)
            assert len(tokens) == len(expected_literals)

            for token, expected_literal in zip(tokens, expected_literals, strict=False):
                assert token.literal == expected_literal

    def test_multi_word_keywords_preserve_spacing(self) -> None:
        """Test that multi-word keywords preserve internal spacing but are case-insensitive."""
        multi_word_keywords = [
            ("give back", TokenType.KW_RETURN),
            ("gives back", TokenType.KW_RETURN),
        ]

        for canonical_form, token_type in multi_word_keywords:
            # Test with different cases but same spacing
            test_cases = [
                canonical_form,
                canonical_form.upper(),
                canonical_form.title(),
                # Mixed case for each word
                " ".join(word.upper() if i % 2 == 0 else word.lower() for i, word in enumerate(canonical_form.split())),
            ]

            for variant in test_cases:
                lexer = Lexer(variant)
                tokens = collect_all_tokens(lexer)
                assert len(tokens) == 1
                assert tokens[0].type == token_type
                assert tokens[0].literal == canonical_form
