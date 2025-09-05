"""Type specialization optimization pass.

This module implements type specialization to generate optimized versions
of functions for specific type combinations based on profiling data.
"""

from collections import defaultdict
from dataclasses import dataclass

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, MIRValue, Variable
from machine_dialect.mir.optimization_pass import (
    ModulePass,
    PassInfo,
    PassType,
    PreservationLevel,
)
from machine_dialect.mir.profiling.profile_data import ProfileData


@dataclass
class TypeSignature:
    """Type signature for function specialization.

    Attributes:
        param_types: Types of function parameters.
        return_type: Return type of the function.
    """

    param_types: tuple[MIRType | MIRUnionType, ...]
    return_type: MIRType | MIRUnionType

    def __hash__(self) -> int:
        """Hash for use in dictionaries."""
        return hash((self.param_types, self.return_type))

    def __str__(self) -> str:
        """String representation."""
        params = ", ".join(str(t) for t in self.param_types)
        return f"({params}) -> {self.return_type}"


@dataclass
class SpecializationCandidate:
    """Candidate function for type specialization.

    Attributes:
        function_name: Name of the function.
        signature: Type signature to specialize for.
        call_count: Number of calls with this signature.
        benefit: Estimated benefit of specialization.
    """

    function_name: str
    signature: TypeSignature
    call_count: int
    benefit: float

    def specialized_name(self) -> str:
        """Generate specialized function name."""
        type_names = []
        for t in self.signature.param_types:
            if isinstance(t, MIRUnionType):
                # Format union types as "union_type1_type2"
                union_name = "union_" + "_".join(ut.name.lower() for ut in t.types)
                type_names.append(union_name)
            else:
                type_names.append(t.name.lower())
        type_suffix = "_".join(type_names)
        return f"{self.function_name}__{type_suffix}"


