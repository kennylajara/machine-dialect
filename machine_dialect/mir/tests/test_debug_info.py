"""Tests for debug information tracking."""

from machine_dialect.ast import (
    BlockStatement,
    Expression,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    InfixExpression,
    Parameter,
    Program,
    ReturnStatement,
    SetStatement,
    StringLiteral,
    WholeNumberLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.debug_info import (
    DebugInfo,
    DebugInfoBuilder,
    DebugVariable,
    SourceLocation,
)
from machine_dialect.mir.hir_to_mir import HIRToMIRLowering
from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Variable


class TestDebugInfoTracking:
    """Test debug information tracking during compilation."""

    def _create_infix(self, left: Expression, op: str, right: Expression) -> InfixExpression:
        """Helper to create InfixExpression properly."""
        token = Token(TokenType.OP_PLUS if op == "+" else TokenType.OP_STAR, op, 0, 0)
        expr = InfixExpression(token, op, left)
        expr.right = right
        return expr

    def _token(self, token_type: TokenType, value: str = "") -> Token:
        """Create a token for testing."""
        return Token(token_type, value, 0, 0)

    def test_source_location_tracking(self) -> None:
        """Test tracking source locations for instructions."""
        debug_info = DebugInfo()
        debug_info.current_file = "test.md"

        # Create a dummy instruction
        inst = LoadConst(Variable("temp", MIRType.INT, 0), Constant(42), (1, 1))
        location = SourceLocation("test.md", 10, 5)

        # Track the location
        debug_info.set_instruction_location(inst, location)

        # Retrieve the location
        retrieved = debug_info.get_instruction_location(inst)
        assert retrieved is not None
        assert retrieved.file == "test.md"
        assert retrieved.line == 10
        assert retrieved.column == 5
        assert str(retrieved) == "test.md:10:5"

    def test_variable_debug_info(self) -> None:
        """Test debug info for variables."""
        debug_info = DebugInfo()

        # Create a variable and its debug info
        var = Variable("count", MIRType.INT)
        debug_var = DebugVariable(name="count", type_name="INT", scope_level=1, is_parameter=False)

        # Add to debug info
        debug_info.add_variable(var, debug_var)

        # Check it was tracked
        assert var in debug_info.variable_info
        assert "count" in debug_info.symbols
        assert debug_info.symbols["count"].type_name == "INT"
        assert debug_info.symbols["count"].scope_level == 1
        assert not debug_info.symbols["count"].is_parameter

    def test_line_mapping(self) -> None:
        """Test bytecode to source line mapping."""
        from machine_dialect.mir.debug_info import LineMapping

        debug_info = DebugInfo()

        # Add some line mappings
        debug_info.add_line_mapping(LineMapping(0, 1))  # Bytecode offset 0 -> line 1
        debug_info.add_line_mapping(LineMapping(10, 2))  # Bytecode offset 10 -> line 2
        debug_info.add_line_mapping(LineMapping(20, 5))  # Bytecode offset 20 -> line 5
        debug_info.add_line_mapping(LineMapping(30, 7))  # Bytecode offset 30 -> line 7

        # Test lookups
        assert debug_info.get_line_for_offset(0) == 1
        assert debug_info.get_line_for_offset(5) == 1  # Between 0 and 10
        assert debug_info.get_line_for_offset(10) == 2
        assert debug_info.get_line_for_offset(15) == 2  # Between 10 and 20
        assert debug_info.get_line_for_offset(25) == 5  # Between 20 and 30
        assert debug_info.get_line_for_offset(35) == 7  # After 30

    def test_source_map_generation(self) -> None:
        """Test source map generation."""
        from machine_dialect.mir.debug_info import LineMapping

        debug_info = DebugInfo()
        debug_info.current_file = "example.md"

        # Add line mappings
        debug_info.add_line_mapping(LineMapping(0, 1))
        debug_info.add_line_mapping(LineMapping(20, 3))
        debug_info.add_line_mapping(LineMapping(40, 5))

        # Add symbols
        var1 = Variable("x", MIRType.INT)
        var2 = Variable("y", MIRType.STRING)
        debug_info.add_variable(var1, DebugVariable("x", "INT", 0, False))
        debug_info.add_variable(var2, DebugVariable("y", "STRING", 1, True))

        # Generate source map
        source_map = debug_info.generate_source_map()

        assert source_map["version"] == 1
        assert source_map["file"] == "example.md"
        assert len(source_map["mappings"]) == 3
        assert source_map["mappings"][0]["bytecode_offset"] == 0
        assert source_map["mappings"][0]["source_line"] == 1

        assert "x" in source_map["symbols"]
        assert source_map["symbols"]["x"]["type"] == "INT"
        assert source_map["symbols"]["x"]["scope_level"] == 0
        assert not source_map["symbols"]["x"]["is_parameter"]

        assert "y" in source_map["symbols"]
        assert source_map["symbols"]["y"]["is_parameter"]

    def test_debug_info_builder(self) -> None:
        """Test the debug info builder."""
        builder = DebugInfoBuilder()

        # Track some variables
        var1 = Variable("local", MIRType.INT)
        var2 = Variable("param", MIRType.STRING)

        builder.track_variable("local", var1, "INT", is_parameter=False)
        builder.track_variable("param", var2, "STRING", is_parameter=True)

        # Track scope changes
        builder.enter_scope()
        var3 = Variable("nested", MIRType.BOOL)
        builder.track_variable("nested", var3, "BOOL", is_parameter=False)

        # Get debug info
        debug_info = builder.get_debug_info()

        assert "local" in debug_info.symbols
        assert debug_info.symbols["local"].scope_level == 0

        assert "param" in debug_info.symbols
        assert debug_info.symbols["param"].is_parameter

        assert "nested" in debug_info.symbols
        assert debug_info.symbols["nested"].scope_level == 1

        # Exit scope
        builder.exit_scope()
        assert builder.scope_level == 0

    def test_instruction_tracking(self) -> None:
        """Test tracking instructions with source locations."""
        builder = DebugInfoBuilder()
        builder.debug_info.current_file = "test.md"

        # Create some instructions
        inst1 = LoadConst(Variable("t1", MIRType.INT, 0), Constant(10), (1, 1))
        inst2 = LoadConst(Variable("t2", MIRType.INT, 0), Constant(20), (1, 1))
        inst3 = BinaryOp(
            Variable("t3", MIRType.INT), "+", Variable("t1", MIRType.INT, 0), Variable("t2", MIRType.INT), (1, 1)
        )

        # Track with line numbers
        builder.track_instruction(inst1, 5, 10)
        builder.track_instruction(inst2, 6, 10)
        builder.track_instruction(inst3, 7, 15)

        debug_info = builder.get_debug_info()

        # Check locations were recorded
        loc1 = debug_info.get_instruction_location(inst1)
        assert loc1 is not None
        assert loc1.line == 5
        assert loc1.column == 10

        loc3 = debug_info.get_instruction_location(inst3)
        assert loc3 is not None
        assert loc3.line == 7
        assert loc3.column == 15

        # Current line should be updated
        assert builder.current_line == 7

    def test_debug_info_in_lowering(self) -> None:
        """Test that debug info is collected during HIR to MIR lowering."""
        program = Program(
            statements=[
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "count"), "count"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "0"), 0),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "message"), "message"),
                    StringLiteral(self._token(TokenType.LIT_TEXT, '"Hello"'), '"Hello"'),
                ),
            ]
        )

        # Create lowerer and lower the program
        lowerer = HIRToMIRLowering()
        lowerer.lower_program(program)

        # Check debug info was collected
        debug_info = lowerer.debug_builder.get_debug_info()

        # Should have tracked variables
        assert len(debug_info.symbols) >= 2
        assert "count" in debug_info.symbols
        assert "message" in debug_info.symbols

        # Check types were tracked (MIRType enum returns lowercase strings)
        assert (
            "int" in debug_info.symbols["count"].type_name.lower()
            or "unknown" in debug_info.symbols["count"].type_name.lower()
        )
        assert (
            "string" in debug_info.symbols["message"].type_name.lower()
            or "unknown" in debug_info.symbols["message"].type_name.lower()
        )

    def test_parameter_debug_info(self) -> None:
        """Test debug info for function parameters."""
        # Create body block and add statements
        body = BlockStatement(self._token(TokenType.OP_GT, ">"))
        body.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "return", 0, 0),
                return_value=self._create_infix(
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    "+",
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                ),
            )
        ]

        func = FunctionStatement(
            token=self._token(TokenType.KW_DEFINE, "define"),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._token(TokenType.MISC_IDENT, "add"), "add"),
            inputs=[
                Parameter(
                    self._token(TokenType.MISC_IDENT, "x"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    "int",
                ),
                Parameter(
                    self._token(TokenType.MISC_IDENT, "y"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    "int",
                ),
            ],
            body=body,
        )

        program = Program(statements=[func])
        lowerer = HIRToMIRLowering()
        lowerer.lower_program(program)

        debug_info = lowerer.debug_builder.get_debug_info()

        # Check parameters were tracked
        assert "x" in debug_info.symbols
        assert "y" in debug_info.symbols
        assert debug_info.symbols["x"].is_parameter
        assert debug_info.symbols["y"].is_parameter
