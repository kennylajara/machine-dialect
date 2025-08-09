"""AST nodes for statement types in Machine Dialect.

This module defines the statement nodes used in the Abstract Syntax Tree (AST)
for Machine Dialect. Statements are complete units of execution that perform
actions but don't produce values (unlike expressions).

Statements include:
- ExpressionStatement: Wraps an expression as a statement
- ReturnStatement: Returns a value from a function or procedure
- SetStatement: Assigns a value to a variable
- BlockStatement: Contains a list of statements with a specific depth
- IfStatement: Conditional statement with consequence and optional alternative
- ErrorStatement: Represents a statement that failed to parse
- Parameter: Represents a parameter with type and optional default value
"""

from machine_dialect.ast import ASTNode, Expression, Identifier
from machine_dialect.lexer import Token


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


class SetStatement(Statement):
    """A statement that assigns a value to a variable.

    Set statements follow the natural language pattern: "Set <variable> to <value>".
    They are the primary way to assign values to variables in Machine Dialect.

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


class CallStatement(Statement):
    """A statement that calls/invokes a function or interaction.

    Call statements follow the pattern: "call <function> [with <arguments>]".
    They are used to invoke functions, actions, or interactions with optional arguments.

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


class Parameter(ASTNode):
    """Represents a parameter with type and optional default value.

    Parameters are used in Actions and Interactions to define inputs and outputs.
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


class ActionStatement(Statement):
    """Represents an Action statement (private method) in Machine Dialect.

    Actions are private methods that can only be called within the same scope.
    They are defined using the markdown-style syntax:
    ### **Action**: `name`

    Attributes:
        name: The identifier naming the action.
        inputs: List of input parameters.
        outputs: List of output parameters.
        body: The block of statements that make up the action body.
        description: Optional description from the summary tag.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Parameter] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize an ActionStatement node.

        Args:
            token: The token that begins this statement (KW_ACTION).
            name: The identifier naming the action.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of output parameters (defaults to empty list).
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


class SayStatement(Statement):
    """Represents a Say statement (output/display) in Machine Dialect.

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


class InteractionStatement(Statement):
    """Represents an Interaction statement (public method) in Machine Dialect.

    Interactions are public methods that can be called from outside the scope.
    They are defined using the markdown-style syntax:
    ### **Interaction**: `name`

    Attributes:
        name: The identifier naming the interaction.
        inputs: List of input parameters.
        outputs: List of output parameters.
        body: The block of statements that make up the interaction body.
        description: Optional description from the summary tag.
    """

    def __init__(
        self,
        token: Token,
        name: Identifier,
        inputs: list[Parameter] | None = None,
        outputs: list[Parameter] | None = None,
        body: BlockStatement | None = None,
        description: str = "",
    ) -> None:
        """Initialize an InteractionStatement node.

        Args:
            token: The token that begins this statement (KW_INTERACTION).
            name: The identifier naming the interaction.
            inputs: List of input parameters (defaults to empty list).
            outputs: List of output parameters (defaults to empty list).
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