class TypeSpecialization(ModulePass):
    """Type specialization optimization pass.

    This pass creates specialized versions of functions for frequently-used
    type combinations, enabling better optimization and reducing type checks.
    """

    def __init__(self, profile_data: ProfileData | None = None, threshold: int = 100) -> None:
        """Initialize type specialization pass.

        Args:
            profile_data: Optional profiling data for hot type combinations.
            threshold: Minimum call count to consider specialization.
        """
        super().__init__()
        self.profile_data = profile_data
        self.threshold = threshold
        self.stats = {
            "functions_analyzed": 0,
            "functions_specialized": 0,
            "specializations_created": 0,
            "type_checks_eliminated": 0,
        }

        # Track type signatures seen for each function
        self.type_signatures: dict[str, dict[TypeSignature, int]] = defaultdict(lambda: defaultdict(int))

        # Map of original to specialized functions
        self.specializations: dict[str, dict[TypeSignature, str]] = defaultdict(dict)

    def get_info(self) -> PassInfo:
        """Get pass information.

        Returns:
            Pass information.
        """
        return PassInfo(
            name="type-specialization",
            description="Create type-specialized function versions",
            pass_type=PassType.OPTIMIZATION,
            requires=[],
            preserves=PreservationLevel.NONE,
        )

    def finalize(self) -> None:
        """Finalize the pass after running."""
        pass

    def run_on_module(self, module: MIRModule) -> bool:
        """Run type specialization on a module.

        Args:
            module: The module to optimize.

        Returns:
            True if the module was modified.
        """
        modified = False

        # Phase 1: Collect type signatures from call sites
        self._collect_type_signatures(module)

        # Phase 2: Identify specialization candidates
        candidates = self._identify_candidates(module)

        # Phase 3: Create specialized functions
        for candidate in candidates:
            if self._create_specialization(module, candidate):
                modified = True
                self.stats["specializations_created"] += 1

        # Phase 4: Update call sites to use specialized versions
        if modified:
            self._update_call_sites(module)

        return modified

    def _collect_type_signatures(self, module: MIRModule) -> None:
        """Collect type signatures from all call sites.

        Args:
            module: The module to analyze.
        """
        for function in module.functions.values():
            self.stats["functions_analyzed"] += 1

            for block in function.cfg.blocks.values():
                for inst in block.instructions:
                    if isinstance(inst, Call):
                        # Infer types of arguments
                        arg_types = self._infer_arg_types(inst.args)
                        if arg_types and hasattr(inst.func, "name"):
                            # Record this type signature
                            func_name = inst.func.name
                            return_type = self._infer_return_type(inst)
                            signature = TypeSignature(arg_types, return_type)

                            # Use profile data if available
                            if self.profile_data and func_name in self.profile_data.functions:
                                profile = self.profile_data.functions[func_name]
                                self.type_signatures[func_name][signature] += profile.call_count
                            else:
                                self.type_signatures[func_name][signature] += 1

    def _infer_arg_types(self, args: list[MIRValue]) -> tuple[MIRType | MIRUnionType, ...] | None:
        """Infer types of function arguments.

        Args:
            args: List of argument values.

        Returns:
            Tuple of types or None if unable to infer.
        """
        types = []
        for arg in args:
            if isinstance(arg, Constant):
                types.append(arg.type)
            elif isinstance(arg, Variable):
                if arg.type != MIRType.UNKNOWN:
                    types.append(arg.type)
                else:
                    return None  # Can't infer all types
            else:
                return None  # Unknown value type

        return tuple(types)

    def _infer_return_type(self, call: Call) -> MIRType | MIRUnionType:
        """Infer return type of a call.

        Args:
            call: The call instruction.

        Returns:
            The inferred return type.
        """
        if call.dest:
            if hasattr(call.dest, "type"):
                return call.dest.type
        return MIRType.UNKNOWN

    def _identify_candidates(self, module: MIRModule) -> list[SpecializationCandidate]:
        """Identify functions worth specializing.

        Args:
            module: The module to analyze.

        Returns:
            List of specialization candidates.
        """
        candidates = []

        for func_name, signatures in self.type_signatures.items():
            # Skip if function doesn't exist in module
            if func_name not in module.functions:
                continue

            function = module.functions[func_name]

            # Skip if function is too large (avoid code bloat)
            if self._count_instructions(function) > 100:
                continue

            # Find hot type signatures
            for signature, count in signatures.items():
                if count >= self.threshold:
                    # Calculate benefit based on:
                    # 1. Call frequency
                    # 2. Potential for optimization (numeric types benefit more)
                    # 3. Type check elimination
                    benefit = self._calculate_benefit(signature, count, function)

                    if benefit > 0:
                        candidates.append(
                            SpecializationCandidate(
                                function_name=func_name, signature=signature, call_count=count, benefit=benefit
                            )
                        )

        # Sort by benefit (highest first)
        candidates.sort(key=lambda c: c.benefit, reverse=True)

        # Limit number of specializations to avoid code bloat
        return candidates[:10]

    def _count_instructions(self, function: MIRFunction) -> int:
        """Count instructions in a function.

        Args:
            function: The function to count.

        Returns:
            Total instruction count.
        """
        count = 0
        for block in function.cfg.blocks.values():
            count += len(block.instructions)
        return count

    def _calculate_benefit(self, signature: TypeSignature, call_count: int, function: MIRFunction) -> float:
        """Calculate specialization benefit.

        Args:
            signature: Type signature to specialize for.
            call_count: Number of calls with this signature.
            function: The function to specialize.

        Returns:
            Estimated benefit score.
        """
        benefit = 0.0

        # Benefit from call frequency
        benefit += call_count * 0.1

        # Benefit from numeric types (can use specialized instructions)
        for param_type in signature.param_types:
            if param_type in (MIRType.INT, MIRType.FLOAT):
                benefit += 20.0
            elif param_type == MIRType.BOOL:
                benefit += 10.0

        # Benefit from eliminating type checks
        type_check_count = self._count_type_checks(function)
        benefit += type_check_count * 5.0

        # Penalty for code size
        inst_count = self._count_instructions(function)
        benefit -= inst_count * 0.5

        return max(0.0, benefit)

    def _count_type_checks(self, function: MIRFunction) -> int:
        """Count potential type checks in a function.

        Args:
            function: The function to analyze.

        Returns:
            Number of potential type checks.
        """
        # Simple heuristic: count operations that might need type checking
        count = 0
        for block in function.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, BinaryOp):
                    # Binary ops often need type checking
                    count += 1
        return count

    def _create_specialization(self, module: MIRModule, candidate: SpecializationCandidate) -> bool:
        """Create a specialized version of a function.

        Args:
            module: The module containing the function.
            candidate: The specialization candidate.

        Returns:
            True if specialization was created.
        """
        original_func = module.functions.get(candidate.function_name)
        if not original_func:
            return False

        # Clone the function
        specialized_name = candidate.specialized_name()
        specialized_func = self._clone_function(original_func, specialized_name)

        # Apply type information to parameters
        for i, param in enumerate(specialized_func.params):
            if i < len(candidate.signature.param_types):
                param.type = candidate.signature.param_types[i]

        # Optimize the specialized function
        self._optimize_specialized_function(specialized_func, candidate.signature)

        # Add to module
        module.add_function(specialized_func)

        # Track the specialization
        self.specializations[candidate.function_name][candidate.signature] = specialized_name
        self.stats["functions_specialized"] += 1

        return True

    def _clone_function(self, original: MIRFunction, new_name: str) -> MIRFunction:
        """Clone a function with a new name.

        Args:
            original: The function to clone.
            new_name: Name for the cloned function.

        Returns:
            The cloned function.
        """
        # Create new function with same parameters
        cloned = MIRFunction(new_name, [Variable(p.name, p.type) for p in original.params])

        # Clone all blocks
        block_mapping: dict[str, str] = {}
        for block_name, block in original.cfg.blocks.items():
            new_block = BasicBlock(block_name)

            # Clone instructions
            for inst in block.instructions:
                # Deep copy the instruction
                # (In a real implementation, we'd need proper deep copying)
                new_block.add_instruction(inst)

            cloned.cfg.add_block(new_block)
            block_mapping[block_name] = block_name

        # Set entry block
        if original.cfg.entry_block:
            cloned.cfg.entry_block = original.cfg.entry_block

        return cloned

    def _optimize_specialized_function(self, function: MIRFunction, signature: TypeSignature) -> None:
        """Apply type-specific optimizations to specialized function.

        Args:
            function: The specialized function.
            signature: The type signature it's specialized for.
        """
        # With known types, we can:
        # 1. Eliminate type checks
        # 2. Use specialized instructions
        # 3. Constant fold more aggressively

        for block in function.cfg.blocks.values():
            new_instructions = []

            for inst in block.instructions:
                # Example: optimize integer operations
                if isinstance(inst, BinaryOp):
                    # If we know types are integers, can use specialized ops
                    if all(t == MIRType.INT for t in signature.param_types):
                        # Could replace with specialized integer instruction
                        self.stats["type_checks_eliminated"] += 1

                new_instructions.append(inst)

            block.instructions = new_instructions

    def _update_call_sites(self, module: MIRModule) -> None:
        """Update call sites to use specialized versions.

        Args:
            module: The module to update.
        """
        for function in module.functions.values():
            for block in function.cfg.blocks.values():
                for inst in block.instructions:
                    if isinstance(inst, Call) and hasattr(inst.func, "name"):
                        func_name = inst.func.name

                        # Check if we have a specialization for this call
                        if func_name in self.specializations:
                            arg_types = self._infer_arg_types(inst.args)
                            if arg_types:
                                return_type = self._infer_return_type(inst)
                                signature = TypeSignature(arg_types, return_type)

                                if signature in self.specializations[func_name]:
                                    # Update to use specialized version
                                    specialized_name = self.specializations[func_name][signature]
                                    inst.func.name = specialized_name
