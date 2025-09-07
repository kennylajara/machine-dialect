"""Type inference for MIR.

This module implements type inference and propagation for MIR values.
"""

from machine_dialect.ast import (
    ASTNode,
    EmptyLiteral,
    FloatLiteral,
    Identifier,
    InfixExpression,
    PrefixExpression,
    StringLiteral,
    URLLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    Copy,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Phi,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType, MIRUnionType, get_binary_op_result_type, get_unary_op_result_type
from machine_dialect.mir.mir_values import Constant, MIRValue, Variable


class TypeInferencer:
    """Type inference for MIR values and instructions."""

    def __init__(self) -> None:
        """Initialize the type inferencer."""
        self.type_map: dict[MIRValue, MIRType | MIRUnionType] = {}
        self.constraints: list[tuple[MIRValue, MIRValue]] = []

    def infer_module_types(self, module: MIRModule) -> None:
        """Infer types for all functions in a module.

        Args:
            module: The MIR module to infer types for.
        """
        for func in module.functions.values():
            self.infer_function_types(func)

    def infer_function_types(self, function: MIRFunction) -> None:
        """Infer types for a MIR function.

        Args:
            function: The function to infer types for.
        """
        # Initialize parameter types
        for param in function.params:
            if param.type == MIRType.UNKNOWN:
                # Try to infer from usage
                param.type = self._infer_parameter_type(param, function)
            self.type_map[param] = param.type

        # Forward pass: propagate types through instructions
        changed = True
        iterations = 0
        max_iterations = 10  # Prevent infinite loops

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for block in function.cfg.blocks.values():
                for inst in block.instructions:
                    if self._infer_instruction_types(inst):
                        changed = True

        # Backward pass: infer from usage
        for _ in range(2):  # Limited backward passes
            for block in function.cfg.blocks.values():
                for inst in block.instructions:
                    self._backward_infer_types(inst)

        # Apply inferred types back to values
        self._apply_inferred_types(function)

    def _infer_parameter_type(self, param: Variable, function: MIRFunction) -> MIRType | MIRUnionType:
        """Infer parameter type from its usage in the function.

        Args:
            param: The parameter to infer type for.
            function: The function containing the parameter.

        Returns:
            The inferred type or UNKNOWN if unable to infer.
        """
        # Look for first usage of parameter
        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, BinaryOp):
                    if inst.left == param or inst.right == param:
                        # Infer from operation
                        if inst.op in ["+", "-", "*", "/", "%"]:
                            return MIRType.INT  # Assume numeric
                        elif inst.op in ["and", "or"]:
                            return MIRType.BOOL
                elif isinstance(inst, UnaryOp):
                    if inst.operand == param:
                        if inst.op == "not":
                            return MIRType.BOOL
                        elif inst.op == "-":
                            return MIRType.INT

        return MIRType.UNKNOWN

    def _infer_instruction_types(self, inst: MIRInstruction) -> bool:
        """Infer types for an instruction.

        Args:
            inst: The instruction to infer types for.

        Returns:
            True if any type was updated.
        """
        changed = False

        if isinstance(inst, LoadConst):
            # Constant has explicit type
            if inst.constant.type != MIRType.UNKNOWN:
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = inst.constant.type
                if old_type != inst.constant.type:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = inst.constant.type

        elif isinstance(inst, Copy):
            # Copy propagates type
            if inst.source in self.type_map:
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = self.type_map[inst.source]
                if old_type != self.type_map[inst.source]:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = self.type_map[inst.source]

        elif isinstance(inst, BinaryOp):
            # Infer result type from operands
            left_type = self._get_type(inst.left)
            right_type = self._get_type(inst.right)

            if left_type != MIRType.UNKNOWN and right_type != MIRType.UNKNOWN:
                result_type = get_binary_op_result_type(inst.op, left_type, right_type)
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = result_type
                if old_type != result_type:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = result_type

        elif isinstance(inst, UnaryOp):
            # Infer result type from operand
            operand_type = self._get_type(inst.operand)

            if operand_type != MIRType.UNKNOWN:
                result_type = get_unary_op_result_type(inst.op, operand_type)
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = result_type
                if old_type != result_type:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = result_type

        elif isinstance(inst, StoreVar):
            # Store propagates type to variable
            if inst.source in self.type_map:
                old_type = self.type_map.get(inst.var, MIRType.UNKNOWN)
                self.type_map[inst.var] = self.type_map[inst.source]
                if old_type != self.type_map[inst.source]:
                    changed = True
                    if hasattr(inst.var, "type"):
                        inst.var.type = self.type_map[inst.source]

        elif isinstance(inst, LoadVar):
            # Load propagates type from variable
            if inst.var in self.type_map:
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = self.type_map[inst.var]
                if old_type != self.type_map[inst.var]:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = self.type_map[inst.var]

        elif isinstance(inst, Phi):
            # Phi node: unify types of incoming values
            types = set()
            for value, _ in inst.incoming:
                val_type = self._get_type(value)
                if val_type != MIRType.UNKNOWN:
                    types.add(val_type)

            if len(types) == 1:
                # All incoming values have same type
                unified_type = types.pop()
                old_type = self.type_map.get(inst.dest, MIRType.UNKNOWN)
                self.type_map[inst.dest] = unified_type
                if old_type != unified_type:
                    changed = True
                    if hasattr(inst.dest, "type"):
                        inst.dest.type = unified_type

        elif isinstance(inst, Call):
            # For now, assume functions return UNKNOWN
            # This could be improved with function signature analysis
            pass

        elif isinstance(inst, Return):
            # Return doesn't define any values
            pass

        return changed

    def _backward_infer_types(self, inst: MIRInstruction) -> None:
        """Backward type inference from usage.

        Args:
            inst: The instruction to backward infer from.
        """
        if isinstance(inst, BinaryOp):
            # If we know the result type, we might infer operand types
            if inst.dest in self.type_map:
                result_type = self.type_map[inst.dest]

                # For comparison operators, operands can be any comparable type
                if inst.op in ["==", "!=", "<", ">", "<=", ">="]:
                    # Result is boolean, operands could be numeric
                    if inst.left not in self.type_map:
                        self.type_map[inst.left] = MIRType.INT
                        if hasattr(inst.left, "type"):
                            inst.left.type = MIRType.INT
                    if inst.right not in self.type_map:
                        self.type_map[inst.right] = MIRType.INT
                        if hasattr(inst.right, "type"):
                            inst.right.type = MIRType.INT

                # For arithmetic, operands match result type
                elif inst.op in ["+", "-", "*", "/", "%"]:
                    if inst.left not in self.type_map:
                        self.type_map[inst.left] = result_type
                        if hasattr(inst.left, "type"):
                            inst.left.type = result_type
                    if inst.right not in self.type_map:
                        self.type_map[inst.right] = result_type
                        if hasattr(inst.right, "type"):
                            inst.right.type = result_type

    def _get_type(self, value: MIRValue) -> MIRType | MIRUnionType:
        """Get the type of a MIR value.

        Args:
            value: The value to get type for.

        Returns:
            The type of the value.
        """
        # Check type map first
        if value in self.type_map:
            return self.type_map[value]

        # Check if value has explicit type
        if hasattr(value, "type"):
            return value.type

        # Constants have explicit types
        if isinstance(value, Constant):
            return value.type

        return MIRType.UNKNOWN

    def _apply_inferred_types(self, function: MIRFunction) -> None:
        """Apply inferred types back to MIR values.

        Args:
            function: The function to apply types to.
        """
        # Update all temps and variables with inferred types
        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                for def_val in inst.get_defs():
                    if def_val in self.type_map:
                        if hasattr(def_val, "type"):
                            def_val.type = self.type_map[def_val]

                for use_val in inst.get_uses():
                    if use_val in self.type_map:
                        if hasattr(use_val, "type"):
                            use_val.type = self.type_map[use_val]


