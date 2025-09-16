"""AST nodes for statement types in Machine Dialect™.

This module defines the statement nodes used in the Abstract Syntax Tree (AST)
for Machine Dialect™. Statements are complete units of execution that perform
actions but don't produce values (unlike expressions).

Statements include:
- DefineStatement: Defines a variable with explicit type information
- ExpressionStatement: Wraps an expression as a statement
- ReturnStatement: Returns a value from a function or procedure
- SetStatement: Assigns a value to a variable
- BlockStatement: Contains a list of statements with a specific depth
- IfStatement: Conditional statement with consequence and optional alternative
- WhileStatement: Loop that executes while a condition is true
- ForEachStatement: Loop that iterates over elements in a collection
- ErrorStatement: Represents a statement that failed to parse
- Parameter: Represents a parameter with type and optional default value
"""

from enum import Enum, auto

from machine_dialect.ast import ASTNode, Expression, Identifier
from machine_dialect.lexer import Token, TokenType


class FunctionVisibility(Enum):
    """Visibility levels for function statements."""

    PRIVATE = auto()  # Action - private method
    PUBLIC = auto()  # Interaction - public method
    FUNCTION = auto()  # Utility - function with return value


class Statement(ASTNode):
    """Base class for all statement nodes in the AST.

    A statement represents a complete unit of execution in the program.
    Unlike expressions, statements don't produce values but perform actions.
    """

    def __init__(self, token: Token) -> None:
        """Initialize a Statement node.

        Args:
            token: The token that begins this statement.
        """
        self.token = token

    def desugar(self) -> "Statement":
        """Default desugar for statements returns self.

        Returns:
            Self unchanged.
        """
        return self


class DefineStatement(Statement):
    """Variable definition statement.

    Defines a new variable with explicit type information and optional
    default value. Variables must be defined before they can be used
    in Set statements.

    Attributes:
        name: Variable identifier to define
        type_spec: List of type names (for union type support)
        initial_value: Optional default value expression

    Examples:
        Define `count` as Whole Number.
        Define `message` as Text (default: _"Hello"_).
    """

    def __init__(
        self, token: Token, name: Identifier, type_spec: list[str], initial_value: Expression | None = None
    ) -> None:
        """Initialize a DefineStatement node.

        Args:
            token: The DEFINE keyword token
            name: The variable identifier
            type_spec: List of type names (e.g., ["Whole Number"], ["Text", "Whole Number"])
            initial_value: Optional default value expression
        """
        super().__init__(token)
        self.name = name
        self.type_spec = type_spec
        self.initial_value = initial_value

    def __str__(self) -> str:
        """Return string representation of the define statement.

        Returns:
            Human-readable string representation.
        """
        type_str = " or ".join(self.type_spec)
        base = f"Define `{self.name.value}` as {type_str}"
        if self.initial_value:
            base += f" (default: {self.initial_value})"
        return base + "."

    def desugar(self) -> Statement:
        """Desugar define statement with default value.

        A Define statement with a default value desugars into:
        1. The Define statement itself (without initial_value)
        2. A Set statement for initialization (if initial_value exists)

        Returns:
            Self if no initial value, otherwise a BlockStatement containing
            the definition and initialization.
        """
        if not self.initial_value:
            return self

        # Create a Define without initial value
        define_only = DefineStatement(self.token, self.name, self.type_spec, None)

        # Create a Set statement for initialization
        set_stmt = SetStatement(self.token, self.name, self.initial_value)

        # Return both as a block
        block = BlockStatement(self.token)
        block.statements = [define_only, set_stmt]
        return block

    def to_hir(self) -> Statement:
        """Convert DefineStatement to HIR representation.

        The HIR representation includes type annotations and
        desugars default values into separate initialization.

        Returns:
            HIR representation of the define statement
        """
        if not self.initial_value:
            # No default value - return as-is
            return DefineStatement(self.token, self.name, self.type_spec, None)

        # With default value - desugar to define + set
        # Create annotated define without initial value
        define_stmt = DefineStatement(self.token, self.name, self.type_spec, None)

        # Create initialization set statement
        set_stmt = SetStatement(
            self.token,
            self.name,
            self.initial_value.to_hir() if hasattr(self.initial_value, "to_hir") else self.initial_value,
        )

        # Return as block
        block = BlockStatement(self.token)
        block.statements = [define_stmt, set_stmt]
        return block


class ExpressionStatement(Statement):
    """A statement that wraps an expression.

    Expression statements allow expressions to be used as statements.
    For example, a function call like `print("Hello")` is an expression
    that becomes a statement when used on its own line.

    Attributes:
        expression: The expression being wrapped as a statement.
    """

    def __init__(self, token: Token, expression: Expression | None) -> None:
        """Initialize an ExpressionStatement node.

        Args:
            token: The first token of the expression.
            expression: The expression to wrap as a statement.
        """
        super().__init__(token)
        self.expression = expression

    def __str__(self) -> str:
        """Return the string representation of the expression statement.

        Returns:
            The string representation of the wrapped expression.
        """
        return str(self.expression)

    def desugar(self) -> "ExpressionStatement":
        """Desugar expression statement by recursively desugaring the expression.

        Returns:
            A new ExpressionStatement with desugared expression.
        """
        desugared = ExpressionStatement(self.token, None)
        if self.expression:
            desugared.expression = self.expression.desugar()
        return desugared


