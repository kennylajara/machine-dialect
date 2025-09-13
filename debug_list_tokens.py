#!/usr/bin/env python3
"""Debug script to see what tokens are generated for list parsing."""

from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tokens import Token

# Test unordered list
source = """Set `shopping` to:
- _"milk"_.
- _"bread"_.
- _"eggs"_."""

print("Source:")
print(source)
print("\nTokens:")

lexer = Lexer(source)
tokens: list[Token] = []
in_list = False

while True:
    # Check if we should set list context
    if tokens and tokens[-1].literal == "to" and len(tokens) > 1 and tokens[-2].literal == "`shopping`":
        in_list = True
        print("  [Setting list context = True]")

    token = lexer.next_token(in_list_context=in_list)
    if token is None:
        break
    tokens.append(token)
    print(f"  {token.type:30} | {token.literal!r:20} | line {token.line}:{token.position}")
    if token.type.name == "MISC_EOF":
        break

print(f"\nTotal tokens: {len(tokens)}")
