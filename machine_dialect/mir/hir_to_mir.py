"""HIR to MIR Lowering.

This module implements the translation from HIR (desugared AST) to MIR
(Three-Address Code representation).
"""


from machine_dialect.ast import (
    Arguments,
    ASTNode,
    BooleanLiteral,
    CallStatement,
    EmptyLiteral,
    FloatLiteral,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    IfStatement,
    InfixExpression,
    IntegerLiteral,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SetStatement,
    StringLiteral,
    URLLiteral,
)
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, MIRValue, Variable


class HIRToMIRLowering:
    """Lowers HIR (desugared AST) to MIR representation."""

    def __init__(self) -> None:
        """Initialize the lowering context."""
        self.module: MIRModule | None = None
        self.current_function: MIRFunction | None = None
        self.current_block: BasicBlock | None = None
        self.variable_map: dict[str, Variable] = {}
        self.label_counter = 0

    def lower_program(self, program: Program) -> MIRModule:
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

        self.module = MIRModule("main")  # Default module name

        # Process all statements
        for stmt in hir.statements:
            self.lower_statement(stmt)

        # Set main function if it exists
        if self.module.get_function("main"):
            self.module.set_main_function("main")

        return self.module

    def lower_statement(self, stmt: ASTNode) -> None:
        """Lower a statement to MIR.

        Args:
            stmt: The statement to lower.
        """
        if isinstance(stmt, FunctionStatement):
            self.lower_function(stmt)
        elif isinstance(stmt, SetStatement):
            self.lower_set_statement(stmt)
        elif isinstance(stmt, IfStatement):
            self.lower_if_statement(stmt)
        elif isinstance(stmt, ReturnStatement):
            self.lower_return_statement(stmt)
        elif isinstance(stmt, CallStatement):
            self.lower_call_statement(stmt)
        else:
            # Other statements can be handled as expressions
            self.lower_expression(stmt)

    def lower_function(self, func: FunctionStatement) -> None:
        """Lower a function definition to MIR.

        Args:
            func: The function to lower.
        """
        # Create parameter variables
        params = []
        for param in func.inputs:
            # Infer parameter type (in a real implementation, we'd have type annotations)
            param_type = MIRType.UNKNOWN
            # Extract name from Parameter's name attribute (which is an Identifier)
            if isinstance(param, Parameter):
                param_name = param.name.value if isinstance(param.name, Identifier) else str(param.name)
            else:
                param_name = str(param)
            var = Variable(param_name, param_type)
            params.append(var)

        # Determine return type based on visibility
        return_type = MIRType.EMPTY if func.visibility != FunctionVisibility.FUNCTION else MIRType.UNKNOWN

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
            # Create new variable
            var_type = value.type if hasattr(value, "type") else MIRType.UNKNOWN
            var = Variable(var_name, var_type)
            self.variable_map[var_name] = var
            self.current_function.add_local(var)
        else:
            var = self.variable_map[var_name]

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
            self.current_block.add_instruction(Return(value))
        else:
            self.current_block.add_instruction(Return())

    def lower_call_statement(self, stmt: CallStatement) -> None:
        """Lower a call statement to MIR.

        Args:
            stmt: The call statement to lower.
        """
        if not self.current_block:
            return

        # Lower arguments
        args = []
        if stmt.arguments and isinstance(stmt.arguments, Arguments):
            # Handle positional arguments
            if hasattr(stmt.arguments, "positional"):
                for arg in stmt.arguments.positional:
                    args.append(self.lower_expression(arg))
            # Handle named arguments if any
            if hasattr(stmt.arguments, "named"):
                for _name, arg in stmt.arguments.named:
                    args.append(self.lower_expression(arg))

        # Get function name from expression
        func_name = ""
        if isinstance(stmt.function_name, StringLiteral):
            func_name = stmt.function_name.value.strip('"')
        elif isinstance(stmt.function_name, Identifier):
            func_name = stmt.function_name.value
        else:
            func_name = str(stmt.function_name)

        # Create function reference
        func_ref = FunctionRef(func_name)

        # Call without storing result (void call)
        self.current_block.add_instruction(Call(None, func_ref, args))

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

            # Get result type
            from machine_dialect.mir.mir_types import get_binary_op_result_type

            left_type = left.type if hasattr(left, "type") else MIRType.UNKNOWN
            right_type = right.type if hasattr(right, "type") else MIRType.UNKNOWN
            result_type = get_binary_op_result_type(expr.operator, left_type, right_type)

            # Create temp for result
            result = self.current_function.new_temp(result_type)
            self.current_block.add_instruction(BinaryOp(result, expr.operator, left, right))
            return result

        # Handle prefix expression
        elif isinstance(expr, PrefixExpression):
            if expr.right is not None:
                operand = self.lower_expression(expr.right)
            else:
                raise ValueError("Prefix expression missing right operand")

            # Get result type
            from machine_dialect.mir.mir_types import get_unary_op_result_type

            operand_type = operand.type if hasattr(operand, "type") else MIRType.UNKNOWN
            result_type = get_unary_op_result_type(expr.operator, operand_type)

            # Create temp for result
            result = self.current_function.new_temp(result_type)
            self.current_block.add_instruction(UnaryOp(result, expr.operator, operand))
            return result

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
                            args.append(self.lower_expression(arg))

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


def lower_to_mir(program: Program) -> MIRModule:
    """Lower a program to MIR.

    Args:
        program: The program to lower.

    Returns:
        The MIR module.
    """
    lowerer = HIRToMIRLowering()
    return lowerer.lower_program(program)