def infer_ast_literal_type(literal: ASTNode) -> MIRType:
    """Infer MIR type from AST literal.

    Args:
        literal: The AST literal node.

    Returns:
        The inferred MIR type.
    """
    if isinstance(literal, WholeNumberLiteral):
        return MIRType.INT
    elif isinstance(literal, FloatLiteral):
        return MIRType.FLOAT
    elif isinstance(literal, StringLiteral):
        return MIRType.STRING
    elif isinstance(literal, YesNoLiteral):
        return MIRType.BOOL
    elif isinstance(literal, EmptyLiteral):
        return MIRType.EMPTY
    elif isinstance(literal, URLLiteral):
        return MIRType.URL
    else:
        return MIRType.UNKNOWN


def infer_ast_expression_type(expr: ASTNode, context: dict[str, MIRType | MIRUnionType]) -> MIRType | MIRUnionType:
    """Infer MIR type from AST expression.

    Args:
        expr: The AST expression node.
        context: Variable type context.

    Returns:
        The inferred MIR type.
    """
    if isinstance(expr, WholeNumberLiteral | FloatLiteral | StringLiteral | YesNoLiteral | EmptyLiteral | URLLiteral):
        return infer_ast_literal_type(expr)

    elif isinstance(expr, Identifier):
        # Look up in context
        return context.get(expr.value, MIRType.UNKNOWN)

    elif isinstance(expr, InfixExpression):
        # Infer from operation
        if expr.operator in ["==", "!=", "<", ">", "<=", ">="]:
            return MIRType.BOOL
        elif expr.operator in ["and", "or"]:
            return MIRType.BOOL
        elif expr.operator in ["+", "-", "*", "/", "%", "^"]:
            # Infer from operands
            left_type = infer_ast_expression_type(expr.left, context)
            if expr.right:
                right_type = infer_ast_expression_type(expr.right, context)
                # If either is float, result is float
                if left_type == MIRType.FLOAT or right_type == MIRType.FLOAT:
                    return MIRType.FLOAT
            return left_type if left_type != MIRType.UNKNOWN else MIRType.INT

    elif isinstance(expr, PrefixExpression):
        if expr.operator == "not":
            return MIRType.BOOL
        elif expr.operator == "-":
            if expr.right:
                operand_type = infer_ast_expression_type(expr.right, context)
                return operand_type if operand_type != MIRType.UNKNOWN else MIRType.INT

    return MIRType.UNKNOWN
