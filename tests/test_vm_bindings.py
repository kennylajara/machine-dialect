#!/usr/bin/env python3
"""Test the Rust VM Python bindings."""

import pytest


def test_vm_import() -> None:
    """Test that we can import the VM module."""
    try:
        import machine_dialect_vm

        assert machine_dialect_vm is not None
    except ImportError:
        pytest.fail(
            "Failed to import machine_dialect_vm. The Rust VM module is not built.\n"
            "To build the module:\n"
            "  1. Install dev dependencies: uv sync --all-groups\n"
            "  2. Build the VM: ./build_vm.sh\n"
            "     (or manually: cd machine_dialect_vm && maturin develop --features pyo3)"
        )


def test_vm_creation() -> None:
    """Test that we can create a VM instance."""
    try:
        import machine_dialect_vm
    except ImportError:
        pytest.fail("machine_dialect_vm module not available - run './build_vm.sh' to build")

    if not hasattr(machine_dialect_vm, "RustVM"):
        pytest.fail("RustVM class not available in machine_dialect_vm module")

    vm = machine_dialect_vm.RustVM()
    assert vm is not None


def test_vm_debug_mode() -> None:
    """Test that we can set debug mode."""
    try:
        import machine_dialect_vm
    except ImportError:
        pytest.fail("machine_dialect_vm module not available - run './build_vm.sh' to build")

    if not hasattr(machine_dialect_vm, "RustVM"):
        pytest.fail("RustVM class not available in machine_dialect_vm module")

    vm = machine_dialect_vm.RustVM()
    vm.set_debug(True)
    # Just check it doesn't crash


def test_instruction_count() -> None:
    """Test that we can get instruction count."""
    try:
        import machine_dialect_vm
    except ImportError:
        pytest.fail("machine_dialect_vm module not available - run './build_vm.sh' to build")

    if not hasattr(machine_dialect_vm, "RustVM"):
        pytest.fail("RustVM class not available in machine_dialect_vm module")

    vm = machine_dialect_vm.RustVM()
    count = vm.instruction_count()
    assert count >= 0
