"""Tests for improved call statement lowering."""

from machine_dialect.ast import (
    Arguments,
    CallStatement,
    Identifier,
    Program,
    StringLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir


class TestCallStatementLowering:
    """Test improved call statement handling."""

    def test_call_with_positional_arguments(self) -> None:
        """Test call statement with positional arguments."""
        # Call `print` with "Hello", 42.
        args = Arguments(Token(TokenType.DELIM_LPAREN, "(", 0, 0))
        args.positional = [
            StringLiteral(Token(TokenType.LIT_TEXT, '"Hello"', 0, 0), '"Hello"'),
            WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 0, 0), 42),
        ]

        call = CallStatement(
            token=Token(TokenType.KW_USE, "use", 0, 0),
            function_name=StringLiteral(Token(TokenType.LIT_TEXT, '"print"', 0, 0), '"print"'),
            arguments=args,
        )

        program = Program(statements=[call])
        mir_module = lower_to_mir(program)

        # Check that main function was created
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Check that call instruction was generated
        found_call = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "Call":
                    found_call = True
                    # Check that we have 2 arguments
                    assert hasattr(inst, "args") and len(inst.args) == 2
                    break

        assert found_call, "Call instruction not found"

    def test_call_with_named_arguments(self) -> None:
        """Test call statement with named arguments."""
        # Call `format` with name: "Alice", age: 30.
        args = Arguments(Token(TokenType.DELIM_LPAREN, "(", 0, 0))
        args.named = [
            (
                Identifier(Token(TokenType.MISC_IDENT, "name", 0, 0), "name"),
                StringLiteral(Token(TokenType.LIT_TEXT, '"Alice"', 0, 0), '"Alice"'),
            ),
            (
                Identifier(Token(TokenType.MISC_IDENT, "age", 0, 0), "age"),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "30", 0, 0), 30),
            ),
        ]

        call = CallStatement(
            token=Token(TokenType.KW_USE, "use", 0, 0),
            function_name=Identifier(Token(TokenType.MISC_IDENT, "format", 0, 0), "format"),
            arguments=args,
        )

        program = Program(statements=[call])
        mir_module = lower_to_mir(program)

        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Check that arguments were processed
        found_call = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "Call":
                    found_call = True
                    assert hasattr(inst, "args") and len(inst.args) == 2  # Named args converted to positional
                    break

        assert found_call

    def test_call_with_mixed_arguments(self) -> None:
        """Test call with both positional and named arguments."""
        args = Arguments(Token(TokenType.DELIM_LPAREN, "(", 0, 0))
        args.positional = [StringLiteral(Token(TokenType.LIT_TEXT, '"test"', 0, 0), '"test"')]
        args.named = [
            (
                Identifier(Token(TokenType.MISC_IDENT, "verbose", 0, 0), "verbose"),
                YesNoLiteral(Token(TokenType.LIT_YES, "true", 0, 0), True),
            )
        ]

        call = CallStatement(
            token=Token(TokenType.KW_USE, "use", 0, 0),
            function_name=StringLiteral(Token(TokenType.LIT_TEXT, '"run"', 0, 0), '"run"'),
            arguments=args,
        )

        program = Program(statements=[call])
        mir_module = lower_to_mir(program)

        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Both arguments should be present
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "Call":
                    assert hasattr(inst, "args") and len(inst.args) == 2

    def test_call_with_single_argument(self) -> None:
        """Test call with single argument not wrapped in Arguments."""
        call = CallStatement(
            token=Token(TokenType.KW_USE, "use", 0, 0),
            function_name=StringLiteral(Token(TokenType.LIT_TEXT, '"print"', 0, 0), '"print"'),
            arguments=StringLiteral(Token(TokenType.LIT_TEXT, '"Hello World"', 0, 0), '"Hello World"'),
        )

        program = Program(statements=[call])
        mir_module = lower_to_mir(program)

        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Should handle single argument
        found_call = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "Call":
                    found_call = True
                    assert hasattr(inst, "args") and len(inst.args) == 1
                    break

        assert found_call

    def test_call_without_arguments(self) -> None:
        """Test call without any arguments."""
        call = CallStatement(
            token=Token(TokenType.KW_USE, "use", 0, 0),
            function_name=Identifier(Token(TokenType.MISC_IDENT, "exit", 0, 0), "exit"),
            arguments=None,
        )

        program = Program(statements=[call])
        mir_module = lower_to_mir(program)

        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Should handle no arguments
        found_call = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "Call":
                    found_call = True
                    assert hasattr(inst, "args") and len(inst.args) == 0
                    break

        assert found_call