class ReturnStatement(Statement):
    """A return statement that exits a function with an optional value.

    Return statements are used to exit from a function or procedure,
    optionally providing a value to return to the caller.

    Attributes:
        return_value: The expression whose value to return, or None for void return.
    """

    def __init__(self, token: Token, return_value: Expression | None = None) -> None:
        """Initialize a ReturnStatement node.

        Args:
            token: The 'return' or 'Return' token.
            return_value: Optional expression to evaluate and return.
        """
        super().__init__(token)
        self.return_value = return_value

    def __str__(self) -> str:
        """Return the string representation of the return statement.

        Returns:
            A string like "\nReturn <value>" or "\nReturn" for void returns.
        """
        out = f"\n{self.token.literal}"
        if self.return_value:
            out += f" {self.return_value}"
        return out

    def desugar(self) -> "ReturnStatement":
        """Desugar return statement by normalizing literal and desugaring return value.

        Normalizes "give back" and "gives back" to canonical "return".

        Returns:
            A new ReturnStatement with normalized literal and desugared return value.
        """
        # Create new token with normalized literal
        normalized_token = Token(
            self.token.type,
            "return",  # Normalize to canonical form
            self.token.line,
            self.token.position,
        )

        desugared = ReturnStatement(normalized_token)
        if self.return_value:
            desugared.return_value = self.return_value.desugar()
        return desugared


class SetStatement(Statement):
    """A statement that assigns a value to a variable.

    Set statements follow the natural language pattern: "Set <variable> to <value>".
    They are the primary way to assign values to variables in Machine Dialect™.

    Attributes:
        name: The identifier (variable name) to assign to.
        value: The expression whose value to assign.
    """

    def __init__(self, token: Token, name: Identifier | None = None, value: Expression | None = None) -> None:
        """Initialize a SetStatement node.

        Args:
            token: The 'Set' token that begins the statement.
            name: The identifier to assign to.
            value: The expression whose value to assign.
        """
        super().__init__(token)
        self.name = name
        self.value = value

    def __str__(self) -> str:
        """Return the string representation of the set statement.

        Returns:
            A string like "Set <name> to <value>".
        """
        out = f"{self.token.literal} "
        if self.name:
            out += f"{self.name} "
        out += "to "
        if self.value:
            out += str(self.value)
        return out

    def desugar(self) -> "SetStatement":
        """Desugar set statement by recursively desugaring name and value.

        Returns:
            A new SetStatement with desugared components.
        """
        desugared = SetStatement(self.token)
        if self.name:
            desugared.name = self.name.desugar() if hasattr(self.name, "desugar") else self.name
        if self.value:
            desugared.value = self.value.desugar()
        return desugared


class CallStatement(Statement):
    """A statement that calls/invokes a function or interaction.

    Call statements follow the pattern: "use <function> [with <arguments>]".
    They are used to invoke utilities, actions, or interactions with optional arguments.

    Attributes:
        function_name: The expression that identifies the function to call (usually a StringLiteral or Identifier).
        arguments: Optional Arguments node containing the function arguments.
    """

    def __init__(
        self, token: Token, function_name: Expression | None = None, arguments: Expression | None = None
    ) -> None:
        """Initialize a CallStatement node.

        Args:
            token: The 'call' token that begins the statement.
            function_name: The expression identifying the function to call.
            arguments: Optional Arguments node containing the function arguments.
        """
        super().__init__(token)
        self.function_name = function_name
        self.arguments = arguments

    def __str__(self) -> str:
        """Return the string representation of the call statement.

        Returns:
            A string like "call <function> [with <arguments>]".
        """
        out = f"{self.token.literal} "
        if self.function_name:
            out += str(self.function_name)
        if self.arguments:
            out += f" with {self.arguments}"
        return out

    def desugar(self) -> "CallStatement":
        """Desugar call statement by recursively desugaring function name and arguments.

        Returns:
            A new CallStatement with desugared components.
        """
        desugared = CallStatement(self.token)
        if self.function_name:
            desugared.function_name = self.function_name.desugar()
        if self.arguments:
            desugared.arguments = self.arguments.desugar()
        return desugared


