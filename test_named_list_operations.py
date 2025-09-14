#!/usr/bin/env python3
"""Test the new Named List operations implementation."""

from pathlib import Path

from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.pipeline import CompilationPipeline
from machine_dialect.parser import Parser
from machine_dialect.semantic.analyzer import SemanticAnalyzer


def test_parser(name: str, source: str) -> bool:
    """Test if the parser accepts the syntax."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {name}")
    print(f"{'=' * 60}")
    print(f"Source:\n{source}")

    parser = Parser()
    program = parser.parse(source)

    if parser.errors:
        print(f"❌ Parser errors: {parser.errors}")
        return False
    else:
        print("✅ Parser: Success")

        # Run semantic analysis
        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        if errors:
            print(f"❌ Semantic errors: {errors}")
            return False
        else:
            print("✅ Semantic: Success")
            return True


def test_compilation(name: str, source: str) -> bool:
    """Test if the code compiles to MIR."""
    config = CompilerConfig(verbose=False)
    pipeline = CompilationPipeline(config)

    test_file = Path(f"test_{name.replace(' ', '_')}.md")
    test_file.write_text(source)

    try:
        context = pipeline.compile_file(test_file)
        if context.has_errors():
            print(f"❌ Compilation errors: {context.errors}")
            return False
        else:
            print("✅ Compilation: Success")

            # Check MIR instructions
            if hasattr(context, "mir_module") and context.mir_module:
                main_func = context.mir_module.get_function("__main__")
                if main_func:
                    from machine_dialect.mir.mir_instructions import (
                        ArrayAppend,
                        ArrayClear,
                        ArrayRemove,
                        DictClear,
                        DictRemove,
                        DictSet,
                    )

                    dict_ops = []
                    array_ops = []

                    for block in main_func.cfg.blocks.values():
                        for inst in block.instructions:
                            if isinstance(inst, DictSet | DictRemove | DictClear):
                                dict_ops.append(type(inst).__name__)
                            elif isinstance(inst, ArrayAppend | ArrayRemove | ArrayClear):
                                array_ops.append(type(inst).__name__)

                    if dict_ops:
                        print(f"  Dict operations: {', '.join(set(dict_ops))}")
                    if array_ops:
                        print(f"  Array operations: {', '.join(set(array_ops))}")

            return True
    finally:
        test_file.unlink(missing_ok=True)


# Test cases
tests = [
    # Named List operations
    (
        "Add to Named List",
        """
Define `person` as Named List.
Set `person` to:
Add "name" to `person` with value _"John"_.
Add "age" to `person` with value _30_.
""",
    ),
    (
        "Remove from Named List",
        """
Define `person` as Named List.
Set `person` to:
- "name": _"John"_.
- "age": _30_.
Remove "age" from `person`.
""",
    ),
    (
        "Update Named List",
        """
Define `person` as Named List.
Set `person` to:
- "name": _"John"_.
- "age": _30_.
Update "name" in `person` to _"Jane"_.
""",
    ),
    (
        "Clear Named List",
        """
Define `person` as Named List.
Set `person` to:
- "name": _"John"_.
- "age": _30_.
Clear `person`.
""",
    ),
    # Array operations
    (
        "Add to Unordered List",
        """
Define `items` as Unordered List.
Set `items` to:
Add _"apple"_ to `items`.
Add _"banana"_ to `items`.
""",
    ),
    (
        "Remove from Ordered List",
        """
Define `tasks` as Ordered List.
Set `tasks` to:
1. _"Task 1"_.
2. _"Task 2"_.
Remove _"Task 1"_ from `tasks`.
""",
    ),
    (
        "Clear Unordered List",
        """
Define `items` as Unordered List.
Set `items` to:
- _"apple"_.
- _"banana"_.
Clear `items`.
""",
    ),
    # Error cases (should fail semantic analysis)
    (
        "Invalid: Add to array with key",
        """
Define `items` as Unordered List.
Set `items` to:
Add "key" to `items` with value _"value"_.
""",
    ),
    (
        "Invalid: Set on Named List",
        """
Define `person` as Named List.
Set `person` to:
Set the first item of `person` to _"value"_.
""",
    ),
    (
        "Invalid: Insert on Named List",
        """
Define `person` as Named List.
Set `person` to:
Insert _"value"_ at position _1_ in `person`.
""",
    ),
]


def main() -> None:
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NAMED LIST OPERATIONS TEST SUITE")
    print("=" * 60)

    results: list[tuple[str, bool, bool]] = []

    for name, source in tests:
        parser_ok = test_parser(name, source)

        if parser_ok:
            compile_ok = test_compilation(name, source)
            results.append((name, True, compile_ok))
        else:
            results.append((name, False, False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, parser_ok, compile_ok in results:
        status = "✅" if parser_ok and compile_ok else "⚠️" if parser_ok else "❌"
        print(f"{status} {name}")

    # Count successes
    total = len(results)
    passed = sum(1 for _, p, c in results if p and c)
    print(f"\nPassed: {passed}/{total}")


if __name__ == "__main__":
    main()
