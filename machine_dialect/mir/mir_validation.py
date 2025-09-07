"""MIR validation and verification framework.

This module provides validation and verification for MIR programs,
ensuring correctness and well-formedness of the intermediate representation.
"""

from machine_dialect.mir.basic_block import CFG, BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    LoadVar,
    MIRInstruction,
    Phi,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import FunctionRef, Temp, Variable


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


class MIRValidator:
    """Validates MIR modules, functions, and instructions."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_module(self, module: MIRModule) -> bool:
        """Validate an entire MIR module.

        Args:
            module: The module to validate.

        Returns:
            True if validation passes, False otherwise.
        """
        self.errors.clear()
        self.warnings.clear()

        # Check module structure
        if not module.name:
            self.errors.append("Module must have a name")

        # Validate each function
        for func_name, func in module.functions.items():
            if not self._validate_function(func, func_name):
                self.errors.append(f"Function '{func_name}' validation failed")

        # Check main function if specified
        if module.main_function:
            if module.main_function not in module.functions:
                self.errors.append(f"Main function '{module.main_function}' not found in module")

        return len(self.errors) == 0

    def _validate_function(self, func: MIRFunction, name: str) -> bool:
        """Validate a MIR function.

        Args:
            func: The function to validate.
            name: The function name.

        Returns:
            True if validation passes, False otherwise.
        """
        func_errors = []

        # Check function name matches
        if func.name != name:
            func_errors.append(f"Function name mismatch: {func.name} vs {name}")

        # Validate parameters
        param_names = set()
        for param in func.params:
            if not isinstance(param, Variable):
                func_errors.append(f"Parameter must be Variable, got {type(param)}")
            elif param.name in param_names:
                func_errors.append(f"Duplicate parameter name: {param.name}")
            else:
                param_names.add(param.name)

        # Validate CFG
        if not self._validate_cfg(func.cfg):
            func_errors.append("CFG validation failed")

        # Validate each block
        for block_label, block in func.cfg.blocks.items():
            if not self._validate_block(block, block_label, func):
                func_errors.append(f"Block '{block_label}' validation failed")

        # Check that all locals are defined
        for local in func.locals.values():
            if not isinstance(local, Variable):
                func_errors.append(f"Local must be Variable, got {type(local)}")

        # Check that all temporaries are valid
        for temp in func.temporaries:
            if not isinstance(temp, Temp):
                func_errors.append(f"Temporary must be Temp, got {type(temp)}")

        if func_errors:
            self.errors.extend(func_errors)
            return False
        return True

    def _validate_cfg(self, cfg: CFG) -> bool:
        """Validate a control flow graph.

        Args:
            cfg: The CFG to validate.

        Returns:
            True if validation passes, False otherwise.
        """
        cfg_errors = []

        # Check entry block exists
        if cfg.entry_block is None:
            cfg_errors.append("CFG must have an entry block")
        elif cfg.entry_block not in cfg.blocks.values():
            cfg_errors.append("Entry block not in CFG blocks")

        # Check block connectivity
        for block_label, block in cfg.blocks.items():
            if block.label != block_label:
                cfg_errors.append(f"Block label mismatch: {block.label} vs {block_label}")

            # Check predecessors
            for pred in block.predecessors:
                if block not in pred.successors:
                    cfg_errors.append(f"Inconsistent CFG: {pred.label} -> {block.label} not bidirectional")

            # Check successors
            for succ in block.successors:
                if block not in succ.predecessors:
                    cfg_errors.append(f"Inconsistent CFG: {block.label} -> {succ.label} not bidirectional")

        # Check for unreachable blocks
        if cfg.entry_block:
            reachable = self._compute_reachable_blocks(cfg)
            for block in cfg.blocks.values():
                if block not in reachable:
                    self.warnings.append(f"Block '{block.label}' is unreachable")

        if cfg_errors:
            self.errors.extend(cfg_errors)
            return False
        return True

    def _compute_reachable_blocks(self, cfg: CFG) -> set[BasicBlock]:
        """Compute reachable blocks from entry.

        Args:
            cfg: The control flow graph.

        Returns:
            Set of reachable blocks.
        """
        if not cfg.entry_block:
            return set()

        reachable = set()
        worklist = [cfg.entry_block]

        while worklist:
            block = worklist.pop()
            if block in reachable:
                continue
            reachable.add(block)

            # Add successors to worklist
            for succ in block.successors:
                if succ not in reachable:
                    worklist.append(succ)

        return reachable

    def _validate_block(self, block: BasicBlock, label: str, func: MIRFunction) -> bool:
        """Validate a basic block.

        Args:
            block: The block to validate.
            label: Expected block label.
            func: The containing function.

        Returns:
            True if validation passes, False otherwise.
        """
        block_errors = []

        # Check label
        if block.label != label:
            block_errors.append(f"Block label mismatch: {block.label} vs {label}")

        # Validate instructions
        for i, inst in enumerate(block.instructions):
            if not self._validate_instruction(inst, block, func):
                block_errors.append(f"Instruction {i} validation failed: {inst}")

        # Check terminator
        if block.instructions:
            last_inst = block.instructions[-1]
            if isinstance(last_inst, Jump | ConditionalJump | Return):
                # Valid terminator
                pass
            else:
                # Check if block has successors
                if block.successors:
                    self.warnings.append(f"Block '{block.label}' has successors but no terminator")

        # Validate phi nodes
        for phi in block.phi_nodes:
            if not self._validate_instruction(phi, block, func):
                return False

        # Check that no phi nodes are in regular instructions (they should be in phi_nodes)
        for inst in block.instructions:
            if isinstance(inst, Phi):
                block_errors.append("Phi nodes must be in phi_nodes list, not instructions")

        if block_errors:
            self.errors.extend(block_errors)
            return False
        return True

    def _validate_instruction(self, inst: MIRInstruction, block: BasicBlock, func: MIRFunction) -> bool:
        """Validate a single instruction.

        Args:
            inst: The instruction to validate.
            block: The containing block.
            func: The containing function.

        Returns:
            True if validation passes, False otherwise.
        """
        # Type-specific validation
        if isinstance(inst, BinaryOp):
            return self._validate_binary_op(inst)
        elif isinstance(inst, UnaryOp):
            return self._validate_unary_op(inst)
        elif isinstance(inst, Call):
            return self._validate_call(inst, func)
        elif isinstance(inst, Jump):
            return self._validate_jump(inst, func)
        elif isinstance(inst, ConditionalJump):
            return self._validate_conditional_jump(inst, func)
        elif isinstance(inst, Phi):
            return self._validate_phi(inst, block, func)
        elif isinstance(inst, Return):
            return self._validate_return(inst, func)
        elif isinstance(inst, Copy | LoadConst | LoadVar | StoreVar):
            # These are generally valid if their operands are valid
            return True
        else:
            # Unknown instruction type is valid (for extensibility)
            return True

    def _validate_binary_op(self, inst: BinaryOp) -> bool:
        """Validate a binary operation.

        Args:
            inst: The binary operation.

        Returns:
            True if valid.
        """
        valid_ops = {
            "+",
            "-",
            "*",
            "/",
            "%",
            "^",
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "and",
            "or",
        }
        if inst.op not in valid_ops:
            self.errors.append(f"Invalid binary operator: {inst.op}")
            return False
        return True

    def _validate_unary_op(self, inst: UnaryOp) -> bool:
        """Validate a unary operation.

        Args:
            inst: The unary operation.

        Returns:
            True if valid.
        """
        valid_ops = {"-", "not"}
        if inst.op not in valid_ops:
            self.errors.append(f"Invalid unary operator: {inst.op}")
            return False
        return True

    def _validate_call(self, inst: Call, func: MIRFunction) -> bool:
        """Validate a call instruction.

        Args:
            inst: The call instruction.
            func: The containing function.

        Returns:
            True if valid.
        """
        if not isinstance(inst.func, FunctionRef):
            self.errors.append(f"Call target must be FunctionRef, got {type(inst.func)}")
            return False
        return True

    def _validate_jump(self, inst: Jump, func: MIRFunction) -> bool:
        """Validate a jump instruction.

        Args:
            inst: The jump instruction.
            func: The containing function.

        Returns:
            True if valid.
        """
        if inst.label not in func.cfg.blocks:
            self.errors.append(f"Jump target '{inst.label}' not found")
            return False
        return True

    def _validate_conditional_jump(self, inst: ConditionalJump, func: MIRFunction) -> bool:
        """Validate a conditional jump instruction.

        Args:
            inst: The conditional jump instruction.
            func: The containing function.

        Returns:
            True if valid.
        """
        if inst.true_label not in func.cfg.blocks:
            self.errors.append(f"Jump target '{inst.true_label}' not found")
            return False
        if inst.false_label and inst.false_label not in func.cfg.blocks:
            self.errors.append(f"Jump target '{inst.false_label}' not found")
            return False
        return True

    def _validate_phi(self, inst: Phi, block: BasicBlock, func: MIRFunction) -> bool:
        """Validate a phi node.

        Args:
            inst: The phi node.
            block: The containing block.
            func: The containing function.

        Returns:
            True if valid.
        """
        # Check that incoming blocks are predecessors
        incoming_labels = {label for _, label in inst.incoming}
        pred_labels = {pred.label for pred in block.predecessors}

        for label in incoming_labels:
            if label not in pred_labels:
                self.errors.append(f"Phi node has incoming from '{label}' which is not a predecessor")
                return False

        # Warn if missing predecessors
        for pred_label in pred_labels:
            if pred_label not in incoming_labels:
                self.warnings.append(f"Phi node missing incoming value from predecessor '{pred_label}'")

        return True

    def _validate_return(self, inst: Return, func: MIRFunction) -> bool:
        """Validate a return instruction.

        Args:
            inst: The return instruction.
            func: The containing function.

        Returns:
            True if valid.
        """
        # Check return type consistency
        if func.return_type == MIRType.EMPTY:
            if inst.value is not None:
                self.warnings.append("Function returns EMPTY but return has value")
        else:
            if inst.value is None:
                self.warnings.append(f"Function returns {func.return_type} but return has no value")

        return True

    def get_errors(self) -> list[str]:
        """Get validation errors.

        Returns:
            List of error messages.
        """
        return self.errors.copy()

    def get_warnings(self) -> list[str]:
        """Get validation warnings.

        Returns:
            List of warning messages.
        """
        return self.warnings.copy()


def validate_module(module: MIRModule) -> tuple[bool, list[str], list[str]]:
    """Validate a MIR module.

    Args:
        module: The module to validate.

    Returns:
        Tuple of (success, errors, warnings).
    """
    validator = MIRValidator()
    success = validator.validate_module(module)
    return success, validator.get_errors(), validator.get_warnings()


def validate_function(func: MIRFunction) -> tuple[bool, list[str], list[str]]:
    """Validate a MIR function.

    Args:
        func: The function to validate.

    Returns:
        Tuple of (success, errors, warnings).
    """
    validator = MIRValidator()
    success = validator._validate_function(func, func.name)
    return success, validator.get_errors(), validator.get_warnings()
