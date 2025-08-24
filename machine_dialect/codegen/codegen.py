"""Code generator for Machine Dialect.

This module implements the main code generator that walks the AST
and produces bytecode using the emitter.
"""

from machine_dialect.ast import (
    BlockStatement,
    BooleanLiteral,
    CallStatement,
    ConditionalExpression,
    EmptyLiteral,
    Expression,
    ExpressionStatement,
    FloatLiteral,
    # Expressions
    Identifier,
    IfStatement,
    InfixExpression,
    # Literals
    IntegerLiteral,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    # Statements
    SetStatement,
    Statement,
    StringLiteral,
    URLLiteral,
    UtilityStatement,
)
from machine_dialect.codegen.emitter import Emitter
from machine_dialect.codegen.isa import Opcode
from machine_dialect.codegen.objects import Chunk, ChunkType, Module, ModuleType
from machine_dialect.codegen.symtab import SymbolTable, SymbolType


class CodeGenerator:
    """Generates bytecode from an AST."""

    def __init__(self) -> None:
        """Initialize the code generator."""
        self.symbol_table = SymbolTable()
        self.current_chunk: Chunk | None = None
        self.emitter: Emitter | None = None
        self.module: Module | None = None
        self.errors: list[str] = []

    def compile(
        self, program: Program, module_name: str = "main", module_type: ModuleType = ModuleType.PROCEDURAL
    ) -> Module:
        """Compile a program AST to bytecode.

        Args:
            program: The program AST to compile.
            module_name: Name for the compiled module (defaults to "main").
            module_type: Type of module to create (defaults to PROCEDURAL).

        Returns:
            A compiled module.
        """
        # Create main chunk with appropriate type
        main_chunk = Chunk(name="main", chunk_type=ChunkType.MAIN)
        self.current_chunk = main_chunk
        self.emitter = Emitter(main_chunk)

        # Create module early so functions can be added to it
        self.module = Module(name=module_name, main_chunk=main_chunk, module_type=module_type)

        # Compile all statements
        for statement in program.statements:
            self._compile_statement(statement)

        # Update chunk metadata
        main_chunk.num_locals = self.symbol_table.num_locals()

        return self.module

    def _compile_statement(self, stmt: Statement) -> None:
        """Compile a statement node.

        Args:
            stmt: The statement to compile.
        """
        if isinstance(stmt, SetStatement):
            self._compile_set_statement(stmt)
        elif isinstance(stmt, ReturnStatement):
            self._compile_return_statement(stmt)
        elif isinstance(stmt, ExpressionStatement):
            self._compile_expression_statement(stmt)
        elif isinstance(stmt, IfStatement):
            self._compile_if_statement(stmt)
        elif isinstance(stmt, BlockStatement):
            self._compile_block_statement(stmt)
        elif isinstance(stmt, SayStatement):
            self._compile_say_statement(stmt)
        elif isinstance(stmt, CallStatement):
            self._compile_call_statement(stmt)
        elif isinstance(stmt, UtilityStatement):
            self._compile_utility_statement(stmt)
        else:
            self._add_error(f"Unsupported statement type: {type(stmt).__name__}")

    def _compile_set_statement(self, stmt: SetStatement) -> None:
        """Compile a set (assignment) statement.

        Args:
            stmt: The set statement to compile.
        """
        assert self.emitter is not None

        # Compile the value expression
        if stmt.value is None:
            self._add_error("SetStatement has no value")
            return
        self._compile_expression(stmt.value)

        # Get or create symbol
        if stmt.name is None:
            self._add_error("SetStatement has no name")
            return
        name = stmt.name.value
        symbol = self.symbol_table.resolve(name)

        if symbol is None:
            # Define new variable
            symbol = self.symbol_table.define(name)

        # Emit store instruction
        if symbol.symbol_type in (SymbolType.LOCAL, SymbolType.PARAMETER):
            self.emitter.emit_store_local(symbol.slot)
        else:
            self.emitter.emit_store_global(name)

    def _compile_return_statement(self, stmt: ReturnStatement) -> None:
        """Compile a return statement.

        Args:
            stmt: The return statement to compile.
        """
        assert self.emitter is not None

        if stmt.return_value:
            self._compile_expression(stmt.return_value)
        else:
            # Return empty/null
            self.emitter.emit_constant(None)

        self.emitter.emit_return()

    def _compile_expression_statement(self, stmt: ExpressionStatement) -> None:
        """Compile an expression statement.

        Args:
            stmt: The expression statement to compile.
        """
        assert self.emitter is not None

        # Compile expression and discard result
        if stmt.expression is None:
            self._add_error("ExpressionStatement has no expression")
            return
        self._compile_expression(stmt.expression)
        self.emitter.emit_pop()

    def _compile_if_statement(self, stmt: IfStatement) -> None:
        """Compile an if statement with optional else.

        Args:
            stmt: The if statement to compile.
        """
        assert self.emitter is not None

        # Compile condition
        if stmt.condition is None:
            self._add_error("IfStatement has no condition")
            return
        self._compile_expression(stmt.condition)

        # Emit conditional jump
        jump_to_else = self.emitter.emit_jump(Opcode.JUMP_IF_FALSE)

        # Compile consequence block
        if stmt.consequence is None:
            self._add_error("IfStatement has no consequence")
            return
        self._compile_block_statement(stmt.consequence)

        if stmt.alternative:
            # Jump over else block
            jump_to_end = self.emitter.emit_jump(Opcode.JUMP)

            # Patch jump to else
            self.emitter.patch_jump(jump_to_else)

            # Compile alternative block
            self._compile_block_statement(stmt.alternative)

            # Patch jump to end
            self.emitter.patch_jump(jump_to_end)
        else:
            # No else block, just patch the conditional jump
            self.emitter.patch_jump(jump_to_else)

    def _compile_block_statement(self, stmt: BlockStatement) -> None:
        """Compile a block statement.

        Args:
            stmt: The block statement to compile.
        """
        # For now, blocks don't create new scopes
        # Just compile all statements in sequence
        for statement in stmt.statements:
            self._compile_statement(statement)

    def _compile_say_statement(self, stmt: SayStatement) -> None:
        """Compile a say (output) statement.

        Args:
            stmt: The say statement to compile.
        """
        assert self.emitter is not None

        # For now, just compile the expression and pop
        # A real implementation would call a print function
        if stmt.expression is None:
            self._add_error("SayStatement has no expression")
            return
        self._compile_expression(stmt.expression)
        self.emitter.emit_pop()

    def _compile_call_as_expression(self, stmt: CallStatement) -> None:
        """Compile a call statement as an expression (leaves result on stack).

        Args:
            stmt: The call statement to compile as expression.
        """
        assert self.emitter is not None

        # Get function name
        if stmt.function_name is None:
            self._add_error("CallStatement has no function name")
            return

        # Handle function name - it should be a StringLiteral or Identifier
        func_name = None
        if isinstance(stmt.function_name, StringLiteral):
            func_name = stmt.function_name.value
        elif isinstance(stmt.function_name, Identifier):
            func_name = stmt.function_name.value
        else:
            self._add_error(f"Unsupported function name type: {type(stmt.function_name).__name__}")
            return

        # Load function onto stack using LOAD_FUNCTION
        self.emitter.emit_load_function(func_name)

        # Compile arguments
        arg_count = 0
        if stmt.arguments is not None:
            from machine_dialect.ast import Arguments

            if isinstance(stmt.arguments, Arguments):
                # Compile positional arguments
                for arg in stmt.arguments.positional:
                    self._compile_expression(arg)
                    arg_count += 1

                # Handle named arguments - need to reorder based on function parameters
                if stmt.arguments.named:
                    # Look up the function to get parameter order
                    func_chunk = None
                    if self.module:
                        func_chunk = self.module.get_function(func_name)

                    if func_chunk and func_chunk.param_names:
                        # Create a dict of name -> value for named arguments
                        # Note: names are Identifier objects, need to extract .value
                        named_args = {name.value: value for name, value in stmt.arguments.named}

                        # Compile named arguments in parameter order
                        # Skip positions already filled by positional arguments
                        for i in range(len(stmt.arguments.positional), len(func_chunk.param_names)):
                            param_name = func_chunk.param_names[i]
                            if param_name in named_args:
                                self._compile_expression(named_args[param_name])
                                arg_count += 1
                                del named_args[param_name]  # Mark as used

                        # Check for any unused named arguments (might be errors)
                        for name in named_args:
                            self._add_error(f"Unknown parameter: {name}")
                    else:
                        # No parameter info - compile in order given (fallback)
                        for _name, value in stmt.arguments.named:
                            self._compile_expression(value)
                            arg_count += 1
            else:
                # Single expression argument
                self._compile_expression(stmt.arguments)
                arg_count = 1

        # Emit call instruction
        self.emitter.emit_call(arg_count)

        # Don't pop result - leave it on stack as expression value

    def _compile_call_statement(self, stmt: CallStatement) -> None:
        """Compile a call statement.

        Args:
            stmt: The call statement to compile.
        """
        # Compile as expression first
        self._compile_call_as_expression(stmt)

        # Don't pop result - let it be the statement's value
        # This allows "Use" statements to return values

    def _compile_utility_statement(self, stmt: UtilityStatement) -> None:
        """Compile a utility statement (function definition).

        Args:
            stmt: The utility statement to compile.
        """
        # Save current compilation state
        prev_chunk = self.current_chunk
        prev_emitter = self.emitter

        # Create new chunk for the function
        func_name = stmt.name.value if stmt.name else "anonymous"

        # Extract parameter names
        param_names = [param.name.value for param in stmt.inputs if param.name]

        func_chunk = Chunk(
            name=func_name,
            chunk_type=ChunkType.FUNCTION,
            num_params=len(stmt.inputs),
            param_names=param_names,
        )

        # Create new emitter for function chunk
        self.current_chunk = func_chunk
        self.emitter = Emitter(func_chunk)

        # Enter new scope for function
        self.symbol_table.enter_scope(func_name)

        # Define parameters as local variables
        for param in stmt.inputs:
            if param.name:
                self.symbol_table.define(param.name.value, is_parameter=True)

        # Compile function body
        if stmt.body is not None:
            self._compile_block_statement(stmt.body)

        # Ensure function returns (add implicit return if needed)
        if not self._last_instruction_is_return():
            # Return None implicitly
            self.emitter.emit_constant(None)
            self.emitter.emit_return()

        # Update local count
        func_chunk.num_locals = self.symbol_table.num_locals()

        # Exit function scope
        self.symbol_table.exit_scope()

        # Add function to module
        if self.module is not None:
            self.module.add_function(func_name, func_chunk)

        # Restore previous compilation state
        self.current_chunk = prev_chunk
        self.emitter = prev_emitter

    def _last_instruction_is_return(self) -> bool:
        """Check if the last instruction is a return.

        Returns:
            True if the last instruction is RETURN, False otherwise.
        """
        if self.current_chunk is None or len(self.current_chunk.bytecode) == 0:
            return False
        return self.current_chunk.bytecode[-1] == Opcode.RETURN

    def _compile_expression(self, expr: Expression) -> None:
        """Compile an expression node.

        Args:
            expr: The expression to compile.
        """
        if isinstance(expr, IntegerLiteral):
            self._compile_integer_literal(expr)
        elif isinstance(expr, FloatLiteral):
            self._compile_float_literal(expr)
        elif isinstance(expr, StringLiteral):
            self._compile_string_literal(expr)
        elif isinstance(expr, BooleanLiteral):
            self._compile_boolean_literal(expr)
        elif isinstance(expr, EmptyLiteral):
            self._compile_empty_literal(expr)
        elif isinstance(expr, URLLiteral):
            self._compile_url_literal(expr)
        elif isinstance(expr, Identifier):
            self._compile_identifier(expr)
        elif isinstance(expr, PrefixExpression):
            self._compile_prefix_expression(expr)
        elif isinstance(expr, InfixExpression):
            self._compile_infix_expression(expr)
        elif isinstance(expr, ConditionalExpression):
            self._compile_conditional_expression(expr)
        elif isinstance(expr, CallStatement):
            # Handle CallStatement used as expression (e.g., in "Set x using `func`")
            self._compile_call_as_expression(expr)
        else:
            self._add_error(f"Unsupported expression type: {type(expr).__name__}")

    def _compile_integer_literal(self, expr: IntegerLiteral) -> None:
        """Compile an integer literal.

        Args:
            expr: The integer literal to compile.
        """
        assert self.emitter is not None
        self.emitter.emit_constant(expr.value)

    def _compile_float_literal(self, expr: FloatLiteral) -> None:
        """Compile a float literal.

        Args:
            expr: The float literal to compile.
        """
        assert self.emitter is not None
        self.emitter.emit_constant(expr.value)

    def _compile_string_literal(self, expr: StringLiteral) -> None:
        """Compile a string literal.

        Args:
            expr: The string literal to compile.
        """
        assert self.emitter is not None
        # Strip quotes from string literal value
        value = expr.value
        if value and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value and value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        self.emitter.emit_constant(value)

    def _compile_boolean_literal(self, expr: BooleanLiteral) -> None:
        """Compile a boolean literal.

        Args:
            expr: The boolean literal to compile.
        """
        assert self.emitter is not None
        self.emitter.emit_constant(expr.value)

    def _compile_empty_literal(self, expr: EmptyLiteral) -> None:
        """Compile an empty (null) literal.

        Args:
            expr: The empty literal to compile.
        """
        assert self.emitter is not None
        self.emitter.emit_constant(None)

    def _compile_url_literal(self, expr: URLLiteral) -> None:
        """Compile a URL literal.

        Args:
            expr: The URL literal to compile.
        """
        assert self.emitter is not None
        # Strip quotes from URL value if present
        value = expr.value
        if value and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value and value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        # URLs are treated as strings in the VM
        self.emitter.emit_constant(value)

    def _compile_identifier(self, expr: Identifier) -> None:
        """Compile an identifier (variable reference).

        Args:
            expr: The identifier to compile.
        """
        assert self.emitter is not None

        name = expr.value
        symbol = self.symbol_table.resolve(name)

        if symbol is None:
            # Treat as global
            self.emitter.emit_load_global(name)
        elif symbol.symbol_type in (SymbolType.LOCAL, SymbolType.PARAMETER):
            self.emitter.emit_load_local(symbol.slot)
        else:
            self.emitter.emit_load_global(name)

    def _compile_prefix_expression(self, expr: PrefixExpression) -> None:
        """Compile a prefix expression.

        Args:
            expr: The prefix expression to compile.
        """
        assert self.emitter is not None

        # Compile operand
        if expr.right is None:
            self._add_error("PrefixExpression has no right operand")
            return
        self._compile_expression(expr.right)

        # Apply operator
        if expr.operator == "-":
            self.emitter.emit(Opcode.NEG)
        elif expr.operator == "not":
            self.emitter.emit(Opcode.NOT)
        else:
            self._add_error(f"Unknown prefix operator: {expr.operator}")

    def _compile_infix_expression(self, expr: InfixExpression) -> None:
        """Compile an infix expression.

        Args:
            expr: The infix expression to compile.
        """
        assert self.emitter is not None

        # Compile left operand
        if expr.left is None:
            self._add_error("InfixExpression has no left operand")
            return
        self._compile_expression(expr.left)

        # Compile right operand
        if expr.right is None:
            self._add_error("InfixExpression has no right operand")
            return
        self._compile_expression(expr.right)

        # Apply operator
        operator_map = {
            "+": Opcode.ADD,
            "-": Opcode.SUB,
            "*": Opcode.MUL,
            "/": Opcode.DIV,
            "%": Opcode.MOD,
            "<": Opcode.LT,
            ">": Opcode.GT,
            "<=": Opcode.LTE,
            ">=": Opcode.GTE,
            "==": Opcode.EQ,
            "!=": Opcode.NEQ,
            "and": Opcode.AND,
            "or": Opcode.OR,
            # Natural language equality operators (canonicalized by parser)
            "equals": Opcode.EQ,
            "is not": Opcode.NEQ,
            # Strict equality operators (canonicalized by parser)
            "is strictly equal to": Opcode.STRICT_EQ,
            "is not strictly equal to": Opcode.STRICT_NEQ,
        }

        opcode = operator_map.get(expr.operator)
        if opcode:
            self.emitter.emit(opcode)
        else:
            self._add_error(f"Unknown infix operator: {expr.operator}")

    def _compile_conditional_expression(self, expr: ConditionalExpression) -> None:
        """Compile a conditional (ternary) expression.

        This compiles to bytecode that evaluates the condition and leaves
        either the consequence or alternative value on the stack.

        Args:
            expr: The conditional expression to compile.
        """
        assert self.emitter is not None

        # Compile condition
        if expr.condition is None:
            self._add_error("ConditionalExpression has no condition")
            return
        self._compile_expression(expr.condition)

        # Jump to alternative if condition is false
        jump_to_alternative = self.emitter.emit_jump(Opcode.JUMP_IF_FALSE)

        # Compile consequence (value when true)
        if expr.consequence is None:
            self._add_error("ConditionalExpression has no consequence")
            return
        self._compile_expression(expr.consequence)

        # Jump over alternative
        jump_to_end = self.emitter.emit_jump(Opcode.JUMP)

        # Patch jump to alternative
        self.emitter.patch_jump(jump_to_alternative)

        # Compile alternative (value when false)
        if expr.alternative is None:
            self._add_error("ConditionalExpression has no alternative")
            return
        self._compile_expression(expr.alternative)

        # Patch jump to end
        self.emitter.patch_jump(jump_to_end)

    def _add_error(self, message: str) -> None:
        """Add a compilation error.

        Args:
            message: Error message.
        """
        self.errors.append(message)

    def has_errors(self) -> bool:
        """Check if compilation produced errors.

        Returns:
            True if there were errors, False otherwise.
        """
        return len(self.errors) > 0

    def get_errors(self) -> list[str]:
        """Get all compilation errors.

        Returns:
            List of error messages.
        """
        return self.errors.copy()
