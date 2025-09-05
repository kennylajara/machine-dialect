"""Semantic analyzer for Machine Dialect.

This module provides semantic analysis capabilities including type checking,
variable usage validation, and scope analysis.
"""

from dataclasses import dataclass
from typing import Any

from machine_dialect.ast import (
    DefineStatement,
    EmptyLiteral,
    Expression,
    FloatLiteral,
    Identifier,
    InfixExpression,
    PrefixExpression,
    Program,
    SetStatement,
    Statement,
    StringLiteral,
    URLLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.errors.exceptions import MDException, MDNameError, MDTypeError, MDUninitializedError
from machine_dialect.parser.symbol_table import SymbolTable
from machine_dialect.semantic.error_messages import ErrorMessageGenerator


@dataclass
class TypeInfo:
    """Type information for expressions and variables.

    Attributes:
        type_name: The resolved type name (e.g., "Whole Number", "Text")
        is_literal: Whether this is a literal value
        literal_value: The actual value if it's a literal
    """

    type_name: str
    is_literal: bool = False
    literal_value: Any = None

    def is_compatible_with(self, allowed_types: list[str]) -> bool:
        """Check if this type is compatible with allowed types.

        Args:
            allowed_types: List of allowed type names

        Returns:
            True if compatible, False otherwise
        """
        # Direct type match
        if self.type_name in allowed_types:
            return True

        # Number type accepts both Whole Number and Float
        if "Number" in allowed_types:
            if self.type_name in ["Whole Number", "Float"]:
                return True

        # Empty is compatible with any nullable type
        if self.type_name == "Empty" and "Empty" in allowed_types:
            return True

        return False


class SemanticAnalyzer:
    """Performs semantic analysis on the AST.

    Validates:
    - Variable definitions and usage
    - Type consistency
    - Scope rules
    - Initialization before use
    """

    def __init__(self) -> None:
        """Initialize the semantic analyzer."""
        self.symbol_table = SymbolTable()
        self.errors: list[MDException] = []
        self.in_function = False
        self.function_return_type: str | None = None

    def analyze(self, program: Program) -> tuple[Program, list[MDException]]:
        """Analyze a program for semantic correctness.

        Args:
            program: The AST program to analyze

        Returns:
            Tuple of (annotated program, list of errors)
        """
        self.errors = []
        self.symbol_table = SymbolTable()

        # Analyze each statement
        for statement in program.statements:
            self._analyze_statement(statement)

        return program, self.errors

    def _analyze_statement(self, stmt: Statement) -> None:
        """Analyze a single statement.

        Args:
            stmt: Statement to analyze
        """
        from machine_dialect.ast.statements import (
            ActionStatement,
            CallStatement,
            FunctionStatement,
            IfStatement,
            InteractionStatement,
            ReturnStatement,
            SayStatement,
            UtilityStatement,
        )

        if isinstance(stmt, DefineStatement):
            self._analyze_define_statement(stmt)
        elif isinstance(stmt, SetStatement):
            self._analyze_set_statement(stmt)
        elif isinstance(stmt, FunctionStatement | ActionStatement | InteractionStatement | UtilityStatement):
            self._analyze_function_statement(stmt)
        elif isinstance(stmt, IfStatement):
            # Analyze condition
            if stmt.condition:
                self._analyze_expression(stmt.condition)
            # Analyze consequence and alternative blocks
            if stmt.consequence:
                self._analyze_statement(stmt.consequence)
            if stmt.alternative:
                self._analyze_statement(stmt.alternative)
        elif isinstance(stmt, SayStatement | ReturnStatement):
            # Analyze the expression being said or returned
            if hasattr(stmt, "expression") and stmt.expression:
                self._analyze_expression(stmt.expression)
            elif hasattr(stmt, "return_value") and stmt.return_value:
                self._analyze_expression(stmt.return_value)
        elif isinstance(stmt, CallStatement):
            # Analyze the function being called and its arguments
            if stmt.function_name:
                self._analyze_expression(stmt.function_name)
            if stmt.arguments:
                self._analyze_expression(stmt.arguments)
        elif hasattr(stmt, "expression"):  # ExpressionStatement
            self._analyze_expression(stmt.expression)
        elif hasattr(stmt, "statements"):  # BlockStatement
            # Enter new scope for block
            self.symbol_table = self.symbol_table.enter_scope()
            for s in stmt.statements:
                self._analyze_statement(s)
            # Exit scope
            parent_table = self.symbol_table.exit_scope()
            if parent_table:
                self.symbol_table = parent_table
        # Add more statement types as needed

    def _analyze_define_statement(self, stmt: DefineStatement) -> None:
        """Analyze a Define statement.

        Args:
            stmt: DefineStatement to analyze
        """
        var_name = stmt.name.value

        # Check for redefinition in current scope
        if self.symbol_table.is_defined_in_current_scope(var_name):
            existing = self.symbol_table.lookup(var_name)
            if existing:
                error_msg = ErrorMessageGenerator.redefinition(
                    var_name,
                    stmt.token.line,
                    stmt.token.position,
                    existing.definition_line,
                    existing.definition_pos,
                )
                self.errors.append(MDNameError(error_msg, stmt.token.line, stmt.token.position))
                return

        # Validate type names
        for type_name in stmt.type_spec:
            if not self._is_valid_type(type_name):
                valid_types = [
                    "Text",
                    "Whole Number",
                    "Float",
                    "Number",
                    "Yes/No",
                    "URL",
                    "Date",
                    "DateTime",
                    "Time",
                    "List",
                    "Empty",
                ]
                error_msg = ErrorMessageGenerator.invalid_type(
                    type_name, stmt.token.line, stmt.token.position, valid_types
                )
                self.errors.append(MDTypeError(error_msg, stmt.token.line, stmt.token.position))
                return

        # Register the variable definition
        try:
            self.symbol_table.define(var_name, stmt.type_spec, stmt.token.line, stmt.token.position)
        except NameError as e:
            self.errors.append(MDNameError(str(e), stmt.token.line, stmt.token.position))
            return

        # Validate default value type if present
        if stmt.initial_value:
            value_type = self._infer_expression_type(stmt.initial_value)
            if value_type and not value_type.is_compatible_with(stmt.type_spec):
                error_msg = (
                    f"Default value type '{value_type.type_name}' is not compatible "
                    f"with declared types: {', '.join(stmt.type_spec)}"
                )
                self.errors.append(MDTypeError(error_msg, stmt.token.line, stmt.token.position))
            else:
                # Mark as initialized since it has a default
                self.symbol_table.mark_initialized(var_name)

    def _analyze_function_statement(self, stmt: Statement) -> None:
        """Analyze a function definition (Action, Interaction, Utility, or Function).

        Args:
            stmt: Function statement to analyze
        """

        # Get function name
        func_name = stmt.name.value if hasattr(stmt, "name") else None
        if not func_name:
            return

        # Check for redefinition
        if self.symbol_table.is_defined_in_current_scope(func_name):
            existing = self.symbol_table.lookup(func_name)
            if existing:
                error_msg = ErrorMessageGenerator.redefinition(
                    func_name,
                    stmt.token.line,
                    stmt.token.position,
                    existing.definition_line,
                    existing.definition_pos,
                )
                self.errors.append(MDNameError(error_msg, stmt.token.line, stmt.token.position))
                return

        # Determine return type from outputs
        return_type = None
        if hasattr(stmt, "outputs") and stmt.outputs:
            # If function has outputs, use the first output's type
            # This is simplified - a full implementation might handle multiple outputs
            if stmt.outputs[0].type_name:
                return_type = stmt.outputs[0].type_name

        # Register the function in the symbol table
        # We'll use a simple approach - store it as a variable with a return_type attribute
        try:
            # First define it as a "Function" type
            self.symbol_table.define(func_name, ["Function"], stmt.token.line, stmt.token.position)
            # Then add return type info if available
            func_info = self.symbol_table.lookup(func_name)
            if func_info and return_type:
                func_info.return_type = return_type
            # Mark as initialized since functions are defined with their body
            self.symbol_table.mark_initialized(func_name)
        except NameError as e:
            self.errors.append(MDNameError(str(e), stmt.token.line, stmt.token.position))
            return

        # Enter new scope for function body
        old_in_function = self.in_function
        old_return_type = self.function_return_type
        self.in_function = True
        self.function_return_type = return_type

        self.symbol_table = self.symbol_table.enter_scope()

        # Analyze parameters (inputs) - they become local variables in the function scope
        if hasattr(stmt, "inputs"):
            for param in stmt.inputs:
                if param.name and param.type_name:
                    try:
                        self.symbol_table.define(
                            param.name.value,
                            [param.type_name],
                            param.token.line if hasattr(param, "token") else stmt.token.line,
                            param.token.position if hasattr(param, "token") else stmt.token.position,
                        )
                        # Parameters are considered initialized
                        self.symbol_table.mark_initialized(param.name.value)
                    except NameError:
                        pass  # Ignore parameter definition errors for now

        # Analyze function body
        if hasattr(stmt, "body") and stmt.body:
            self._analyze_statement(stmt.body)

        # Exit function scope
        parent_table = self.symbol_table.exit_scope()
        if parent_table:
            self.symbol_table = parent_table

        self.in_function = old_in_function
        self.function_return_type = old_return_type

    def _analyze_set_statement(self, stmt: SetStatement) -> None:
        """Analyze a Set statement.

        Args:
            stmt: SetStatement to analyze
        """
        if stmt.name is None:
            return
        var_name = stmt.name.value

        # Check if variable is defined
        var_info = self.symbol_table.lookup(var_name)
        if not var_info:
            # Get list of all defined variables for suggestions
            all_vars: list[str] = []
            current_table: SymbolTable | None = self.symbol_table
            while current_table:
                all_vars.extend(current_table.symbols.keys())
                current_table = current_table.parent

            # Find similar variables using ErrorMessageGenerator
            similar_vars = ErrorMessageGenerator._find_similar(var_name, all_vars) if all_vars else None

            error_msg = ErrorMessageGenerator.undefined_variable(
                var_name, stmt.token.line, stmt.token.position, similar_vars
            )
            self.errors.append(MDNameError(error_msg, stmt.token.line, stmt.token.position))
            return

        # Analyze the value expression (this will check for uninitialized variables)
        if stmt.value:
            # First analyze the expression to check for errors
            self._analyze_expression(stmt.value)

            # Then check type compatibility
            value_type = self._infer_expression_type(stmt.value)
            if value_type and not value_type.is_compatible_with(var_info.type_spec):
                # Try to get string representation of the value for better error message
                value_repr = None
                if value_type.is_literal and value_type.literal_value is not None:
                    if value_type.type_name == "Text":
                        value_repr = f'"{value_type.literal_value}"'
                    else:
                        value_repr = str(value_type.literal_value)

                error_msg = ErrorMessageGenerator.type_mismatch(
                    var_name,
                    var_info.type_spec,
                    value_type.type_name,
                    stmt.token.line,
                    stmt.token.position,
                    value_repr,
                )
                self.errors.append(MDTypeError(error_msg, stmt.token.line, stmt.token.position))
                return

        # Mark variable as initialized
        self.symbol_table.mark_initialized(var_name)

    def _analyze_expression(self, expr: Expression | None) -> TypeInfo | None:
        """Analyze an expression and return its type.

        Args:
            expr: Expression to analyze

        Returns:
            TypeInfo of the expression, or None if cannot be determined
        """
        if not expr:
            return None

        type_info = self._infer_expression_type(expr)

        # Check variable usage in expressions
        if isinstance(expr, Identifier):
            var_info = self.symbol_table.lookup(expr.value)
            if not var_info:
                # Get list of all defined variables for suggestions
                all_vars: list[str] = []
                current_table: SymbolTable | None = self.symbol_table
                while current_table:
                    all_vars.extend(current_table.symbols.keys())
                    current_table = current_table.parent

                similar_vars = ErrorMessageGenerator._find_similar(expr.value, all_vars) if all_vars else None
                error_msg = ErrorMessageGenerator.undefined_variable(
                    expr.value, expr.token.line, expr.token.position, similar_vars
                )
                self.errors.append(MDNameError(error_msg, expr.token.line, expr.token.position))
            elif not var_info.initialized:
                error_msg = ErrorMessageGenerator.uninitialized_use(
                    expr.value, expr.token.line, expr.token.position, var_info.definition_line
                )
                self.errors.append(MDUninitializedError(error_msg, expr.token.line, expr.token.position))

        return type_info

    def _infer_expression_type(self, expr: Expression) -> TypeInfo | None:
        """Infer the type of an expression.

        Args:
            expr: Expression to type-check

        Returns:
            TypeInfo or None if type cannot be inferred
        """
        # Literal types
        if isinstance(expr, WholeNumberLiteral):
            return TypeInfo("Whole Number", is_literal=True, literal_value=expr.value)
        elif isinstance(expr, FloatLiteral):
            return TypeInfo("Float", is_literal=True, literal_value=expr.value)
        elif isinstance(expr, StringLiteral):
            return TypeInfo("Text", is_literal=True, literal_value=expr.value)
        elif isinstance(expr, YesNoLiteral):
            return TypeInfo("Yes/No", is_literal=True, literal_value=expr.value)
        elif isinstance(expr, URLLiteral):
            return TypeInfo("URL", is_literal=True, literal_value=expr.value)
        elif isinstance(expr, EmptyLiteral):
            return TypeInfo("Empty", is_literal=True, literal_value=None)

        # Identifier - look up its type
        elif isinstance(expr, Identifier):
            var_info = self.symbol_table.lookup(expr.value)
            if var_info:
                # For union types, we can't determine exact type statically
                # Return the first type as a best guess
                return TypeInfo(var_info.type_spec[0])
            return None

        # Prefix expressions
        elif isinstance(expr, PrefixExpression):
            if expr.operator == "-":
                if expr.right:
                    right_type = self._infer_expression_type(expr.right)
                    if right_type and right_type.type_name in ["Whole Number", "Float", "Number"]:
                        return right_type
            elif expr.operator in ["not", "!"]:
                return TypeInfo("Yes/No")

        # Infix expressions
        elif isinstance(expr, InfixExpression):
            left_type = self._infer_expression_type(expr.left) if expr.left else None
            right_type = self._infer_expression_type(expr.right) if expr.right else None

            # Arithmetic operators
            if expr.operator in ["+", "-", "*", "/", "^", "**"]:
                if left_type and right_type:
                    if left_type.type_name == "Float" or right_type.type_name == "Float":
                        return TypeInfo("Float")
                    elif left_type.type_name == "Whole Number" and right_type.type_name == "Whole Number":
                        if expr.operator == "/":
                            return TypeInfo("Float")  # Division always returns float
                        return TypeInfo("Whole Number")
                    return TypeInfo("Number")  # Generic number type

            # Comparison operators
            elif expr.operator in ["<", ">", "<=", ">=", "==", "!=", "===", "!=="]:
                return TypeInfo("Yes/No")

            # Logical operators
            elif expr.operator in ["and", "or"]:
                return TypeInfo("Yes/No")

            # Bitwise operators
            elif expr.operator in ["|", "&", "^", "<<", ">>"]:
                # Bitwise operators work on integers and return integers
                if left_type and right_type:
                    if left_type.type_name == "Whole Number" and right_type.type_name == "Whole Number":
                        return TypeInfo("Whole Number")
                return None

        # Additional expression types for better coverage
        # Import these types if needed
        from machine_dialect.ast.call_expression import CallExpression
        from machine_dialect.ast.expressions import Arguments, ConditionalExpression, ErrorExpression

        # Check for grouped/parenthesized expressions
        # GroupedExpression would just pass through the inner expression type
        # but since we don't have a specific GroupedExpression class,
        # parenthesized expressions are handled transparently by the parser

        # Arguments expression type
        if isinstance(expr, Arguments):
            # Arguments don't have a single type, they're a collection
            # Return None as we can't determine a single type
            return None

        # Conditional expressions (ternary: condition ? true_expr : false_expr)
        if isinstance(expr, ConditionalExpression):
            # Type is the common type of consequence and alternative
            if expr.consequence and expr.alternative:
                cons_type = self._infer_expression_type(expr.consequence)
                alt_type = self._infer_expression_type(expr.alternative)
                if cons_type and alt_type:
                    # If both branches have same type, return that type
                    if cons_type.type_name == alt_type.type_name:
                        return cons_type
                    # If one is Empty, return the other
                    if cons_type.type_name == "Empty":
                        return alt_type
                    if alt_type.type_name == "Empty":
                        return cons_type
                    # If numeric types, return Float as common type
                    if cons_type.type_name in ["Whole Number", "Float"] and alt_type.type_name in [
                        "Whole Number",
                        "Float",
                    ]:
                        return TypeInfo("Float")
            return None

        # Call expressions - check user-defined and built-in functions
        elif isinstance(expr, CallExpression):
            # Check if it's a user-defined function by looking it up
            if expr.function_name and isinstance(expr.function_name, Identifier):
                func_name = expr.function_name.value

                # Try to find the function in the symbol table
                func_info = self.symbol_table.lookup(func_name)
                if func_info and func_info.return_type:
                    # User-defined function with known return type
                    return TypeInfo(func_info.return_type)
                elif func_info:
                    # Function without return type
                    return None

                # TODO: Check if it's a built-in function from runtime/builtins.py
                # Built-ins like 'len' return Whole Number, 'str' returns Text, etc.
                # For now, built-in functions are not tracked in the symbol table

            # Unknown function or complex call expression
            return None

        # Error expressions always have unknown type
        elif isinstance(expr, ErrorExpression):
            return None

        return None

    def _is_valid_type(self, type_name: str) -> bool:
        """Check if a type name is valid.

        Args:
            type_name: Type name to validate

        Returns:
            True if valid, False otherwise
        """
        valid_types = {
            "Text",
            "Whole Number",
            "Float",
            "Number",
            "Yes/No",
            "URL",
            "Date",
            "DateTime",
            "Time",
            "List",
            "Empty",
            "Function",  # Added to support function definitions
        }
        return type_name in valid_types
