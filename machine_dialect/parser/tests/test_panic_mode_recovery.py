"""Tests for parser panic mode recovery.

This module tests the parser's panic mode recovery mechanism which allows
the parser to recover from errors and continue parsing to find more errors.
"""

from machine_dialect.errors.exceptions import MDSyntaxError
from machine_dialect.parser import Parser


class TestPanicModeRecovery:
    """Test panic mode recovery in the parser."""

    def test_recovery_at_period_boundary(self) -> None:
        """Test that panic mode stops at period boundaries."""
        source = "Define `x` as Whole Number. Set @ to 42. Set `x` to 5."
        parser = Parser()

        program = parser.parse(source)

        # Should have one error for the illegal @ character
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)
        assert "@" in str(parser.errors[0])

        # Should have parsed the statements successfully
        assert len(program.statements) == 3  # Define + 2 Sets
        # First statement should be Define
        assert program.statements[0] is not None
        # Second statement should be incomplete (error due to @)
        assert program.statements[1] is not None
        # Third statement should be complete
        assert program.statements[2] is not None

    def test_recovery_at_eof_boundary(self) -> None:
        """Test that panic mode stops at EOF."""
        source = "Set @ to 42"  # No period at end
        parser = Parser()

        program = parser.parse(source)

        # Should have one error for the illegal @ character
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)

        # Should have one statement (incomplete due to error)
        assert len(program.statements) == 1

    def test_multiple_errors_with_recovery(self) -> None:
        """Test that multiple errors are collected with recovery between them."""
        source = "Define `x` as Whole Number. Set @ to 42. Set # to 10. Set `x` to 5."
        parser = Parser()

        program = parser.parse(source)

        # Should have two errors for the illegal characters
        assert len(parser.errors) == 2
        assert "@" in str(parser.errors[0])
        assert "#" in str(parser.errors[1])
        # @ is now MDSyntaxError (illegal token), # remains MDNameError (unexpected identifier)

        # Should have four statements (Define + 3 Sets)
        assert len(program.statements) == 4

    def test_recovery_in_expression_context(self) -> None:
        """Test panic recovery when error occurs in expression parsing."""
        source = "Define `x` as Whole Number. Define `y` as Whole Number. Set `x` to @ + 5. Set `y` to 10."
        parser = Parser()

        program = parser.parse(source)

        # Should have one error for the illegal @ in expression
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)

        # Should have four statements (2 defines + 2 sets)
        assert len(program.statements) == 4

    def test_recovery_with_missing_keyword(self) -> None:
        """Test panic recovery when 'to' keyword is missing."""
        source = "Define `x` as Whole Number. Define `y` as Whole Number. Set `x` 42. Set `y` to 10."
        parser = Parser()

        program = parser.parse(source)

        # Should have one error for missing 'to'
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)

        # Should have four statements (2 defines + 2 sets)
        assert len(program.statements) == 4

    def test_recovery_with_consecutive_errors(self) -> None:
        """Test panic recovery with errors in consecutive statements."""
        source = "Set @ to 42. Set # to 10."
        parser = Parser()

        program = parser.parse(source)

        # Should have two errors
        assert len(parser.errors) == 2

        # Should have two statements (both incomplete)
        assert len(program.statements) == 2

    def test_panic_counter_limit(self) -> None:
        """Test that panic counter prevents infinite loops."""
        # Create a source with many errors (more than 20)
        statements = [f"Set @{i} to {i}." for i in range(25)]
        source = " ".join(statements)

        parser = Parser()

        program = parser.parse(source)

        # Parser should stop after 20 panic recoveries
        # We might have fewer errors if parser stops early
        assert len(parser.errors) <= 20
        assert len(program.statements) <= 20

    def test_recovery_preserves_valid_parts(self) -> None:
        """Test that valid parts of statements are preserved during recovery."""
        source = "give back @. give back 42."
        parser = Parser()

        program = parser.parse(source)

        # Should have one error for illegal @
        assert len(parser.errors) == 1
        assert isinstance(parser.errors[0], MDSyntaxError)

        # Should have two return statements
        assert len(program.statements) == 2
        # First should be incomplete, second should be complete
        from machine_dialect.ast import ReturnStatement

        if isinstance(program.statements[1], ReturnStatement):
            assert program.statements[1].return_value is not None

    def test_no_recovery_for_valid_code(self) -> None:
        """Test that valid code doesn't trigger panic recovery."""
        source = """Define `x` as Whole Number.
Define `y` as Whole Number.
Set `x` to _42_.
Set `y` to _10_.
give back `x`."""
        parser = Parser()

        program = parser.parse(source)

        # Should have no errors
        assert len(parser.errors) == 0

        # Should have five complete statements (2 defines + 2 sets + 1 return)
        assert len(program.statements) == 5

    def test_recovery_with_mixed_statement_types(self) -> None:
        """Test panic recovery across different statement types."""
        source = """Define `x` as Whole Number.
Set @ to 42.
give back #.
Set `x` to _5_."""
        parser = Parser()

        program = parser.parse(source)

        # Should have two errors (@ is illegal, # is illegal)
        assert len(parser.errors) == 2

        # Should have four statements (1 define + 3 attempts)
        assert len(program.statements) == 4