class BlockStatement(Statement):
    """A block of statements with a specific depth.

    Block statements contain a list of statements that are executed together.
    The depth is indicated by the number of '>' symbols at the beginning of
    each line in the block.

    Attributes:
        depth: The depth level of this block (number of '>' symbols).
        statements: List of statements contained in this block.
    """

    def __init__(self, token: Token, depth: int = 1) -> None:
        """Initialize a BlockStatement node.

        Args:
            token: The token that begins the block (usually ':' or first '>').
            depth: The depth level of this block.
        """
        super().__init__(token)
        self.depth = depth
        self.statements: list[Statement] = []

    def __str__(self) -> str:
        """Return the string representation of the block statement.

        Returns:
            A string showing the block with proper indentation.
        """
        indent = ">" * self.depth + " "
        statements_str = "\n".join(indent + str(stmt) for stmt in self.statements)
        return f":\n{statements_str}"

    def desugar(self) -> "Statement | BlockStatement":
        """Desugar block statement.

        Always returns a BlockStatement to preserve scope semantics.
        This ensures proper scope instructions are generated in MIR.

        Returns:
            A new BlockStatement with desugared statements.
        """
        # Desugar all contained statements - they return Statement type
        desugared_statements: list[Statement] = []
        for stmt in self.statements:
            result = stmt.desugar()
            # The desugar might return any Statement subclass
            assert isinstance(result, Statement)
            desugared_statements.append(result)

        # Always return a new block with desugared statements to preserve scope
        desugared = BlockStatement(self.token, self.depth)
        desugared.statements = desugared_statements
        return desugared


class IfStatement(Statement):
    """A conditional statement with if-then-else structure.

    If statements evaluate a condition and execute different blocks of code
    based on whether the condition is true or false. Supports various keywords:
    if/when/whenever for the condition, else/otherwise for the alternative.

    Attributes:
        condition: The boolean expression to evaluate.
        consequence: The block of statements to execute if condition is true.
        alternative: Optional block of statements to execute if condition is false.
    """

    def __init__(self, token: Token, condition: Expression | None = None) -> None:
        """Initialize an IfStatement node.

        Args:
            token: The 'if', 'when', or 'whenever' token.
            condition: The boolean expression to evaluate.
        """
        super().__init__(token)
        self.condition = condition
        self.consequence: BlockStatement | None = None
        self.alternative: BlockStatement | None = None

    def __str__(self) -> str:
        """Return the string representation of the if statement.

        Returns:
            A string like "if <condition> then: <consequence> [else: <alternative>]".
        """
        out = f"{self.token.literal} {self.condition}"
        if self.consequence:
            out += f" then{self.consequence}"
        if self.alternative:
            out += f"\nelse{self.alternative}"
        return out

    def desugar(self) -> "IfStatement":
        """Desugar if statement by recursively desugaring all components.

        Returns:
            A new IfStatement with desugared condition, consequence, and alternative.
        """
        desugared = IfStatement(self.token)
        if self.condition:
            desugared.condition = self.condition.desugar()
        if self.consequence:
            # BlockStatement.desugar may return a non-block if it has single statement
            consequence_desugared = self.consequence.desugar()
            # Ensure consequence is always a BlockStatement for consistency
            if isinstance(consequence_desugared, BlockStatement):
                desugared.consequence = consequence_desugared
            else:
                # Wrap single statement back in a block
                block = BlockStatement(self.token, self.consequence.depth)
                block.statements = [consequence_desugared]
                desugared.consequence = block
        if self.alternative:
            # Same treatment for alternative
            alternative_desugared = self.alternative.desugar()
            if isinstance(alternative_desugared, BlockStatement):
                desugared.alternative = alternative_desugared
            else:
                block = BlockStatement(self.token, self.alternative.depth)
                block.statements = [alternative_desugared]
                desugared.alternative = block
        return desugared


class ErrorStatement(Statement):
    """A statement that failed to parse correctly.

    ErrorStatements preserve the AST structure even when parsing fails,
    allowing the parser to continue and collect multiple errors. They
    contain the tokens that were skipped during panic-mode recovery.

    Attributes:
        skipped_tokens: List of tokens that were skipped during panic recovery.
        message: Human-readable error message describing what went wrong.
    """

    def __init__(self, token: Token, skipped_tokens: list[Token] | None = None, message: str = "") -> None:
        """Initialize an ErrorStatement node.

        Args:
            token: The token where the error began.
            skipped_tokens: Tokens that were skipped during panic recovery.
            message: Error message describing the parsing failure.
        """
        super().__init__(token)
        self.skipped_tokens = skipped_tokens or []
        self.message = message

    def __str__(self) -> str:
        """Return the string representation of the error statement.

        Returns:
            A string like "<error: message>".
        """
        if self.message:
            return f"<error: {self.message}>"
        return "<error>"

    def desugar(self) -> "ErrorStatement":
        """Error statements remain unchanged during desugaring.

        Returns:
            Self unchanged.
        """
        return self


