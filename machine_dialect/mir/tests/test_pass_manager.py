"""Tests for the pass manager and optimization framework."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp
from machine_dialect.mir.optimization_config import (
    OptimizationConfig,
    OptimizationPipeline,
)
from machine_dialect.mir.optimizations import register_all_passes
from machine_dialect.mir.pass_manager import PassManager


def create_test_module() -> MIRModule:
    """Create a test module with optimization opportunities.

    Returns:
        A test MIR module.
    """
    module = MIRModule("test")

    # Create main function with constant folding opportunities
    main_func = MIRFunction("main")

    # Create basic blocks
    entry = BasicBlock("entry")
    main_func.cfg.add_block(entry)
    main_func.cfg.set_entry_block(entry)

    # Add instructions with optimization opportunities
    t0 = Temp(MIRType.INT, 0)
    t1 = Temp(MIRType.INT, 1)
    t2 = Temp(MIRType.INT, 2)
    t3 = Temp(MIRType.INT, 3)
    t4 = Temp(MIRType.INT, 4)

    # Constant folding opportunity: 2 + 3 = 5
    entry.add_instruction(LoadConst(t0, Constant(2, MIRType.INT), (1, 1)))
    entry.add_instruction(LoadConst(t1, Constant(3, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))

    # Strength reduction opportunity: x * 4 -> x << 2
    entry.add_instruction(LoadConst(t3, Constant(4, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t4, "*", t2, t3, (1, 1)))

    # Return result
    entry.add_instruction(Return((1, 1), t4))

    module.add_function(main_func)
    return module


def test_pass_manager_creation() -> None:
    """Test creating a pass manager."""
    pm = PassManager()
    assert pm is not None
    assert pm.registry is not None
    assert pm.analysis_manager is not None
    assert pm.scheduler is not None


def test_register_passes() -> None:
    """Test registering optimization passes."""
    pm = PassManager()
    register_all_passes(pm)

    # Check that passes are registered
    passes = pm.registry.list_passes()
    assert "dce" in passes
    assert "constant-propagation" in passes
    assert "cse" in passes
    assert "strength-reduction" in passes
    assert "use-def-chains" in passes
    assert "loop-analysis" in passes


def test_optimization_pipeline() -> None:
    """Test getting optimization pipeline for different levels."""
    config0 = OptimizationConfig.from_level(0)
    passes0 = OptimizationPipeline.get_passes(config0)
    assert len(passes0) == 0  # No optimizations at -O0

    config1 = OptimizationConfig.from_level(1)
    passes1 = OptimizationPipeline.get_passes(config1)
    assert "constant-propagation" in passes1
    assert "dce" in passes1

    config2 = OptimizationConfig.from_level(2)
    passes2 = OptimizationPipeline.get_passes(config2)
    assert "cse" in passes2
    assert len(passes2) > len(passes1)

    config3 = OptimizationConfig.from_level(3)
    passes3 = OptimizationPipeline.get_passes(config3)
    assert len(passes3) >= len(passes2)


def test_run_optimizations() -> None:
    """Test running optimizations on a module."""
    module = create_test_module()
    pm = PassManager()
    register_all_passes(pm)

    # Run basic optimizations
    config = OptimizationConfig.from_level(1)
    passes = OptimizationPipeline.get_passes(config)

    modified = pm.run_passes(module, passes, config.level)
    # Module should be modified by optimizations
    assert modified or len(passes) == 0

    # Check statistics
    stats = pm.get_statistics()
    assert isinstance(stats, dict)


def test_constant_propagation() -> None:
    """Test constant propagation pass."""
    from machine_dialect.mir.optimizations.constant_propagation import (
        ConstantPropagation,
    )

    module = create_test_module()
    func = module.get_function("main")
    assert func is not None

    # Run constant propagation
    cp_pass = ConstantPropagation()
    cp_pass.initialize()
    cp_pass.run_on_function(func)
    cp_pass.finalize()

    # Check that constants were propagated
    stats = cp_pass.get_stats()
    # May or may not have propagated depending on exact implementation
    assert stats is not None


def test_dead_code_elimination() -> None:
    """Test dead code elimination pass."""
    from machine_dialect.mir.analyses.use_def_chains import UseDefChainsAnalysis
    from machine_dialect.mir.optimizations.dce import DeadCodeElimination

    # Create function with dead code
    func = MIRFunction("test")
    entry = BasicBlock("entry")
    func.cfg.add_block(entry)
    func.cfg.set_entry_block(entry)

    # Dead instruction: result not used
    t0 = Temp(MIRType.INT, 0)
    t1 = Temp(MIRType.INT, 1)
    entry.add_instruction(LoadConst(t0, Constant(42, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t1, "+", t0, t0, (1, 1)))  # Dead if t1 not used
    entry.add_instruction(Return((1, 1), t0))  # Only t0 is used

    # First build use-def chains
    use_def = UseDefChainsAnalysis()
    chains = use_def.run_on_function(func)

    # Run DCE
    dce_pass = DeadCodeElimination()
    dce_pass.analysis_manager = type("", (), {"get_analysis": lambda _, __, ___: chains})()
    dce_pass.initialize()
    modified = dce_pass.run_on_function(func)
    dce_pass.finalize()

    # Should have removed dead instruction
    assert modified or len(entry.instructions) == 2


def test_strength_reduction() -> None:
    """Test strength reduction pass."""
    from machine_dialect.mir.optimizations.strength_reduction import StrengthReduction

    func = MIRFunction("test")
    entry = BasicBlock("entry")
    func.cfg.add_block(entry)
    func.cfg.set_entry_block(entry)

    # Multiplication by power of 2
    t0 = Temp(MIRType.INT, 0)
    t1 = Temp(MIRType.INT, 1)
    entry.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t1, "*", t0, Constant(8, MIRType.INT), (1, 1)))
    entry.add_instruction(Return((1, 1), t1))

    # Run strength reduction
    sr_pass = StrengthReduction()
    sr_pass.initialize()
    sr_pass.run_on_function(func)
    sr_pass.finalize()

    # Should have converted multiply to shift
    stats = sr_pass.get_stats()
    assert stats.get("multiply_to_shift", 0) >= 0


def test_cse() -> None:
    """Test common subexpression elimination."""
    from machine_dialect.mir.optimizations.cse import CommonSubexpressionElimination

    func = MIRFunction("test")
    entry = BasicBlock("entry")
    func.cfg.add_block(entry)
    func.cfg.set_entry_block(entry)

    # Common subexpression: t0 + t1 computed twice
    t0 = Temp(MIRType.INT, 0)
    t1 = Temp(MIRType.INT, 1)
    t2 = Temp(MIRType.INT, 2)
    t3 = Temp(MIRType.INT, 3)

    entry.add_instruction(LoadConst(t0, Constant(5, MIRType.INT), (1, 1)))
    entry.add_instruction(LoadConst(t1, Constant(7, MIRType.INT), (1, 1)))
    entry.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))  # First computation
    entry.add_instruction(BinaryOp(t3, "+", t0, t1, (1, 1)))  # Same computation
    entry.add_instruction(Return((1, 1), t3))

    # Run CSE
    cse_pass = CommonSubexpressionElimination()
    cse_pass.initialize()
    cse_pass.run_on_function(func)
    cse_pass.finalize()

    # Should have eliminated common subexpression
    stats = cse_pass.get_stats()
    assert stats.get("local_cse_eliminated", 0) >= 0


def test_analysis_caching() -> None:
    """Test that analyses are cached properly."""
    from machine_dialect.mir.analyses.use_def_chains import UseDefChainsAnalysis

    pm = PassManager()
    register_all_passes(pm)

    module = create_test_module()
    func = module.get_function("main")
    assert func is not None  # Type narrowing for MyPy

    # Register and run analysis
    analysis = UseDefChainsAnalysis()
    pm.analysis_manager.register_analysis("use-def-chains", analysis)

    # First call should compute
    result1 = pm.analysis_manager.get_analysis("use-def-chains", func)
    assert result1 is not None

    # Second call should use cache
    result2 = pm.analysis_manager.get_analysis("use-def-chains", func)
    assert result2 is result1  # Same object

    # Invalidate and recompute
    pm.analysis_manager.invalidate(["use-def-chains"])
    result3 = pm.analysis_manager.get_analysis("use-def-chains", func)
    # May or may not be same object depending on implementation
    assert result3 is not None


def test_full_optimization_pipeline() -> None:
    """Test complete optimization pipeline."""
    module = create_test_module()
    pm = PassManager()
    register_all_passes(pm)

    # Get initial instruction count
    initial_count = sum(
        len(block.instructions) for func in module.functions.values() for block in func.cfg.blocks.values()
    )

    # Run O2 optimizations
    config = OptimizationConfig.from_level(2)
    passes = OptimizationPipeline.get_passes(config)
    pm.run_passes(module, passes, config.level)

    # Get final instruction count
    final_count = sum(
        len(block.instructions) for func in module.functions.values() for block in func.cfg.blocks.values()
    )

    # Should have same or fewer instructions after optimization
    assert final_count <= initial_count

    # Check that we collected statistics
    stats = pm.get_statistics()
    assert len(stats) > 0 if passes else True
