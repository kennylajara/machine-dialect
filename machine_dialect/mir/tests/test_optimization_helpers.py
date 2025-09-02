"""Helper utilities for testing optimization passes."""

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimization_pass import OptimizationPass
from machine_dialect.mir.pass_manager import PassManager


def run_optimization_with_analyses(
    pass_manager: PassManager,
    pass_name: str,
    function: MIRFunction,
    required_analyses: list[str] | None = None,
) -> bool:
    """Run an optimization pass with its required analyses.

    Args:
        pass_manager: The pass manager.
        pass_name: Name of the optimization pass.
        function: Function to optimize.
        required_analyses: List of required analysis names.

    Returns:
        True if the function was modified.
    """
    # Create a module if needed
    module = MIRModule("test")
    module.functions[function.name] = function

    # Get the optimization pass
    opt_pass = pass_manager.registry.get_pass(pass_name)
    if not opt_pass:
        return False

    # For optimization passes, set up the analysis manager
    if isinstance(opt_pass, OptimizationPass):
        opt_pass.analysis_manager = pass_manager.analysis_manager

        # Run required analyses
        if required_analyses:
            for analysis_name in required_analyses:
                analysis_pass = pass_manager.registry.get_pass(analysis_name)
                if analysis_pass:
                    # Store the analysis result
                    result = analysis_pass.run_on_function(function)
                    # Cache it in a simple way - just store the pass itself
                    # which has the result
                    pass_manager.analysis_manager._analyses[analysis_name] = analysis_pass

    # Run the optimization
    return opt_pass.run_on_function(function)