class Parameter(ASTNode):
    """Represents an input parameter with type and optional default value.

    Parameters are used in Actions, Interactions, and Utilities to define inputs.
    They follow the syntax: `name` **as** Type (required|optional, default: value)

    Attributes:
        name: The identifier naming the parameter.
        type_name: The type of the parameter (e.g., "Text", "Whole Number", "Status").
        is_required: Whether the parameter is required or optional.
        default_value: The default value for optional parameters.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        type_name: str = "",
        is_required: bool = True,
        default_value: Expression | None = None,
    ) -> None:
        """Initialize a Parameter node.

        Args:
            token: The token that begins this parameter.
            name: The identifier naming the parameter.
            type_name: The type of the parameter.
            is_required: Whether the parameter is required.
            default_value: The default value for optional parameters.
        """
        self.token = token
        self.name = name
        self.type_name = type_name
        self.is_required = is_required
        self.default_value = default_value

    def __str__(self) -> str:
        """Return string representation of the parameter.

        Returns:
            A string representation of the parameter.
        """
        result = f"{self.name} as {self.type_name}"
        if not self.is_required:
            result += " (optional"
            if self.default_value:
                result += f", default: {self.default_value}"
            result += ")"
        else:
            result += " (required)"
        return result


class Output(ASTNode):
    """Represents an output with type and optional default value.

    Outputs are used in Actions, Interactions, and Utilities to define return values.
    They follow the syntax: `name` **as** Type (default: value)

    Attributes:
        name: The identifier naming the output.
        type_name: The type of the output (e.g., "Text", "Number", "Status").
        default_value: The optional default value for the output.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        type_name: str = "",
        default_value: Expression | None = None,
    ) -> None:
        """Initialize an Output node.

        Args:
            token: The token that begins this output.
            name: The identifier naming the output.
            type_name: The type of the output.
            default_value: The optional default value.
        """
        self.token = token
        self.name = name
        self.type_name = type_name
        self.default_value = default_value

    def __str__(self) -> str:
        """Return string representation of the output.

        Returns:
            A string like "`name` as Type" or "`name` as Type (default: value)".
        """
        result = f"`{self.name.value}` as {self.type_name}"
        if self.default_value is not None:
            result += f" (default: {self.default_value})"
        return result


class ActionStatement(Statement):
    """Represents an Action statement (private method) in Machine Dialect™.

    Actions are private methods that can only be called within the same scope.
    They are defined using the markdown-style syntax:
    ### **Action**: `name`

    Attributes:
        name: The identifier naming the action.
        inputs: List of input parameters.
        outputs: List of outputs.
        body: The block of statements that make up the action body.
        description: Optional description from the summary tag.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Output] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize an ActionStatement node.

        Args:
            token: The token that begins this statement (KW_ACTION).
            name: The identifier naming the action.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of outputs (defaults to empty list).
            body: The block of statements in the action body.
            description: Optional description from summary tag.
        """
        super().__init__(token)
        self.name = name
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.body = body if body is not None else BlockStatement(token)
        self.description = description

    def token_literal(self) -> str:
        """Return the literal value of the action token.

        Returns:
            The literal value of the action keyword token.
        """
        return self.token.literal

    def __str__(self) -> str:
        """Return string representation of the action statement.

        Returns:
            A string representation of the action with its name and body.
        """
        inputs_str = ", ".join(str(p) for p in self.inputs)
        outputs_str = ", ".join(str(p) for p in self.outputs)
        result = f"action {self.name}"
        if inputs_str:
            result += f"(inputs: {inputs_str})"
        if outputs_str:
            result += f" -> {outputs_str}"
        result += f" {{\n{self.body}\n}}"
        return result

    def desugar(self) -> "FunctionStatement":
        """Desugar action statement to unified FunctionStatement.

        Returns:
            A FunctionStatement with PRIVATE visibility.
        """
        desugared_body: BlockStatement | None = None
        if self.body:
            body_result = self.body.desugar()
            # Ensure body is always a BlockStatement
            if isinstance(body_result, BlockStatement):
                desugared_body = body_result
            else:
                # Wrap single statement in a block
                desugared_body = BlockStatement(self.token)
                desugared_body.statements = [body_result]

        return FunctionStatement(
            self.token,
            FunctionVisibility.PRIVATE,
            self.name.desugar() if hasattr(self.name, "desugar") else self.name,
            self.inputs,
            self.outputs,
            desugared_body,
            self.description,
        )


class SayStatement(Statement):
    """Represents a Say statement (output/display) in Machine Dialect™.

    Say statements output or display expressions to the user.
    They are similar to print statements in other languages.

    Attributes:
        expression: The expression to output.
    """

    def __init__(self, token: Token, expression: Expression | None = None) -> None:
        """Initialize a SayStatement node.

        Args:
            token: The token that begins this statement (KW_SAY).
            expression: The expression to output.
        """
        super().__init__(token)
        self.expression = expression

    def token_literal(self) -> str:
        """Return the literal value of the say token.

        Returns:
            The literal value of the say keyword token.
        """
        return self.token.literal

    def __str__(self) -> str:
        """Return string representation of the say statement.

        Returns:
            A string representation like "Say expression".
        """
        return f"Say {self.expression}" if self.expression else "Say"

    def desugar(self) -> "SayStatement":
        """Desugar say statement by recursively desugaring its expression.

        Returns:
            A new SayStatement with desugared expression.
        """
        desugared = SayStatement(self.token)
        if self.expression:
            desugared.expression = self.expression.desugar()
        return desugared


