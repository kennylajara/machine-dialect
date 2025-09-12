"""Debug script to see what the parser actually produces for mixed lists."""

from machine_dialect.parser import Parser

source = """
Define `mixed` as list.
Set `mixed` to:
- _"unordered item"_
1. _"ordered item"_
"""

parser = Parser()
program = parser.parse(source)

print(f"Number of statements: {len(program.statements)}")
for i, stmt in enumerate(program.statements):
    print(f"Statement {i}: {type(stmt).__name__}")
    if hasattr(stmt, "value"):
        print(f"  Value type: {type(stmt.value).__name__}")
        if hasattr(stmt.value, "elements"):
            print(f"  Elements: {len(stmt.value.elements)}")

print(f"\nParser errors: {len(parser.errors)}")
for error in parser.errors:
    print(f"  {error}")
