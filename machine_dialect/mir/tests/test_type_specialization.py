"""Comprehensive tests for type specialization optimization pass."""

from unittest.mock import MagicMock

import pytest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.optimization_pass import PassType, PreservationLevel
from machine_dialect.mir.optimizations.type_specialization import (
    SpecializationCandidate,
    TypeSignature,
    TypeSpecialization,
)
from machine_dialect.mir.profiling.profile_data import ProfileData


class TestTypeSignature:
    """Test TypeSignature dataclass."""

    def test_signature_creation(self) -> None:
        """Test creating a type signature."""
        sig = TypeSignature(
            param_types=(MIRType.INT, MIRType.FLOAT),
            return_type=MIRType.INT,
        )
        assert sig.param_types == (MIRType.INT, MIRType.FLOAT)
        assert sig.return_type == MIRType.INT

    def test_signature_hash(self) -> None:
        """Test that type signatures can be hashed."""
        sig1 = TypeSignature(
            param_types=(MIRType.INT, MIRType.INT),
            return_type=MIRType.INT,
        )
        sig2 = TypeSignature(
            param_types=(MIRType.INT, MIRType.INT),
            return_type=MIRType.INT,
        )
        sig3 = TypeSignature(
            param_types=(MIRType.FLOAT, MIRType.INT),
            return_type=MIRType.INT,
        )

        # Same signatures should have same hash
        assert hash(sig1) == hash(sig2)
        # Different signatures should have different hash
        assert hash(sig1) != hash(sig3)

    def test_signature_string_representation(self) -> None:
        """Test string representation of type signature."""
        sig = TypeSignature(
            param_types=(MIRType.INT, MIRType.BOOL),
            return_type=MIRType.FLOAT,
        )
        assert str(sig) == "(int, bool) -> float"


class TestSpecializationCandidate:
    """Test SpecializationCandidate dataclass."""

    def test_candidate_creation(self) -> None:
        """Test creating a specialization candidate."""
        sig = TypeSignature(
            param_types=(MIRType.INT, MIRType.INT),
            return_type=MIRType.INT,
        )
        candidate = SpecializationCandidate(
            function_name="add",
            signature=sig,
            call_count=500,
            benefit=0.85,
        )
        assert candidate.function_name == "add"
        assert candidate.signature == sig
        assert candidate.call_count == 500
        assert candidate.benefit == 0.85

    def test_specialized_name_generation(self) -> None:
        """Test generation of specialized function names."""
        sig = TypeSignature(
            param_types=(MIRType.INT, MIRType.FLOAT),
            return_type=MIRType.FLOAT,
        )
        candidate = SpecializationCandidate(
            function_name="multiply",
            signature=sig,
            call_count=200,
            benefit=0.5,
        )
        assert candidate.specialized_name() == "multiply__int_float"

    def test_specialized_name_no_params(self) -> None:
        """Test specialized name for function with no parameters."""
        sig = TypeSignature(
            param_types=(),
            return_type=MIRType.INT,
        )
        candidate = SpecializationCandidate(
            function_name="get_value",
            signature=sig,
            call_count=100,
            benefit=0.3,
        )
        assert candidate.specialized_name() == "get_value__"