class InteractionStatement(Statement):
    """Represents an Interaction statement (public method) in Machine Dialect™.

    Interactions are public methods that can be called from outside the scope.
    They are defined using the markdown-style syntax:
    ### **Interaction**: `name`

    Attributes:
        name: The identifier naming the interaction.
        inputs: List of input parameters.
        outputs: List of outputs.
        body: The block of statements that make up the interaction body.
        description: Optional description from the summary tag.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Output] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize an InteractionStatement node.

        Args:
            token: The token that begins this statement (KW_INTERACTION).
            name: The identifier naming the interaction.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of outputs (defaults to empty list).
            body: The block of statements in the interaction body.
            description: Optional description from summary tag.
        """
        super().__init__(token)
        self.name = name
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.body = body if body is not None else BlockStatement(token)
        self.description = description

    def token_literal(self) -> str:
        """Return the literal value of the interaction token.

        Returns:
            The literal value of the interaction keyword token.
        """
        return self.token.literal

    def __str__(self) -> str:
        """Return string representation of the interaction statement.

        Returns:
            A string representation of the interaction with its name and body.
        """
        inputs_str = ", ".join(str(p) for p in self.inputs)
        outputs_str = ", ".join(str(p) for p in self.outputs)
        result = f"interaction {self.name}"
        if inputs_str:
            result += f"(inputs: {inputs_str})"
        if outputs_str:
            result += f" -> {outputs_str}"
        result += f" {{\n{self.body}\n}}"
        return result

    def desugar(self) -> "FunctionStatement":
        """Desugar interaction statement to unified FunctionStatement.

        Returns:
            A FunctionStatement with PUBLIC visibility.
        """
        desugared_body: BlockStatement | None = None
        if self.body:
            body_result = self.body.desugar()
            # Ensure body is always a BlockStatement
            if isinstance(body_result, BlockStatement):
                desugared_body = body_result
            else:
                # Wrap single statement in a block
                desugared_body = BlockStatement(self.token)
                desugared_body.statements = [body_result]

        return FunctionStatement(
            self.token,
            FunctionVisibility.PUBLIC,
            self.name.desugar() if hasattr(self.name, "desugar") else self.name,
            self.inputs,
            self.outputs,
            desugared_body,
            self.description,
        )


class UtilityStatement(Statement):
    """Represents a Utility statement (function) in Machine Dialect™.

    Utilities are functions that can be called and return values.
    They are defined using the markdown-style syntax:
    ### **Utility**: `name`

    Attributes:
        name: The identifier naming the utility.
        inputs: List of input parameters.
        outputs: List of outputs.
        body: The block of statements that make up the utility body.
        description: Optional description from the summary tag.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Output] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize a UtilityStatement node.

        Args:
            token: The token that begins this statement (KW_UTILITY).
            name: The identifier naming the utility.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of outputs (defaults to empty list).
            body: The block of statements in the utility body.
            description: Optional description from summary tag.
        """
        super().__init__(token)
        self.name = name
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.body = body if body is not None else BlockStatement(token)
        self.description = description

    def token_literal(self) -> str:
        """Return the literal value of the utility token.

        Returns:
            The literal value of the utility keyword token.
        """
        return self.token.literal

    def __str__(self) -> str:
        """Return string representation of the utility statement.

        Returns:
            A string representation of the utility with its name and body.
        """
        inputs_str = ", ".join(str(p) for p in self.inputs)
        outputs_str = ", ".join(str(p) for p in self.outputs)
        result = f"utility {self.name}"
        if inputs_str:
            result += f"(inputs: {inputs_str})"
        if outputs_str:
            result += f" -> {outputs_str}"
        result += f" {{\n{self.body}\n}}"
        return result

    def desugar(self) -> "FunctionStatement":
        """Desugar utility statement to unified FunctionStatement.

        Returns:
            A FunctionStatement with FUNCTION visibility.
        """
        desugared_body: BlockStatement | None = None
        if self.body:
            body_result = self.body.desugar()
            # Ensure body is always a BlockStatement
            if isinstance(body_result, BlockStatement):
                desugared_body = body_result
            else:
                # Wrap single statement in a block
                desugared_body = BlockStatement(self.token)
                desugared_body.statements = [body_result]

        return FunctionStatement(
            self.token,
            FunctionVisibility.FUNCTION,
            self.name.desugar() if hasattr(self.name, "desugar") else self.name,
            self.inputs,
            self.outputs,
            desugared_body,
            self.description,
        )


