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

from enum import Enum, auto

from machine_dialect.ast import ASTNode, Expression, Identifier
from machine_dialect.lexer import Token


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

    def canonicalize(self) -> "Statement":
        """Default canonicalize for statements returns self.

        Returns:
            Self unchanged.
        """
        return self


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

    def canonicalize(self) -> "ExpressionStatement":
        """Canonicalize expression statement by recursively canonicalizing the expression.

        Returns:
            A new ExpressionStatement with canonicalized expression.
        """
        canonicalized = ExpressionStatement(self.token, None)
        if self.expression:
            expr_canon = self.expression.canonicalize()
            assert isinstance(expr_canon, Expression)
            canonicalized.expression = expr_canon
        return canonicalized


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

    def canonicalize(self) -> "ReturnStatement":
        """Canonicalize return statement by recursively canonicalizing return value.

        Returns:
            A new ReturnStatement with canonicalized return value.
        """
        canonicalized = ReturnStatement(self.token)
        if self.return_value:
            return_canon = self.return_value.canonicalize()
            assert isinstance(return_canon, Expression)
            canonicalized.return_value = return_canon
        return canonicalized


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

    def canonicalize(self) -> "SetStatement":
        """Canonicalize set statement by recursively canonicalizing name and value.

        Returns:
            A new SetStatement with canonicalized components.
        """
        canonicalized = SetStatement(self.token)
        if self.name:
            name_canon = self.name.canonicalize()
            assert isinstance(name_canon, Identifier)
            canonicalized.name = name_canon
        if self.value:
            value_canon = self.value.canonicalize()
            assert isinstance(value_canon, Expression)
            canonicalized.value = value_canon
        return canonicalized


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

    def canonicalize(self) -> "BlockStatement":
        """Canonicalize block statement by recursively canonicalizing all statements.

        Returns:
            A new BlockStatement with canonicalized statements.
        """
        canonicalized_statements = [stmt.canonicalize() for stmt in self.statements]
        canonicalized = BlockStatement(self.token, self.depth)
        canonicalized.statements = canonicalized_statements
        return canonicalized


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

    def canonicalize(self) -> "IfStatement":
        """Canonicalize if statement by recursively canonicalizing all components.

        Returns:
            A new IfStatement with canonicalized condition, consequence, and alternative.
        """
        canonicalized = IfStatement(self.token)
        if self.condition:
            condition_canon = self.condition.canonicalize()
            assert isinstance(condition_canon, Expression)
            canonicalized.condition = condition_canon
        if self.consequence:
            consequence_canon = self.consequence.canonicalize()
            assert isinstance(consequence_canon, BlockStatement)
            canonicalized.consequence = consequence_canon
        if self.alternative:
            alternative_canon = self.alternative.canonicalize()
            assert isinstance(alternative_canon, BlockStatement)
            canonicalized.alternative = alternative_canon
        return canonicalized


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
    """Represents an Action statement (private method) in Machine Dialect.

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
    """Represents an Interaction statement (public method) in Machine Dialect.

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
    """Represents a Utility statement (function) in Machine Dialect.

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