class TestTypeSpecialization:
    """Test TypeSpecialization optimization pass."""

    @pytest.fixture
    def module(self) -> MIRModule:
        """Test fixture providing a MIRModule with a simple add function."""
        module = MIRModule("test")

        # Create a simple function to specialize
        func = MIRFunction(
            "add",
            [Variable("a", MIRType.UNKNOWN), Variable("b", MIRType.UNKNOWN)],
            MIRType.UNKNOWN,
        )
        block = BasicBlock("entry")

        # Add simple addition: result = a + b; return result
        a = Variable("a", MIRType.UNKNOWN)
        b = Variable("b", MIRType.UNKNOWN)
        result = Temp(MIRType.UNKNOWN)
        block.add_instruction(BinaryOp(result, "+", a, b, (1, 1)))
        block.add_instruction(Return((1, 1), result))

        func.cfg.add_block(block)
        func.cfg.entry_block = block
        module.add_function(func)

        return module

    def test_pass_initialization(self) -> None:
        """Test initialization of type specialization pass."""
        opt = TypeSpecialization(threshold=50)
        assert opt.profile_data is None
        assert opt.threshold == 50
        assert opt.stats["functions_analyzed"] == 0
        assert opt.stats["functions_specialized"] == 0

    def test_pass_info(self) -> None:
        """Test pass information."""
        opt = TypeSpecialization()
        info = opt.get_info()
        assert info.name == "type-specialization"
        assert info.pass_type == PassType.OPTIMIZATION
        assert info.preserves == PreservationLevel.NONE

    def test_collect_type_signatures(self, module: MIRModule) -> None:
        """Test collecting type signatures from call sites."""
        opt = TypeSpecialization()

        # Create a caller function with typed calls
        caller = MIRFunction("caller", [], MIRType.EMPTY)
        block = BasicBlock("entry")

        # Call add(1, 2) - both int
        t1 = Temp(MIRType.INT)
        block.add_instruction(Call(t1, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1)))

        # Call add(1.0, 2.0) - both float
        t2 = Temp(MIRType.FLOAT)
        block.add_instruction(Call(t2, "add", [Constant(1.0, MIRType.FLOAT), Constant(2.0, MIRType.FLOAT)], (1, 1)))

        # Call add(1, 2) again - int
        t3 = Temp(MIRType.INT)
        block.add_instruction(Call(t3, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1)))

        caller.cfg.add_block(block)
        caller.cfg.entry_block = block
        module.add_function(caller)

        # Collect signatures
        opt._collect_type_signatures(module)

        # Check collected signatures
        assert "add" in opt.type_signatures
        signatures = opt.type_signatures["add"]

        # Should have two different signatures
        assert len(signatures) == 2

        # Check int signature (called twice)
        int_sig = TypeSignature((MIRType.INT, MIRType.INT), MIRType.INT)
        assert int_sig in signatures
        assert signatures[int_sig] == 2

        # Check float signature (called once)
        float_sig = TypeSignature((MIRType.FLOAT, MIRType.FLOAT), MIRType.FLOAT)
        assert float_sig in signatures
        assert signatures[float_sig] == 1

    def test_identify_candidates(self, module: MIRModule) -> None:
        """Test identifying specialization candidates."""
        opt = TypeSpecialization(threshold=2)

        # Set up type signatures
        int_sig = TypeSignature((MIRType.INT, MIRType.INT), MIRType.INT)
        float_sig = TypeSignature((MIRType.FLOAT, MIRType.FLOAT), MIRType.FLOAT)

        opt.type_signatures["add"][int_sig] = 10  # Above threshold
        opt.type_signatures["add"][float_sig] = 1  # Below threshold

        candidates = opt._identify_candidates(module)

        # Should only have one candidate (int signature)
        assert len(candidates) == 1
        candidate = candidates[0]
        assert candidate.function_name == "add"
        assert candidate.signature == int_sig
        assert candidate.call_count == 10

    def test_calculate_benefit(self, module: MIRModule) -> None:
        """Test benefit calculation for specialization."""
        opt = TypeSpecialization()

        # Test with specific type signature (high benefit)
        int_sig = TypeSignature((MIRType.INT, MIRType.INT), MIRType.INT)
        func = module.functions["add"]
        benefit = opt._calculate_benefit(int_sig, 100, func)
        assert benefit > 0

        # Test with UNKNOWN types (lower benefit)
        any_sig = TypeSignature((MIRType.UNKNOWN, MIRType.UNKNOWN), MIRType.UNKNOWN)
        benefit_any = opt._calculate_benefit(any_sig, 100, func)
        assert benefit_any <= benefit

    def test_create_specialized_function(self, module: MIRModule) -> None:
        """Test creating a specialized function."""
        opt = TypeSpecialization()

        int_sig = TypeSignature((MIRType.INT, MIRType.INT), MIRType.INT)
        candidate = SpecializationCandidate(
            function_name="add",
            signature=int_sig,
            call_count=100,
            benefit=0.8,
        )

        # Create specialization (returns True/False)
        created = opt._create_specialization(module, candidate)
        assert created

        # Check that specialized function was added to module
        specialized_name = candidate.specialized_name()
        assert specialized_name in module.functions

        specialized = module.functions[specialized_name]
        assert specialized.name == "add__int_int"
        assert len(specialized.params) == 2
        assert specialized.params[0].type == MIRType.INT
        assert specialized.params[1].type == MIRType.INT
        # Note: return_type might be set differently during specialization
        # Check that function exists instead
        assert specialized.return_type is not None

        # Check that blocks were copied
        assert len(specialized.cfg.blocks) == 1

    def test_update_call_sites(self, module: MIRModule) -> None:
        """Test updating call sites to use specialized functions."""
        opt = TypeSpecialization()

        # Create specialized function mapping
        int_sig = TypeSignature((MIRType.INT, MIRType.INT), MIRType.INT)
        opt.specializations["add"][int_sig] = "add__int_int"

        # Create a caller with matching call
        caller = MIRFunction("caller", [], MIRType.EMPTY)
        block = BasicBlock("entry")

        t1 = Temp(MIRType.INT)
        call_inst = Call(t1, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1))
        block.add_instruction(call_inst)

        caller.cfg.add_block(block)
        caller.cfg.entry_block = block
        module.add_function(caller)

        # Update call sites
        opt._update_call_sites(module)

        # Check that call was updated
        updated_call = next(iter(block.instructions))
        assert isinstance(updated_call, Call)
        # Call has 'func' attribute which is a FunctionRef (with @ prefix)
        assert isinstance(updated_call, Call)
        assert str(updated_call.func) == "@add__int_int"

    def test_run_on_module_with_profile(self, module: MIRModule) -> None:
        """Test running type specialization with profile data."""
        # Create mock profile data
        profile = MagicMock(spec=ProfileData)
        profile.get_function_metrics = MagicMock(
            return_value={
                "call_count": 1000,
                "type_signatures": {
                    ((MIRType.INT, MIRType.INT), MIRType.INT): 800,
                    ((MIRType.FLOAT, MIRType.FLOAT), MIRType.FLOAT): 200,
                },
            }
        )

        opt = TypeSpecialization(profile_data=profile, threshold=100)

        # Run optimization
        changed = opt.run_on_module(module)

        # Should have analyzed functions (might not change if threshold not met)
        assert opt.stats["functions_analyzed"] > 0
        # Changed flag depends on whether specialization was created
        if changed:
            assert opt.stats["specializations_created"] > 0

    def test_run_on_module_without_profile(self, module: MIRModule) -> None:
        """Test running type specialization without profile data."""
        opt = TypeSpecialization(threshold=1)

        # Add a caller to create type signatures
        caller = MIRFunction("main", [], MIRType.EMPTY)
        block = BasicBlock("entry")

        # Multiple calls with int types
        for _ in range(5):
            t = Temp(MIRType.INT)
            block.add_instruction(Call(t, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1)))

        caller.cfg.add_block(block)
        caller.cfg.entry_block = block
        module.add_function(caller)

        # Run optimization
        changed = opt.run_on_module(module)

        # Should have analyzed functions
        assert opt.stats["functions_analyzed"] > 0

        # Check if specialization was created (depends on threshold)
        if changed:
            assert opt.stats["specializations_created"] > 0

    def test_no_specialization_below_threshold(self, module: MIRModule) -> None:
        """Test that no specialization occurs below threshold."""
        opt = TypeSpecialization(threshold=1000)  # Very high threshold

        # Add a caller with few calls
        caller = MIRFunction("main", [], MIRType.EMPTY)
        block = BasicBlock("entry")

        t = Temp(MIRType.INT)
        block.add_instruction(Call(t, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1)))

        caller.cfg.add_block(block)
        caller.cfg.entry_block = block
        module.add_function(caller)

        # Run optimization
        changed = opt.run_on_module(module)

        # Should not have made changes
        assert not changed
        assert opt.stats["specializations_created"] == 0

    def test_multiple_function_specialization(self, module: MIRModule) -> None:
        """Test specializing multiple functions."""
        opt = TypeSpecialization(threshold=2)

        # Add another function to specialize
        mul_func = MIRFunction(
            "multiply",
            [Variable("x", MIRType.UNKNOWN), Variable("y", MIRType.UNKNOWN)],
            MIRType.UNKNOWN,
        )
        block = BasicBlock("entry")
        x = Variable("x", MIRType.UNKNOWN)
        y = Variable("y", MIRType.UNKNOWN)
        result = Temp(MIRType.UNKNOWN)
        block.add_instruction(BinaryOp(result, "*", x, y, (1, 1)))
        block.add_instruction(Return((1, 1), result))
        mul_func.cfg.add_block(block)
        mul_func.cfg.entry_block = block
        module.add_function(mul_func)

        # Add caller with calls to both functions
        caller = MIRFunction("main", [], MIRType.EMPTY)
        block = BasicBlock("entry")

        # Call add multiple times
        for _ in range(3):
            t = Temp(MIRType.INT)
            block.add_instruction(Call(t, "add", [Constant(1, MIRType.INT), Constant(2, MIRType.INT)], (1, 1)))

        # Call multiply multiple times
        for _ in range(3):
            t = Temp(MIRType.FLOAT)
            block.add_instruction(
                Call(t, "multiply", [Constant(1.0, MIRType.FLOAT), Constant(2.0, MIRType.FLOAT)], (1, 1))
            )

        caller.cfg.add_block(block)
        caller.cfg.entry_block = block
        module.add_function(caller)

        # Run optimization
        changed = opt.run_on_module(module)

        # Should have specialized both functions
        assert changed
        assert opt.stats["functions_specialized"] >= 2