class CollectionMutationStatement(Statement):
    """Statement for mutating collections (lists and named lists).

    Handles operations like:
    Arrays (Ordered/Unordered Lists):
    - Add _value_ to list
    - Remove _value_ from list
    - Set the second item of list to _value_
    - Set item _5_ of list to _value_
    - Insert _value_ at position _3_ in list
    - Clear list

    Named Lists (Dictionaries):
    - Add "key" to dict with value _value_
    - Remove "key" from dict
    - Update "key" in dict to _value_
    - Clear dict

    Attributes:
        operation: The mutation operation ('add', 'remove', 'set', 'insert', 'clear', 'update').
        collection: The collection expression to mutate.
        value: The value for add/remove/set/insert/update operations.
        position: The position/index/key for set/insert/update operations (can be ordinal, numeric, or key).
        position_type: Type of position ('ordinal', 'numeric', 'key', None).
    """

    def __init__(
        self,
        token: Token,
        operation: str,
        collection: Expression,
        value: Expression | None = None,
        position: Expression | str | int | None = None,
        position_type: str | None = None,
    ) -> None:
        """Initialize a CollectionMutationStatement node.

        Args:
            token: The token that begins this statement (KW_ADD, KW_REMOVE, etc.).
            operation: The mutation operation type.
            collection: The collection to mutate.
            value: The value for the operation (None for 'empty').
            position: The position/index for set/insert (ordinal string, numeric int, or expression).
            position_type: Type of position ('ordinal', 'numeric', or None).
        """
        super().__init__(token)
        self.operation = operation
        self.collection = collection
        self.value = value
        self.position = position
        self.position_type = position_type

    def __str__(self) -> str:
        """Return string representation of the mutation statement.

        Returns:
            A human-readable string representation.
        """
        if self.operation == "add":
            if self.position_type == "key":
                return f"Add {self.position} to {self.collection} with value {self.value}."
            else:
                return f"Add {self.value} to {self.collection}."
        elif self.operation == "remove":
            return f"Remove {self.value} from {self.collection}."
        elif self.operation == "set":
            if self.position_type == "ordinal":
                return f"Set the {self.position} item of {self.collection} to {self.value}."
            else:  # numeric
                return f"Set item _{self.position}_ of {self.collection} to {self.value}."
        elif self.operation == "insert":
            return f"Insert {self.value} at position _{self.position}_ in {self.collection}."
        elif self.operation == "clear":
            return f"Clear {self.collection}."
        elif self.operation == "update":
            return f"Update {self.position} in {self.collection} to {self.value}."
        return f"<collection mutation: {self.operation}>"

    def desugar(self) -> "CollectionMutationStatement":
        """Desugar collection mutation statement by recursively desugaring components.

        Returns:
            A new CollectionMutationStatement with desugared components.
        """
        desugared = CollectionMutationStatement(
            self.token,
            self.operation,
            self.collection.desugar(),
            self.value.desugar() if self.value else None,
            self.position,
            self.position_type,
        )
        # If position is an expression, desugar it
        if isinstance(self.position, Expression):
            desugared.position = self.position.desugar()
        return desugared

    def to_hir(self) -> "CollectionMutationStatement":
        """Convert collection mutation to HIR representation.

        Converts one-based user indices to zero-based for internal use.

        Returns:
            HIR representation with adjusted indices.
        """
        # Convert collection to HIR
        hir_collection = self.collection.to_hir() if hasattr(self.collection, "to_hir") else self.collection

        # Convert value to HIR if present
        hir_value = None
        if self.value:
            hir_value = self.value.to_hir() if hasattr(self.value, "to_hir") else self.value

        # Process position based on type
        hir_position = self.position
        if self.position_type == "ordinal":
            # Convert ordinals to zero-based numeric indices
            ordinal_map = {"first": 0, "second": 1, "third": 2}
            if isinstance(self.position, str) and self.position.lower() in ordinal_map:
                hir_position = ordinal_map[self.position.lower()]
                # Return with numeric type since we converted
                return CollectionMutationStatement(
                    self.token,
                    self.operation,
                    hir_collection,
                    hir_value,
                    hir_position,
                    "numeric",
                )
            elif self.position == "last":
                # Keep "last" as special case
                hir_position = "last"
        elif self.position_type == "numeric":
            # Convert one-based to zero-based index
            if isinstance(self.position, int):
                hir_position = self.position - 1  # Convert to 0-based
            elif isinstance(self.position, Expression):
                # For expressions, we'll handle in MIR generation
                hir_position = self.position.to_hir() if hasattr(self.position, "to_hir") else self.position
        elif isinstance(self.position, Expression):
            hir_position = self.position.to_hir() if hasattr(self.position, "to_hir") else self.position

        return CollectionMutationStatement(
            self.token,
            self.operation,
            hir_collection,
            hir_value,
            hir_position,
            self.position_type,
        )


