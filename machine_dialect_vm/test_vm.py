#!/usr/bin/env python3
"""Test the Rust VM Python bindings."""

import sys

# Try to import the Rust VM module
try:
    import machine_dialect_vm

    print("✓ Successfully imported machine_dialect_vm")
    # Version may not be available yet
    if hasattr(machine_dialect_vm, "__version__"):
        print(f"  Version: {machine_dialect_vm.__version__}")

    # Create a VM instance
    if hasattr(machine_dialect_vm, "RustVM"):
        vm = machine_dialect_vm.RustVM()
    else:
        print("✗ RustVM class not available (module not built yet?)")
        sys.exit(1)
    print("✓ Created RustVM instance")

    # Enable debug mode
    vm.set_debug(True)
    print("✓ Set debug mode")

    # Check instruction count
    count = vm.instruction_count()
    print(f"✓ Initial instruction count: {count}")

    print("\n✅ All basic tests passed!")

except ImportError as e:
    print(f"✗ Failed to import machine_dialect_vm: {e}")
    print("\nTo build the module:")
    print("  1. Install maturin: pip install maturin")
    print("  2. Build and install: maturin develop --features pyo3")
    sys.exit(1)

except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)
