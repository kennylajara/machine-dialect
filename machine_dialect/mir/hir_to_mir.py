"""HIR to MIR Lowering.

This module implements the translation from HIR (desugared AST) to MIR
(Three-Address Code representation).
"""

from machine_dialect.ast import (
    ActionStatement,
    Arguments,
    ASTNode,
    BlockStatement,
    CallStatement,
    CollectionAccessExpression,
    CollectionMutationStatement,
    ConditionalExpression,
    DefineStatement,
    EmptyLiteral,
    ErrorExpression,
    ErrorStatement,
    Expression,
    ExpressionStatement,
    FloatLiteral,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    IfStatement,
    InfixExpression,
    InteractionStatement,
    NamedListLiteral,
    OrderedListLiteral,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    Statement,
    StringLiteral,
    UnorderedListLiteral,
    URLLiteral,
    UtilityStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.debug_info import DebugInfoBuilder
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    ArrayAppend,
    ArrayCreate,
    ArrayGet,
    ArrayLength,
    ArraySet,
    Assert,
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    MIRInstruction,
    Pop,
    Print,
    Return,
    Scope,
    Select,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType, MIRUnionType, ast_type_to_mir_type
from machine_dialect.mir.mir_values import (
    Constant,
    FunctionRef,
    MIRValue,
    ScopedVariable,
    Temp,
    Variable,
    VariableScope,
)
from machine_dialect.mir.ssa_construction import construct_ssa
from machine_dialect.mir.type_inference import TypeInferencer, infer_ast_expression_type


class HIRToMIRLowering:
    """Lowers HIR (desugared AST) to MIR representation."""

    def __init__(self) -> None:
        """Initialize the lowering context."""
        self.module: MIRModule | None = None
        self.current_function: MIRFunction | None = None
        self.current_block: BasicBlock | None = None
        self.variable_map: dict[str, Variable | ScopedVariable] = {}
        self.label_counter = 0
        self.type_context: dict[str, MIRType | MIRUnionType] = {}  # Track variable types
        self.union_type_context: dict[str, MIRUnionType] = {}  # Track union types separately
        self.debug_builder = DebugInfoBuilder()  # Debug information tracking

    def _add_instruction(self, instruction: "MIRInstruction", ast_node: ASTNode) -> None:
        """Add an instruction to the current block with source location.

        Args:
            instruction: The MIR instruction to add.
            ast_node: The AST node to extract location from (required).
        """
        location = ast_node.get_source_location()
        if location is None:
            # If the node doesn't have location info, raise an error
            # This forces all nodes to have proper location tracking
            raise ValueError(f"AST node {type(ast_node).__name__} missing source location")
        instruction.source_location = location
        if self.current_block is not None:
            self.current_block.add_instruction(instruction)

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
        last_stmt = None
        for stmt in statements:
            self.lower_statement(stmt)
            last_stmt = stmt

        # Add implicit return if needed
        if not self.current_block.is_terminated():
            # For implicit returns, we need a source location
            # Use the location from the last statement
            if last_stmt is None:
                raise ValueError("Cannot create implicit return without any statements")
            source_loc = last_stmt.get_source_location()
            if source_loc is None:
                raise ValueError("Last statement missing source location for implicit return")
            return_inst = Return(source_loc)
            return_inst.source_location = source_loc
            if self.current_block is not None:
                self.current_block.add_instruction(return_inst)

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
        elif isinstance(stmt, DefineStatement):
            self._convert_define_statement(stmt)
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
        elif isinstance(stmt, CollectionMutationStatement):
            self.lower_collection_mutation(stmt)
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
        params: list[Variable | ScopedVariable] = []
        for param in func.inputs:
            # Infer parameter type from default value if available
            param_type: MIRType | MIRUnionType = MIRType.UNKNOWN
            if isinstance(param, Parameter):
                param_name = param.name.value if isinstance(param.name, Identifier) else str(param.name)
                # Try to infer type from default value
                if hasattr(param, "default_value") and param.default_value:
                    param_type = infer_ast_expression_type(param.default_value, self.type_context)
            else:
                param_name = str(param)

            # If still unknown, will be inferred later from usage
            # Parameters are always scoped as PARAMETER
            var = ScopedVariable(param_name, VariableScope.PARAMETER, param_type)
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
        param_var: Variable | ScopedVariable
        for param_var in params:
            self.variable_map[param_var.name] = param_var
            mir_func.add_local(param_var)

        # Lower function body
        last_stmt = None
        if func.body:
            for stmt in func.body.statements:
                self.lower_statement(stmt)
                last_stmt = stmt

        # Add implicit return if needed
        if self.current_block and not self.current_block.is_terminated():
            # Use function's source location for implicit return
            source_loc = func.get_source_location()
            if source_loc is None:
                # If function has no location, try to use last statement's location
                if last_stmt:
                    source_loc = last_stmt.get_source_location()
                if source_loc is None:
                    raise ValueError(f"Function {func_name} missing source location for implicit return")

            if return_type == MIRType.EMPTY:
                return_inst = Return(source_loc)
                return_inst.source_location = source_loc
                if self.current_block is not None:
                    self.current_block.add_instruction(return_inst)
            else:
                # Return a default value
                temp = self.current_function.new_temp(return_type)
                load_inst = LoadConst(temp, None, source_loc)
                if self.current_block is not None:
                    self.current_block.add_instruction(load_inst)
                return_inst = Return(source_loc, temp)
                return_inst.source_location = source_loc
                if self.current_block is not None:
                    self.current_block.add_instruction(return_inst)

        # Add function to module
        if self.module:
            self.module.add_function(mir_func)

        self.current_function = None
        self.current_block = None

    def lower_set_statement(self, stmt: SetStatement) -> None:
        """Lower a set statement to MIR with enhanced type tracking.

        Args:
            stmt: The set statement to lower.
        """
        if not self.current_function or not self.current_block:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("SetStatement missing source location")

        # Lower the value expression
        if stmt.value is not None:
            value = self.lower_expression(stmt.value)
        else:
            # This shouldn't happen but handle gracefully
            value = Constant(None, MIRType.ERROR)

        # Get or create variable
        var_name = stmt.name.value if isinstance(stmt.name, Identifier) else str(stmt.name)
        var: Variable | ScopedVariable
        if var_name not in self.variable_map:
            # Variable wasn't defined - this should be caught by semantic analysis
            # Create with inferred type for error recovery
            var_type = (
                value.type
                if hasattr(value, "type")
                else infer_ast_expression_type(stmt.value, self.type_context)
                if stmt.value
                else MIRType.UNKNOWN
            )

            # Check if we're inside a function (not main)
            if self.current_function and self.current_function.name != "main":
                # Check if this is a parameter
                is_param = any(p.name == var_name for p in self.current_function.params)
                if is_param:
                    # This shouldn't happen - parameters should already be in variable_map
                    var = ScopedVariable(var_name, VariableScope.PARAMETER, var_type)
                else:
                    # This is a function-local variable
                    var = ScopedVariable(var_name, VariableScope.LOCAL, var_type)
            else:
                # This is a global variable (module-level)
                var = ScopedVariable(var_name, VariableScope.GLOBAL, var_type)

            self.variable_map[var_name] = var
            self.current_function.add_local(var)
            self.type_context[var_name] = var_type

            # Track variable for debugging
            self.debug_builder.track_variable(var_name, var, str(var_type), is_parameter=False)
        else:
            var = self.variable_map[var_name]

            # For union types, track the actual runtime type being assigned
            if var_name in self.union_type_context:
                if hasattr(value, "type") and value.type != MIRType.UNKNOWN:
                    # This assignment narrows the type for flow-sensitive analysis
                    # Store this info for optimization passes
                    if hasattr(var, "runtime_type"):
                        var.runtime_type = value.type
            else:
                # Update type context if we have better type info
                if hasattr(value, "type") and value.type != MIRType.UNKNOWN:
                    self.type_context[var_name] = value.type

        # If the value is a constant, load it into a temporary first
        if isinstance(value, Constant):
            # Create a temporary variable for the constant
            temp = self.current_function.new_temp(value.type)
            self._add_instruction(LoadConst(temp, value, source_loc), stmt)
            # Use the temp as the source
            value = temp

        # Store the value
        self._add_instruction(StoreVar(var, value, source_loc), stmt)

    def _convert_define_statement(self, stmt: DefineStatement) -> None:
        """Convert DefineStatement to MIR with enhanced type tracking.

        Args:
            stmt: DefineStatement from HIR
        """
        if not self.current_function:
            return

        var_name = stmt.name.value if isinstance(stmt.name, Identifier) else str(stmt.name)

        # Convert type specification to MIR type
        mir_type = ast_type_to_mir_type(stmt.type_spec)

        # Create typed variable in MIR
        # Check if we're inside a function (not main) to determine scope
        if self.current_function and self.current_function.name != "main":
            # This is a function-local variable
            scope = VariableScope.LOCAL
        else:
            # This is a global variable (module-level)
            scope = VariableScope.GLOBAL

        if isinstance(mir_type, MIRUnionType):
            # For union types, track both the union and create a variable with UNKNOWN type
            # The actual type will be refined during type inference and optimization
            var = ScopedVariable(var_name, scope, MIRType.UNKNOWN)

            # Store the union type information separately for optimization passes
            self.union_type_context[var_name] = mir_type
            self.type_context[var_name] = MIRType.UNKNOWN

            # Add metadata to the variable for optimization passes
            var.union_type = mir_type
        else:
            # Single type - use it directly
            var = ScopedVariable(var_name, scope, mir_type)
            self.type_context[var_name] = mir_type

        # Register in variable map with type
        self.variable_map[var_name] = var

        # Add to function locals
        self.current_function.add_local(var)

        # Track variable for debugging with full type information
        self.debug_builder.track_variable(var_name, var, str(mir_type), is_parameter=False)

        # If there's an initial value (shouldn't happen after HIR desugaring but handle it)
        if stmt.initial_value:
            # This case shouldn't occur as HIR desugars default values
            # But handle it for completeness
            if self.current_block:
                source_loc = stmt.get_source_location()
                if source_loc is None:
                    raise ValueError("DefineStatement missing source location")

                value = self.lower_expression(stmt.initial_value)

                # If the value is a constant, load it into a temporary first
                if isinstance(value, Constant):
                    temp = self.current_function.new_temp(value.type)
                    self._add_instruction(LoadConst(temp, value, source_loc), stmt)
                    value = temp

                # Store the value
                self._add_instruction(StoreVar(var, value, source_loc), stmt)

    def lower_if_statement(self, stmt: IfStatement) -> None:
        """Lower an if statement to MIR.

        Args:
            stmt: The if statement to lower.
        """
        if not self.current_function or not self.current_block:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("IfStatement missing source location")

        # Lower condition
        if stmt.condition is not None:
            condition = self.lower_expression(stmt.condition)
        else:
            # Should not happen - if statements always have conditions
            raise ValueError("If statement missing condition")

        # Load constant into temporary if needed
        if isinstance(condition, Constant):
            temp = self.current_function.new_temp(condition.type)
            self._add_instruction(LoadConst(temp, condition, source_loc), stmt)
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
            self._add_instruction(ConditionalJump(condition, then_label, source_loc, else_label), stmt)
            self.current_function.cfg.connect(self.current_block, then_block)
            self.current_function.cfg.connect(self.current_block, else_block)
        else:
            # Jump to then block if true, otherwise to merge
            self._add_instruction(ConditionalJump(condition, then_label, source_loc, merge_label), stmt)
            self.current_function.cfg.connect(self.current_block, then_block)
            self.current_function.cfg.connect(self.current_block, merge_block)

        # Lower then block
        self.current_block = then_block
        if stmt.consequence:
            for s in stmt.consequence.statements:
                self.lower_statement(s)

        # Add jump to merge if not terminated
        if not self.current_block.is_terminated():
            self._add_instruction(Jump(merge_label, source_loc), stmt)
            self.current_function.cfg.connect(self.current_block, merge_block)

        # Lower else block if present
        if else_label and stmt.alternative:
            self.current_block = else_block
            for s in stmt.alternative.statements:
                self.lower_statement(s)

            # Add jump to merge if not terminated
            if not self.current_block.is_terminated():
                self._add_instruction(Jump(merge_label, source_loc), stmt)
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

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("ReturnStatement missing source location")

        if stmt.return_value:
            value = self.lower_expression(stmt.return_value)

            # Load constant into temporary if needed
            if isinstance(value, Constant):
                if self.current_function is None:
                    raise RuntimeError("No current function context")
                temp = self.current_function.new_temp(value.type)
                self._add_instruction(LoadConst(temp, value, source_loc), stmt)
                value = temp

            self._add_instruction(Return(source_loc, value), stmt)
        else:
            self._add_instruction(Return(source_loc), stmt)

    def lower_call_statement(self, stmt: CallStatement) -> None:
        """Lower a call statement to MIR.

        Args:
            stmt: The call statement to lower.
        """
        if not self.current_block or not self.current_function:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("CallStatement missing source location")

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
                            self._add_instruction(LoadConst(temp, val, source_loc), stmt)
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
                            self._add_instruction(LoadConst(temp, val, source_loc), stmt)
                            val = temp
                        args.append(val)
            else:
                # Single argument not wrapped in Arguments
                val = self.lower_expression(stmt.arguments)
                if isinstance(val, Constant):
                    temp = self.current_function.new_temp(val.type)
                    self._add_instruction(LoadConst(temp, val, source_loc), stmt)
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
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("CallStatement missing source location")
        call_inst = Call(None, func_ref, args, source_loc)
        self._add_instruction(call_inst, stmt)

    def lower_say_statement(self, stmt: SayStatement) -> None:
        """Lower a say statement to MIR.

        Args:
            stmt: The say statement to lower.
        """
        if not self.current_block:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("SayStatement missing source location")

        # Lower the expression to print
        if stmt.expression:
            value = self.lower_expression(stmt.expression)
            # Load constant into temporary if needed
            if isinstance(value, Constant):
                if self.current_function is None:
                    raise RuntimeError("No current function context")
                temp = self.current_function.new_temp(value.type)
                self._add_instruction(LoadConst(temp, value, source_loc), stmt)
                value = temp
            self._add_instruction(Print(value, source_loc), stmt)

    def lower_collection_mutation(self, stmt: CollectionMutationStatement) -> None:
        """Lower a collection mutation statement to MIR.

        Handles operations like:
        - Add _value_ to list
        - Remove _value_ from list
        - Set the second item of list to _value_
        - Insert _value_ at position _3_ in list
        - Empty list

        Args:
            stmt: The collection mutation statement to lower.
        """
        if not self.current_block or not self.current_function:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            source_loc = (1, 1)

        # Lower the collection expression
        collection = self.lower_expression(stmt.collection)

        # Ensure collection is loaded into a temp if it's a variable
        if isinstance(collection, Variable):
            temp_collection = self.current_function.new_temp(collection.type)
            self._add_instruction(Copy(temp_collection, collection, source_loc), stmt)
            collection = temp_collection

        # Handle different operations
        if stmt.operation == "add":
            # Add operation: append to array
            if stmt.value:
                value = self.lower_expression(stmt.value)

                # Load constant into temp if needed
                if isinstance(value, Constant):
                    temp_value = self.current_function.new_temp(value.type)
                    self._add_instruction(LoadConst(temp_value, value, source_loc), stmt)
                    value = temp_value

                # Use ArrayAppend instruction
                self._add_instruction(ArrayAppend(collection, value, source_loc), stmt)

        elif stmt.operation == "set":
            # Set operation: array[index] = value
            if stmt.value and stmt.position is not None:
                value = self.lower_expression(stmt.value)

                # Load value constant into temp if needed
                if isinstance(value, Constant):
                    temp_value = self.current_function.new_temp(value.type)
                    self._add_instruction(LoadConst(temp_value, value, source_loc), stmt)
                    value = temp_value

                # Handle position (already converted to 0-based in HIR)
                if isinstance(stmt.position, int):
                    index = Constant(stmt.position, MIRType.INT)
                    temp_index = self.current_function.new_temp(MIRType.INT)
                    self._add_instruction(LoadConst(temp_index, index, source_loc), stmt)
                elif isinstance(stmt.position, str) and stmt.position == "last":
                    # Special case for "last" - get array length - 1
                    length_temp = self.current_function.new_temp(MIRType.INT)
                    self._add_instruction(ArrayLength(length_temp, collection, source_loc), stmt)

                    # Subtract 1
                    one = Constant(1, MIRType.INT)
                    temp_one = self.current_function.new_temp(MIRType.INT)
                    self._add_instruction(LoadConst(temp_one, one, source_loc), stmt)

                    temp_index = self.current_function.new_temp(MIRType.INT)
                    self._add_instruction(BinaryOp(temp_index, "-", length_temp, temp_one, source_loc), stmt)
                else:
                    # Expression for index
                    if isinstance(stmt.position, Expression):
                        index_value = self.lower_expression(stmt.position)
                        if isinstance(index_value, Constant):
                            temp_index = self.current_function.new_temp(MIRType.INT)
                            self._add_instruction(LoadConst(temp_index, index_value, source_loc), stmt)
                        elif isinstance(index_value, Temp):
                            temp_index = index_value
                        else:
                            # Handle other MIRValue types - shouldn't happen but be safe
                            temp_index = self.current_function.new_temp(MIRType.INT)
                            self._add_instruction(Copy(temp_index, index_value, source_loc), stmt)
                    else:
                        # This shouldn't happen if HIR is correct, but handle gracefully
                        temp_index = self.current_function.new_temp(MIRType.INT)
                        self._add_instruction(LoadConst(temp_index, Constant(0, MIRType.INT), source_loc), stmt)

                # Perform the array set
                self._add_instruction(ArraySet(collection, temp_index, value, source_loc), stmt)

        elif stmt.operation == "remove":
            # Remove operation: need to find and remove element
            # This is more complex - would need to:
            # 1. Find the element's index
            # 2. Shift remaining elements
            # 3. Decrease array size
            # For now, we'll leave this as a TODO
            pass

        elif stmt.operation == "insert":
            # Insert operation: insert at specific position
            # This would need to:
            # 1. Shift elements from position onwards
            # 2. Set the value at position
            # 3. Increase array size
            # For now, we'll leave this as a TODO
            pass

        elif stmt.operation == "empty":
            # Empty operation: clear the array
            # This would reset the array to size 0
            # For now, we'll leave this as a TODO
            pass

    def lower_block_statement(self, stmt: BlockStatement) -> None:
        """Lower a block statement to MIR.

        Args:
            stmt: The block statement to lower.
        """
        if not self.current_block:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("BlockStatement missing source location")

        # Add scope begin instruction
        self._add_instruction(Scope(source_loc, is_begin=True), stmt)

        # Lower all statements in the block
        for s in stmt.statements:
            self.lower_statement(s)

        # Add scope end instruction
        # Always add end scope - it's safe even if block is terminated
        if self.current_block:
            self._add_instruction(Scope(source_loc, is_begin=False), stmt)

    def lower_expression_statement(self, stmt: ExpressionStatement) -> None:
        """Lower an expression statement to MIR.

        Args:
            stmt: The expression statement to lower.
        """
        if not self.current_block:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("ExpressionStatement missing source location")

        # Lower the expression and discard the result
        if stmt.expression:
            result = self.lower_expression(stmt.expression)
            # Generate a Pop instruction to discard the unused result
            if result is not None:
                self._add_instruction(Pop(result, source_loc), stmt)

    def lower_error_statement(self, stmt: ErrorStatement) -> None:
        """Lower an error statement to MIR.

        Args:
            stmt: The error statement to lower.
        """
        if not self.current_block or not self.current_function:
            return

        # Get source location from the statement
        source_loc = stmt.get_source_location()
        if source_loc is None:
            raise ValueError("ErrorStatement missing source location")

        # Generate an assert with error message
        # This will fail at runtime with the parse error
        error_msg = f"Parse error: {stmt.message}"
        false_val = Constant(False, MIRType.BOOL)
        self._add_instruction(Assert(false_val, source_loc, error_msg), stmt)

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
        if isinstance(expr, WholeNumberLiteral):
            return Constant(expr.value, MIRType.INT)
        elif isinstance(expr, FloatLiteral):
            return Constant(expr.value, MIRType.FLOAT)
        elif isinstance(expr, StringLiteral):
            return Constant(expr.value, MIRType.STRING)
        elif isinstance(expr, YesNoLiteral):
            return Constant(expr.value, MIRType.BOOL)
        elif isinstance(expr, EmptyLiteral):
            return Constant(None, MIRType.EMPTY)
        elif isinstance(expr, URLLiteral):
            return Constant(expr.value, MIRType.URL)

        # Handle list literals
        elif isinstance(expr, UnorderedListLiteral | OrderedListLiteral):
            # Get source location
            source_loc = expr.get_source_location()
            if source_loc is None:
                source_loc = (1, 1)

            # Create array with size
            size = Constant(len(expr.elements), MIRType.INT)
            # Load size constant into register for proper constant pool usage
            temp_size = self.current_function.new_temp(MIRType.INT)
            self._add_instruction(LoadConst(temp_size, size, source_loc), expr)

            array_var = self.current_function.new_temp(MIRType.ARRAY)
            self._add_instruction(ArrayCreate(array_var, temp_size, source_loc), expr)

            # Add elements to array
            for i, element in enumerate(expr.elements):
                elem_value = self.lower_expression(element)

                # Load constant values into registers for proper constant pool usage
                if isinstance(elem_value, Constant):
                    temp_elem = self.current_function.new_temp(elem_value.type)
                    self._add_instruction(LoadConst(temp_elem, elem_value, source_loc), expr)
                    elem_value = temp_elem

                # Create index value
                index = Constant(i, MIRType.INT)
                # Load index constant into register too
                temp_index = self.current_function.new_temp(MIRType.INT)
                self._add_instruction(LoadConst(temp_index, index, source_loc), expr)

                self._add_instruction(ArraySet(array_var, temp_index, elem_value, source_loc), expr)

            return array_var

        elif isinstance(expr, NamedListLiteral):
            # For named lists (dictionaries), we'd need dict operations
            # For now, just create an empty array as placeholder
            source_loc = expr.get_source_location()
            if source_loc is None:
                source_loc = (1, 1)

            # TODO: Implement dictionary operations
            size = Constant(0, MIRType.INT)
            # Load size constant into register for proper constant pool usage
            temp_size = self.current_function.new_temp(MIRType.INT)
            self._add_instruction(LoadConst(temp_size, size, source_loc), expr)

            dict_var = self.current_function.new_temp(MIRType.DICT)
            self._add_instruction(ArrayCreate(dict_var, temp_size, source_loc), expr)
            return dict_var

        # Handle collection access
        elif isinstance(expr, CollectionAccessExpression):
            source_loc = expr.get_source_location()
            if source_loc is None:
                source_loc = (1, 1)

            # Lower the collection
            collection = self.lower_expression(expr.collection)

            # Ensure collection is in a temp register
            if isinstance(collection, Constant):
                temp_collection = self.current_function.new_temp(MIRType.ARRAY)
                self._add_instruction(LoadConst(temp_collection, collection, source_loc), expr)
                collection = temp_collection

            # Handle index based on access type
            if expr.access_type == "numeric":
                # Numeric index (already 0-based from HIR)
                if isinstance(expr.accessor, int):
                    index = Constant(expr.accessor, MIRType.INT)
                    temp_index = self.current_function.new_temp(MIRType.INT)
                    self._add_instruction(LoadConst(temp_index, index, source_loc), expr)
                else:
                    # Expression for index
                    if isinstance(expr.accessor, Expression):
                        index_value = self.lower_expression(expr.accessor)
                        if isinstance(index_value, Constant):
                            temp_index = self.current_function.new_temp(MIRType.INT)
                            self._add_instruction(LoadConst(temp_index, index_value, source_loc), expr)
                        elif isinstance(index_value, Temp):
                            temp_index = index_value
                        else:
                            # Handle other MIRValue types
                            temp_index = self.current_function.new_temp(MIRType.INT)
                            self._add_instruction(Copy(temp_index, index_value, source_loc), expr)
                    else:
                        # This shouldn't happen, but handle gracefully
                        temp_index = self.current_function.new_temp(MIRType.INT)
                        self._add_instruction(LoadConst(temp_index, Constant(0, MIRType.INT), source_loc), expr)
            elif expr.access_type == "ordinal" and expr.accessor == "last":
                # Special case for "last"
                length_temp = self.current_function.new_temp(MIRType.INT)
                self._add_instruction(ArrayLength(length_temp, collection, source_loc), expr)

                # Subtract 1
                one = Constant(1, MIRType.INT)
                temp_one = self.current_function.new_temp(MIRType.INT)
                self._add_instruction(LoadConst(temp_one, one, source_loc), expr)

                temp_index = self.current_function.new_temp(MIRType.INT)
                self._add_instruction(BinaryOp(temp_index, "-", length_temp, temp_one, source_loc), expr)
            else:
                # Other access types - not yet supported
                return Constant(None, MIRType.ERROR)

            # Perform the array get
            result = self.current_function.new_temp(MIRType.UNKNOWN)
            self._add_instruction(ArrayGet(result, collection, temp_index, source_loc), expr)
            return result

        # Handle identifier
        elif isinstance(expr, Identifier):
            if expr.value in self.variable_map:
                var = self.variable_map[expr.value]
                # Use type from context if available
                if expr.value in self.type_context and var.type == MIRType.UNKNOWN:
                    var.type = self.type_context[expr.value]
                # Load variable into temp
                temp = self.current_function.new_temp(var.type)
                self._add_instruction(Copy(temp, var, expr.get_source_location() or (1, 1)), expr)
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
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("InfixExpression missing source location")
                self._add_instruction(LoadConst(temp_left, left, source_loc), expr)
                left = temp_left

            if isinstance(right, Constant):
                temp_right = self.current_function.new_temp(right.type)
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("InfixExpression missing source location")
                self._add_instruction(LoadConst(temp_right, right, source_loc), expr)
                right = temp_right

            # Map AST operators to MIR operators
            # AST uses ^ for power, but MIR/bytecode use ** for power and ^ for XOR
            mir_operator = expr.operator
            if expr.operator == "^":
                mir_operator = "**"  # In AST, ^ means power; convert to ** for MIR

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
            source_loc = expr.get_source_location()
            if source_loc is None:
                raise ValueError("InfixExpression missing source location")
            self._add_instruction(BinaryOp(result, mir_operator, left, right, source_loc), expr)
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
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("PrefixExpression missing source location")
                self._add_instruction(LoadConst(temp_operand, operand, source_loc), expr)
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
            source_loc = expr.get_source_location()
            if source_loc is None:
                raise ValueError("PrefixExpression missing source location")
            self._add_instruction(UnaryOp(result, expr.operator, operand, source_loc), expr)
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
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("ConditionalExpression missing source location")
                self._add_instruction(LoadConst(temp_cond, condition, source_loc), expr)
                condition = temp_cond

            if isinstance(true_val, Constant):
                temp_true = self.current_function.new_temp(true_val.type)
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("ConditionalExpression missing source location")
                self._add_instruction(LoadConst(temp_true, true_val, source_loc), expr)
                true_val = temp_true

            if isinstance(false_val, Constant):
                temp_false = self.current_function.new_temp(false_val.type)
                source_loc = expr.get_source_location()
                if source_loc is None:
                    raise ValueError("ConditionalExpression missing source location")
                self._add_instruction(LoadConst(temp_false, false_val, source_loc), expr)
                false_val = temp_false

            # Get result type (should be the same for both branches)
            result_type = true_val.type if hasattr(true_val, "type") else MIRType.UNKNOWN

            # Create temp for result
            result = self.current_function.new_temp(result_type)

            # Use Select instruction for conditional expression
            source_loc = expr.get_source_location()
            if source_loc is None:
                raise ValueError("ConditionalExpression missing source location")
            self._add_instruction(Select(result, condition, true_val, false_val, source_loc), expr)
            return result

        # Handle error expression
        elif isinstance(expr, ErrorExpression):
            # Generate an assert for error expressions with position information
            # ErrorExpression MUST have a token with position info
            error_msg = f"line {expr.token.line}, column {expr.token.position}: Expression error: {expr.message}"
            false_val = Constant(False, MIRType.BOOL)
            # Load constant into temporary
            temp_false = self.current_function.new_temp(false_val.type)
            source_loc = (expr.token.line, expr.token.position)
            self._add_instruction(LoadConst(temp_false, false_val, source_loc), expr)
            self._add_instruction(Assert(temp_false, source_loc, error_msg), expr)
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
                                source_loc = expr.get_source_location()
                                if source_loc is None:
                                    raise ValueError("Call expression missing source location")
                                self._add_instruction(LoadConst(temp, val, source_loc), expr)
                                val = temp
                            args.append(val)

            # Get function name
            func_name_expr = getattr(expr, "function_name", None)
            if isinstance(func_name_expr, Identifier):
                func_name = func_name_expr.value
            elif isinstance(func_name_expr, StringLiteral):
                func_name = func_name_expr.value.strip('"').strip("'")
            else:
                func_name = str(func_name_expr) if func_name_expr else "unknown"
            func_ref = FunctionRef(func_name)

            # Create temp for result
            result = self.current_function.new_temp(MIRType.UNKNOWN)
            source_loc = expr.get_source_location()
            if source_loc is None:
                raise ValueError("Call expression missing source location")
            call_inst = Call(result, func_ref, args, source_loc)
            self._add_instruction(call_inst, expr)
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