class FunctionStatement(Statement):
    """Unified function statement for Actions, Interactions, and Utilities.

    This is the desugared form of ActionStatement, InteractionStatement, and
    UtilityStatement. It represents all function-like constructs with a
    visibility modifier.

    Attributes:
        visibility: The visibility level (PRIVATE, PUBLIC, or FUNCTION).
        name: The identifier naming the function.
        inputs: List of input parameters.
        outputs: List of outputs.
        body: The block of statements that make up the function body.
        description: Optional description.
    """

    def __init__(
        self,
        token: Token,
        visibility: FunctionVisibility,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Output] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize a FunctionStatement node.

        Args:
            token: The token that begins this statement.
            visibility: The visibility level of the function.
            name: The identifier naming the function.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of outputs (defaults to empty list).
            body: The block of statements in the function body.
            description: Optional description.
        """
        super().__init__(token)
        self.visibility = visibility
        self.name = name
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.body = body if body is not None else BlockStatement(token)
        self.description = description

    def __str__(self) -> str:
        """Return string representation of the function statement.

        Returns:
            A string representation of the function with its visibility, name and body.
        """
        visibility_str = {
            FunctionVisibility.PRIVATE: "action",
            FunctionVisibility.PUBLIC: "interaction",
            FunctionVisibility.FUNCTION: "utility",
        }[self.visibility]

        inputs_str = ", ".join(str(p) for p in self.inputs)
        outputs_str = ", ".join(str(p) for p in self.outputs)
        result = f"{visibility_str} {self.name}"
        if inputs_str:
            result += f"(inputs: {inputs_str})"
        if outputs_str:
            result += f" -> {outputs_str}"
        result += f" {{\n{self.body}\n}}"
        return result

    def desugar(self) -> "FunctionStatement":
        """Desugar function statement by recursively desugaring its components.

        Returns:
            A new FunctionStatement with desugared components.
        """
        desugared_body: BlockStatement | None = None
        if self.body:
            body_result = self.body.desugar()
            # Ensure body is always a BlockStatement
            if isinstance(body_result, BlockStatement):
                desugared_body = body_result
            else:
                # Wrap single statement in a block
                desugared_body = BlockStatement(self.token)
                desugared_body.statements = [body_result]

        desugared = FunctionStatement(
            self.token,
            self.visibility,
            self.name.desugar() if hasattr(self.name, "desugar") else self.name,
            self.inputs,  # Parameters don't have desugar yet
            self.outputs,  # Outputs don't have desugar yet
            desugared_body,
            self.description,
        )
        return desugared


class WhileStatement(Statement):
    """A while loop statement in Machine Dialect™.

    While statements follow the pattern: "While <condition>: <body>"
    They repeatedly execute the body block as long as the condition evaluates to true.

    Attributes:
        condition: The expression to evaluate for loop continuation.
        body: The block of statements to execute while condition is true.
    """

    def __init__(self, token: Token, condition: Expression | None = None, body: BlockStatement | None = None) -> None:
        """Initialize a WhileStatement node.

        Args:
            token: The 'while' token that begins the statement.
            condition: The loop condition expression.
            body: The block of statements to execute.
        """
        super().__init__(token)
        self.condition = condition
        self.body = body

    def __str__(self) -> str:
        """Return the string representation of the while statement.

        Returns:
            A string like "While <condition>: <body>".
        """
        out = f"While {self.condition}:"
        if self.body:
            out += f"\n{self.body}"
        return out

    def desugar(self) -> "WhileStatement":
        """Desugar while statement by recursively desugaring condition and body.

        Returns:
            A new WhileStatement with desugared components.
        """
        desugared = WhileStatement(self.token)
        if self.condition:
            desugared.condition = self.condition.desugar()
        if self.body:
            body_result = self.body.desugar()
            # Ensure body is a BlockStatement
            if isinstance(body_result, BlockStatement):
                desugared.body = body_result
            else:
                # This shouldn't happen but handle gracefully
                desugared.body = BlockStatement(self.token)
                desugared.body.statements = [body_result]
        return desugared

    def to_hir(self) -> "WhileStatement":
        """Convert to HIR by desugaring.

        Returns:
            HIR representation of the while statement.
        """
        return self.desugar()


class ForEachStatement(Statement):
    """A for-each loop statement in Machine Dialect™.

    For-each statements follow the pattern: "For each <item> in <collection>: <body>"
    They iterate over each element in a collection.

    Attributes:
        item: The identifier for the loop variable.
        collection: The expression that evaluates to the collection to iterate over.
        body: The block of statements to execute for each item.
    """

    # Class-level counter for generating unique synthetic variable names
    _gensym_counter = 0

    def __init__(
        self,
        token: Token,
        item: Identifier | None = None,
        collection: Expression | None = None,
        body: BlockStatement | None = None,
    ) -> None:
        """Initialize a ForEachStatement node.

        Args:
            token: The 'for' token that begins the statement.
            item: The loop variable identifier.
            collection: The collection to iterate over.
            body: The block of statements to execute.
        """
        super().__init__(token)
        self.item = item
        self.collection = collection
        self.body = body

    def __str__(self) -> str:
        """Return the string representation of the for-each statement.

        Returns:
            A string like "For each <item> in <collection>: <body>".
        """
        out = f"For each {self.item} in {self.collection}:"
        if self.body:
            out += f"\n{self.body}"
        return out

    @classmethod
    def _gensym(cls, prefix: str) -> Identifier:
        """Generate a unique identifier for internal synthetic variables.

        Uses a $ prefix which is not valid in user-defined identifiers
        to guarantee no name collisions.

        Args:
            prefix: A descriptive prefix for the synthetic variable.

        Returns:
            A unique Identifier that cannot collide with user variables.
        """
        cls._gensym_counter += 1
        # Use $ prefix to ensure no collision with user variables
        # $ is not a valid character in Machine Dialect identifiers
        name = f"${prefix}_{cls._gensym_counter}"
        # Create a synthetic token for the identifier
        synthetic_token = Token(TokenType.MISC_IDENT, name, 0, 0)
        return Identifier(synthetic_token, name)

    def desugar(self) -> "Statement":
        """Desugar for-each loop into a while loop.

        Transforms:
            For each `item` in `collection`:
                body

        Into:
            index = 0
            length = len(collection)
            While index < length:
                item = collection[index]
                body
                index = index + 1

        Returns:
            A WhileStatement representing the desugared for-each loop.
        """
        if not self.item or not self.collection:
            # If malformed, return an empty while statement
            return WhileStatement(self.token)

        # Import here to avoid circular imports
        from machine_dialect.ast.call_expression import CallExpression
        from machine_dialect.ast.expressions import CollectionAccessExpression, InfixExpression
        from machine_dialect.ast.literals import WholeNumberLiteral

        # Generate unique synthetic variables
        index_var = self._gensym("foreach_idx")
        length_var = self._gensym("foreach_len")

        # Create synthetic tokens for literals
        zero_token = Token(TokenType.LIT_WHOLE_NUMBER, "0", 0, 0)
        one_token = Token(TokenType.LIT_WHOLE_NUMBER, "1", 0, 0)

        # Build the initialization statements:
        # Set index to 0
        init_index = SetStatement(Token(TokenType.KW_SET, "Set", 0, 0), index_var, WholeNumberLiteral(zero_token, 0))

        # Set length to len(collection)
        # Import Arguments for function call
        from machine_dialect.ast.expressions import Arguments

        call_args = Arguments(Token(TokenType.MISC_IDENT, "args", 0, 0))
        call_args.positional = [self.collection.desugar() if self.collection else self.collection]
        call_args.named = []

        len_call = CallExpression(
            Token(TokenType.MISC_IDENT, "len", 0, 0),
            Identifier(Token(TokenType.MISC_IDENT, "len", 0, 0), "len"),
            call_args,
        )
        init_length = SetStatement(Token(TokenType.KW_SET, "Set", 0, 0), length_var, len_call)

        # Build the while condition: index < length
        condition = InfixExpression(Token(TokenType.OP_LT, "<", 0, 0), "<", index_var)
        condition.right = length_var

        # Build the while body
        while_body = BlockStatement(self.token)
        while_body.statements = []

        # Add: item = collection[index]
        collection_access = CollectionAccessExpression(
            Token(TokenType.MISC_IDENT, "access", 0, 0),  # Token for the access operation
            self.collection.desugar() if self.collection else self.collection,
            index_var,
            "numeric",  # Using numeric access type
        )
        set_item = SetStatement(
            Token(TokenType.KW_SET, "Set", 0, 0),
            self.item,
            collection_access,
        )
        while_body.statements.append(set_item)

        # Add the original body statements
        if self.body:
            desugared_body = self.body.desugar()
            if isinstance(desugared_body, BlockStatement):
                while_body.statements.extend(desugared_body.statements)
            else:
                while_body.statements.append(desugared_body)

        # Add: index = index + 1
        increment = InfixExpression(Token(TokenType.OP_PLUS, "+", 0, 0), "+", index_var)
        increment.right = WholeNumberLiteral(one_token, 1)
        set_increment = SetStatement(Token(TokenType.KW_SET, "Set", 0, 0), index_var, increment)
        while_body.statements.append(set_increment)

        # Create the while statement
        while_stmt = WhileStatement(Token(TokenType.KW_WHILE, "While", 0, 0), condition, while_body)

        # Wrap everything in a block statement
        result_block = BlockStatement(self.token)
        result_block.statements = [init_index, init_length, while_stmt]

        # Since we need to return a Statement, we'll return the block
        # The HIR generation will handle this properly
        return result_block

    def to_hir(self) -> "Statement":
        """Convert to HIR by desugaring to while loop.

        Returns:
            HIR representation (desugared while loop).
        """
        return self.desugar()
