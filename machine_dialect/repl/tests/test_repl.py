#!/usr/bin/env python3
"""Test the REPL with some sample inputs"""

from machine_dialect.lexer.lexer import Lexer

# Test inputs
test_inputs = [
    "if x > 0 then return true",
    "Set x to Integer 42",
    "Define a rule called add that takes Number a and Number b",
    "**bold** text with #hash",
    "URL: https://example.com",
    "Date: 2024-01-15",
]

print("Testing Machine Dialect Lexer")
print("=" * 60)

for input_text in test_inputs:
    print(f"\nInput: {input_text!r}")
    print("-" * 60)

    lexer = Lexer(input_text)
    tokens = lexer.tokenize()

    print(f"Tokens ({len(tokens)}):")
    for token in tokens:
        print(f"  {token.type.name:<20} | {token.literal!r}")
    print()
