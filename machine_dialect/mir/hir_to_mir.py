"""HIR to MIR Lowering.

This module implements the translation from HIR (desugared AST) to MIR
(Three-Address Code representation).
"""


from machine_dialect.ast import (
    ActionStatement,
    Arguments,
    ASTNode,
    BlockStatement,
    BooleanLiteral,
    CallStatement,
    ConditionalExpression,
    EmptyLiteral,
    ErrorExpression,
    ErrorStatement,
    ExpressionStatement,
    FloatLiteral,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    IfStatement,
    InfixExpression,
    IntegerLiteral,
    InteractionStatement,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    Statement,
    StringLiteral,
    URLLiteral,
    UtilityStatement,
)
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.debug_info import DebugInfoBuilder
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Print,
    Return,
    Scope,
    Select,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, MIRValue, Variable
from machine_dialect.mir.ssa_construction import construct_ssa
from machine_dialect.mir.type_inference import TypeInferencer, infer_ast_expression_type


class HIRToMIRLowering:
    """Lowers HIR (desugared AST) to MIR representation."""

    def __init__(self) -> None:
        """Initialize the lowering context."""
        self.module: MIRModule | None = None
        self.current_function: MIRFunction | None = None
        self.current_block: BasicBlock | None = None
        self.variable_map: dict[str, Variable] = {}
        self.label_counter = 0
        self.type_context: dict[str, MIRType] = {}  # Track variable types
        self.debug_builder = DebugInfoBuilder()  # Debug information tracking

    def lower_program(self, program: Program, module_name: str = "main") -> MIRModule:
        """Lower a complete program to MIR.

        Args:
            program: The HIR program to lower.

        Returns:
            The MIR module.
        """
        # Desugar the AST to HIR
        hir = program.desugar()
        if not isinstance(hir, Program):
            raise TypeError("Expected Program after desugaring")

        self.module = MIRModule(module_name)

        # Separate functions from top-level statements
        functions = []
        top_level_statements = []

        for stmt in hir.statements:
            if isinstance(stmt, FunctionStatement | UtilityStatement | ActionStatement | InteractionStatement):
                functions.append(stmt)
            else:
                top_level_statements.append(stmt)

        # Process function definitions first
        for func_stmt in functions:
            self.lower_function(func_stmt)

        # If there are top-level statements, create an implicit main function
        if top_level_statements and not self.module.get_function("main"):
            self._create_implicit_main(top_level_statements)

        # Set main function if it exists
        if self.module.get_function("main"):
            self.module.set_main_function("main")

        # Apply SSA construction to all functions
        for func in self.module.functions.values():
            construct_ssa(func)

        # Apply type inference
        inferencer = TypeInferencer()
        inferencer.infer_module_types(self.module)

        return self.module

    def _create_implicit_main(self, statements: list[Statement]) -> None:
        """Create an implicit main function for top-level statements.

        Args:
            statements: The top-level statements to include in main.
        """
        # Create main function
        main = MIRFunction("main", [], MIRType.EMPTY)
        self.current_function = main

        # Create entry block
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)
        self.current_block = entry

        # Lower all top-level statements
        for stmt in statements:
            self.lower_statement(stmt)

        # Add implicit return if needed
        if not self.current_block.is_terminated():
            self.current_block.add_instruction(Return())

        # Add main function to module
        if self.module:
            self.module.add_function(main)

        # Reset context
        self.current_function = None
        self.current_block = None
        self.variable_map = {}

    def lower_statement(self, stmt: ASTNode) -> None:
        """Lower a statement to MIR.

        Args:
            stmt: The statement to lower.
        """
        if isinstance(stmt, FunctionStatement | UtilityStatement | ActionStatement | InteractionStatement):
            self.lower_function(stmt)
        elif isinstance(stmt, SetStatement):
            self.lower_set_statement(stmt)
        elif isinstance(stmt, IfStatement):
            self.lower_if_statement(stmt)
        elif isinstance(stmt, ReturnStatement):
            self.lower_return_statement(stmt)
        elif isinstance(stmt, CallStatement):
            self.lower_call_statement(stmt)
        elif isinstance(stmt, SayStatement):
            self.lower_say_statement(stmt)
        elif isinstance(stmt, BlockStatement):
            self.lower_block_statement(stmt)
        elif isinstance(stmt, ExpressionStatement):
            self.lower_expression_statement(stmt)
        elif isinstance(stmt, ErrorStatement):
            self.lower_error_statement(stmt)
        else:
            # Other statements can be handled as expressions
            self.lower_expression(stmt)

    def lower_function(
        self,
        func: FunctionStatement | UtilityStatement | ActionStatement | InteractionStatement,
    ) -> None:
        """Lower a function definition to MIR.

        Args:
            func: The function to lower (any type of function).
        """
        # Create parameter variables
        params = []
        for param in func.inputs:
            # Infer parameter type from default value if available
            param_type = MIRType.UNKNOWN
            if isinstance(param, Parameter):
                param_name = param.name.value if isinstance(param.name, Identifier) else str(param.name)
                # Try to infer type from default value
                if hasattr(param, "default_value") and param.default_value:
                    param_type = infer_ast_expression_type(param.default_value, self.type_context)
            else:
                param_name = str(param)

            # If still unknown, will be inferred later from usage
            var = Variable(param_name, param_type)
            params.append(var)
            self.type_context[param_name] = param_type

            # Track parameter for debugging
            self.debug_builder.track_variable(param_name, var, str(param_type), is_parameter=True)

        # Determine return type based on function type
        # UtilityStatement = Function (returns value)
        # ActionStatement = Private method (returns nothing)
        # InteractionStatement = Public method (returns nothing)
        # FunctionStatement has visibility attribute
        if isinstance(func, UtilityStatement):
            return_type = MIRType.UNKNOWN  # Functions return values
        elif isinstance(func, ActionStatement | InteractionStatement):
            return_type = MIRType.EMPTY  # Methods return nothing
        elif isinstance(func, FunctionStatement):
            return_type = MIRType.EMPTY if func.visibility != FunctionVisibility.FUNCTION else MIRType.UNKNOWN
        else:
            return_type = MIRType.UNKNOWN

        # Get function name from Identifier
        func_name = func.name.value if isinstance(func.name, Identifier) else str(func.name)

        # Create MIR function
        mir_func = MIRFunction(func_name, params, return_type)
        self.current_function = mir_func

        # Create entry block
        entry = BasicBlock("entry")
        mir_func.cfg.add_block(entry)
        mir_func.cfg.set_entry_block(entry)
        self.current_block = entry

        # Initialize parameter variables
        self.variable_map.clear()
        for var in params:
            self.variable_map[var.name] = var
            mir_func.add_local(var)

        # Lower function body
        if func.body:
            for stmt in func.body.statements:
                self.lower_statement(stmt)

        # Add implicit return if needed
        if self.current_block and not self.current_block.is_terminated():
            if return_type == MIRType.EMPTY:
                self.current_block.add_instruction(Return())
            else:
                # Return a default value
                temp = self.current_function.new_temp(return_type)
                self.current_block.add_instruction(LoadConst(temp, None))
                self.current_block.add_instruction(Return(temp))

        # Add function to module
        if self.module:
            self.module.add_function(mir_func)

        self.current_function = None
        self.current_block = None

    def lower_set_statement(self, stmt: SetStatement) -> None:
        """Lower a set statement to MIR.

        Args:
            stmt: The set statement to lower.
        """
        if not self.current_function or not self.current_block:
            return

        # Lower the value expression
        if stmt.value is not None:
            value = self.lower_expression(stmt.value)
        else:
            # This shouldn't happen but handle gracefully
            value = Constant(None, MIRType.ERROR)

        # Get or create variable
        var_name = stmt.name.value if isinstance(stmt.name, Identifier) else str(stmt.name)
        if var_name not in self.variable_map:
            # Create new variable with inferred type
            var_type = (
                value.type
                if hasattr(value, "type")
                else infer_ast_expression_type(stmt.value, self.type_context)
                if stmt.value
                else MIRType.UNKNOWN
            )
            var = Variable(var_name, var_type)
            self.variable_map[var_name] = var
            self.current_function.add_local(var)
            self.type_context[var_name] = var_type

            # Track variable for debugging
            self.debug_builder.track_variable(var_name, var, str(var_type), is_parameter=False)
        else:
            var = self.variable_map[var_name]
            # Update type context if we have better type info
            if hasattr(value, "type") and value.type != MIRType.UNKNOWN:
                self.type_context[var_name] = value.type

        # If the value is a constant, load it into a temporary first
        if isinstance(value, Constant):
            # Create a temporary variable for the constant
            temp = self.current_function.new_temp(value.type)
            self.current_block.add_instruction(LoadConst(temp, value))
            # Use the temp as the source
            value = temp

        # Store the value
        self.current_block.add_instruction(StoreVar(var, value))

    def lower_if_statement(self, stmt: IfStatement) -> None:
        """Lower an if statement to MIR.

        Args:
            stmt: The if statement to lower.
        """
        if not self.current_function or not self.current_block:
            return

        # Lower condition
        if stmt.condition is not None:
            condition = self.lower_expression(stmt.condition)
        else:
            # Should not happen - if statements always have conditions
            raise ValueError("If statement missing condition")

        # Load constant into temporary if needed
        if isinstance(condition, Constant):
            temp = self.current_function.new_temp(condition.type)
            self.current_block.add_instruction(LoadConst(temp, condition))
            condition = temp

        # Create blocks
        then_label = self.generate_label("then")
        else_label = self.generate_label("else") if stmt.alternative else None
        merge_label = self.generate_label("merge")

        then_block = BasicBlock(then_label)
        merge_block = BasicBlock(merge_label)
        self.current_function.cfg.add_block(then_block)
        self.current_function.cfg.add_block(merge_block)

        if else_label:
            else_block = BasicBlock(else_label)
            self.current_function.cfg.add_block(else_block)

            # Add conditional jump
            self.current_block.add_instruction(ConditionalJump(condition, then_label, else_label))
            self.current_function.cfg.connect(self.current_block, then_block)
            self.current_function.cfg.connect(self.current_block, else_block)
        else:
            # Jump to then block if true, otherwise to merge
            self.current_block.add_instruction(ConditionalJump(condition, then_label, merge_label))
            self.current_function.cfg.connect(self.current_block, then_block)
            self.current_function.cfg.connect(self.current_block, merge_block)

        # Lower then block
        self.current_block = then_block
        if stmt.consequence:
            for s in stmt.consequence.statements:
                self.lower_statement(s)

        # Add jump to merge if not terminated
        if not self.current_block.is_terminated():
            self.current_block.add_instruction(Jump(merge_label))
            self.current_function.cfg.connect(self.current_block, merge_block)

        # Lower else block if present
        if else_label and stmt.alternative:
            self.current_block = else_block
            for s in stmt.alternative.statements:
                self.lower_statement(s)

            # Add jump to merge if not terminated
            if not self.current_block.is_terminated():
                self.current_block.add_instruction(Jump(merge_label))
                self.current_function.cfg.connect(self.current_block, merge_block)

        # Continue with merge block
        self.current_block = merge_block

    def lower_return_statement(self, stmt: ReturnStatement) -> None:
        """Lower a return statement to MIR.

        Args:
            stmt: The return statement to lower.
        """
        if not self.current_block:
            return

        if stmt.return_value:
            value = self.lower_expression(stmt.return_value)

            # Load constant into temporary if needed
            if isinstance(value, Constant):
                if self.current_function is None:
                    raise RuntimeError("No current function context")
                temp = self.current_function.new_temp(value.type)
                self.current_block.add_instruction(LoadConst(temp, value))
                value = temp

            self.current_block.add_instruction(Return(value))
        else:
            self.current_block.add_instruction(Return())

    def lower_call_statement(self, stmt: CallStatement) -> None:
        """Lower a call statement to MIR.

        Args:
            stmt: The call statement to lower.
        """
        if not self.current_block or not self.current_function:
            return

        # Lower arguments
        args = []
        if stmt.arguments:
            if isinstance(stmt.arguments, Arguments):
                # Handle positional arguments
                if hasattr(stmt.arguments, "positional") and stmt.arguments.positional:
                    for arg in stmt.arguments.positional:
                        val = self.lower_expression(arg)
                        # Load constants into temporaries if needed
                        if isinstance(val, Constant):
                            temp = self.current_function.new_temp(val.type)
                            self.current_block.add_instruction(LoadConst(temp, val))
                            val = temp
                        args.append(val)

                # Handle named arguments - convert to positional for now
                # In a full implementation, we'd need to match these with parameter names
                if hasattr(stmt.arguments, "named") and stmt.arguments.named:
                    for _name, arg in stmt.arguments.named:
                        val = self.lower_expression(arg)
                        # Load constants into temporaries if needed
                        if isinstance(val, Constant):
                            temp = self.current_function.new_temp(val.type)
                            self.current_block.add_instruction(LoadConst(temp, val))
                            val = temp
                        args.append(val)
            else:
                # Single argument not wrapped in Arguments
                val = self.lower_expression(stmt.arguments)
                if isinstance(val, Constant):
                    temp = self.current_function.new_temp(val.type)
                    self.current_block.add_instruction(LoadConst(temp, val))
                    val = temp
                args.append(val)

        # Get function name from expression
        func_name = ""
        if isinstance(stmt.function_name, StringLiteral):
            func_name = stmt.function_name.value.strip('"').strip("'")
        elif isinstance(stmt.function_name, Identifier):
            func_name = stmt.function_name.value
        else:
            func_name = str(stmt.function_name)

        # Create function reference
        func_ref = FunctionRef(func_name)

        # Call without storing result (void call)
        self.current_block.add_instruction(Call(None, func_ref, args))

    def lower_say_statement(self, stmt: SayStatement) -> None:
        """Lower a say statement to MIR.

        Args:
            stmt: The say statement to lower.
        """
        if not self.current_block:
            return

        # Lower the expression to print
        if stmt.expression:
            value = self.lower_expression(stmt.expression)
            # Load constant into temporary if needed
            if isinstance(value, Constant):
                if self.current_function is None:
                    raise RuntimeError("No current function context")
                temp = self.current_function.new_temp(value.type)
                self.current_block.add_instruction(LoadConst(temp, value))
                value = temp
            self.current_block.add_instruction(Print(value))

    def lower_block_statement(self, stmt: BlockStatement) -> None:
        """Lower a block statement to MIR.

        Args:
            stmt: The block statement to lower.
        """
        if not self.current_block:
            return

        # Add scope begin instruction
        self.current_block.add_instruction(Scope(is_begin=True))

        # Lower all statements in the block
        for s in stmt.statements:
            self.lower_statement(s)

        # Add scope end instruction
        # Always add end scope - it's safe even if block is terminated
        if self.current_block:
            self.current_block.add_instruction(Scope(is_begin=False))

    def lower_expression_statement(self, stmt: ExpressionStatement) -> None:
        """Lower an expression statement to MIR.

        Args:
            stmt: The expression statement to lower.
        """
        if not self.current_block:
            return

        # Lower the expression and discard the result
        if stmt.expression:
            self.lower_expression(stmt.expression)
            # Result is not used, no need to store it

    def lower_error_statement(self, stmt: ErrorStatement) -> None:
        """Lower an error statement to MIR.

        Args:
            stmt: The error statement to lower.
        """
        if not self.current_block or not self.current_function:
            return

        # Generate an assert with error message
        # This will fail at runtime with the parse error
        error_msg = f"Parse error: {stmt.message}"
        false_val = Constant(False, MIRType.BOOL)
        self.current_block.add_instruction(Assert(false_val, error_msg))

    def lower_expression(self, expr: ASTNode) -> MIRValue:
        """Lower an expression to MIR.

        Args:
            expr: The expression to lower.

        Returns:
            The MIR value representing the expression result.
        """
        if not self.current_function or not self.current_block:
            return Constant(None)

        # Handle literals
        if isinstance(expr, IntegerLiteral):
            return Constant(expr.value, MIRType.INT)
        elif isinstance(expr, FloatLiteral):
            return Constant(expr.value, MIRType.FLOAT)
        elif isinstance(expr, StringLiteral):
            return Constant(expr.value, MIRType.STRING)
        elif isinstance(expr, BooleanLiteral):
            return Constant(expr.value, MIRType.BOOL)
        elif isinstance(expr, EmptyLiteral):
            return Constant(None, MIRType.EMPTY)
        elif isinstance(expr, URLLiteral):
            return Constant(expr.value, MIRType.URL)

        # Handle identifier
        elif isinstance(expr, Identifier):
            if expr.value in self.variable_map:
                var = self.variable_map[expr.value]
                # Use type from context if available
                if expr.value in self.type_context and var.type == MIRType.UNKNOWN:
                    var.type = self.type_context[expr.value]
                # Load variable into temp
                temp = self.current_function.new_temp(var.type)
                self.current_block.add_instruction(Copy(temp, var))
                return temp
            else:
                # Unknown identifier, return error value
                return Constant(None, MIRType.ERROR)

        # Handle infix expression
        elif isinstance(expr, InfixExpression):
            left = self.lower_expression(expr.left)
            if expr.right is not None:
                right = self.lower_expression(expr.right)
            else:
                raise ValueError("Infix expression missing right operand")

            # Load constants into temporaries if needed
            if isinstance(left, Constant):
                temp_left = self.current_function.new_temp(left.type)
                self.current_block.add_instruction(LoadConst(temp_left, left))
                left = temp_left

            if isinstance(right, Constant):
                temp_right = self.current_function.new_temp(right.type)
                self.current_block.add_instruction(LoadConst(temp_right, right))
                right = temp_right

            # Map AST operators to MIR operators
            # In MIR: ^ is XOR (bitwise), ** is power (arithmetic)
            mir_operator = expr.operator
            if expr.operator == "^":
                mir_operator = "**"  # Power operator in MIR

            # Get result type
            from machine_dialect.mir.mir_types import get_binary_op_result_type

            left_type = left.type if hasattr(left, "type") else infer_ast_expression_type(expr.left, self.type_context)
            right_type = (
                right.type
                if hasattr(right, "type")
                else infer_ast_expression_type(expr.right, self.type_context)
                if expr.right
                else MIRType.UNKNOWN
            )
            result_type = get_binary_op_result_type(mir_operator, left_type, right_type)

            # Create temp for result
            result = self.current_function.new_temp(result_type)
            self.current_block.add_instruction(BinaryOp(result, mir_operator, left, right))
            return result

        # Handle prefix expression
        elif isinstance(expr, PrefixExpression):
            if expr.right is not None:
                operand = self.lower_expression(expr.right)
            else:
                raise ValueError("Prefix expression missing right operand")

            # Load constant into temporary if needed
            if isinstance(operand, Constant):
                temp_operand = self.current_function.new_temp(operand.type)
                self.current_block.add_instruction(LoadConst(temp_operand, operand))
                operand = temp_operand

            # Get result type
            from machine_dialect.mir.mir_types import get_unary_op_result_type

            operand_type = (
                operand.type
                if hasattr(operand, "type")
                else infer_ast_expression_type(expr.right, self.type_context)
                if expr.right
                else MIRType.UNKNOWN
            )
            result_type = get_unary_op_result_type(expr.operator, operand_type)

            # Create temp for result
            result = self.current_function.new_temp(result_type)
            self.current_block.add_instruction(UnaryOp(result, expr.operator, operand))
            return result

        # Handle conditional expression (ternary)
        elif isinstance(expr, ConditionalExpression):
            if expr.condition is None or expr.consequence is None or expr.alternative is None:
                raise ValueError("Conditional expression missing required parts")

            # Lower condition
            condition = self.lower_expression(expr.condition)

            # Lower both branches
            true_val = self.lower_expression(expr.consequence)
            false_val = self.lower_expression(expr.alternative)

            # Load constants into temporaries if needed
            if isinstance(condition, Constant):
                temp_cond = self.current_function.new_temp(condition.type)
                self.current_block.add_instruction(LoadConst(temp_cond, condition))
                condition = temp_cond

            if isinstance(true_val, Constant):
                temp_true = self.current_function.new_temp(true_val.type)
                self.current_block.add_instruction(LoadConst(temp_true, true_val))
                true_val = temp_true

            if isinstance(false_val, Constant):
                temp_false = self.current_function.new_temp(false_val.type)
                self.current_block.add_instruction(LoadConst(temp_false, false_val))
                false_val = temp_false

            # Get result type (should be the same for both branches)
            result_type = true_val.type if hasattr(true_val, "type") else MIRType.UNKNOWN

            # Create temp for result
            result = self.current_function.new_temp(result_type)

            # Use Select instruction for conditional expression
            self.current_block.add_instruction(Select(result, condition, true_val, false_val))
            return result

        # Handle error expression
        elif isinstance(expr, ErrorExpression):
            # Generate an assert for error expressions
            error_msg = f"Expression error: {expr.message}"
            false_val = Constant(False, MIRType.BOOL)
            # Load constant into temporary
            temp_false = self.current_function.new_temp(false_val.type)
            self.current_block.add_instruction(LoadConst(temp_false, false_val))
            self.current_block.add_instruction(Assert(temp_false, error_msg))
            # Return error value
            return Constant(None, MIRType.ERROR)

        # Handle call expression (not available in AST, using CallStatement instead)
        # This would need to be refactored if we have call expressions
        elif hasattr(expr, "function_name"):  # Check if it's a call-like expression
            # Lower arguments
            args = []
            if hasattr(expr, "arguments"):
                arguments = expr.arguments
                if isinstance(arguments, Arguments):
                    if hasattr(arguments, "positional"):
                        for arg in arguments.positional:
                            val = self.lower_expression(arg)
                            # Load constants into temporaries if needed
                            if isinstance(val, Constant):
                                temp = self.current_function.new_temp(val.type)
                                self.current_block.add_instruction(LoadConst(temp, val))
                                val = temp
                            args.append(val)

            # Get function name
            func_name = getattr(expr, "function_name", "unknown")
            func_ref = FunctionRef(func_name)

            # Create temp for result
            result = self.current_function.new_temp(MIRType.UNKNOWN)
            self.current_block.add_instruction(Call(result, func_ref, args))
            return result

        # Default: return error value
        return Constant(None, MIRType.ERROR)

    def generate_label(self, prefix: str = "L") -> str:
        """Generate a unique label.

        Args:
            prefix: Label prefix.

        Returns:
            A unique label.
        """
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label


def lower_to_mir(program: Program, module_name: str = "main") -> MIRModule:
    """Lower a program to MIR.

    Args:
        program: The program to lower.
        module_name: Name for the MIR module.

    Returns:
        The MIR module.
    """
    lowerer = HIRToMIRLowering()
    return lowerer.lower_program(program, module_name)
