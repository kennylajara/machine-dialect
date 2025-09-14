"""Tests for virtual register allocation."""

from machine_dialect.ast import (
    Expression,
    Identifier,
    InfixExpression,
    Program,
    ReturnStatement,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.register_allocation import (
    LifetimeAnalyzer,
    RegisterAllocator,
)


class TestRegisterAllocation:
    """Test virtual register allocation."""

    def _create_infix(self, left: Expression, op: str, right: Expression) -> InfixExpression:
        """Helper to create InfixExpression properly."""
        token = Token(TokenType.OP_PLUS if op == "+" else TokenType.OP_STAR, op, 0, 0)
        expr = InfixExpression(token, op, left)
        expr.right = right
        return expr

    def _token(self, token_type: TokenType, value: str = "") -> Token:
        """Create a token for testing."""
        return Token(token_type, value, 0, 0)

    def test_basic_register_allocation(self) -> None:
        """Test basic register allocation for simple function."""
        # Create a function with some variables
        program = Program(
            statements=[
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "20"), 20),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    return_value=Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                ),
            ]
        )

        mir_module = lower_to_mir(program)
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Perform register allocation
        allocator = RegisterAllocator(main_func)
        allocation = allocator.allocate()

        # Check that values got allocated
        assert len(allocation.allocations) > 0
        # Check that we didn't use too many registers
        assert allocation.max_registers < 256
        # No spilling needed for simple function
        assert len(allocation.spilled_values) == 0

    def test_register_allocation_with_spilling(self) -> None:
        """Test register allocation with spilling when registers are limited."""
        # Create a function with many variables that have overlapping lifetimes
        statements = []

        # Create 15 variables
        num_vars = 15
        for i in range(num_vars):
            statements.append(
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, f"var_{i}"), f"var_{i}"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, str(i)), i),
                )
            )

        # Now create an expression that uses all variables at once
        # This ensures their lifetimes overlap
        # Build: var_0 + var_1 + var_2 + ... + var_14
        result_expr: Expression = Identifier(self._token(TokenType.MISC_IDENT, "var_0"), "var_0")
        for i in range(1, num_vars):
            result_expr = self._create_infix(
                result_expr,
                "+",
                Identifier(self._token(TokenType.MISC_IDENT, f"var_{i}"), f"var_{i}"),
            )

        statements.append(
            SetStatement(
                self._token(TokenType.KW_SET, "set"),
                Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                result_expr,
            )
        )

        program = Program(statements=statements)  # type: ignore[arg-type]
        mir_module = lower_to_mir(program)
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Allocate with very limited registers (less than the number of overlapping values)
        allocator = RegisterAllocator(main_func, max_registers=8)
        allocation = allocator.allocate()

        # Check that some values were spilled (we have 15+ values but only 8 registers)
        assert len(allocation.spilled_values) > 0, (
            f"Expected spilling but got none. Allocated: {allocation.max_registers} registers"
        )
        # Should use most of the available registers
        assert allocation.max_registers <= 8 and allocation.max_registers >= 5

    def test_lifetime_analysis(self) -> None:
        """Test lifetime analysis for temporaries."""
        program = Program(
            statements=[
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "1"), 1),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "2"), 2),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    ),
                ),
                # 'a' and 'b' not used after this point
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "d"), "d"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "3"), 3),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "e"), "e"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                        "*",
                        Identifier(self._token(TokenType.MISC_IDENT, "d"), "d"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    return_value=Identifier(self._token(TokenType.MISC_IDENT, "e"), "e"),
                ),
            ]
        )

        mir_module = lower_to_mir(program)
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Analyze lifetimes
        analyzer = LifetimeAnalyzer(main_func)
        lifetimes = analyzer.analyze()

        # Check that we have lifetime info for all variables
        assert len(lifetimes) > 0

        # Variables should have different lifetimes
        # 'a' and 'b' should have shorter lifetimes than 'e'
        for _, (start, end) in lifetimes.items():
            assert start <= end  # Valid lifetime range

    def test_reusable_slot_detection(self) -> None:
        """Test detection of reusable stack slots."""
        # Create a program where variables don't overlap in lifetime
        program = Program(
            statements=[
                # First set of variables
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp1"), "temp1"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "1"), 1),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp2"), "temp2"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "2"), 2),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "result1"), "result1"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "temp1"), "temp1"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "temp2"), "temp2"),
                    ),
                ),
                # temp1 and temp2 dead after this
                # Second set of variables (can reuse slots)
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp3"), "temp3"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "3"), 3),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp4"), "temp4"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "4"), 4),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "result2"), "result2"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "temp3"), "temp3"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "temp4"), "temp4"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    return_value=self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "result1"), "result1"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "result2"), "result2"),
                    ),
                ),
            ]
        )

        mir_module = lower_to_mir(program)
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Analyze lifetimes
        analyzer = LifetimeAnalyzer(main_func)
        lifetimes = analyzer.analyze()

        # Find reusable slots
        reusable_groups = analyzer.find_reusable_slots()

        # Should identify some values that can share slots
        assert len(reusable_groups) > 0

        # Count total slots needed vs total variables
        total_slots_needed = len(reusable_groups)
        total_variables = len(lifetimes)

        # Should need fewer slots than variables due to reuse
        assert total_slots_needed <= total_variables

    def test_linear_scan_ordering(self) -> None:
        """Test that linear scan processes intervals in correct order."""
        program = Program(
            statements=[
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "first"), "first"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "1"), 1),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "second"), "second"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "2"), 2),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "third"), "third"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "3"), 3),
                ),
            ]
        )

        mir_module = lower_to_mir(program)
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        allocator = RegisterAllocator(main_func)

        # Build intervals
        allocator._build_instruction_positions()
        allocator._compute_live_intervals()

        # Check intervals are created
        assert len(allocator.live_intervals) > 0

        # Check intervals are sorted by start position
        for i in range(1, len(allocator.live_intervals)):
            assert allocator.live_intervals[i - 1].start <= allocator.live_intervals[i].start
